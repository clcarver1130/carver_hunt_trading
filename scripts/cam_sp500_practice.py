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
symbols = save_sp500_tickers()
max_positions = 5 # How many positions to hold at one time and will be used to determine how to split up cash.
api = connect_paper_api(paper_key_id, paper_secret_key)


def main():
    logging.info('Starting script...')


    schedule.every().monday.at("09:30").do(daily_trading, symbols)
    schedule.every().tuesday.at("09:30").do(daily_trading, symbols)
    schedule.every().wednesday.at("09:30").do(daily_trading, symbols)
    schedule.every().thursday.at("09:30").do(daily_trading, symbols)
    schedule.every().friday.at("09:30").do(daily_trading, symbols)
    schedule.every(11).minutes.do(during_day_check)

    while True:
        schedule.run_pending()
        time.sleep(1)

def daily_trading(symbols):
    todays_date = str(pd.Timestamp.today())[0:10]
    logging.info('Calculating metrics for {today}...'.format(today=todays_date))
    df = calculate_metrics(symbols)

    # Save dataframe as a report to the cloud
    save_report_s3(df)

    print('Top 5 stocks are: ')
    print(df.head())

    logging.info('Calculating and then executing any sell orders...')
    calculate_execute_sell_orders(df)

    logging.info('Letting all sell orders complete...')
    while len(api.list_orders()) > 0:
        time.sleep(2)

    logging.info('Calculating and then executing any buy orders...')
    calculate_execute_buy_orders(df)
    logging.info('{} morning script complete.'.format(todays_date))


def calculate_metrics(symbols):

    time.sleep(10)

    # Create 'metric_dict' dictionary to hold metrics. Will convert it ot a Dataframe at the end
    metric_dict = dict()
    for sym in symbols:
        hist_close = pull_hist_data(api, sym, '200 days')[['close', 'open']]
        metric_dict[sym] = {}

        # 100 Day Metrics:
        metric_dict[sym]['100_ewma'] =  hist_close.close[-100:].ewm(span=100).mean().iloc[-1]
        metric_dict[sym]['100_ewma_shifted'] = hist_close.close[-101:-1].ewm(span=100).mean().iloc[-1]
        metric_dict[sym]['100_slope'] = calculate_slope(metric_dict[sym]['100_ewma_shifted'], metric_dict[sym]['100_ewma'])

        # 10 Day Metrics:
        metric_dict[sym]['10_ewma'] =  hist_close.close[-10:].ewm(span=10).mean().iloc[-1]
        metric_dict[sym]['10_ewma_shifted'] = hist_close.close[-11:-1].ewm(span=10).mean().iloc[-1]
        metric_dict[sym]['10_slope'] = calculate_slope(metric_dict[sym]['10_ewma_shifted'], metric_dict[sym]['10_ewma'])

        # 3 Day Metrics:
        metric_dict[sym]['3_ewma'] =  hist_close.close[-3:].ewm(span=3).mean().iloc[-1]
        metric_dict[sym]['3_ewma_shifted'] = hist_close.close[-4:-1].ewm(span=3).mean().iloc[-1]
        metric_dict[sym]['3_slope'] = calculate_slope(metric_dict[sym]['3_ewma_shifted'], metric_dict[sym]['3_ewma'])

        # Other metrics:
        metric_dict[sym]['current_price'] = hist_close.close.iloc[-1]
        metric_dict[sym]['open_price'] = hist_close.open.iloc[-1]

        df = pd.DataFrame.from_dict(metric_dict, orient='index').sort_values(by='10_slope',ascending=False)

    # Sell conditions:
    positions = {p.symbol: p for p in api.list_positions()}
    df['Sell'] = np.nan
    for i, stock in df.iterrows():
        if i in positions.keys():
            # If [3_slope < 0] OR [(3_ewma < 10_ewma) OR (current price has dropped 2% from lastday_price)]
            if  ((stock['3_slope'] < 0) or (stock['3_ewma'] < stock['10_ewma']) or (float(positions[i].change_today) <= -0.02)):
                df.loc[i]['Sell'] = 1
            else:
                df.loc[i]['Sell'] = 0
        else:
            pass

    # Buy conditions:
    df['Buy'] = np.nan
    for i, stock in df.iterrows():
        #if 3 day slope > 0 AND 100 day slope > 0 AND 3 day avg > 10 day avg
        if (stock['3_slope'] > 0) and (stock['100_slope'] > 0) and (stock['3_ewma'] > stock['10_ewma']):
            df.loc[i]['Buy'] = 1
        else:
            df.loc[i]['Buy'] = 0

    # Convert to dict to df, sort by 100_slope, and return as a dataframe object:
    return df


