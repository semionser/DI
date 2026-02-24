from flask import Flask, render_template
from datetime import datetime
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify

app = Flask(__name__)

start_date = datetime(2023, 12, 1, 0, 0, 0)

# Координаты центра Москвы
MOSCOW_LAT = 55.7558
MOSCOW_LON = 37.6176

# Астрономические данные для Москвы (24 февраля 2026)
SUN_DATA = {
    'sunrise': '07:34',
    'sunset': '17:52',
    'day_length': '10ч 23м'
}

MOON_DATA = {
    'phase': 'Первая четверть',
    'illumination': '48%'
}


def get_wind_direction(degrees):
    """Конвертирует градусы ветра в текстовое направление"""
    if degrees is None:
        return 'штиль'
    directions = ['северный', 'северо-восточный', 'восточный', 'юго-восточный',
                  'южный', 'юго-западный', 'западный', 'северо-западный']
    index = round(degrees / 45) % 8
    return directions[index]


def get_current_weather():
    """Получение текущей погоды от Open-Meteo"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': MOSCOW_LAT,
            'longitude': MOSCOW_LON,
            'current': [
                'temperature_2m',
                'relative_humidity_2m',
                'apparent_temperature',
                'is_day',
                'precipitation',
                'weather_code',
                'wind_speed_10m',
                'wind_direction_10m',
                'wind_gusts_10m',
                'pressure_msl'
            ],
            'timezone': 'Europe/Moscow'
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})

            weather_code = current.get('weather_code', 0)
            is_day = bool(current.get('is_day', 1))

            # Определяем тип осадков
            precip_type = 'none'
            if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]:
                precip_type = 'rain'
            elif weather_code in [71, 73, 75, 77, 85, 86]:
                precip_type = 'snow'

            # Определяем код для стиля
            style_code = 'cloudy'
            if weather_code == 0:
                style_code = 'clear'
            elif weather_code in [1, 2]:
                style_code = 'partly'
            elif weather_code in [45, 48]:
                style_code = 'fog'
            elif precip_type == 'rain':
                style_code = 'rain'
            elif precip_type == 'snow':
                style_code = 'snow'
            elif weather_code in [95, 96, 99]:
                style_code = 'storm'

            return {
                'temp': round(current.get('temperature_2m', 0)),
                'feels': round(current.get('apparent_temperature', 0)),
                'humidity': current.get('relative_humidity_2m', 0),
                'pressure': round(current.get('pressure_msl', 1013) * 0.75),
                'wind': round(current.get('wind_speed_10m', 0), 1),
                'gusts': round(current.get('wind_gusts_10m', 0), 1),
                'wind_dir': get_wind_direction(current.get('wind_direction_10m')),
                'desc': get_weather_description(weather_code, is_day),
                'style': style_code,
                'precip': precip_type,
                'code': weather_code,
                'is_day': is_day,
                'precip_mm': round(current.get('precipitation', 0), 1)
            }
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


def get_weather_description(code, is_day):
    """Краткое описание погоды"""
    desc = {
        0: 'ясно',
        1: 'преимущественно ясно',
        2: 'переменная облачность',
        3: 'пасмурно',
        45: 'туман', 48: 'изморозь',
        51: 'легкая морось', 53: 'морось', 55: 'сильная морось',
        56: 'ледяная морось', 57: 'сильная ледяная морось',
        61: 'небольшой дождь', 63: 'дождь', 65: 'сильный дождь',
        66: 'ледяной дождь', 67: 'сильный ледяной дождь',
        71: 'небольшой снег', 73: 'снег', 75: 'сильный снег',
        77: 'снежные зерна',
        80: 'ливень', 81: 'сильный ливень', 82: 'шквал',
        85: 'снегопад', 86: 'сильный снегопад',
        95: 'гроза', 96: 'гроза с градом', 99: 'сильная гроза'
    }
    return desc.get(code, 'неизвестно')


def get_weekly_forecast():
    """Получение недельного прогноза"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': MOSCOW_LAT,
            'longitude': MOSCOW_LON,
            'daily': [
                'weather_code',
                'temperature_2m_max',
                'temperature_2m_min',
                'precipitation_probability_max',
                'wind_speed_10m_max'
            ],
            'timezone': 'Europe/Moscow',
            'forecast_days': 7
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            daily = data.get('daily', {})

            forecast = []
            for i in range(7):
                date = datetime.strptime(daily['time'][i], '%Y-%m-%d')
                code = daily['weather_code'][i]

                forecast.append({
                    'date': date.strftime('%d.%m'),
                    'weekday': get_weekday_ru(date.weekday()),
                    'icon': get_weather_icon(code),
                    'temp_max': round(daily['temperature_2m_max'][i]),
                    'temp_min': round(daily['temperature_2m_min'][i]),
                    'precip': daily['precipitation_probability_max'][i],
                    'wind': round(daily['wind_speed_10m_max'][i], 1)
                })

            return forecast
        return None
    except Exception as e:
        print(f"Ошибка прогноза: {e}")
        return None


def get_weather_icon(code):
    """Иконка для прогноза"""
    if code == 0:
        return '☀️'
    elif code in [1, 2]:
        return '⛅'
    elif code == 3:
        return '☁️'
    elif code in [45, 48]:
        return '🌫️'
    elif code in [51, 53, 55, 61, 63, 80]:
        return '🌧️'
    elif code in [65, 66, 67, 81, 82]:
        return '🌦️'
    elif code in [71, 73, 85]:
        return '❄️'
    elif code in [75, 77, 86]:
        return '🌨️'
    elif code in [95, 96, 99]:
        return '⛈️'
    return '☁️'


def get_weekday_ru(weekday):
    weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    return weekdays[weekday]






@app.route('/')
def valentine():

    return render_template('valentine.html', start_date=start_date.strftime("%Y-%m-%dT%H:%M:%S"))



@app.route('/weather')
def index_weather():
    return render_template('index_minimal.html', sun_data=SUN_DATA, moon_data=MOON_DATA)


@app.route('/api/weather')
def api_weather():
    weather = get_current_weather()
    if not weather:
        weather = {
            'temp': -3, 'feels': -7, 'humidity': 93,
            'pressure': 745, 'wind': 7, 'gusts': 12,
            'wind_dir': 'южный', 'desc': 'снег', 'style': 'snow',
            'precip': 'snow', 'code': 73, 'is_day': False,
            'precip_mm': 0.5
        }
    weather['timestamp'] = datetime.now().strftime('%H:%M')
    return jsonify(weather)


@app.route('/api/weekly')
def api_weekly():
    forecast = get_weekly_forecast()
    if not forecast:
        forecast = []
        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            forecast.append({
                'date': date.strftime('%d.%m'),
                'weekday': get_weekday_ru(date.weekday()),
                'icon': '❄️',
                'temp_max': -3 + i,
                'temp_min': -7 + i,
                'precip': 70,
                'wind': 7.5
            })
    return jsonify(forecast)




if __name__ == '__main__':
    app.run(debug=True)