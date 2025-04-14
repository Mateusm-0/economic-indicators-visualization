import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bcb import sgs #https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=csv&dataInicial=12/04/2015&dataFinal=12/04/2025
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import io
import base64

#https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries
indicators = {
    'USD': (1, 'c.m.u./US$', 'D'),
    'Selic accumulated in the month': (4390, '% p.m.', 'M'),
    'CDI': (12, '%', 'D'),
    'IPCA': (433, 'Monthly % var.', 'M'),
    'IBC-Br (adjusted)': (24364, 'index', 'M'),
    'Unemployment': (24369, '%', 'M')
                 }

one_month_before = '2017-12-01'
final_date = '2024-12-31'

data_list = [] #"{}" would create a dictionary

for name, (code, unit, freq) in indicators.items():
    df = sgs.get(code, start=one_month_before, end=final_date, freq=freq)

    # If index is PeriodIndex, convert to Timestamp
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.to_timestamp()

    df.sort_index(inplace=True)
    df = df.reset_index() #Moves date index into a column
    df.columns = ['date', 'value'] #Rename columns
    df['indicator'] = (name) #for concat
    df['unit'] = (unit) #for concat
    df['freq'] = (freq) #for concat
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = df['value'].astype(float)    

    if freq == 'D':
        print(f"Processing {name}...")
        # Convert to monthly, get last value of each month
        df = (
            df.set_index('date')
              .resample('MS')#)
              .first()
              .reset_index()
        )
        print(df.head(1))
        #df['freq'] = df['freq'].replace('D', 'M')#.reset_index(drop=True)

    if unit not in ['Monthly % var.', '% p.d.']:
        print(f"Processing {name}...")
        df['value'] = df['value'].pct_change()
        print(df.iloc[2])

    if name not in ['IPCA']:
        print(df[df['value'].isna()])
        df['value'] = (1 + df['value'].fillna(0)).cumprod()
        print(f"{df.iloc[2]} is not IPCA")

    else:
        print(df[df['value'].isna()])
        df['value'] = (1 + df['value'].fillna(0) / 100).cumprod()
        print(f"Precessing {df.iloc[2]} to IPCA_accumulated")        

    # Make sure date is datetime and standardized to first-of-month
    df['date'] = pd.to_datetime(df['date']).dt.to_period('M')#.dt.start_time if you want point in time (YYYY-MM-DD 00:00:00)
    #print(df.dtypes)
    #df['date'] = df['date'].dt.strftime('%Y-%m')
    data_list.append(df)

# Remove first row of each df (usually NaN due to pct_change)
data_list = [df.iloc[1:].reset_index(drop=True) for df in data_list]

# Combine all into one DataFrame with clean index
final_df = pd.concat(data_list, ignore_index=True)

print(final_df)

# Remove duplicates
final_df = final_df.drop_duplicates(subset=['date', 'indicator'], keep='last')#.reset_index(drop=True)

print(final_df)

# Optional: Pivot to wide format
final_pivot = final_df.pivot(index='date', columns='indicator', values='value').reset_index()#remove 'unit' and 'freq'

# Initialize rebased and relative change columns
for col in final_pivot.columns:
    if col == 'date':
        continue
    series = final_pivot[col]
    if series.notna().any():
        base_value = series.iloc[0]

        # Relative change from first available month (in percentage)
        final_pivot[f'{col}(vs start)'] = (series / base_value - 1) * 100

df = final_pivot.copy()

# Convert date column properly
if 'date' in df.columns:
    if hasattr(df['date'], 'dt') and hasattr(df['date'].dt, 'to_timestamp'):
        df['date'] = df['date'].dt.to_timestamp()
    # Then set as index
    df.set_index('date', inplace=True)

# If the index is still a PeriodIndex, convert it to DatetimeIndex
if hasattr(df.index, 'to_timestamp'):
    df.index = df.index.to_timestamp()

# Define variables
if 'Selic accumulated in the month' in df.columns:
    selic = df['Selic accumulated in the month']
    available_indicators = [col for col in df.columns if col != 'Selic accumulated in the month']
