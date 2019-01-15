import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time

api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')
symbol = 'AAPL'
max_shares = 100

def main():
    api.submit_order(
        symbol=symbol,
        qty=max_shares,
        side='buy',
        type='market',
        time_in_force='day'
        )

if __name__ == '__main__':
    main()
