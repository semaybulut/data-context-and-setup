# TO CONTENT CREATORS: MIRROR UPDATES OF THIS FILE INTO
# -`olist/seller.py`
# - `04-Logistic-Regression/Recap/seller_updated_solution.py`

import pandas as pd
import numpy as np
from olist.data import Olist
from olist.order import Order


class Seller:
    def __init__(self):
        # Import data only once
        olist = Olist()
        self.data = olist.get_data()
        self.order = Order()

    def get_seller_features(self):
        """
        Returns a DataFrame with:
        'seller_id', 'seller_city', 'seller_state'
        """
        sellers = self.data['sellers'].copy(
        )  # Make a copy before using inplace=True so as to avoid modifying self.data
        sellers.drop('seller_zip_code_prefix', axis=1, inplace=True)
        sellers.drop_duplicates(
            inplace=True)  # There can be multiple rows per seller
        return sellers

    def get_seller_delay_wait_time(self):
        """
        Returns a DataFrame with:
        'seller_id', 'delay_to_carrier', 'wait_time'
        """
        # Get data
        order_items = self.data['order_items'].copy()
        orders = self.data['orders'].query("order_status=='delivered'").copy()

        ship = order_items.merge(orders, on='order_id')

        # Handle datetime
        ship.loc[:, 'shipping_limit_date'] = pd.to_datetime(
            ship['shipping_limit_date'])
        ship.loc[:, 'order_delivered_carrier_date'] = pd.to_datetime(
            ship['order_delivered_carrier_date'])
        ship.loc[:, 'order_delivered_customer_date'] = pd.to_datetime(
            ship['order_delivered_customer_date'])
        ship.loc[:, 'order_purchase_timestamp'] = pd.to_datetime(
            ship['order_purchase_timestamp'])

        # Compute delay and wait_time
        def delay_to_logistic_partner(d):
            days = np.mean(
                (d.order_delivered_carrier_date - d.shipping_limit_date) /
                np.timedelta64(24, 'h'))
            if days > 0:
                return days
            else:
                return 0

        def order_wait_time(d):
            days = np.mean(
                (d.order_delivered_customer_date - d.order_purchase_timestamp)
                / np.timedelta64(24, 'h'))
            return days

        delay = ship.groupby('seller_id')\
                    .apply(delay_to_logistic_partner)\
                    .reset_index()
        delay.columns = ['seller_id', 'delay_to_carrier']

        wait = ship.groupby('seller_id')\
                   .apply(order_wait_time)\
                   .reset_index()
        wait.columns = ['seller_id', 'wait_time']

        df = delay.merge(wait, on='seller_id')

        return df

    def get_active_dates(self):
        """
        Returns a DataFrame with:
        'seller_id', 'date_first_sale', 'date_last_sale', 'months_on_olist'
        """
        # First, get only orders that are approved
        orders_approved = self.data['orders'][[
            'order_id', 'order_approved_at'
        ]].dropna()

        # Then, create a (orders <> sellers) join table because a seller can appear multiple times in the same order
        orders_sellers = orders_approved.merge(self.data['order_items'],
                                               on='order_id')[[
                                                   'order_id', 'seller_id',
                                                   'order_approved_at'
                                               ]].drop_duplicates()
        orders_sellers["order_approved_at"] = pd.to_datetime(
            orders_sellers["order_approved_at"])

        # Compute dates
        orders_sellers["date_first_sale"] = orders_sellers["order_approved_at"]
        orders_sellers["date_last_sale"] = orders_sellers["order_approved_at"]
        df = orders_sellers.groupby('seller_id').agg({
            "date_first_sale": "min",
            "date_last_sale": "max"
        })
        df['months_on_olist'] = round(
            (df['date_last_sale'] - df['date_first_sale']) /
            np.timedelta64(30, 'D'))
        return df

    def get_quantity(self):
        """
        Returns a DataFrame with:
        'seller_id', 'n_orders', 'quantity', 'quantity_per_order'
        """
        order_items = self.data['order_items']

        n_orders = order_items.groupby('seller_id')['order_id']\
            .nunique()\
            .reset_index()
        n_orders.columns = ['seller_id', 'n_orders']

        quantity = order_items.groupby('seller_id', as_index=False).agg(
            {'order_id': 'count'})
        quantity.columns = ['seller_id', 'quantity']

        result = n_orders.merge(quantity, on='seller_id')
        result['quantity_per_order'] = result['quantity'] / result['n_orders']
        return result

    def get_sales(self):
        """
        Returns a DataFrame with:
        'seller_id', 'sales'
        """
        return self.data['order_items'][['seller_id', 'price']]\
            .groupby('seller_id')\
            .sum()\
            .rename(columns={'price': 'sales'})


    def get_review_score(self):
        """
        Returns a DataFrame with:
        'seller_id', 'share_of_five_stars', 'share_of_one_stars', 'review_score', 'cost_of_reviews'
        """
        # 1. Gerekli ham verileri çekelim
        # order_items köprü görevi görür: hangi order hangi seller'ın?
        orders_reviews = self.data['order_reviews']
        order_items = self.data['order_items']

        # 2. Puanlar ile Satıcıları birleştirelim
        # Sadece ihtiyacımız olan sütunları alarak hafızayı yormayalım
        reviews_df = orders_reviews[['order_id', 'review_score']]
        items_df = order_items[['order_id', 'seller_id']]
        
        # Merge: Her yorumun yanına o ürünü satan satıcıyı ekledik
        df = items_df.merge(reviews_df, on='order_id')

        # 3. Yıldız oranları için yardımcı sütunlar (0 veya 1)
        df['is_one_star'] = df['review_score'].map(lambda x: 1 if x == 1 else 0)
        df['is_five_star'] = df['review_score'].map(lambda x: 1 if x == 5 else 0)
        
        # 4. Maliyet hesabı (1 ve 2 yıldız Olist'e pahalıya patlar)
        # 1 yıldız -> 100 BRL, 2 yıldız -> 50 BRL, diğerleri 0 BRL gibi modellenebilir 
        # (Şimdilik sadece varlığını işaretleyelim, gerçek rakamlar sonraki adımda gelecek)
        df['cost_of_reviews'] = df['review_score'].map({1: 100, 2: 50, 3: 40, 4: 0, 5: 0})

        # 5. Gruplayalım (Aggregation)
        # Her satıcı (seller_id) için ortalamaları alıyoruz
        result = df.groupby('seller_id').agg({
            'review_score': 'mean',
            'is_one_star': 'mean',
            'is_five_star': 'mean',
            'cost_of_reviews': 'sum' # Toplam maliyet
        }).reset_index()

        # Sütun isimlerini dokümantasyona uygun hale getirelim
        result.columns = ['seller_id', 'review_score', 'share_of_one_stars', 
                         'share_of_five_stars', 'cost_of_reviews']
        
        return result


    def get_training_data(self):
        # Tüm fonksiyonları sırayla çağırıp sonuçları değişkenlere ata
        features = self.get_seller_features()
        delay_wait = self.get_seller_delay_wait_time()
        active_dates = self.get_active_dates()
        quantity = self.get_quantity()
        sales = self.get_sales()
        reviews = self.get_review_score()

        # Tüm tabloları 'seller_id' üzerinden birbirine bağla (Chain merging)
        # Önce features ile başla, sonra diğerlerini ekle
        df = features.merge(delay_wait, on='seller_id', how='outer')\
                     .merge(active_dates, on='seller_id', how='outer')\
                     .merge(quantity, on='seller_id', how='outer')\
                     .merge(sales, on='seller_id', how='outer')\
                     .merge(reviews, on='seller_id', how='outer')
        
        # Gerekiyorsa yeni sütunlar ekle (revenues, profits vb.)
        # Şimdilik ana tabloyu döndürelim
        return df
