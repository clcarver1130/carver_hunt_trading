import pandas as pd

def pull_hist_data(symbol, start_dt, end_dt='now', agg='day', tz='US/Eastern'):

    '''Pulls historical stock data by day or minute from the Polygon API. Must be connected to the alpaca api.

    Input:
    symbol: str, The string of the stock symbol you want to pull
    start_dt: str, The date/datetime you want the historical data to begin. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD:HH:mm:ss'
    end_dt: str, the date/date you want the historical data to end. Defaults to 'now' if you want to pull up to the current data.
    agg: str, How you want the data to aggregate. Options are 'day' or 'minute'.
    tz: str, The timezone you want the end_dt to end in. Defaults to 'US/Eastern' which most exchanges are in.

    Output:
    Returns a pandas dataframe of the historical data with open, close, high, and low price points'''

    if end_dt = 'now':
        now = pd.Timestamp.now(tz=tz)
        end_dt = now
    else:
        end_dt = end_dt

    return api.polygon.historic_agg(size=agg, symbol=symbol, _from=start_dt, to=end_dt).df