else:
    selic = pd.Series()
    available_indicators = []

app = dash.Dash(__name__)

def calculate_best_shift(series, target, max_lag=12):
    best_lag = 0
    best_corr = 0
    for lag in range(-max_lag, max_lag + 1):
        shifted = series.shift(lag)
        corr = shifted.corr(target)
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    return best_lag, best_corr

def generate_correlation_heatmap(dataframe):
    corr = dataframe.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

app.layout = html.Div([
    html.H2("Compare Economic Indicators to Selic"),

    html.Div([
        html.Label("Choose an Indicator:"),
        dcc.Dropdown(
            id='indicator-dropdown',
            options=[{'label': i, 'value': i} for i in available_indicators],
            value=available_indicators[0] if available_indicators else None
        ),

        dcc.Checklist(
            id='shift-check',
            options=[{'label': 'Shift for Best Correlation (absolute)', 'value': 'shift'}],
            value=[]
        ),
    ], style={'width': '40%', 'display': 'inline-block'}),

    dcc.Graph(id='comparison-plot'),

    html.Hr(),

    html.Label("Choose Indicators for Cumulative Comparison:"),
    dcc.Dropdown(
        id='multi-indicator',
        options=[{'label': i, 'value': i} for i in available_indicators],
        value=available_indicators[:3] if len(available_indicators) >= 3 else available_indicators,
        multi=True
    ),

    dcc.Graph(id='cumulative-graph'),

    html.Hr(),

    html.H3("Correlation Matrix"),
    html.Img(id='correlation-heatmap', style={'maxWidth': '100%'})
])

@app.callback(
    Output('comparison-plot', 'figure'),
    [Input('indicator-dropdown', 'value'),
     Input('shift-check', 'value')]
)
def update_graph(selected_indicator, shift_option):
    if selected_indicator and 'Selic accumulated in the month' in df.columns:
        selic = df['Selic accumulated in the month']
        series = df[selected_indicator]
        best_shift = 0
        subtitle = ""

        if 'shift' in shift_option:
            best_shift, max_corr = calculate_best_shift(series, selic)
            series = series.shift(best_shift)
            subtitle = f"(Shifted by {best_shift} months, corr={max_corr:.2f})"

        # Create main comparison plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=series, mode='lines', name=selected_indicator))
        fig.add_trace(go.Scatter(x=df.index, y=selic, mode='lines', name='Selic'))

        fig.update_layout(
            title=f"{selected_indicator} vs Selic {subtitle}",
            xaxis_title="Date",
            yaxis_title="Accumulated % Change",
            template="plotly_white"
        )
        return fig
    else:
        # Return empty figure if data is not available
        return go.Figure().update_layout(title="No data available or invalid selection")

@app.callback(
    Output('cumulative-graph', 'figure'),
    [Input('multi-indicator', 'value')]
)
def update_cumulative(selected_indicators):
    if selected_indicators:
        fig = go.Figure()
        for col in selected_indicators:
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col))

        fig.update_layout(
            title="Cumulative Economic Indicators Over Time",
            xaxis_title="Date",
            yaxis_title="Accumulated %",
            template="plotly_white"
        )
        return fig
    else:
        return go.Figure().update_layout(title="No indicators selected")

@app.callback(
    Output('correlation-heatmap', 'src'),
    [Input('multi-indicator', 'value')]
)
def update_heatmap(selected_indicators):
    if selected_indicators:
        # Filter dataframe to include only selected indicators plus Selic
        columns_to_include = selected_indicators.copy()
        if 'Selic accumulated in the month' in df.columns:
            columns_to_include.append('Selic accumulated in the month')
        
        subset_df = df[columns_to_include]
        heatmap_img = generate_correlation_heatmap(subset_df)
        return f'data:image/png;base64,{heatmap_img}'
    else:
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, "No data available for correlation", ha='center', va='center')
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        empty_img = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f'data:image/png;base64,{empty_img}'

if __name__ == '__main__':
    app.run(debug=True)