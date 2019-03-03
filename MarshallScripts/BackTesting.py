import alpaca_trade_api as tradeapi
#from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time
import requests
import bs4 as bs
import datetime

old_date = datetime.date(1999,1,1)
test_date = datetime.date(1999,1,4)

def main():
    df = pd.DataFrame(save_sp500_tickers(), columns=['Symbol'])
    df = df.sort_values(by='Symbol')
    api = tradeapi.REST('PKTX545YNJ2BANL31U62', 'nVOTbvbZngyGaT6jreYC0pNgLpHAgBlgMZog9c11', 'https://paper-api.alpaca.markets')
    df['Date'] = ''
    df['50 day avg'] = 0
    df['50 day avg offset'] = 0
    df['50 day slope'] = 0
    df['5 day avg'] = 0
    df['5 day avg offset'] = 0
    df['5 day slope'] = 0
    df['10 day avg'] = 0
    df['10 day avg offset'] = 0
    df['10 day slope'] = 0
    df['Todays close'] = 0
    df['Todays open'] = 0
    df['Buy'] = '0'
    df['Sell'] = '0'

    df = stock_stats(api, df, old_date)
    df = doIBuy(df)
    print(df)
    df.to_csv('thisisatest.csv')
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
        ticker = row.findAll('td')[1].text
        tickers.append(ticker)
    tickers = [x.replace('-', '.') for x in tickers]
    return tickers


def stock_stats(api, stock_list, date_from):
    df = stock_list
    start_date = date_from

    #for each stock it must calculate the averages and then add them back to the main stock list.
    for i , stock in stock_list.iterrows():
        testing_date = start_date.replace(year=start_date.year-1)
        end_dt = testing_date.replace(year=testing_date.year +2)
        #for longer time period tests, max rows returned is 3000 per call, so you have to take the historical data in chunks
        #while testing_date < (end_dt - datetime.timedelta(days=10)):
        hist_data = api.polygon.historic_agg(
                'day', stock[0], _from=testing_date, to=end_dt).df
        if not (hist_data.empty):
            hist_data['Date'] = pd.to_datetime(hist_data.index).date
            hist_data['Symbol'] = stock[0]
            #creating date offset to see how far back each day is from current.
            hist_data['DaysInPast'] = pd.to_datetime(hist_data.index).date - end_dt
            hist_data['5 day avg'] = hist_data['close'].rolling(5).mean()
            hist_data['5 day avg offset'] = hist_data['close'].rolling(5).mean().shift(1)
            hist_data['5 day slope'] = (hist_data['5 day avg'] - hist_data['5 day avg offset'])/hist_data['5 day avg offset']
            hist_data['10 day avg'] = hist_data['close'].rolling(10).mean()
            hist_data['10 day avg offset'] = hist_data['close'].rolling(10).mean().shift(1)
            hist_data['10 day slope'] = (hist_data['10 day avg'] - hist_data['10 day avg offset'])/hist_data['10 day avg offset']
            hist_data['50 day avg'] = hist_data['close'].rolling(50).mean()
            hist_data['50 day avg offset'] = hist_data['close'].rolling(50).mean().shift(1)
            hist_data['50 day slope'] = (hist_data['50 day avg'] - hist_data['50 day avg offset'])/hist_data['50 day avg offset']
            #testing_date = hist_data['Date'].iloc[-1]
            #start_date = testing_date

            if df['5 day avg'].iloc[0] == 0:
                df = hist_data
            else:
                df = pd.concat([df, hist_data])#.append(hist_data, sort=True)
            #df.to_csv('histdatatest.csv')
            #reset the dates for next stock
            #start_date = datetime.date(1999,1,1)
            #testing_date = start_date
            #stock_list.loc[stock_list['Symbol'] == stock[0], 'Date'] = hist_data['Date'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '5 day avg'] = hist_data['5 day avg'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '5 day avg offset'] = hist_data['5 day avg offset'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '5 day slope'] = hist_data['5 day slope'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '10 day avg'] = hist_data['10 day avg'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '10 day avg offset'] = hist_data['10 day avg offset'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '10 day slope'] = hist_data['10 day slope'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '100 day avg'] = hist_data['100 day avg'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '100 day avg offset'] = hist_data['100 day avg offset'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], '100 day slope'] = hist_data['100 day slope'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], 'Todays close'] = hist_data['close'].iloc[-1]
            #stock_list.loc[stock_list['Symbol'] == stock[0], 'Todays open'] = hist_data['open'].iloc[-1]
            print(stock[0])
    #df.to_csv('histdatatest.csv')

    df_of_day = df.loc[df['Date'] == test_date]

    return df_of_day

def doIBuy(stock_list):
    stock_list = stock_list.sort_values(by='50 day slope',ascending=False)
    stock_list.reset_index()

    for i,stock in stock_list.iterrows():
        #if 5 day slope > 0 and 5 day avg > 10 day avg
        if stock[10] > 0 and stock[8] > stock[11]:
            stock_list.loc[stock_list['Symbol'] == stock[6], 'Buy'] = 'Yes'
        else:
            stock_list.loc[stock_list['Symbol'] == stock[6], 'Buy'] = 'No'

    return stock_list


if __name__ == '__main__':
    main()
