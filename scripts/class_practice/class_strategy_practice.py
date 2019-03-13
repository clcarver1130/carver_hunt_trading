import sys
sys.path.append('../')
import alpaca_trade_api as tradeapi
from helper_functions import *
from cam_paper_keys import *
import pandas as pd
import numpy as np
from Strategy import Strategy

test_strategy = Strategy('testing_strategy')
symbols = save_sp500_tickers()
api = connect_paper_api(paper_key_id, paper_secret_key)


def calculate_metrics(symbols):
    metric_dict = dict()
    for sym in symbols:
        try:
            hist_close = pull_hist_data(api, sym, '50 days')[['close', 'open']]
            metric_dict[sym] = {}

            # 10 Day Metrics:
            metric_dict[sym]['10_ewma'] =  hist_close.close[-10:].ewm(span=10).mean().iloc[-1]
            metric_dict[sym]['10_ewma_shifted'] = hist_close.close[-11:-1].ewm(span=10).mean().iloc[-1]
            metric_dict[sym]['10_slope'] = calculate_slope(metric_dict[sym]['10_ewma_shifted'], metric_dict[sym]['10_ewma'])

            # 3 Day Metrics:
            metric_dict[sym]['3_ewma'] =  hist_close.close[-3:].ewm(span=3).mean().iloc[-1]
            metric_dict[sym]['3_ewma_shifted'] = hist_close.close[-4:-1].ewm(span=3).mean().iloc[-1]
            metric_dict[sym]['3_slope'] = calculate_slope(metric_dict[sym]['3_ewma_shifted'], metric_dict[sym]['3_ewma'])

            # Other metrics:
            metric_dict[sym]['current_price'] = hist_close.close.iloc[-1]
            metric_dict[sym]['open_price'] = hist_close.open.iloc[-1]
        except:
            print('Polygon Error. Skipping {}'.format(symbol))

    df = pd.DataFrame.from_dict(metric_dict, orient='index').sort_values(by='10_slope',ascending=False)
    return df

def ewma_10_3_rules(df):
    # Sell conditions:
    positions = {p.symbol: p for p in api.list_positions()}
    df['Sell'] = np.nan
    for i, stock in df.iterrows():
        if i in positions.keys():
            current_price = float(positions[i].current_price)
            yesterday_price = float(positions[i].lastday_price)
            # If [3_slope < 0] OR [(3_ewma < 10_ewma) OR (current price has dropped 2% from lastday_price)]
            if  ((stock['3_slope'] < 0) or (stock['3_ewma'] < stock['10_ewma']) or (float(positions[i].unrealized_plpc) <= -0.01)):
                df.loc[i]['Sell'] = 1
            else:
                df.loc[i]['Sell'] = 0
        else:
            pass

    # Buy conditions:
    df['Buy'] = np.nan
    for i, stock in df.iterrows():
        #if 3 day slope > 0 AND 100 day slope > 0 AND 3 day avg > 10 day avg
        if (stock['3_slope'] > 0) and (stock['3_ewma'] > stock['10_ewma']):
            df.loc[i]['Buy'] = 1
        else:
            df.loc[i]['Buy'] = 0

    # Convert to dict to df, sort by 100_slope, and return as a dataframe object:
    return df

test_strategy.add_metrics(calculate_metrics, symbols)
test_strategy.add_entry_exit_rules(ewma_10_3_rules)
