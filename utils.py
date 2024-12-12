import pandas as pd
import numpy as np
import httpx
import streamlit as st


# Реальные средние температуры (примерные данные) для городов по сезонам
seasonal_temperatures = {
    "New York": {"winter": 0, "spring": 10, "summer": 25, "autumn": 15},
    "London": {"winter": 5, "spring": 11, "summer": 18, "autumn": 12},
    "Paris": {"winter": 4, "spring": 12, "summer": 20, "autumn": 13},
    "Tokyo": {"winter": 6, "spring": 15, "summer": 27, "autumn": 18},
    "Moscow": {"winter": -10, "spring": 5, "summer": 18, "autumn": 8},
    "Sydney": {"winter": 12, "spring": 18, "summer": 25, "autumn": 20},
    "Berlin": {"winter": 0, "spring": 10, "summer": 20, "autumn": 11},
    "Beijing": {"winter": -2, "spring": 13, "summer": 27, "autumn": 16},
    "Rio de Janeiro": {"winter": 20, "spring": 25, "summer": 30, "autumn": 25},
    "Dubai": {"winter": 20, "spring": 30, "summer": 40, "autumn": 30},
    "Los Angeles": {"winter": 15, "spring": 18, "summer": 25, "autumn": 20},
    "Singapore": {"winter": 27, "spring": 28, "summer": 28, "autumn": 27},
    "Mumbai": {"winter": 25, "spring": 30, "summer": 35, "autumn": 30},
    "Cairo": {"winter": 15, "spring": 25, "summer": 35, "autumn": 25},
    "Mexico City": {"winter": 12, "spring": 18, "summer": 20, "autumn": 15},
}

# Сопоставление месяцев с сезонами
month_to_season = {12: "winter", 1: "winter", 2: "winter",
                   3: "spring", 4: "spring", 5: "spring",
                   6: "summer", 7: "summer", 8: "summer",
                   9: "autumn", 10: "autumn", 11: "autumn"}

# Генерация данных о температуре
@st.cache_resource
def generate_realistic_temperature_data(cities, num_years=10):
    dates = pd.date_range(start="2010-01-01", periods=365 * num_years, freq="D")
    data = []

    for city in cities:
        for date in dates:
            season = month_to_season[date.month]
            mean_temp = seasonal_temperatures[city][season]
            # Добавляем случайное отклонение
            temperature = np.random.normal(loc=mean_temp, scale=5)
            data.append({"city": city, "timestamp": date, "temperature": temperature})

    df = pd.DataFrame(data)
    df['season'] = df['timestamp'].dt.month.map(lambda x: month_to_season[x])
    return df


@st.cache_resource
async def get_weather(city, api_key):
    """
    Асинхронное получение текущей температуры для указанного города через API OpenWeatherMap.

    Параметры:
        city (str): Название города для запроса.
        api_key (str): API-ключ для доступа к OpenWeatherMap.

    Возвращает:
        dict: Ответ API в формате JSON, если запрос успешен.
        str: Текст ошибки, если запрос не удался.
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
        else:
            return response.text

        return data

@st.cache_data
def calc_statistics(data):
    """
    Вычисление скользящего среднего, доверительных интервалов и выявление выбросов.

    Параметры:
        data (pd.DataFrame): Датасет с температурными данными.

    Возвращает:
        pd.DataFrame: Обновленный датасет с дополнительными расчетными столбцами:
            - moving_average: Скользящее среднее (30-дневное).
            - std: Стандартное отклонение для города и сезона.
            - mean: Среднее значение температуры для города и сезона.
            - ci_up, ci_down: Верхняя и нижняя границы доверительного интервала (95%).
            - is_outlier: Метка выбросов (1, если температура вне доверительного интервала).
    """
    # Вычисление скользящего среднего
    data['moving_average'] = data.groupby(
        'city'
        )['temperature'].transform(
            lambda x: x.rolling(window=30).mean()
            )

    # Вычисление стандартного отклонения для каждого города и сезона
    data['std'] = data.groupby(
        ['city', 'season']
        )['temperature'].transform('std')

    # Вычисление среднего значения для каждого города и сезона
    data['mean'] = data.groupby(
        ['city', 'season']
        )['temperature'].transform('mean')

    # Вычисление доверительных интервалов
    data['ci_up'] = data['std'] * 1.96 + data['moving_average']
    data['ci_down'] = data['std'] * -1.96 + data['moving_average']

    # Определение выбросов
    data['is_outlier'] = np.where(
        (data['temperature'] < data['mean'] - data['std'] * 1.96) 
        | (data['temperature'] > data['mean'] + data['std'] * 1.96),
        1, 0
        )

    return data
