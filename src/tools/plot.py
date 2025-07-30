import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np

def plot_rank_vs_peak(df):
    fig, ax = plt.subplots()
    x = df["Rank"]
    y = df["Worldwide gross"]
    ax.scatter(x, y)
    m, b = np.polyfit(x, y, 1)
    ax.plot(x, m*x + b, linestyle='dotted', color='red')
    ax.set_xlabel("Rank")
    ax.set_ylabel("Worldwide Gross (Billion $)")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close()
    return f"data:image/png;base64,{encoded[:100000]}"  # clip if needed
