import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time

def doIBuy(stock_list):
    stock_list = stock_list.sort_values(by='100 day slope',ascending=False)
    stock_list.reset_index()

    stock_list.to_csv('testing.csv')

    print(stock_list)

    return 0
