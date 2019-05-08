import json
import hmac
import time
import uuid
import urllib
import hashlib
import requests
import urllib.parse
from base64 import b64encode
from googletrans import Translator
from urllib.request import urlopen


class Weather:
    # 60 req/min - max
    def openweathermap(self):
        translator = Translator()
        API_KEY = ''
        s_city = "Moscow,RU"
        r = requests.get("http://api.openweathermap.org/data/2.5/find",
                         params={'q': s_city, 'units': 'metric', 'APPID': API_KEY})
        data = r.json()

        temp = data['list'][0]['main']
        wind = data['list'][0]['wind']['speed']
        clouds = data['list'][0]['clouds']['all']
        wtype = data['list'][0]['weather'][0]['main']
        wdesc = data['list'][0]['weather'][0]['description']

        wtype_tr = translator.translate(wtype, dest="ru").text + " ("
        wdesc_tr = translator.translate(wdesc, dest="ru").text + ")"

        res = "Температура: `" + str(temp['temp']) + "°`" + \
              "\nМинимальная: `" + str(temp['temp_min']) + "°`" + \
              "\nМаксимальная: `" + str(temp['temp_max']) + "°`" + \
              "\nДавление: `" + str(temp['pressure'] * 0.75) + " мм рт. ст.`" + \
              "\nВлажность: `" + str(temp['humidity']) + "%`" + \
              "\nВетер: `" + str(wind) + " (м/с)`" + \
              "\nОблачность: `" + str(clouds) + "%`" + \
              "\nСейчас: `" + wtype_tr + wdesc_tr + "`"
        return res

    # 50 req/day - max
    def yandex(self):
        API_KEY = ''
        url = 'https://api.weather.yandex.ru/v1/forecast?'

        headers = {
            'X-Yandex-API-Key': API_KEY
        }
        data = {
            'lat': 55.7,
            'lon': 37.6,
            'lang': 'ru_RU',
        }

        r = requests.get(url, headers=headers, data=data)
        data = r.json()

        temp = data['fact']['temp']
        feels_temp = data['fact']['feels_like']
        condition = data['fact']['condition']
        wind = data['fact']['wind_speed']
        pressure = data['fact']['pressure_mm']
        humidity = data['fact']['humidity']

        cond = {'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно с прояснениями',
                'overcast': 'пасмурно', 'partly-cloudy-and-light-rain': 'небольшой дождь',
                'partly-cloudy-and-rain': 'дождь', 'overcast-and-rain': 'сильный дождь',
                'overcast-thunderstorms-with-rain': 'сильный дождь, гроза', 'cloudy-and-light-rain': 'небольшой дождь',
                'overcast-and-light-rain': 'небольшой дождь', 'cloudy-and-rain': 'дождь',
                'overcast-and-wet-snow': 'дождь со снегом', 'partly-cloudy-and-light-snow': 'небольшой снег',
                'partly-cloudy-and-snow': 'снег', 'overcast-and-snow': 'снегопад',
                'cloudy-and-light-snow': 'небольшой снег', 'overcast-and-light-snow': 'небольшой снег',
                'cloudy-and-snow': 'снег'}

        res = "*По данным Яндекс.Погоды:*\nТемпература: `" + str(temp) + "°`" + \
              "\nОщущается как: `" + str(feels_temp) + "°`" + \
              "\nДавление: `" + str(pressure) + " мм рт. ст.`" + \
              "\nВлажность: `" + str(humidity) + "%`" + \
              "\nВетер: `" + str(wind) + " (м/с)`" + \
              "\nСейчас: `" + cond[condition] + "`"
        return res

    def _generate_signature(self, key, data):
        key_bytes = bytes(key, 'utf-8')
        data_bytes = bytes(data, 'utf-8')
        signature = hmac.new(
            key_bytes,
            data_bytes,
            hashlib.sha1
        ).digest()
        return b64encode(signature).decode()

    def yahoo(self):
        translator = Translator()
        woeid = '24553585'  # Moscow
        app_id = ''
        consumer_key = ''
        consumer_secret = ''
        url = 'https://weather-ydn-yql.media.yahoo.com/forecastrss'

        method = 'GET'
        concat = '&'
        query = {
            'woeid': woeid,
            'u': 'c',
            'format': 'json'
        }
        oauth = {
            'oauth_consumer_key': consumer_key,
            'oauth_nonce': uuid.uuid4().hex,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0'
        }

        # Prepare signature string (merge all params and SORT them)
        merged_params = query.copy()
        merged_params.update(oauth)
        sorted_params = [
            k + '=' + urllib.parse.quote(merged_params[k], safe='')
            for k in sorted(merged_params.keys())
        ]
        signature_base_str = (
                method +
                concat +
                urllib.parse.quote(
                    url,
                    safe=''
                ) +
                concat +
                urllib.parse.quote(concat.join(sorted_params), safe='')
        )

        # Generate signature
        composite_key = urllib.parse.quote(
            consumer_secret,
            safe=''
        ) + concat
        oauth_signature = self._generate_signature(
            composite_key,
            signature_base_str
        )

        # Prepare Authorization header
        oauth['oauth_signature'] = oauth_signature
        auth_header = (
                'OAuth ' +
                ', '.join(
                    [
                        '{}="{}"'.format(k, v)
                        for k, v in oauth.items()
                    ]
                )
        )

        # Send request
        url = url + '?' + urllib.parse.urlencode(query)
        request = urllib.request.Request(url)
        request.add_header('Authorization', auth_header)
        request.add_header('X-Yahoo-App-Id', app_id)
        response = urllib.request.urlopen(request).read()
        JSON_object = json.loads(response.decode('utf-8'))

        wind = JSON_object['current_observation']['wind']['speed']
        humidity = JSON_object['current_observation']['atmosphere']['humidity']
        pressure = JSON_object['current_observation']['atmosphere']['pressure']
        temp = JSON_object['current_observation']['condition']['temperature']
        now = JSON_object['current_observation']['condition']['text']
        now_tr = translator.translate(now, dest="ru").text

        res = "*По данным Yahoo:*\nТемпература: `" + str(temp) + "°`" + \
              "\nДавление: `" + str(pressure * 0.75) + " мм рт. ст.`" + \
              "\nВлажность: `" + str(humidity) + "%`" + \
              "\nВетер: `" + str(wind * 0.27) + " (м/с)`" + \
              "\nСейчас: `" + now_tr + "`"
        return res
