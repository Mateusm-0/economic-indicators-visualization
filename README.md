# economic-indicators-visualization
Interactive dashboard visualizing the correlation between Brazil's Selic interest rate and some economic indicators. Created with Python (Pandas, Dash, Plotly) and Central Bank of Brazil data. Analysis includes time-lag correlations and cumulative trend visualization.

<img width="649" alt="image" src="https://github.com/user-attachments/assets/06ab39d1-107d-47fb-9a95-dff1106b906a" />

Features

Interactive indicator comparison: Compare any economic indicator with the Selic interest rate
Time-lag analysis: Automatically calculate and visualize the optimal time shift for maximum correlation
Correlation heatmap: View the interconnections between all economic indicators
Cumulative trend analysis: Track the accumulated changes of multiple indicators over time

Data
The dashboard analyzes monthly economic data from Brazil, including:

Selic interest rate (Brazil's benchmark interest rate)
IPCA (Brazilian Consumer Price Index)
Foreign exchange rates (USD/BRL)
CDI (Interbank Deposit Certificates)
IPCA (Broad National Consumer Price Index)
IBC-Br (adjusted) (Central Bank Economic Activity Index - seasonally adjusted)
Unemployment (Unemployment rate)

Analysis
Key Findings

The Selic rate shows a lagged negative correlation with inflation, demonstrating the effectiveness of monetary policy
Economic indicators typically respond to Selic rate changes with a 3-6 month lag
The positive correlation between Selic and USD (0.17) suggests that interest rate decisions are influenced by factors beyond simple currency stabilization.
The unemployment data exhibits a strong negative correlation (-0.92) when shifted back by 4 months, suggesting that final responses take approximately 4 months to fully materialize.

Methodology
The analysis employs time-series correlation techniques with adjustable time lags to identify:

How different economic sectors respond to interest rate changes
The optimal timing of monetary policy interventions
Potential leading indicators for economic performance

Technology Stack

Data Processing: Pandas
Data Source: BCB (Banco Central do Brasil) API
Visualization: Plotly, Matplotlib, Seaborn
Dashboard Framework: Dash
Development Environment: VS Code, Jupyter Notebook
Additional Libraries: io, base64
Deployment: (Your chosen deployment platform)

Contact
Mateus - mateus.vinci@outlook.com
License
This project is available for viewing and educational purposes. The source code is not open for redistribution or commercial use without permission.
