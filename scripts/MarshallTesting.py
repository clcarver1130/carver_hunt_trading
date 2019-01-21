import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import HistoricalData
import CheckingToBuy

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
#               - Sort by 50 day moving avg slope

def main():

    #pull in list of stocks to consider for buying. Currently just the S&P 500
    #this eventually needs a function to make sure all stocks are valid incase companies merge
    #because then the symbol would no longer be valid and throw an error.
    df = pd.read_csv('data/sp500_stocks.csv.csv')
    df = df.sort_values(by=['Symbol'])
    df.reset_index()

    #creating columns to help track averages. This is part of the current strategy to test.
    df['100 day avg'] = 0
    df['100 day avg offset'] = 0
    df['100 day slope'] = 0
    df['3 day avg'] = 0
    df['3 day avg offset'] = 0
    df['3 day slope'] = 0
    df['10 day avg'] = 0
    df['10 day avg offset'] = 0
    df['10 day slope'] = 0
    df['Todays close'] = 0


    #pulling historical data to calculate averages.
    hist_data = HistoricalData.last_200_days(df)

    #determine stocks to buy
    stocks_to_buy = CheckingToBuy.doIBuy(hist_data)

    return

if __name__ == '__main__':
    main()
