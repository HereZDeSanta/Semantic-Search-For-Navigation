import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from matplotlib.patches import Circle

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
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return f"data:image/png;base64,{img_base64}"