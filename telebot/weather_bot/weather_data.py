import os
import json
import hmac
import time
import uuid
import urllib
import hashlib
import platform
import requests
import urllib.parse
from base64 import b64encode
from selenium import webdriver
from googletrans import Translator
from urllib.request import urlopen
from fake_useragent import UserAgent
from selenium.webdriver.firefox.options import Options


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

        d = {}
        with open("conditions.txt", 'r', encoding='utf-8') as f:
            for i in f.readlines():
                key, val = i.strip().split(':')
                d[key] = val

        res = "*По данным Яндекс.Погоды:*\nТемпература: `" + str(temp) + "°`" + \
              "\nОщущается как: `" + str(feels_temp) + "°`" + \
              "\nДавление: `" + str(pressure) + " мм рт. ст.`" + \
              "\nВлажность: `" + str(humidity) + "%`" + \
              "\nВетер: `" + str(wind) + " (м/с)`" + \
              "\nСейчас: `" + d[str(condition)] + "`"
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
        now = JSON_object['current_observation']['condition']['code']

        d = {}
        with open("conditions.txt", 'r', encoding='utf-8') as f:
            for i in f.readlines():
                key, val = i.strip().split(':')
                d[key] = val

        wind = round(wind * 0.27, 2)
        res = "*По данным Yahoo:*\nТемпература: `" + str(temp) + "°`" + \
              "\nДавление: `" + str(pressure * 0.75) + " мм рт. ст.`" + \
              "\nВлажность: `" + str(humidity) + "%`" + \
              "\nВетер: `" + str(wind) + " (м/с)`" + \
              "\nСейчас: `" + d[str(now)] + "`"
        return res

    # 50 calls/day
    def accuweather(self):
        API_KEY = ''
        location_key = '294021'
        url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={API_KEY}&language=ru-ru&details=true'
        r = requests.get(url)
        data = r.json()

        now = data[0]['WeatherText']
        temp = data[0]['Temperature']['Metric']['Value']
        feels_temp = data[0]['RealFeelTemperatureShade']['Metric']['Value']
        relative_humidity = data[0]['RelativeHumidity']
        wind = data[0]['Wind']['Speed']['Metric']['Value']  # km/h
        pressure = data[0]['Pressure']['Metric']['Value']  # mb

        wind = round(wind * 0.27, 2)
        res = "*По данным AccuWeather:*\nТемпература: `" + str(temp) + "°`" + \
              "\nОщущается как: `" + str(feels_temp) + "°`" + \
              "\nДавление: `" + str(pressure * 0.75) + " мм рт. ст.`" + \
              "\nВлажность: `" + str(relative_humidity) + "%`" + \
              "\nВетер: `" + str(wind) + " (м/с)`" + \
              "\nСейчас: `" + now + "`"

        return res

    @staticmethod
    def rain_map():
        """
        For CLI CentOS7:
            wget <geckodriver.tar.gz>
            wget <firefox.tar.bz2>
            yum install gtk3
            yum install xorg-x11-server-Xvfb <optional>
        :return:
        """

        # <optional>
        # if platform.system() == "Linux":
        #     try:
        #         os.system("Xvfb :0 -ac & export DISPLAY=:0")
        #     except Exception as err:
        #         print(err)

        ua = UserAgent()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", ua.random)
        options = Options()
        options.add_argument('--headless')

        if platform.system() == "Windows":
            driver = webdriver.Firefox(
                firefox_profile=profile,
                options=options
            )
        else:
            driver = webdriver.Firefox(
                firefox_profile=profile,
                executable_path='/usr/local/bin/geckodriver',
                firefox_binary='/usr/local/firefox/firefox',
                options=options
            )

        url = 'https://www.windy.com/55.750/37.620?rain,55.761,37.895,9'
        driver.get(url)
        time.sleep(3)
        driver.get_screenshot_as_file('source/rain.png')
        driver.quit()
