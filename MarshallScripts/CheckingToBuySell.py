import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time

def doIBuy(stock_list):
    stock_list = stock_list.sort_values(by='100 day slope',ascending=False)
    stock_list.reset_index()

    for stock in stock_list.iterrows():
        #if closing price > 3 day avg and 3 day avg > 0 and 3 day avg > 10 day avg
        if stock[1][10] > stock[1][4] and  stock[1][4] > 0 and stock[1][4] > stock[1][7]:
            stock_list.loc[stock_list['Symbol'] == stock[1][0], 'Buy'] = 'Yes'
        else:
            stock_list.loc[stock_list['Symbol'] == stock[1][0], 'Buy'] = 'No'

    stock_list.to_csv('testing.csv')

    return stock_list


def checkCurrentPositions(positions, stock_list):
    for position in positions:
    #    stock = stock_list.loc[stock_list['Symbol'] == position[1,1]]
        print(stock)
        #if closing price > 3 day avg and 3 day avg > 0 and 3 day avg > 10 day avg
        #if stock[1][10] > stock[1][4] and  stock[1][4] > 0 and stock[1][4] > stock[1][7]:
        #    stock_list.loc[stock_list['Symbol'] == stock[1][0], 'Buy'] = 'Yes'
        #else:
        #    stock_list.loc[stock_list['Symbol'] == stock[1][0], 'Buy'] = 'No'


    return 0#positionStatus
