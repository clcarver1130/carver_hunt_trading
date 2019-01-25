import alpaca_trade_api as tradeapi
import pandas as pd
import bs4 as bs
import requests

def connect_paper_api(paper_key_id, paper_secret_key):

    '''Connects to the paper trading api

    INPUT:
    paper_key_id: str, key_id from your paper alapaca account
    paper_secert_key: str, secret_key from your paper alapaca account

    OUTPUT:
    Returns an alpaca_trade_api object
     '''


    api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')
    return api

def save_sp500_tickers():

    '''Pulls the S&P500 Ticker symbols straight from Wikipeida's 'List of S&P500 Companies' that is updated regularly.

    OUTPUT:
    An array with all 500 ticker symbols'''

    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)
    tickers = [x.replace('-', '.') for x in tickers]
    return tickers

def pull_hist_data(api, symbol, start_, days=True, end_='now', agg='day', tz='US/Eastern'):

    '''Pulls historical stock data by day or minute from the Polygon API. Must be connected to the alpaca api.

    Input:
    api: object, The api alpaca object that you created when you connected
    symbol: str, The string of the stock symbol you want to pull
    days: bool, The days parameter determines how you input the 'start_' parameter. If days is True, the input of the start time will be how many days in the past you want to pull. If it is False you must specify the exact date in which to start.
    start_dt: str, The number of days or the datetime you want the historical data to begin. Format: 'YYYY-MM-DD' or ' ### days'
    end_dt: str, the date/date you want the historical data to end. Defaults to 'now' if you want to pull up to the current data.
    agg: str, How you want the data to aggregate. Options are 'day' or 'minute'.
    tz: str, The timezone you want the end_dt to end in. Defaults to 'US/Eastern' which most exchanges are in.

    Output:
    Returns a pandas dataframe of the historical data with open, close, high, and low price points'''

    # Specify end_dt
    if end_ == 'now':
        end_dt = pd.Timestamp.now(tz=tz)
    else:
        end_dt = end_dt

    # Specify start_dt
    if days == True:
        start_dt = end_dt - pd.Timedelta(start_)
    else:
        start_dt = start_

    return api.polygon.historic_agg(size=agg, symbol=symbol, _from=start_dt, to=end_dt).df

def calculate_slope(y_old, y_new):
    return (y_new - y_old) / y_old

def make_order(api, status, sym, qty, order_type='market', off_set=0.005):
    '''
    Sends an order to the alpaca API

    INPUT:
    api: object, The api alpaca object that you created when you connected
    status: str, buy, sell, or pass
    symbol: str, The string of the stock symbol you want to place an order in
    qty: int, the # of shares to buy or sell
    type: str, the type of order. Market, limit, or stop order. If limit or stop must specify the limit_price or stop_price
    '''
    if status == 'sell':
        positions = {p.symbol: p for p in api.list_positions()}
        current_price = positions[sym].current_price
        stop_price = float(current_price) * (1-off_set)
    elif status == 'buy':
        current_price = pull_hist_data(api, sym, pd.Timestamp.now(), agg='minute', days='1 days')['close'][-1]
        limit_price = float(current_price) * (1+off_set)
    else:
        raise ValueError('Not a valid status. Must be buy or sell')

    if order_type == 'market':
        api.submit_order(
            symbol=sym,
            qty=qty,
            side=status,
            type='market',
            time_in_force='day',
            )

    elif order_type == 'stop':
        api.submit_order(
            symbol=sym,
            qty=qty,
            side=status,
            type='stop',
            time_in_force='day',
            stop_price=stop_price
            )

    elif order_type == 'limit':
        api.submit_order(
            symbol=sym,
            qty=qty,
            side=status,
            type='limit',
            time_in_force='day',
            limit_price=limit_price
            )
    else:
        raise ValueError('Not a valid order_type. Must be market, stop, or limit')
