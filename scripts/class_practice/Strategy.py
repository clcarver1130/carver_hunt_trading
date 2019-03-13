import sys
sys.path.append('../')
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
import numpy as np


class Strategy(object):
    """A class object that hold the entry and exit rules of a trading strategy """
    def __init__(self, strategy_name):
        self.name = strategy_name

    def add_rules(self, rule):
        self.rules = rule
