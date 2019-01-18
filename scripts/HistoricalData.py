import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time

api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')

def last_200_days(stock_list):
    now = pd.Timestamp.now(tz='US/Eastern')
    end_dt = now
    start_dt = end_dt - pd.Timedelta('200 days')

    print(stock_list.loc[['A']].index.name)

    #for stock in stock_list.iterrows():
    #    aggs = api.polygon.historic_agg(
    #            'day', stock['Symbol'], _from=start_dt, to=end_dt).df
        #print(aggs)

    return aggs
