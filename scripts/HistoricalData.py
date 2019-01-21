import alpaca_trade_api as tradeapi
from hunt import paper_key_id, paper_secret_key
import pandas as pd
from logger import logging
import time

api = tradeapi.REST(paper_key_id, paper_secret_key, 'https://paper-api.alpaca.markets')

def last_200_days(stock_list):
    now = pd.Timestamp.now(tz='US/Eastern')
    now_no_tz = pd.Timestamp.now()
    end_dt = now

    #this is imprecise, but easily accounts for any holidays and weekends.
    start_dt = end_dt - pd.Timedelta('300 days')

    #pulling historical data: open, close, high, low, volumne, date.
    hist_data = api.polygon.historic_agg(
                'day', stock_list['Symbol'][1], _from=start_dt, to=end_dt).df

    #creating date offset to see how far back each day is from current.
    hist_data['DaysInPast'] = (hist_data.index.to_series().dt.date - now_no_tz.date()).dt.days

    #for each stock it must calculate the averages and then add them back to the main stock list.
    for stock in stock_list.iterrows():
        hist_data = api.polygon.historic_agg(
                'day', stock[1][0], _from=start_dt, to=end_dt).df

        hist_data['3 day avg'] = hist_data['close'].rolling(3).mean()
        hist_data['3 day avg offset'] = hist_data['close'].rolling(3).mean().shift(1)
        hist_data['3 day slope'] = (hist_data['3 day avg'] - hist_data['3 day avg offset'])/hist_data['3 day avg offset']
        hist_data['10 day avg'] = hist_data['close'].rolling(10).mean()
        hist_data['10 day avg offset'] = hist_data['close'].rolling(10).mean().shift(1)
        hist_data['10 day slope'] = (hist_data['10 day avg'] - hist_data['10 day avg offset'])/hist_data['10 day avg offset']
        hist_data['100 day avg'] = hist_data['close'].rolling(100).mean()
        hist_data['100 day avg offset'] = hist_data['close'].rolling(100).mean().shift(1)
        hist_data['100 day slope'] = (hist_data['100 day avg'] - hist_data['100 day avg offset'])/hist_data['100 day avg offset']
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '3 day avg'] = hist_data['3 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '3 day avg offset'] = hist_data['3 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '3 day slope'] = hist_data['3 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '10 day avg'] = hist_data['10 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '10 day avg offset'] = hist_data['10 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '10 day slope'] = hist_data['10 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '100 day avg'] = hist_data['100 day avg'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '100 day avg offset'] = hist_data['100 day avg offset'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], '100 day slope'] = hist_data['100 day slope'].iloc[-1]
        stock_list.loc[stock_list['Symbol'] == stock[1][0], 'Todays close'] = hist_data['close'].iloc[-1]

    return stock_list
