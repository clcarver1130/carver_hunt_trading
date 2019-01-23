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
    for sym in symbols:
        hist_close = pull_hist_data(api, sym, '200 days')[['close']] 
