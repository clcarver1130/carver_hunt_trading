import alpaca_trade_api as tradeapi
from cam_paper_keys import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time

api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')
symbol = 'AAPL'
max_shares = 100

def main():
    done = None
    logging.info('start running')
    while True:
        # clock API returns the server time including
        # the boolean flag for market open
        clock = api.get_clock()
        now = clock.timestamp
        if clock.is_open and done != now.strftime('%H-%M'):

            df_hist = pull_hist_data(symbol)
            order_status = calculate_order_status(df_hist)
            make_orders(order_status)

        # flag it as done so it doesn't work again for the day
            done = now.strftime('%H:%M')
            logging.info(f'done for {done}')

def pull_hist_data(symbol):
    now = pd.Timestamp.now(tz='US/Eastern')
    end_dt = now
    start_dt = end_dt - pd.Timedelta('6 hours')

    return api.polygon.historic_agg(
            'minute', symbol, _from=start_dt, to=end_dt).df

def calculate_order_status(hist_data):
    ema_50 = hist_data.close.ewm(span=50).mean().mean()
    ema_200 = hist_data.close.ewm(span=200).mean().mean()
    status = None
    if ema_50 >= ema_200:
        status = 'buy'
    else:
        status = 'sell'

    if (len(api.list_positions()) > 0) & (status == 'sell'):
        return 'sell'
    elif (len(api.list_positions()) == 0) & (status == 'buy'):
        return 'buy'
    else:
        return 'pass'

def make_orders(status):
    # If we own Apple stock and we should sell...
    if status == 'sell':
        logging.info(f'selling {max_shares} shares')
        api.submit_order(
            symbol=symbol,
            qty=max_shares,
            side='sell',
            type='market',
            time_in_force='day'
            )

    # If we don't own Apple stock and we should buy...
    elif status == 'buy':
        logging.info(f'selling {max_shares} shares')
        api.submit_order(
            symbol=symbol,
            qty=max_shares,
            side='buy',
            type='market',
            time_in_force='day'
            )
    else:
        logging.info('Pass')
        pass

if __name__ == '__main__':
    main()
