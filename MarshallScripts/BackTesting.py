import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import requests
import bs4 as bs


def main():
    df = pd.DataFrame(save_sp500_tickers(), columns=['Symbol'])
    api = tradeapi.REST('PK0W7YZAF8SUDVLI7ORQ', 'EGUB4sNLAlMUHObSW1vVhq0Xal7N4XSQGPz36pKZ', 'https://paper-api.alpaca.markets')
    df['Date'] = ''
    df['100 day avg'] = 0
    df['100 day avg offset'] = 0
    df['100 day slope'] = 0
    df['3 day avg'] = 0
    df['3 day avg offset'] = 0
    df['3 day slope'] = 0
    df['10 day avg'] = 0
    df['10 day avg offset'] = 0
    df['10 day slope'] = 0
    df['Todays close'] = 0
    df['Todays open'] = 0
    df['Buy'] = '0'
    df['Sell'] = '0'

    onestock = df.loc[df['Symbol'] == 'AAPL']

    stock_stats(api, onestock)

    return


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
    start_dt = '01/01/2000'

    #pulling historical data: open, close, high, low, volumne, date.
    hist_data = api.polygon.historic_agg(
                'day', stock_list.iloc[0][0], _from=start_dt, to=end_dt).df

    #creating date offset to see how far back each day is from current.
    hist_data['DaysInPast'] = (hist_data.index.to_series().dt.date - now_no_tz.date()).dt.days
    hist_data['Date'] = hist_data.index
    #hist_data['Date'] = pd.to_datetime(hist_data['Date'])
    print(type(hist_data['Date']))

    hist_data['3 day avg'] = hist_data['close'].rolling(3).mean()
    hist_data['3 day avg offset'] = hist_data['close'].rolling(3).mean().shift(1)
    hist_data['3 day slope'] = (hist_data['3 day avg'] - hist_data['3 day avg offset'])/hist_data['3 day avg offset']
    hist_data['10 day avg'] = hist_data['close'].rolling(10).mean()
    hist_data['10 day avg offset'] = hist_data['close'].rolling(10).mean().shift(1)
    hist_data['10 day slope'] = (hist_data['10 day avg'] - hist_data['10 day avg offset'])/hist_data['10 day avg offset']
    hist_data['100 day avg'] = hist_data['close'].rolling(100).mean()
    hist_data['100 day avg offset'] = hist_data['close'].rolling(100).mean().shift(1)
    hist_data['100 day slope'] = (hist_data['100 day avg'] - hist_data['100 day avg offset'])/hist_data['100 day avg offset']
    #print(hist_data.iloc[0])
    #print(hist_data.iloc[1])
    #print(hist_data.iloc[2])
    #print(hist_data.iloc[3])
    #print(hist_data.iloc[4])
    #print(hist_data.loc['2000-01-01%'])

    #for each stock it must calculate the averages and then add them back to the main stock list.
    for i , stock in stock_list.iterrows():
        hist_data = api.polygon.historic_agg(
                'day', stock[0], _from=start_dt, to=end_dt).df

if __name__ == '__main__':
    main()
