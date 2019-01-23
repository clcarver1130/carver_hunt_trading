import alpaca_trade_api as tradeapi
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
from logger import logging
import numpy as np

# Connect to the alpaca api and pull in the symbol list using helper_functions methods.
api = connect_paper_api(paper_key_id, paper_secret_key)
symbols = save_sp500_tickers()


def main.py():
    logging.info('Script running...')
    while True:


def calculate_metrics(symbols):
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

    # Convert to dict to df:
    return pd.DataFrame.from_dict(metric_dict, orient='index')

def calculate_orders(df):

    # Prioritze:
    df_sorted = df.sort_values(by='100_slope',ascending=False)

    # Check current positions:
    positions = [{x.symbol: {'current_price': float(x.current_price), 'lastday_price': float(x.lastday_price)}} for x in api.list_positions()]

    # Sell conditions:
    df_sorted['Sell'] = np.nan
    for i, stock in df_sorted.iterrows():
        # 1) If we own the stock 2) (3_ewma < 10_ewma OR current price has dropped 2% from lastday_price)
        if (i in positions[0]) and ((stock['3_ewma'] < stock['10_ewma']) or ((positions[0][i]['current_price']/positions[0][i]['lastday_price']) <= 0.98)):
            df_sorted.loc[i]['Sell'] = 1
        else:
            df_sorted.loc[i]['Sell'] = 0


    # Buy conditons:
    df_sorted['Buy'] = np.nan
    for i, stock in df_sorted.iterrows():
        #if closing price > 3 day avg and 3 day avg > 0 and 3 day avg > 10 day avg
        if (stock['current_price'] > stock['3_ewma']) and (stock['3_slope'] > 0) and (stock['3_ewma'] > stock['10_ewma']):
            df_sorted.loc[i]['Buy'] = 1
        else:
            df_sorted.loc[i]['Buy'] = 0

    return df_sorted
