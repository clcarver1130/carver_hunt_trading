import alpaca_trade_api as tradeapi
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
import numpy as np
from logger import logging
import boto
import schedule
import time

# Connect to the alpaca api and pull in the symbol list using helper_functions methods.
api = connect_paper_api(paper_key_id, paper_secret_key)
symbols = save_sp500_tickers()
max_positions = 3 # How many positions to hold at one time and will be used to determine how to split up cash.


def main():
    logging.info('Trading is live...')

    clock = api.get_clock()
    if clock.is_open:
        schedule.every().day.at("09:35").do(daily_trading(symbols))
        schedule.every(15).minutes.do(during_day_check)
    else:
        pass

    while True:
        schedule.run_pending()
        time.sleep(1)

def daily_trading(symbols):
    logging.info('Calculating metrics...')
    df = calculate_metrics(symbols)

    print('Top 5 stocks are: ')
    print(df.head())

    logging.info('Calculating and then executing sell orders...')
    calculate_execute_sell_orders(df)

    logging.info('Sell orders pending...')
    time.sleep(20)

    logging.info('Calculating and then executing buy orders...')
    calculate_execute_buy_orders(df)
    logging.info('Morning script complete.')


def calculate_metrics(symbols):

    # Create 'metric_dict' dictionary to hold metrics. Will convert it ot a Dataframe at the end
    metric_dict = dict()
    for sym in symbols:
        hist_close = pull_hist_data(api, sym, '200 days')[['close']]
        metric_dict[sym] = {}

        # 100 Day Metrics:
        metric_dict[sym]['100_ewma'] =  hist_close[-100:].ewm(span=100).mean().iloc[-1][0]
        metric_dict[sym]['100_ewma_shited'] = hist_close[-101:-1].ewm(span=100).mean().iloc[-1][0]
        metric_dict[sym]['100_slope'] = calculate_slope(metric_dict[sym]['100_ewma_shited'], metric_dict[sym]['100_ewma'])

        # 10 Day Metrics:
        metric_dict[sym]['10_ewma'] =  hist_close[-10:].ewm(span=10).mean().iloc[-1][0]
        metric_dict[sym]['10_ewma_shited'] = hist_close[-11:-1].ewm(span=10).mean().iloc[-1][0]
        metric_dict[sym]['10_slope'] = calculate_slope(metric_dict[sym]['10_ewma_shited'], metric_dict[sym]['10_ewma'])

        # 3 Day Metrics:
        metric_dict[sym]['3_ewma'] =  hist_close[-3:].ewm(span=3).mean().iloc[-1][0]
        metric_dict[sym]['3_ewma_shited'] = hist_close[-4:-1].ewm(span=3).mean().iloc[-1][0]
        metric_dict[sym]['3_slope'] = calculate_slope(metric_dict[sym]['3_ewma_shited'], metric_dict[sym]['3_ewma'])

        # Other metrics:
        metric_dict[sym]['current_price'] = hist_close.iloc[-1][0]

    # Convert to dict to df, sort by 100_slope, and return as a dataframe object:
    return pd.DataFrame.from_dict(metric_dict, orient='index').sort_values(by='100_slope',ascending=False)


def calculate_execute_sell_orders(df):

    # Check current positions:
    positions = [{x.symbol: {'current_price': float(x.current_price), 'lastday_price': float(x.lastday_price), 'qty': int(x.qty)}} for x in api.list_positions()]

    if len(positions) == 0:
        pass
    else: # Sell conditions:
        df['Sell'] = np.nan
        for i, stock in df.iterrows():
            # If we own the stock AND [(3_ewma < 10_ewma) OR (current price has dropped 2% from lastday_price)]
            if (i in positions[0]) and ((stock['3_ewma'] < stock['10_ewma']) or ((positions[0][i]['current_price']/positions[0][i]['lastday_price']) <= 0.98)):
                df.loc[i]['Sell'] = 1
            else:
                df.loc[i]['Sell'] = 0

        # Filter for stocks to sell. Create orders:
        to_sell = df[df['Sell'] == 1].index.tolist()
        for sym in to_sell:
            make_order(api, 'sell', sym, positions[0][sym]['qty'], order_type='market')
            logging.info('Sold {qty} shares of {sym} stock'.format(qty=positions[0][sym]['qty'], sym=sym))

def save_report_s3(df):

    conn = boto.connect_s3(AWSAccessKeyId, AWSSecretKey)
    bucket = conn.get_bucket('algotradingreports')

    string_df = df.to_csv(None)
    todays_date = str(pd.Timestamp.date())[0:10]

    file_df = bucket.new_key('reports/{today}_metrics_report.csv'.format(today=todays_date))
    file_df.set_contents_from_string(string_df)
    logging.info('{today} report saved to data s3 bucket'.format(today=todays_date))

def calculate_execute_buy_orders(df):

    # Buy conditons:
    df['Buy'] = np.nan
    for i, stock in df.iterrows():
        #if closing price > 3 day avg and 3 day avg > 0 and 3 day avg > 10 day avg
        if (stock['current_price'] > stock['3_ewma']) and (stock['3_slope'] > 0) and (stock['3_ewma'] > stock['10_ewma']):
            df.loc[i]['Buy'] = 1
        else:
            df.loc[i]['Buy'] = 0

    # Check avaliable cash:
    cash_on_hand = float(api.get_account().cash)

    # Filter for stocks to buy. Create orders. Qty of shares is based on cash_on_hand and max_positions
    to_buy = df[(df['Buy'] == 1)].index.tolist()
    for sym in to_buy:
        if df.loc[sym]['current_price'] <= (cash_on_hand/max_positions):
            qty_to_buy = int((cash_on_hand/max_positions) / df.loc[sym]['current_price'])
            make_order(api, 'buy', sym, qty_to_buy, order_type='market')
            logging.info('Bought {qty} shares of {sym} stock'.format(qty=qty_to_buy, sym=sym))
            if len(api.list_positions()) >= max_positions:
                break
            else:
                continue
        else:
            continue

    # After orders are calculated, save a report to s3
    save_report_s3(df)

def during_day_check():

    logging.info('15 min check...')
    # Check current positions:
    positions = {p.symbol: p for p in api.list_positions()}

    if len(positions) == 0:
        pass
    else:
        position_symbol = set(positions.keys())
        for sym in position_symbol:
            if float(positions[sym].current_price)/float(positions[sym].lastday_price) <= 0.98:
                make_order(api, 'sell', sym, positions[sym].qty, order_type='market')
                logging.info('Sold {qty} shares of {sym} stock'.format(qty=positions[sym].qty, sym=sym))
            else:
                pass


if __name__ == '__main__':
    main()
