import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_temp(data, city, date, days):
    """
    Построение графика изменения температуры за заданный период.

    Параметры:
        data (pd.DataFrame): Датасет с температурными данными.
        city (str): Название города для анализа.
        date (datetime): Дата начала анализа.
        days (int): Количество дней для анализа.

    Возвращает:
        plotly.graph_objs._figure.Figure: График с изменением температуры, 
        скользящим средним и доверительными интервалами.
    """
    stop = date + pd.Timedelta(days=days)
    return px.line(
            data.query('timestamp >= @date and timestamp <= @stop'), 
            x="timestamp", 
            y=["temperature", "moving_average", "ci_up", "ci_down"],  
            title=f'Среднесуточная температура в {city}',
            color_discrete_map={'temperature': 'darkblue', 'moving_average': 'red', 'ci_up': 'orange', 'ci_down': 'orange'},
        )

def plot_moving_average(data, city):
    """
    Построение графика скользящего среднего температуры с выделением выбросов.

    Параметры:
        data (pd.DataFrame): Датасет с температурными данными.
        city (str): Название города для анализа.

    Возвращает:
        plotly.graph_objs._figure.Figure: График скользящего среднего, выбросов и среднего по сезону.
    """
    fig = go.Figure()

    # Добавляем линию скользящего среднего
    fig.add_trace(
        go.Scatter(
            name='moving average',
            x=data['timestamp'],
            y=data['moving_average'],
            line_color='darkblue',
    ))

    # Выделяем выбросы (outliers)
    outliers = data[data.is_outlier == 1]

    fig.add_trace(
        go.Scatter(
            name='outliers',
            x=outliers['timestamp'] ,
            y=outliers['temperature'],
            mode='markers',
            marker_color='darkorange'
        )
    )

    # Добавляем линию среднего по сезону
    fig.add_trace(
        go.Scatter(
            name='average temperature in season',
            x=data['timestamp'],
            y=data['mean']
        )
    )

    # Настройки оформления графика
    fig.update_layout(
        title=dict(
            text=f"Скользящее среднее температуры в {city}"
        ),
        xaxis=dict(
            title=dict(
                text="timestamp"
            )
        ),
        yaxis=dict(
            title=dict(
                text="value"
            )
        ))

    return fig
