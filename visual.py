import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Connect to the database and load data
conn = sqlite3.connect('browsing_history.db')
df = pd.read_sql_query("SELECT * FROM history", conn)
conn.close()

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create a summary dataframe
summary = df.groupby('category').agg({
    'url': 'count',
    'timestamp': ['min', 'max']
}).reset_index()
summary.columns = ['Category', 'Visit Count', 'First Visit', 'Last Visit']

# Create the main figure with subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Category Distribution", "Daily Visits",
                    "Top 10 Domains", "Interactive Data Table"),
    specs=[[{"type": "pie"}, {"type": "scatter"}],
           [{"type": "bar"}, {"type": "table"}]]
)

# Pie chart for category distribution
pie = go.Pie(labels=summary['Category'],
             values=summary['Visit Count'], name="Categories")
fig.add_trace(pie, row=1, col=1)

# Line chart for daily visits
daily_visits = df.groupby(
    df['timestamp'].dt.date).size().reset_index(name='count')
line = go.Scatter(x=daily_visits['timestamp'],
                  y=daily_visits['count'], mode='lines', name="Daily Visits")
fig.add_trace(line, row=1, col=2)

# Bar chart for top 10 domains
top_domains = df['url'].apply(
    lambda x: x.split('/')[2]).value_counts().nlargest(10)
bar = go.Bar(x=top_domains.index, y=top_domains.values, name="Top Domains")
fig.add_trace(bar, row=2, col=1)

# Interactive data table
table = go.Table(
    header=dict(values=list(summary.columns)),
    cells=dict(values=[summary[col] for col in summary.columns])
)
fig.add_trace(table, row=2, col=2)

# Update layout
fig.update_layout(height=1000, title_text="Browsing History Dashboard")

# Create an interactive table with all data
full_table = go.Figure(data=[go.Table(
    header=dict(values=list(df.columns)),
    cells=dict(values=[df[col] for col in df.columns])
)])
full_table.update_layout(height=600, title_text="Full Browsing History")

# Combine both figures into an HTML file
with open('browsing_history_dashboard.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
    f.write(full_table.to_html(full_html=False, include_plotlyjs='cdn'))

print("Dashboard saved as 'browsing_history_dashboard.html'")
