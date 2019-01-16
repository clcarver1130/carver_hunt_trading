import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import HistoricalData

api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')

#overall trading strategy
#BUY CONDITION:
#               - 3 day moving avg above 10 day moving average
#               - 3 day moving avg slop positive
#
#SELL CONDITION
#               - 3 day moving avg slope negative
#                           OR
#               - 3 day moving avg drops below 10 day
#                           OR
#               - Lose of more than 5%
#PRIORITY CONDITION
#               - Sort by 200 day moving avg slope

def main():
    df = pd.read_csv('sp500_stocks.csv.csv')
    df = df.sort_values(by=['Symbol'])
    stock_list = df['Symbol']

    HistoricalData.last_200_days(stock_list)

    return

if __name__ == '__main__':
    main()
