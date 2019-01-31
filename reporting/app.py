import sys
sys.path.append('../scripts')
from helper_functions import *
from cam_paper_keys import *
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import boto

# Connect to the API
api = connect_paper_api(paper_key_id, paper_secret_key)

# Pull metric data
conn = boto.connect_s3(AWSAccessKeyId, AWSSecretKey)
bucket = conn.get_bucket('algotradingreports')
todays_date = str(pd.Timestamp.today())[0:10]
df_metrics = pd.read_csv('https://s3-us-west-2.amazonaws.com/algotradingreports/reports/{today}_metrics_report.csv'.format(today=todays_date))

# Prepare dataframe
df_metrics = df_metrics[['Unnamed: 0','open_price', 'current_price', '100_ewma', '100_slope', '10_ewma', '10_slope', '3_ewma', '3_slope', 'Sell', 'Buy']]
df_metrics.columns = ['Symbol', 'Open', 'Current', '100 EWMA', '100 Slope', '10 EWMA', '10 Slope', '3 EWMA', '3 Slope', 'Sell', 'Buy']
df_metrics.rename(columns={'Unnamed: 0': 'Symbol'}, inplace=True)
positions = {p.symbol: p for p in api.list_positions()}
position_symbol = set(positions.keys())
df_positions = df_metrics[df_metrics['Symbol'].isin(position_symbol)].reset_index()
for col in df_positions.columns[1:9]:
    df_positions.loc[:, [col]] = round(df_positions.loc[:, [col], 4)



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(children=[
        html.H1('Trading Report'),
        html.H5('Current Positions'),
        dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in df_positions.columns],
                    data=df_positions.to_dict("rows"),
                            )
                                ])

if __name__ == '__main__':
    app.run_server(debug=True)
