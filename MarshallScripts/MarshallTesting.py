import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import BackTesting
import HelperFunctions
import schedule

api = tradeapi.REST('PKS8S75FAGDSQ0W3RDT3', 'ZOzmy2F2dIyLuO0dNHAMumzByea/5o7eFmbQu/Qu', 'https://paper-api.alpaca.markets')

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
        positions = {p.symbol: p for p in api.list_positions()}
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
                    HelperFunctions.make_order(api, 'sell', sym[1][0], position.qty, order_type='stop',stop_price=stop_price)

        #wait for orders to fill before trying to see if more stocks need bought
        while len(api.list_orders()) > 0:
            time.sleep(2)

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

        if df['5 day avg'].iloc[0] == 0:
            first_of_day_trades(api, df)

        positions = {p.symbol: p for p in api.list_positions()}
        position_symbol = set(positions.keys())

        for sym in position_symbol:
            stock = df.loc[df['Symbol'] == sym]
            max_price_loss = -.02
            if ((stock['Todays open'].iloc[0] - stock['Todays close'].iloc[0])/stock['Todays open'].iloc[0]) <= max_price_loss:
                stop_price = float(positions[sym].current_price) * .95
                logging.info('Trying to sell {qty_to_sell} shares of {sym} stock for {price}'.format(qty_to_sell=positions[sym].qty, sym=sym,price=stop_price))
                HelperFunctions.make_order(api, 'sell', sym, positions[sym].qty, order_type='stop', stop_price=stop_price)
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
