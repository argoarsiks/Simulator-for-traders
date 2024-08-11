import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import webbrowser
from dash import dcc, html, Input, Output, State, Dash
import dash_bootstrap_components as dbc
import random


# Функция для получения исторических данных с интервалом в 15 минут
def get_historical_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date, interval='15m')
    return data


# Функция для расчета скользящей средней
def calculate_moving_average(data, window_size):
    data['SMA'] = data['Close'].rolling(window=window_size).mean()
    return data


# Функция для генерации торговых сигналов
def generate_signals(data):
    data['Signal'] = 0
    data.loc[data['Close'] > data['SMA'], 'Signal'] = 1  # Long
    data.loc[data['Close'] < data['SMA'], 'Signal'] = -1  # Short
    return data


# Функция для выбора случайной даты и времени
def get_random_date_and_time(data):
    last_date = data.index[-1]
    first_date = data.index[0]
    random_date = first_date + (last_date - first_date) * np.random.random()
    random_time = random.choice(pd.date_range(start='00:00', end='23:45', freq='15min').to_pydatetime())
    random_datetime = datetime.combine(random_date.date(), random_time.time())
    return random_datetime


# Функция для построения графика свечей
def plot_candlestick(data, start_time, end_time, entry_price=None, last_price=None):
    # Фильтруем данные по выбранному диапазону времени
    filtered_data = data.loc[start_time:end_time]

    # Создаем график свечей
    fig = go.Figure()

    # Добавляем график свечей
    fig.add_trace(go.Candlestick(
        x=filtered_data.index,
        open=filtered_data['Open'],
        high=filtered_data['High'],
        low=filtered_data['Low'],
        close=filtered_data['Close'],
        name='Candlestick'
    ))

    # Добавляем скользящую среднюю
    fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=filtered_data['SMA'],
        mode='lines',
        name='Simple Moving Average',
        line=dict(color='red')
    ))

    if entry_price is not None:
        # Добавляем полоску от цены входа
        fig.add_trace(go.Scatter(
            x=[filtered_data.index[0], filtered_data.index[-1]],
            y=[entry_price, entry_price],
            mode='lines',
            name='Entry Price',
            line=dict(color='blue', dash='dash')
        ))

    if last_price is not None:
        # Добавляем линию последней цены
        fig.add_trace(go.Scatter(
            x=[filtered_data.index[0], filtered_data.index[-1]],
            y=[last_price, last_price],
            mode='lines',
            name='Last Price',
            line=dict(color='green', dash='dash')
        ))

    fig.update_layout(
        title='Price and Trading Signals',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis=dict(
            rangeslider=dict(visible=False),
            fixedrange=True
        ),
        yaxis=dict(
            fixedrange=True
        ),
        autosize=True,
        height=800,  # Увеличение высоты графика
        dragmode=False,
        hovermode='closest'
    )

    return fig


# Основной код
if __name__ == "__main__":
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    ticker = 'BTC-USD'
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d')
    window_size = 20

    # Получаем исторические данные
    data = get_historical_data(ticker, start_date, end_date)

    # Расчитываем скользящую среднюю
    data = calculate_moving_average(data, window_size)

    # Генерируем торговые сигналы
    data = generate_signals(data)

    # Выбираем случайную дату и время
    random_datetime = get_random_date_and_time(data)
    start_time = random_datetime - timedelta(hours=12)
    end_time = random_datetime + timedelta(hours=12)

    # Переменные для отслеживания состояния сделки
    app_state = {
        'entry_price': None,
        'direction': None,
        'entry_time': None,
        'last_price': None,
        'step_count': 0
    }

    app.layout = html.Div([
        html.Div([
            dbc.Button('Long', id='long-button', color='success', n_clicks=0, className='me-2'),
            dbc.Button('Short', id='short-button', color='danger', n_clicks=0, className='me-2'),
            dbc.Button('Next Step', id='next-step', color='primary', n_clicks=0, disabled=False)
        ], style={'margin-bottom': '20px'}),
        dcc.Graph(id='candlestick-graph'),
        html.Div(id='profit-loss', style={'margin-top': '20px', 'font-size': '20px'})
    ], style={'padding': '20px'})


    @app.callback(
        [Output('candlestick-graph', 'figure'),
         Output('profit-loss', 'children'),
         Output('next-step', 'disabled')],
        [Input('long-button', 'n_clicks'),
         Input('short-button', 'n_clicks'),
         Input('next-step', 'n_clicks')],
        [State('candlestick-graph', 'figure')]
    )
    def update_graph(long_clicks, short_clicks, next_step_clicks, existing_figure):
        global app_state

        # Определяем новое время для графика
        if next_step_clicks > app_state['step_count']:
            app_state['step_count'] += 1
            if app_state['step_count'] > 5:
                return existing_figure, '', True  # Деактивируем кнопку после 5 шагов
            new_start_time = start_time + timedelta(hours=app_state['step_count'])
            new_end_time = new_start_time + timedelta(hours=24)
        else:
            new_start_time = start_time + timedelta(hours=app_state['step_count'])
            new_end_time = new_start_time + timedelta(hours=24)

        # Определяем последнюю цену на текущем графике
        last_price = data.loc[new_end_time]['Close'] if new_end_time in data.index else None
        app_state['last_price'] = last_price

        # Если выбрана кнопка Long или Short, устанавливаем начальную цену
        if long_clicks > 0 or short_clicks > 0:
            if last_price is not None:
                if app_state['entry_price'] is None:  # Устанавливаем цену входа только если она не установлена
                    app_state['entry_price'] = last_price
                    app_state['entry_time'] = new_end_time
                    app_state['direction'] = 'long' if long_clicks > 0 else 'short'

        fig = plot_candlestick(data, new_start_time, new_end_time, app_state['entry_price'], app_state['last_price'])

        profit_loss_text = ''
        if app_state['direction'] and app_state['entry_price']:
            if next_step_clicks > 0:
                future_datetime = new_end_time

                if future_datetime in data.index:
                    exit_price = data.loc[future_datetime]['Close']
                    if app_state['direction'] == 'long':
                        profit_loss = exit_price - app_state['entry_price']
                    else:
                        profit_loss = app_state['entry_price'] - exit_price

                    profit_loss_text = f"Profit/Loss: ${profit_loss:.2f} ({(profit_loss / app_state['entry_price']) * 100:.2f}%)"

        return fig, profit_loss_text, app_state['step_count'] >= 5


    # Открываем браузер с Dash приложением
    webbrowser.open('http://127.0.0.1:8050/')

    app.run_server(debug=True)
