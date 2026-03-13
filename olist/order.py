import pandas as pd
import numpy as np
from olist.utils import haversine_distance
from olist.data import Olist



class Order:
    

    def __init__(self):
        # Olist().get_data() ile verileri çekiyoruz
        self.data = Olist().get_data()

    def get_wait_time(self, is_wait_time_outlier=False):
        # 1. Veriyi hazırla
        orders = self.data['orders'].copy()
        orders = orders[orders['order_status'] == 'delivered'].copy()
        
        # 2. Tarih dönüşümleri
        cols = ['order_purchase_timestamp', 'order_delivered_customer_date', 'order_estimated_delivery_date']
        for col in cols:
            orders[col] = pd.to_datetime(orders[col])
            
        # 3. Hesaplamalar
        orders['wait_time'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']) / np.timedelta64(1, 'D')
        orders['expected_wait_time'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']) / np.timedelta64(1, 'D')
        
        orders['delay_vs_expected'] = (orders['order_delivered_customer_date'] - orders['order_estimated_delivery_date']) / np.timedelta64(1, 'D')
        orders['delay_vs_expected'] = orders['delay_vs_expected'].clip(lower=0)
        
        # 4. İstenen DataFrame'i döndür
        return orders[['order_id', 'wait_time', 'expected_wait_time', 'delay_vs_expected', 'order_status']]


    def get_review_score(self):
        reviews = self.data['order_reviews'].copy()
        
        reviews['dim_is_five_star'] = reviews['review_score'].map(lambda x:1 if x==5 else 0)
        reviews['dim_is_one_star'] = reviews['review_score'].map(lambda x:1 if x==1 else 0)
        review_features = reviews[['order_id', 'dim_is_five_star', 'dim_is_one_star', 'review_score']]
        return review_features

    def get_number_items(self):
        """
        Returns a DataFrame with:
        order_id, number_of_items
        """
        pass  # YOUR CODE HERE

    def get_number_sellers(self):
        """
        Returns a DataFrame with:
        order_id, number_of_sellers
        """
        pass  # YOUR CODE HERE

    def get_price_and_freight(self):
        """
        Returns a DataFrame with:
        order_id, price, freight_value
        """
        pass  # YOUR CODE HERE

    # Optional
    def get_distance_seller_customer(self):
        """
        Returns a DataFrame with:
        order_id, distance_seller_customer
        """
        pass  # YOUR CODE HERE

    def get_training_data(self,
                          is_delivered=True,
                          with_distance_seller_customer=False):
        """
        Returns a clean DataFrame (without NaN), with the all following columns:
        ['order_id', 'wait_time', 'expected_wait_time', 'delay_vs_expected',
        'order_status', 'dim_is_five_star', 'dim_is_one_star', 'review_score',
        'number_of_items', 'number_of_sellers', 'price', 'freight_value',
        'distance_seller_customer']
        """
        # Hint: make sure to re-use your instance methods defined above
        pass  # YOUR CODE HERE
