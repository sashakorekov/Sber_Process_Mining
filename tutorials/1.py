from sberpm import DataHolder
import pandas as pd

path = 'example.csv'
data_holder = DataHolder(data=path, 
                         id_column='id', 
                         activity_column='stages', 
                         start_timestamp_column='dt', 
                         user_column='users', 
                         time_format='%Y-%m-%d')
