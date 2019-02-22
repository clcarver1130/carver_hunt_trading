import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import BackTesting
import HelperFunctions
import schedule

api = tradeapi.REST('AKLCHJW2WVMZFTVETW9Y', 'Mk7h3DNLHJEmzY6wW0noYRqdeAbPEl4nGCvK3dcY', 'https://api.alpaca.markets')

df = pd.DataFrame(HelperFunctions.save_sp500_tickers(), columns=['Symbol'])

#creating columns to help track averages. This is part of the current strategy to test.
df['50 day avg'] = 0
df['50 day avg offset'] = 0
df['50 day slope'] = 0
df['5 day avg'] = 0
df['5 day avg offset'] = 0
df['5 day slope'] = 0
df['10 day avg'] = 0
df['10 day avg offset'] = 0
df['10 day slope'] = 0
df['Todays close'] = 0
df['Todays open'] = 0
df['Buy'] = '0'
df['Sell'] = '0'

def main():
    HelperFunctions.buy_with_excess_cash(api)
    logging.info('Starting Up...')

    schedule.every().day.at("09:31").do(first_of_day_trades, api, df)
    schedule.every(5).minutes.do(during_day_check, api, df)

    while True:
        schedule.run_pending()
        time.sleep(1)


def first_of_day_trades(api, dataframe):
    clock =api.get_clock()
    target_positions = HelperFunctions.calc_target_positions(api)

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

        #if positions need sold, sell them. Check for any pending sell orders first.
        to_sell = df[df['Sell'] == 'Yes']
        pending_orders = api.list_orders()

        #if there is a pending sell order, remove it from list of stocks to sell
        for order in pending_orders:
            if(order.side=='sell'):
                to_sell = to_sell.drop(to_sell.loc[to_sell['Symbol'] ==order.symbol].index, axis=0)

        #need to add a wait in here, if an order is pending then wait to finish so that it will buy on time
        for sym in to_sell.iterrows():
            for position in positions:
                if position.symbol == sym[1][0]:
                    #5% buffer added to limit price to help make sure it executes. The best price possible is used to fulfill
                    stop_price = (float(sym[1][10]) * .95)
                    logging.info('Trying to sell {qty_to_sell} shares of {sym} stock for {price}'.format(qty_to_sell=position.qty, sym=sym[1][0],price=stop_price))
                    HelperFunctions.make_order(api, 'sell', sym[1][0], position.qty, order_type='limit',limit_price=stop_price)

        #wait for orders to fill before trying to see if more stocks need bought
        while len(api.list_orders()) > 0:
            logging.info('Orders pending.... waiting....')
            time.sleep(2)

        #if number of stocks in portfolio is less than target, try to BUY
        number_of_positions = len(api.list_positions())
        positions_to_fill = target_positions - number_of_positions
        if number_of_positions < target_positions:
            df = HelperFunctions.buy_positions(api, df, target_positions)

        #wait for buy orders to complete
        while len(api.list_orders()) > 0:
            logging.info('Orders pending.... waiting....')
            time.sleep(2)

        #if there is excess cash, try to use it in the market instead of it being idle
        HelperFunctions.buy_with_excess_cash(api)

    else:
        df.iloc[0:0]

def during_day_check(api, stock_list):
    clock =api.get_clock()
    target_positions = HelperFunctions.calc_target_positions(api)

    if clock.is_open:
        logging.info('During Day Check...')
        global df
        df = stock_list

        if df['5 day avg'].iloc[0] == 0:
            first_of_day_trades(api, df)

        positions = api.list_positions()

        for position in positions:
            stock = df.loc[df['Symbol'] == position.symbol]
            max_price_loss = -.02
            if ((float(position.current_price) - float(stock['Todays open']))/float(stock['Todays open'])) <= max_price_loss:
                stop_price = float(position.current_price) * .95
                logging.info('Trying to sell {qty_to_sell} shares of {sym} stock for {price}'.format(qty_to_sell=position.qty, sym=position.symbol,price=stop_price))
                HelperFunctions.make_order(api, 'sell', position.symbol, position.qty, order_type='limit', limit_price=stop_price)
            else:
                pass

        while len(api.list_orders()) > 0:
            logging.info('Orders pending.... waiting....')
            time.sleep(2)

        positions = api.list_positions()
        #If any stocks sold, new stocks need bought
        number_of_positions = len(positions)
        if number_of_positions < target_positions:
            df = HelperFunctions.buy_positions(api, df, target_positions)
    else:
        logging.info('Markets Closed...')
        df.iloc[0:0]

if __name__ == '__main__':
    main()
