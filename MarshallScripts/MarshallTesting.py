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

api = tradeapi.REST('PKTAXGJQG57RUH6E13WI', 'PKPg6zuoYzq1kLmO97rIfzKTrOFn3oySCmyNBpyk', 'https://paper-api.alpaca.markets')

def main():
    logging.info('Starting Up...')
    while True:
        logging.info('Starting Loop...')

#-------------------------testing---------------------------
        df = pd.DataFrame(HelperFunctions.save_sp500_tickers(), columns=['Symbol'])
        hist_data =HelperFunctions.stock_stats(api, df)
        positions = [{x.symbol: {'current_price': float(x.current_price), 'lastday_price': float(x.lastday_price), 'qty': int(x.qty)}} for x in api.list_positions()]
        #positions = api.list_positions()
        stock_list_with_positions = HelperFunctions.checkCurrentPositions(positions, hist_data)
        stock_list_updated = HelperFunctions.doIBuy(stock_list_with_positions)
        to_sell = stock_list_updated[stock_list_updated['Sell'] == 'Yes']
        print(to_sell)
        print(positions)
        for sym in to_sell.iterrows():
            position = positions[0] == sym[1][0]
            print(position)
#-------------------------end testing-----------------------

        clock = api.get_clock()
        while clock.is_open:
            counter = 1
            if counter == 1:
                logging.info('Markets Open, beginning to trade...')
                df = pd.DataFrame(HelperFunctions.save_sp500_tickers(), columns=['Symbol'])
                counter += 1
            schedule.every().day.at("09:32").do(first_of_day_trades(df))
            schedule.every(10).minutes.do(during_day_check)

    return

def first_of_day_trades(df):
    logging.info('First Trades Starting...')
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

    #pulling historical data to calculate averages.
    hist_data =HelperFunctions.stock_stats(api, df)

    #pull current positions to check to see if any need to be sold
    positions = api.list_positions() #[{x.symbol: {'current_price': float(x.current_price), 'lastday_price': float(x.lastday_price), 'qty': int(x.qty)}} for x in api.list_positions()]
    stock_list_with_positions = HelperFunctions.checkCurrentPositions(positions, hist_data)

    #determine stocks to buy
    stock_list_updated = HelperFunctions.doIBuy(stock_list_with_positions)

    #if positions need sold, sell them
    to_sell = stock_list_updated[stock_list_updated['Sell'] == 'Yes']
    print(to_sell)
    print(positions)
    for sym in to_sell.iterrows():
        position = positions.index(sym[1][0])
        #logging.info('Trying to sell {qty_to_buy} shares of {sym} stock'.format(qty_to_buy=qty_to_buy, sym=stock[1][0]))
        HelperFunctions.make_order(api, 'sell', sym[1][0], position.qty, 'stop', (sym[1][10] * .999))

    #if number of stocks in portfolio is less than target, try to BUY
    number_of_positions = len(api.list_positions())
    positions_to_fill = 5 - number_of_positions
    if number_of_positions < 5:
        cash_on_hand = float(api.get_account().cash)
        potential_stocks_to_buys = stock_list_updated[(stock_list_updated['Buy'] == 'Yes') & (stock_list_updated['Sell'] == '0')]
        potential_stocks_to_buy = potential_stocks_to_buys.sort_values(by='100 day slope',ascending=False)
        for stock in potential_stocks_to_buy.iterrows():
            if stock[1][10] <= (cash_on_hand/positions_to_fill) and number_of_positions < 5:
                qty_to_buy = int((cash_on_hand/positions_to_fill)/(stock[1][10] * 1.001))
                logging.info('Trying to buy {qty_to_buy} shares of {sym} stock'.format(qty_to_buy=qty_to_buy, sym=stock[1][0]))
                HelperFunctions.make_order(api, 'buy', stock[1][0], qty_to_buy, 'limit', (stock[1][10] * 1.001))
                number_of_positions += 1
                positions_to_fill += -1
                cash_on_hand = float(api.get_account().cash)
            else:
                continue

def during_day_check():
    positions = {p.symbol: p for p in api.list_positions()}
    position_symbol = set(positions.keys())

    #this will need updated to pull the open price for the day instead of the close price from yesterday
    for sym in position_symbol:
        if float(positions[sym].current_price)/float(positions[sym].lastday_price) <= 0.98:
            HelperFunctions.make_order(api, 'sell', sym, positions[sym].qty)
        else:
            pass

if __name__ == '__main__':
    main()
