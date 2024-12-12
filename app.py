from datetime import datetime
import streamlit as st
import pandas as pd
import asyncio

# Импортируем реализованные функции из локальных модулей
from utils import generate_realistic_temperature_data, seasonal_temperatures, \
    month_to_season, get_weather, calc_statistics
from graphs import plot_temp, plot_moving_average


async def main():
    # Заголовок приложения
    st.title('Анализ температурных данных и мониторинг текущей температуры')
    st.header('Загрузка данных')

    # Выбираем источник данных: пользователь загружает файл или генерирует данные
    source = st.radio(
        "Выберите источник данных",
        ["Загрузить файл", "Генерация данных"],
        captions=[
            "Загрузить исторические данные о погоде.",
            "Сгенерировать фиктивные данные о погоде.",
        ],
    )

    data = None  # Переменная для хранения данных

    # Если пользователь выбирает загрузку файла
    if source == "Загрузить файл":
        # Загружаем CSV-файл
        upload_file = st.file_uploader('Загрузить csv-файл', type=['csv'])
        if upload_file is not None:
            # Читаем файл и преобразуем столбец 'timestamp' в формат даты
            data = pd.read_csv(upload_file, parse_dates=['timestamp'])

    # Если пользователь выбирает генерацию данных
    elif source == "Генерация данных":
        # Генерируем фиктивные данные на основе шаблонов из seasonal_temperatures
        data = generate_realistic_temperature_data(list(seasonal_temperatures.keys()))

    # Проверяем, что данные доступны
    if data is not None:
        st.subheader("Семь случайных строк из датасета")
        # Отображаем 7 случайных строк из загруженного или сгенерированного датасета
        st.dataframe(data.sample(7))

        st.header('Аналитика исторических данных о температуре')

        # Пользователь выбирает город из доступных в данных
        city = st.selectbox('Выберите город', data['city'].unique())
        
        # Фильтруем данные для выбранного города
        df = data.query('city == @city')

        # Вычисляем статистики для данных
        df = calc_statistics(df)

        # Описательные статистики для температуры
        st.subheader("Описательные статистики")
        st.dataframe(df[['timestamp', 'temperature']].describe())

        # Типичные температуры по сезонам
        st.subheader('Типичные температуры по сезонам')
        st.dataframe(df.groupby(['season'])['mean'].max())

        # Динамика изменения температуры
        st.subheader('Динамика температуры')

        # Пользователь выбирает временной диапазон для анализа
        days = st.number_input(label='Выберите количество дней', min_value=50, max_value=365, value=365)
        date = st.date_input('Выберите дату начала', value=df['timestamp'].max() - pd.Timedelta(days=days))

        # Генерируем график изменения температуры за выбранный период
        fig = plot_temp(df, city, date, days)
        st.plotly_chart(fig)

        # Генерируем график скользящего среднего за все время
        fig = plot_moving_average(df, city)
        st.plotly_chart(fig)

        st.subheader('Анализ текущей температуры')

        # Проверяем, что данные о погоде доступны
        if data is not None:
            # Пользователь вводит API-ключ для получения данных о текущей погоде
            api_key = st.text_input("Введите ваш API-ключ OpenWeatherMap:")    

            if api_key:
                # Асинхронный запрос для получения текущей температуры через OpenWeatherMap API
                # так как у нас IO задача, то ассинхронные запросы работают быстрее
                # все эксперименты в experiment.ipynb
                resp = await get_weather(city, api_key)
                
                if 'main' in resp:
                    temp = resp['main']['temp']  # Текущая температура
                    st.write(f'Текущая температура в {city}: {temp} градусов.')

                    # Определяем текущий сезон на основе текущего месяца
                    season = month_to_season[datetime.now().month]
                    
                    # Находим среднее значение температуры и стандартное отклонение для текущего сезона
                    mean_season = df.query('season == @season')['mean'].iloc[0]
                    std_season = df.query('season == @season')['std'].iloc[0]

                    # Вычисляем доверительный интервал (95%)
                    up = mean_season + std_season * 1.96
                    down = mean_season - std_season * 1.96

                    # Сравниваем текущую температуру с доверительным интервалом
                    if temp > up or temp < down:
                        st.write(f'Сегодняшняя температура существенно отличается от типичной для этого сезона.')
                    else:
                        st.write(f'Сегодняшняя температура существенно не отличается от типичной для этого сезона.')

                    # Отображаем доверительный интервал
                    st.write(f'95% доверительный интервал - ({down}, {up})')
                else:
                    # Если API не возвращает данные, выводим ответ
                    st.write(resp)

                
if __name__ == '__main__':
    asyncio.run(main())

