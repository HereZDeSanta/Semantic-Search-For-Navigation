import matplotlib.pyplot as plt
import os
import uuid
from datetime import datetime

PLOTS_DIR = "static/plots"
os.makedirs(PLOTS_DIR, exist_ok=True)

def plot_route(df_all, df_highlight, title="Route"):
    plt.figure(figsize=(12, 8))
    plt.scatter(df_all['longitude'], df_all['latitude'], 
                c='lightgray', s=5, alpha=0.6, label='Весь путь')
    if not df_highlight.empty:
        plt.scatter(df_highlight['longitude'], df_highlight['latitude'], 
                    c='red', s=20, label='Целевые точки')
    plt.xlabel('Долгота')
    plt.ylabel('Широта')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{timestamp}_{unique_id}.png"
    filepath = os.path.join(PLOTS_DIR, filename)
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.close()
    
    return f"http://localhost:8000/static/plots/{filename}"