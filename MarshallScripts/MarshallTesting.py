import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import BackTesting
import HelperFunctions
import schedule

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


#first 15 minutes of market open - check to see if stocks need sold. Protects against sudden price movements
#after first 15 minutes - normal loop can commence. Check to sell then check to buy

api = tradeapi.REST('PKS8S75FAGDSQ0W3RDT3', 'ZOzmy2F2dIyLuO0dNHAMumzByea/5o7eFmbQu/Qu', 'https://paper-api.alpaca.markets')
df = pd.DataFrame(HelperFunctions.save_sp500_tickers(), columns=['Symbol'])

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
df['Todays open'] = 0
df['Buy'] = '0'
df['Sell'] = '0'

target_positions = HelperFunctions.calc_target_positions(api)

def main():
    logging.info('Starting Up...')

    schedule.every().day.at("09:32").do(first_of_day_trades, api, df)
    schedule.every(10).minutes.do(during_day_check, api, df)

    while True:
        schedule.run_pending()
        time.sleep(1)


def first_of_day_trades(api, dataframe):
    clock =api.get_clock()
    if clock.is_open:
        global df
        df = dataframe

        logging.info('First Trades Starting...')

        #pulling historical data to calculate averages.
        df = HelperFunctions.stock_stats(api, df)

        #pull current positions to check to see if any need to be sold
        positions = api.list_positions()
        df = HelperFunctions.checkCurrentPositions(positions, df)

        #determine stocks to buy
        df = HelperFunctions.doIBuy(df)

        #if positions need sold, sell them
        to_sell = df[df['Sell'] == 'Yes']
        for sym in to_sell.iterrows():
            for position in positions:
                if position.symbol = sym[1][0]
                    HelperFunctions.make_order(api, 'sell', sym[1][0], position.qty, 'stop', (float(sym[1][10]) * float(.999)))

        #if number of stocks in portfolio is less than target, try to BUY
        number_of_positions = len(api.list_positions())
        positions_to_fill = target_positions - number_of_positions
        if number_of_positions < target_positions:
            df = HelperFunctions.buy_positions(api, df, target_positions)

    else:
        df.iloc[0:0]

def during_day_check(api, stock_list):
    clock =api.get_clock()
    if clock.is_open:
        logging.info('During Day Check...')
        global df
        df = stock_list

        if df['3 day avg'].iloc[0] == 0:
            first_of_day_trades(api, df)

        positions = {p.symbol: p for p in api.list_positions()}
        position_symbol = set(positions.keys())

        for sym in position_symbol:
            stock = df.loc[df['Symbol'] == sym]

            if float(positions[sym].current_price)/float(stock['Todays open']) <= 0.98:
                HelperFunctions.make_order(api, 'sell', sym, positions[sym].qty, 'stop', (float(positions[sym].current_price) * float(.999)))
            else:
                pass

        #If any stocks sold, new stocks need bought
        number_of_positions = len(positions)
        if number_of_positions < target_positions:
            df = HelperFunctions.buy_positions(api, df, target_positions)
    else:
        logging.info('Markets Closed...')
        df.iloc[0:0]

if __name__ == '__main__':
    main()
