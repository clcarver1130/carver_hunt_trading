import alpaca_trade_api as tradeapi
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
from logger import logging

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
        metric_dict[sym]['current_price'] = hist_close.iloc[-1]

    # Convert to dict to df:
    return pd.DataFrame.from_dict(metric_dict, orient='index')
