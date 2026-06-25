import requests
import pandas as pd
import time
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

NYT_API_KEY = "yVHf9pHxN7ZJ4lEhvv5ux0mJh4ijrnAYZXQhuJHR0zA7RRmF"

nyt_query = "artificial intelligence music"
nyt_base_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
nyt_articles = []

for page in range(0, 3):

    print(f"Fetching NYT page {page}...")

    params = {
        "q": nyt_query,
        "page": page,
        "api-key": NYT_API_KEY
    }

    response = requests.get(nyt_base_url, params=params)

    if response.status_code == 200:

        docs = response.json().get("response", {}).get("docs", [])

        for article in docs:

            nyt_articles.append({
                "title": article.get("headline", {}).get("main", ""),
                "author": article.get("byline", {}).get("original", ""),
                "snippet": article.get("snippet", ""),
                "section": article.get("section_name", ""),
                "pub_date": article.get("pub_date", ""),
                "url": article.get("web_url", "")
            })

    else:
        print(f"Error: {response.status_code}")
        print(response.text)

    time.sleep(6)

df_nyt = pd.DataFrame(nyt_articles)

df_nyt["pub_date"] = pd.to_datetime(df_nyt["pub_date"])
df_nyt["date_only"] = df_nyt["pub_date"].dt.date

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
server = app.server

app.layout = dbc.Container([

    html.H1("NYT Article Dashboard"),

    html.Label("Select a date range:"),

    dcc.DatePickerRange(
        id="date-range",
        min_date_allowed=df_nyt["date_only"].min(),
        max_date_allowed=df_nyt["date_only"].max(),
        start_date=df_nyt["date_only"].min(),
        end_date=df_nyt["date_only"].max()
    ),

    dcc.Graph(id="articles-over-time"),

    dcc.Graph(id="articles-by-section")

])

@app.callback(
    Output("articles-over-time", "figure"),
    Output("articles-by-section", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_graphs(start_date, end_date):

    mask = (
        (df_nyt["date_only"] >= pd.to_datetime(start_date).date()) &
        (df_nyt["date_only"] <= pd.to_datetime(end_date).date())
    )

    filtered_df = df_nyt.loc[mask]

    articles_by_day = (
        filtered_df.groupby("date_only")
        .size()
        .reset_index(name="article_count")
    )

    fig_time = px.line(
        articles_by_day,
        x="date_only",
        y="article_count",
        title="Articles Over Time"
    )

    articles_by_section = (
        filtered_df.groupby("section")
        .size()
        .reset_index(name="article_count")
    )

    fig_section = px.bar(
        articles_by_section,
        x="section",
        y="article_count",
        title="Articles by Section"
    )

    return fig_time, fig_section

if __name__ == "__main__":
    app.run(debug=False)
