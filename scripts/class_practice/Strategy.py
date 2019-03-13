import sys
sys.path.append('../')
import alpaca_trade_api as tradeapi
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
import numpy as np


class Strategy(object):
    """A class object that hold the entry and exit rules of a trading strategy """
    def __init__(self, strategy_name):
        self.name = strategy_name

    def add_metrics(self, calculate_metrics, symbols):
            self.data = calculate_metrics(symbols)
            return self.data

    def add_entry_exit_rules(self, rule):
        self.rules = rule

    # def backtest(start, stop, possible_symbols, ):
    #     api = connect_paper_api(paper_key_id, paper_secret_key)
