from tools.web_scraper import fetch_wikipedia_table
from tools.data_tools import analyze_highest_grossing_films
from tools.plot import plot_rank_vs_peak

def process_task(task: str) -> dict:
    if "highest grossing films" in task.lower():
        df = fetch_wikipedia_table()
        summary = analyze_highest_grossing_films(df)
        plot_uri = plot_rank_vs_peak(df)
        return summary | {"plot": plot_uri}
    else:
        return {"error": "Task not recognized or supported yet"}
