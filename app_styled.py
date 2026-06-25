# --------------------------------------------------
# Part A: Import libraries
# --------------------------------------------------

import requests
import pandas as pd
import time
import re
from collections import Counter

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px


# --------------------------------------------------
# Part B: NYT API setup
# --------------------------------------------------

NYT_API_KEY = "yVHf9pHxN7ZJ4lEhvv5ux0mJh4ijrnAYZXQhuJHR0zA7RRmF"

nyt_query = "artificial intelligence music"
nyt_base_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
nyt_articles = []


# Stopwords are common words we do not want to count
stop_words = {
    "the", "a", "an", "and", "or",
    "of", "to", "in", "on", "for",
    "with", "is", "are", "was", "were",
    "about", "over", "new", "review",
    "what", "like", "have", "has", "had",
    "how", "why", "from", "by", "as",
    "at", "be", "this", "that", "it",
    "its", "into", "after", "before", "music",
}


# --------------------------------------------------
# Part C: Retrieve NYT articles
# --------------------------------------------------

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


# --------------------------------------------------
# Part D: Create dataframe
# --------------------------------------------------

df_nyt = pd.DataFrame(nyt_articles)

df_nyt["pub_date"] = pd.to_datetime(df_nyt["pub_date"])
df_nyt["date_only"] = df_nyt["pub_date"].dt.date

min_date = df_nyt["date_only"].min()
max_date = df_nyt["date_only"].max()


# --------------------------------------------------
# Part E: Start Dash app
# --------------------------------------------------

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA]
)

server = app.server


# --------------------------------------------------
# Part F: Dashboard layout
# --------------------------------------------------

app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.Div([

                html.H1(
                    "NYT Article Dashboard",
                    className="dashboard-title"
                ),

                html.P(
                    "Interactive dashboard using NYT article data",
                    className="dashboard-subtitle"
                )

            ], className="hero-section")
        ])
    ]),

    dbc.Row([

        dbc.Col([
            html.Label(
                "Start Date",
                className="control-label"
            ),

            dcc.DatePickerSingle(
                id="start-date",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                date=min_date
            )
        ], width=6),

        dbc.Col([
            html.Label(
                "End Date",
                className="control-label"
            ),

            dcc.DatePickerSingle(
                id="end-date",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                date=max_date
            )
        ], width=6)

    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id="articles-over-time")
                ])
            ], className="dashboard-card")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id="articles-by-section")
                ])
            ], className="dashboard-card")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id="common-title-words")
                ])
            ], className="dashboard-card")
        ])
    ])

], fluid=True)


# --------------------------------------------------
# Part G: Callback function
# --------------------------------------------------

@app.callback(
    Output("articles-over-time", "figure"),
    Output("articles-by-section", "figure"),
    Output("common-title-words", "figure"),
    Input("start-date", "date"),
    Input("end-date", "date")
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

    all_titles = " ".join(
        filtered_df["title"].dropna()
    )

    words = re.findall(
        r"\b[a-zA-Z]+\b",
        all_titles.lower()
    )

    filtered_words = [
        word for word in words
        if word not in stop_words
        and len(word) > 2
    ]

    word_counts = Counter(filtered_words)

    common_words = pd.DataFrame(
        word_counts.most_common(10),
        columns=["word", "count"]
    )

    fig_words = px.bar(
        common_words,
        x="word",
        y="count",
        title="Most Common Title Words"
    )

    return fig_time, fig_section, fig_words


# --------------------------------------------------
# Part H: Run app
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False)