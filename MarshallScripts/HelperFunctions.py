import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import requests
import bs4 as bs
import boto
import boto3
import numpy as np
from io import StringIO

aws_access_key = 'AKIAIZJ6G3HA2VRYIINQ'
aws_secret_key = '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'

def save_sp500_tickers():

    '''Pulls the S&P500 Ticker symbols straight from Wikipeida's 'List of S&P500 Companies' that is updated regularly.
    OUTPUT:
    An array with all 500 ticker symbols'''

    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[1].text
        tickers.append(ticker)
    tickers = [x.replace('-', '.') for x in tickers]
    return tickers


def stock_stats(api, stock_list):
    now = pd.Timestamp.now(tz='America/New_York')
    now_no_tz = pd.Timestamp.now()
    end_dt = now

    #this is imprecise, but easily accounts for any holidays and weekends.
    start_dt = end_dt - pd.Timedelta('200 days')

    #pulling historical data: open, close, high, low, volumne, date.
    hist_data = api.polygon.historic_agg(
                'day', stock_list['Symbol'][1], _from=start_dt, to=end_dt).df

    #creating date offset to see how far back each day is from current.
    hist_data['DaysInPast'] = (pd.to_datetime(hist_data.index) - now).days

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

        #save_to_s3_stock_stats(stock_list)

    return stock_list


def doIBuy(stock_list):
    stock_list = stock_list.sort_values(by='100 day slope',ascending=False)
    stock_list.reset_index()

    for i,stock in stock_list.iterrows():
        #if 3 day slope > 0 and 3 day avg > 10 day avg and current price >= 98.5% of open
        if stock[6] > 0 and stock[4] > stock[7] and (stock[10]/stock[11]) > .985:
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
        #if 3 day slope < 0 or close(current) price >= 2% drop from open
            if (stock['3 day slope'] < 0) or (((stock['Todays close'] - stock['Todays open'])/stock['Todays open']) <= sellingThreshold):
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
                    make_order(api, 'buy', stock[1][0], qty_to_buy, 'limit', (stock[1][10] * 1.001))
                    #have to update the stock list so it wont be sold if bought today
                    stock_list.loc[stock_list['Symbol'] == stock[1][0], 'Sell'] = 'Just Bought'
                    number_of_positions += 1
                    positions_to_fill += -1
                    #needed to wait a little bit so the buy order could complete
                    time.sleep(10)
                    #needs to account for any orders already pending
                    pending_orders = api.list_orders()
                    cash_pending_orders = 0
                    for order in pending_orders:
                        if(order.side=='buy'):
                            cash_pending_orders += int(order.qty) * float(order.limit_price)
                    cash_on_hand = float(api.get_account().cash) - cash_pending_orders

    return stock_list

def calc_target_positions(api):
    number_of_positions = 0

    positions = {p.symbol: p for p in api.list_positions()}
    position_symbol = set(positions.keys())
    total_value = float(api.get_account().cash)

    for sym in position_symbol:
        position_value = float(positions[sym].qty) * float(positions[sym].current_price)
        total_value = total_value + position_value

    if total_value <= 200:
        number_of_positions = 1
    elif total_value > 200 and total_value <= 300:
        number_of_positions = 2
    elif total_value > 300 and total_value <= 400:
        number_of_positions = 3
    elif total_value > 400 and total_value <= 500:
        number_of_positions = 4
    else:
        number_of_positions = 5

    return number_of_positions


#def save_to_s3_stock_stats(df):
#    conn = boto.connect_s3(aws_access_key, aws_secret_key)
#    bucket = conn.get_bucket('carver-hunt-trading')
#
#    todays_date = str(pd.Timestamp.today())[0:10]
#    string_df = df.to_csv(None)
#
#    file_df = bucket.new_key('stock-stats/{today}_stock_stats_report.csv'.format(today=todays_date))
#    file_df.set_contents_from_string(string_df)
#    logging.info('{today} stock report saved to reports s3 bucket'.format(today=todays_date))
#
#    return

#def save_to_s3_order_history(stock_price, ticker, order_date, buy_or_sell, shares):
#    df = pd.DataFrame(np.array([[order_date, ticker, stock_price, buy_or_sell, shares]]),
#                        columns=['order_date', 'ticker', 'stock_price', 'buy_or_sell', 'shares'])
#    connboto3 = boto3.client('s3', aws_access_key_id = aws_access_key, aws_secret_access_key = aws_secret_key)
#    conn = boto.connect_s3(aws_access_key, aws_secret_key)
#    csv_obj = connboto3.get_object(Bucket='carver-hunt-trading',Key = 'order-history/order_history_report.csv')
#    body = csv_obj['Body']
#    csv_str = body.read().decode('utf-8')
#    dff = pd.read_csv(StringIO(csv_str))
#    dff.append(df)
#
#    bucket = conn.get_bucket('carver-hunt-trading')
#    string_df = dff.to_csv(None)
#
#    file_df = bucket.new_key('order-history/order_history_report.csv')
#    file_df.set_contents_from_string(string_df)
#    logging.info('Order History report updated')
#
#    return
