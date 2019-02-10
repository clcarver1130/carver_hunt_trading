import alpaca_trade_api as tradeapi
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
import numpy as np
from logger import logging
import boto
import schedule
import time

# Set up parameters
max_positions = 1
max_intraday_trades = 3

# Connect to the alpaca api
api = connect_paper_api(paper_key_id, paper_secret_key)
symbols = save_sp500_tickers()

# Pull in historical data and calculate metrics
def calculate_metrics(symbols):
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
