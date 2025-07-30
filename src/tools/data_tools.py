import pandas as pd

def analyze_highest_grossing_films(df: pd.DataFrame):
    df["Worldwide gross"] = df["Worldwide gross"].replace('[\$,]', '', regex=True).astype(float) / 1e9
    df["Year"] = pd.to_datetime(df["Year"], errors='coerce').dt.year
    over_2bn = df[(df["Worldwide gross"] >= 2) & (df["Year"] < 2020)]
    over_15bn = df[df["Worldwide gross"] > 1.5]
    earliest = over_15bn.sort_values("Year").iloc[0]["Title"]

    corr = df[["Rank", "Worldwide gross"]].corr().iloc[0, 1]
    return {
        "How many $2 bn movies were released before 2020?": len(over_2bn),
        "Which is the earliest film that grossed over $1.5 bn?": earliest,
        "What's the correlation between the Rank and Peak?": round(corr, 3),
    }