def calculate_execute_sell_orders(df):
    # Check current positions:
    positions = {p.symbol: p for p in api.list_positions()}

    if len(positions) == 0:
        return
    else:
        # Filter for stocks to sell. Create orders:
        to_sell = df[df['Sell'] == 1].index.tolist()
        for sym in to_sell:
            stop_price = float(positions[sym].current_price) * .999
            make_order(api, 'sell', sym, positions[sym].qty, order_type='stop', stop_price=stop_price)
            logging.info('Attempting to sell {qty} shares of {sym} stock for {stop} each'.format(qty=positions[sym].qty, sym=sym, stop=stop_price))


def save_report_s3(df):
    conn = boto.connect_s3(AWSAccessKeyId, AWSSecretKey)
    bucket = conn.get_bucket('algotradingreports')

    todays_date = str(pd.Timestamp.today())[0:10]
    string_df = df.to_csv(None)

    file_df = bucket.new_key('reports/{today}_metrics_report.csv'.format(today=todays_date))
    file_df.set_contents_from_string(string_df)
    logging.info('{today} report saved to reports s3 bucket'.format(today=todays_date))


def calculate_execute_buy_orders(df):
    # Check max_positions
    if len(api.list_positions()) == max_positions:
        logging.info('Max positions reached. No buy orders triggered.')
        return
    else:
        # Check avaliable cash
        cash_on_hand = float(api.get_account().cash)

        # Filter for stocks to buy. Create orders. Qty of shares is based on cash_on_hand and max_positions
        to_buy = df[(df['Buy'] == 1)].index.tolist()
        for sym in to_buy:
            # If we've reached our max postions, stop making orders:
            if len(api.list_positions()) == max_positions:
                logging.info('Max positions reached. No buy orders triggered.')
                break
            else:
                # If we have enough cash for a share:
                if df.loc[sym]['current_price'] <= (cash_on_hand/max_positions):
                    # Calculate the number of shares we can hold with the current # of positions:
                    qty_to_buy = int((cash_on_hand/max_positions) / df.loc[sym]['current_price'])
                    # And make an order
                    limit_price = df.loc[sym]['current_price'] * 1.001
                    make_order(api, 'buy', sym, qty_to_buy, order_type='limit', limit_price=limit_price)
                    logging.info('Attempting to buy {qty} shares of {sym} stock for {limit}'.format(qty=qty_to_buy, sym=sym, limit=limit_price))
                    # Wait for current order to complete before starting a new order
                    while len(api.list_orders()) > 0:
                        time.sleep(2)
                else:
                    continue
        logging.info('Buy orders complete.')

def during_day_check():
    clock = api.get_clock()
    if clock.is_open:
        logging.info('{} price check...'.format(pd.Timestamp.now()))
        # Check current positions:
        positions = {p.symbol: p for p in api.list_positions()}

        # Check the price change of all current positons. Sell if it drops 2% or more
        if len(positions) == 0:
            pass
        else:
            position_symbol = set(positions.keys())
            for sym in position_symbol:
                if float(positions[sym].change_today) <= -0.02:
                    stop_price = float(positions[sym].current_price) * .999
                    make_order(api, 'sell', sym, positions[sym].qty, order_type='stop', stop_price=stop_price)
                    logging.info('Attempting to sell {qty} shares of {sym} stock for {stop} each'.format(qty=positions[sym].qty, sym=sym, stop=stop_price))
                    while len(api.list_orders()) > 0:
                        time.sleep(2)
                else:
                    continue

        time.sleep(5)
        positions = {p.symbol: p for p in api.list_positions()}
        if len(positions) < max_positions:
            # Pull today's metrics:
            conn = boto.connect_s3(AWSAccessKeyId, AWSSecretKey)
            bucket = conn.get_bucket('algotradingreports')
            todays_date = str(pd.Timestamp.today())[0:10]
            df = pd.read_csv('https://s3-us-west-2.amazonaws.com/algotradingreports/reports/{today}_metrics_report.csv'.format(today=todays_date))
            df = pd.read_csv('https://s3-us-west-2.amazonaws.com/algotradingreports/reports/{today}_metrics_report.csv'.format(today=todays_date), index_col='Unnamed: 0')
            calculate_execute_buy_orders(df)
        else:
            pass

        logging.info('Price check complete for {}.'.format(pd.Timestamp.now()))
    else:
        pass
        logging.info('Market closed.')

if __name__ == '__main__':
    main()
