# -*- coding: utf-8 -*-
# author: klosyx
# last modified: 2020-7-3 21:27

import os
import time
from threading import Thread
import requests


WORD = 'GO AHEAD' # one WORD that will be displayed
WEATHER = "LOADING"  # initilization of weather
WORK_TIME = 45  # tomato clock WORK_TIME setup
REST_TIME = 5 # tomato clock REST_TIME setup
CITY = 'Guangzhou'  # CITY name for weather query
DISTRICT = ''  # DISTRICT name for weather query
TIME_LEFT = '0 day left'
KEY_TIME = '2021-2-24 00:00:00'  # %Y-%m-%d %X


def get_time_left():
    end = time.mktime(time.strptime(KEY_TIME, '%Y-%m-%d %X'))
    now = time.time()
    res = ''.join((str(int((end - now) // (24 * 3600))), ' days left'))
    return res


class MainClock(Thread):

    def __init__(self):
        super().__init__()
        self._this = True # run main clock at first start
        self._running = True
        self._start = ""

    def set_this(self):
        self._this = not self._this
        self._start = ""

    def terminate(self):
        self._running = False

    def run(self):
        global WORD
        global WEATHER
        global TIME_LEFT
        
        while self._running:
            if time.strftime('%M', time.localtime()) != self._start:
                if self._this:
                    TIME_LEFT = get_time_left()
                    command = ''.join(('./showclock.sh ', '\'', WORD, '\' \'', WEATHER,
                                       '\' \'', TIME_LEFT, '\''))
                    os.system(command)
                self._start = time.strftime('%M', time.localtime())
            time.sleep(1)

    def flush(self):
        global WORD
        global WEATHER
        
        if self._this:
            command = ' '.join(('./showclock.sh', WORD, WEATHER))
            os.system(command)


class TomatoClock(Thread):

    def __init__(self):
        super().__init__()
        self._running = True
        self._start = 0.0
        self._this = False

    def terminate(self):
        self._running = False

    def set_this(self):
        self._this = not self._this
        self._start = 0.0

    def run(self):
        global WORK_TIME
        global REST_TIME
        # os.system('./tomato.sh ' + '2 5 31')
        while self._running:
            if self._this:
                x = WORK_TIME
                while x >= 0 and self._running and self._this:
                    if time.time() - self._start > 60.0:
                        if x != 0:
                            command = ' '.join(('./tomato.sh',
                                                str(x // 10 % 10), str(x % 10), '31'))
                            os.system(command)
                        self._start = time.time()
                        x = x - 1
                    time.sleep(1)   
                x = REST_TIME
                self._start = 0.0
                # os.system('./tomato.sh ' + '0 5 32')
                while x >= 0 and self._running and self._this:
                    if time.time() - self._start > 60.0:
                        if x != 0:
                            command = ' '.join(('./tomato.sh', str(0), str(x % 10), '32'))
                            os.system(command)
                        self._start = time.time()
                        x = x - 1
                    time.sleep(1)
            time.sleep(1)


def replace_special_symbol(msg):
    replacement_dict = {
        '→': 'W',
        '↑': 'S',
        '←': 'E',
        '↓': 'N',
        '↗': 'WS',
        '↖': 'ES',
        '↙': 'EN',
        '↘': 'WN'
                   }
    for ch in msg:
        if ch in replacement_dict.keys():
            msg = msg.replace(ch, ''.join((replacement_dict[ch], '-')))
        else:
            pass
    return msg

def weather_logging(msg):
    global CITY
    line = ' '.join((CITY, time.strftime(': %Y-%m-%d %H:%M ',
                                         time.localtime()), msg, '\n'))
    with open('./weather.log', 'a+') as f:
        f.write(line)
    return


class GetWeather(Thread):
    
    def __init__(self, flushtime = 1800.0):
        super().__init__()
        self._running = True
        self._flushtime = flushtime
        self._start = 0.0

    def terminate(self):
        self._running = False

    def run(self):
        global WEATHER
        while self._running:
            if time.time() - self._start > float(self._flushtime):
                _weather = ''
                while _weather == '' and self._running:
                    try:
                        url = ''.join(('https://wttr.in/', '~', DISTRICT,
                                       '+', CITY, '?format=%C+%t+%h+%w+%o'))
                        r = requests.get(url, timeout=10)
                        r.raise_for_status()  # if respond code is not 200, rasie exception
                    except Exception:
                        time.sleep(10)
                        continue
                    _weather = r.text.strip()
                    if _weather:
                        WEATHER = replace_special_symbol(_weather[0:-2])
                        # weather_logging(WEATHER)
                        self._start = time.time()
                    time.sleep(10)
            time.sleep(1)
            
            

def run():
    t1 = MainClock()
    t2 = TomatoClock()
    t3 = GetWeather(600.0)
    threads = [t1,t2,t3]
    for t in threads:
        t.start()
    
    try:
        while True: # main cycle
            input() # waiting for enter to change thread
            t1.set_this()
            t2.set_this()
    
    except KeyboardInterrupt:
        pass

    finally:
        for t in threads:
            t.terminate()
            t.join()


if __name__ == '__main__':
    run()
