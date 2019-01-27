<<<<<<< HEAD
import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import requests
import bs4 as bs

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


def stock_stats(api, stock_list):
    now = pd.Timestamp.now(tz='US/Eastern')
    now_no_tz = pd.Timestamp.now()
    end_dt = now

    #this is imprecise, but easily accounts for any holidays and weekends.
    start_dt = end_dt - pd.Timedelta('200 days')

    #pulling historical data: open, close, high, low, volumne, date.
    hist_data = api.polygon.historic_agg(
                'day', stock_list['Symbol'][1], _from=start_dt, to=end_dt).df

    #creating date offset to see how far back each day is from current.
    hist_data['DaysInPast'] = (hist_data.index.to_series().dt.date - now_no_tz.date()).dt.days

    #for each stock it must calculate the averages and then add them back to the main stock list.
    for i , stock in stock_list.iterrows():
        hist_data = api.polygon.historic_agg(
                'day', stock[0], _from=start_dt, to=end_dt).df

        hist_data['3 day avg'] = hist_data['close'].rolling(3).mean()
        hist_data['3 day avg offset'] = hist_data['close'].rolling(3).mean().shift(1)
        hist_data['3 day slope'] = (hist_data['3 day avg'] - hist_data['3 day avg offset'])/hist_data['3 day avg offset']
        hist_data['10 day avg'] = hist_data['close'].rolling(10).mean()
        hist_data['10 day avg offset'] = hist_data['close'].rolling(10).mean().shift(1)
        hist_data['10 day slope'] = (hist_data['10 day avg'] - hist_data['10 day avg offset'])/hist_data['10 day avg offset']
        hist_data['100 day avg'] = hist_data['close'].rolling(100).mean()
        hist_data['100 day avg offset'] = hist_data['close'].rolling(100).mean().shift(1)
        hist_data['100 day slope'] = (hist_data['100 day avg'] - hist_data['100 day avg offset'])/hist_data['100 day avg offset']
        stock_list.loc[stock_list['Symbol'] == stock[0], '3 day avg'] = hist_data['3 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '3 day avg offset'] = hist_data['3 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '3 day slope'] = hist_data['3 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '10 day avg'] = hist_data['10 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '10 day avg offset'] = hist_data['10 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '10 day slope'] = hist_data['10 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '100 day avg'] = hist_data['100 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '100 day avg offset'] = hist_data['100 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '100 day slope'] = hist_data['100 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], 'Todays close'] = hist_data['close'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], 'Todays open'] = hist_data['open'].iloc[-1]

    return stock_list


def doIBuy(stock_list):
    stock_list = stock_list.sort_values(by='100 day slope',ascending=False)
    stock_list.reset_index()

    for i,stock in stock_list.iterrows():
        #if 3 day avg > 0 and 3 day avg > 10 day avg
        if stock[4] > 0 and stock[4] > stock[7]:
            stock_list.loc[stock_list['Symbol'] == stock[0], 'Buy'] = 'Yes'
        else:
            stock_list.loc[stock_list['Symbol'] == stock[0], 'Buy'] = 'No'

    stock_list.to_csv('testing.csv')

    return stock_list


def checkCurrentPositions(positions, stock_list):
    sellingThreshold = -.02

    for position in positions:
        stocks = stock_list.loc[stock_list['Symbol'] == position.symbol]
        for i, stock in stocks.iterrows():
        #if 3 day avg < 0 or close(current) price >= 2% drop from open
            if (stock['3 day avg'] < 0) or (((stock['Todays close'] - stock['Todays open'])/stock['Todays open']) <= sellingThreshold):
                stock_list.loc[stock_list['Symbol'] == stock[0], 'Sell'] = 'Yes'
            else:
                stock_list.loc[stock_list['Symbol'] == stock[0], 'Sell'] = 'No'

    stock_list.to_csv('testing.csv')

    return stock_list


def make_order(api, status, symbol, qty, order_type='market', limit_price=None, stop_price=None):
    '''
    Sends an order to the alpaca API
    INPUT:
    api: object, The api alpaca object that you created when you connected
    status: str, buy, sell, or pass
    symbol: str, The string of the stock symbol you want to place an order in
    qty: int, the # of shares to buy or sell
    type: str, the type of order. Market, limit, or stop order. If limit or stop must specify the limit_price or stop_price
    '''
    api.submit_order(
        symbol=symbol,
        qty=qty,
        side=status,
        type=order_type,
        time_in_force='day',
        limit_price=limit_price,
        stop_price=stop_price
        )

    return

def buy_positions(api, stock_list, target_positions):
    number_of_positions = len(api.list_positions())
    positions_to_fill = target_positions - number_of_positions
    if number_of_positions < target_positions:
        cash_on_hand = float(api.get_account().cash)
        potential_stocks_to_buys = stock_list[(stock_list['Buy'] == 'Yes') & (stock_list['Sell'] == '0')]
        potential_stocks_to_buy = potential_stocks_to_buys.sort_values(by='100 day slope',ascending=False)
        for stock in potential_stocks_to_buy.iterrows():
            if positions_to_fill > 0:
                if stock[1][10] <= (cash_on_hand/positions_to_fill) and number_of_positions < 5:
                    qty_to_buy = int((cash_on_hand/positions_to_fill)/(stock[1][10] * 1.001))
                    logging.info('Trying to buy {qty_to_buy} shares of {sym} stock'.format(qty_to_buy=qty_to_buy, sym=stock[1][0]))
                    HelperFunctions.make_order(api, 'buy', stock[1][0], qty_to_buy, 'limit', (stock[1][10] * 1.001))
                    number_of_positions += 1
                    positions_to_fill += -1
                    #needed to wait a little bit so the buy order could complete
                    time.sleep(10)
                    cash_on_hand = float(api.get_account().cash)

    return
=======
import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import requests
import bs4 as bs

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


def stock_stats(api, stock_list):
    now = pd.Timestamp.now(tz='US/Eastern')
    now_no_tz = pd.Timestamp.now()
    end_dt = now

    #this is imprecise, but easily accounts for any holidays and weekends.
    start_dt = end_dt - pd.Timedelta('200 days')

    #pulling historical data: open, close, high, low, volumne, date.
    hist_data = api.polygon.historic_agg(
                'day', stock_list['Symbol'][1], _from=start_dt, to=end_dt).df

    #creating date offset to see how far back each day is from current.
    hist_data['DaysInPast'] = (hist_data.index.to_series().dt.date - now_no_tz.date()).dt.days

    #for each stock it must calculate the averages and then add them back to the main stock list.
    for i , stock in stock_list.iterrows():
        hist_data = api.polygon.historic_agg(
                'day', stock[0], _from=start_dt, to=end_dt).df

        hist_data['3 day avg'] = hist_data['close'].rolling(3).mean()
        hist_data['3 day avg offset'] = hist_data['close'].rolling(3).mean().shift(1)
        hist_data['3 day slope'] = (hist_data['3 day avg'] - hist_data['3 day avg offset'])/hist_data['3 day avg offset']
        hist_data['10 day avg'] = hist_data['close'].rolling(10).mean()
        hist_data['10 day avg offset'] = hist_data['close'].rolling(10).mean().shift(1)
        hist_data['10 day slope'] = (hist_data['10 day avg'] - hist_data['10 day avg offset'])/hist_data['10 day avg offset']
        hist_data['100 day avg'] = hist_data['close'].rolling(100).mean()
        hist_data['100 day avg offset'] = hist_data['close'].rolling(100).mean().shift(1)
        hist_data['100 day slope'] = (hist_data['100 day avg'] - hist_data['100 day avg offset'])/hist_data['100 day avg offset']
        stock_list.loc[stock_list['Symbol'] == stock[0], '3 day avg'] = hist_data['3 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '3 day avg offset'] = hist_data['3 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '3 day slope'] = hist_data['3 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '10 day avg'] = hist_data['10 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '10 day avg offset'] = hist_data['10 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '10 day slope'] = hist_data['10 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '100 day avg'] = hist_data['100 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '100 day avg offset'] = hist_data['100 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], '100 day slope'] = hist_data['100 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], 'Todays close'] = hist_data['close'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[0], 'Todays open'] = hist_data['open'].iloc[-1]

    return stock_list


def doIBuy(stock_list):
    stock_list = stock_list.sort_values(by='100 day slope',ascending=False)
    stock_list.reset_index()

    for i,stock in stock_list.iterrows():
        #if 3 day avg > 0 and 3 day avg > 10 day avg
        if stock[4] > 0 and stock[4] > stock[7]:
            stock_list.loc[stock_list['Symbol'] == stock[0], 'Buy'] = 'Yes'
        else:
            stock_list.loc[stock_list['Symbol'] == stock[0], 'Buy'] = 'No'

    stock_list.to_csv('testing.csv')

    return stock_list


def checkCurrentPositions(positions, stock_list):
    sellingThreshold = -.02

    for position in positions:
        stocks = stock_list.loc[stock_list['Symbol'] == position.symbol]
        for i, stock in stocks.iterrows():
        #if 3 day avg < 0 or close(current) price >= 2% drop from open
            if (stock['3 day avg'] < 0) or (((stock['Todays close'] - stock['Todays open'])/stock['Todays open']) <= sellingThreshold):
                stock_list.loc[stock_list['Symbol'] == stock[0], 'Sell'] = 'Yes'
            else:
                stock_list.loc[stock_list['Symbol'] == stock[0], 'Sell'] = 'No'

    stock_list.to_csv('testing.csv')

    return stock_list


def make_order(api, status, symbol, qty, order_type='market', limit_price=None, stop_price=None):
    '''
    Sends an order to the alpaca API
    INPUT:
    api: object, The api alpaca object that you created when you connected
    status: str, buy, sell, or pass
    symbol: str, The string of the stock symbol you want to place an order in
    qty: int, the # of shares to buy or sell
    type: str, the type of order. Market, limit, or stop order. If limit or stop must specify the limit_price or stop_price
    '''
    api.submit_order(
        symbol=symbol,
        qty=qty,
        side=status,
        type=order_type,
        time_in_force='day',
        limit_price=limit_price,
        stop_price=stop_price
        )

    return
>>>>>>> fc1c76106360929251e366e733cb2993ef41cd05
