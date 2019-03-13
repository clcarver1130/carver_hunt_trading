import pandas as pd
import numpy as np
from Strategy import Strategy

test_strategy = Strategy('testing_strategy')

def rule1():
    df_raw = pd.read_csv('../../data/100_test.csv')
    metric_dict = dict()
    for col in df_raw:
        metric_dict[col] = {}
        metric_dict[col]['10_ewm'] = df_raw[col].ewm(span=10).mean().iloc[-1]
        metric_dict[col]['3_ewm'] = df_raw [col].ewm(span=3).mean().iloc[-1]
    df = pd.DataFrame.from_dict(metric_dict, orient='index')
    df['entry'] = np.nan
    df['exit'] = np.nan
    for sym, metrics in df.iterrows():
        if metrics['3_ewm'] > metrics['10_ewm']:
            df.loc[sym]['entry'] = 1
        else:
            df.loc[sym]['entry'] = 0
    # for sym, metrics in df.iterrows():
    #     if metrics['3_ewm'] < metrics['10_ewm']:
    #         df.loc[sym]['exit'] = 1
    #     else:
    #         df.loc[sym]['exit'] = 0
    return df

test_strategy.add_rules(rule1)
