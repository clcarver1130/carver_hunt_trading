
class Strategy:

    # Create a strategy object - give it a name
    def __init__(self, name):
        self.name = name
        self.rules = []

    def add_rule(self, function):
        self.rules = function


    # Backtest strategy:
    def backtest(self, start_time, end_time):
        '''
        A backtesting method that allows you to quickly backtest a strategy in a user-passed time frame.

        Inputs:
        1. Start time in the format: 'YYYY-MM-DD'
        2. End time in the format: 'YYYY-MM-DD'

        Returns:
        A strategy report that includes a CSV of trades and prices during the testing period.
        '''
