import pandas as pd

def fetch_wikipedia_table():
    url = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
    tables = pd.read_html(url)
    for table in tables:
        if "Rank" in table.columns and "Worldwide gross" in table.columns:
            return table
    raise ValueError("Could not find expected table.")
