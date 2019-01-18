import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import HistoricalData

api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')

#overall trading strategy
#BUY CONDITION:
#               - 3 day moving avg (ohlc/4 exp) above 10 day moving average
#               - 3 day moving avg (ohlc/4 exp) slope positive
#
#SELL CONDITION
#               - 3 day moving avg (ohlc/4 exp) slope negative
#                           OR
#               - 3 day moving avg (ohlc/4 exp) drops below 10 day
#                           OR
#               - Loss of more than 2% off highest price for day
#PRIORITY CONDITION
#               - Sort by 200 day moving avg slope

def main():
    df = pd.read_csv('data/sp500_stocks.csv.csv')
    df = df.sort_values(by=['Symbol'])
    df.reset_index()
    df['200 day avg'] = 0
    df['3 day ema'] = 0
    df['10 day avg'] = 0

    df[df['Symbol']=='AAPL']

    #hist_data = HistoricalData.last_200_days(df)

    print(hist_data)

    return

if __name__ == '__main__':
    main()
