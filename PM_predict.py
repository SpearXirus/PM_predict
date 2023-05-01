from flask import Flask, render_template
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import time
import joblib

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('PM_predict/ready.html')

@app.route('/predict')
def predict():
    url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%EB%82%A0%EC%94%A8'
    url1 = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%EB%AF%B8%EC%84%B8%EB%A8%BC%EC%A7%80'
    url2 = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%EC%B4%88%EB%AF%B8%EC%84%B8%EB%A8%BC%EC%A7%80'
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(2)
    driver.find_element(By.CLASS_NAME, 'title_select').click()
    driver.find_elements(By.CLASS_NAME, 'item_link')[1].click()
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    temperatures = [int(soup.select('.temperature_text')[0].text.strip().split('도')[1].strip('°'))]
    humidities = [int(soup.select('.sort')[1].text.split()[1].strip('%'))]
    winds = [soup.select('.sort')[2].text.replace('\n', ' ').strip().strip('m/s')]
    for i in range(23):
        temperatures.append(int(soup.select('.num')[i].text.strip('°')))
        humidities.append(int(soup.select('.num')[i + 144].text))
        winds.append(soup.select('.value')[i + 72].text + ' ' + soup.select('.num')[i + 72].text)
    rains = []
    for i in range(24):
        rains.append(float(soup.select('.data_inner')[i].text.strip()))
    temperature = sum(temperatures) / len(temperatures)
    rain = sum(rains)
    humidity = sum(humidities) / len(humidities)
    def convert_wind(wind):
        way = wind.split()[0]
        speed = float(wind.split()[1])
        converted_wind = np.zeros(16)
        if way == '북풍':
            converted_wind = np.array([speed, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '북북동풍':
            converted_wind = np.array([0, speed, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '북동풍':
            converted_wind = np.array([0, 0, speed, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '동북동풍':
            converted_wind = np.array([0, 0, 0, speed, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '동풍':
            converted_wind = np.array([0, 0, 0, 0, speed, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '동남동풍':
            converted_wind = np.array([0, 0, 0, 0, 0, speed, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '남동풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, speed, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '남남동':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, speed,
                                       0, 0, 0, 0, 0, 0, 0, 0])
        if way == '남풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       speed, 0, 0, 0, 0, 0, 0, 0])
        if way == '남남서':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, speed, 0, 0, 0, 0, 0, 0])
        if way == '남서풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, speed, 0, 0, 0, 0, 0])
        if way == '서남서풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, speed, 0, 0, 0, 0])
        if way == '서풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, speed, 0, 0, 0])
        if way == '서북서풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, speed, 0, 0])
        if way == '북서풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, speed, 0])
        if way == '북북서풍':
            converted_wind = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, speed])
        return converted_wind
    converted_winds = []
    for wind in winds:
        converted_winds.append(convert_wind(wind))
    wind_sum = np.zeros(16)
    for converted_wind in converted_winds:
        wind_sum += converted_wind
    wind = wind_sum / 24
    driver.close()
    res1 = requests.get(url1)
    soup1 = BeautifulSoup(res1.text, 'html.parser')
    res2 = requests.get(url2)
    soup2 = BeautifulSoup(res2.text, 'html.parser')
    PM10 = int(soup1.select('td > span')[0].text)
    PM25 = int(soup2.select('td > span')[0].text)
    if rain > 0:
        precipitation = [0, 1]
    else:
        precipitation = [1, 0]
    test_set = [[PM10, PM25, temperature, rain, humidity] + list(wind) + precipitation]
    scaler = joblib.load('C:/PM_predict/scaler.sav')
    model = joblib.load('C:/PM_predict/final.model')
    predict = model.predict(scaler.transform(test_set))[0]
    probablity = model.predict_proba(scaler.transform(test_set))[0][1]
    if predict == 0:
        message = "내일 공기가 나쁘지 않습니다. 마스크를 안 쓰셔도 좋습니다."
    if predict == 1:
        message = "내일 공기가 나쁩니다. 마스크 착용을 권장드립니다."
    return render_template('PM_predict/result.html',
                           message=message, probablity=probablity * 100)

if __name__ == '__main__':
    app.run(port=8000, threaded=False)



