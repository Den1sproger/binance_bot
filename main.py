import time
import json

import unicorn_binance_websocket_api
import talib
import requests
import numpy as np

from config import API_KEY, SECRET_KEY
from binance.client import Client


SYMBOL = 'BTCUSDT'
INTERVAL = '1m'


class Stream:
    """Streaming data about the last, low and high prices via websockets"""
    

    def __init__(self, symbol: str, interval: str) -> None:
        self.symbol = symbol
        self.interval = interval
        self.prices_data = self.get_prices()     # list with the last prices
        self.client = Client(api_key=API_KEY, api_secret=SECRET_KEY)
        self.buy = False
        self.sell = True
        self.last_ema_50 = None
        self.last_ema_150 = None
        self.last_slowk = None
        self.last_slowd = None
        self.last_number_of_trades = 0


    def get_prices(self) -> list[list[float]]:
        url = f'https://api.binance.com/api/v3/klines?symbol={self.symbol}&interval={self.interval}'
        r = requests.get(url)

        data = []
        for i in range(2, 5):    # high price, low price, close price
            item = [float(kline[i]) for kline in r.json()]
            data.append(item)

        return data   # prices

        
    def place_order(self, order_type: str) -> None:     # buy or sell
        if order_type.lower() == 'buy':
            order = self.client.create_order(symbol=SYMBOL, side='buy', type='MARKET', )
            print('Open position', order)
        elif order_type.lower() == 'sell':
            order = self.client.create_order(symbol=SYMBOL, side='sell', type='MARKET')
            print('Close position', order)


    def update_price_list(self, kline: dict,
                          delete_index: int = -1) -> None:
        count = 0
        for i in ['h', 'l', 'c']:            # high price, low price, close price
            self.prices_data[count].pop(delete_index)
            self.prices_data[count].append(float(kline.get(i)))
            count += 1


    def on_message(self, kline: dict) -> None:    # get data from websockets
        number_of_trades = int(kline.get('n'))
        print(kline.get('c'))
        if self.last_number_of_trades > number_of_trades:
            self.update_price_list(kline, delete_index=0)
        else:
            self.update_price_list(kline)
        # print(self.prices_data[2][-1])
        # ema 50 and 150
        ema_50 = talib.EMA(np.array(self.prices_data[2]), timeperiod=50)[-1]
        ema_150 = talib.EMA(np.array(self.prices_data[2]), timeperiod=150)[-1]
        # print(f'50: {ema_50}')
        # print(f'150 {ema_150}\n')
        # stochastic
        slowk, slowd = talib.STOCH(
            high=np.array(self.prices_data[0]),
            low=np.array(self.prices_data[1]),
            close=np.array(self.prices_data[2]),
            fastk_period=5, slowk_period=5, slowd_period=5
        )
        # print(f'Orange: {slowk[-1]}')
        # print(f'Blue: {slowd[-1]}')

        # condition
        if (ema_50 < ema_150 and self.last_ema_50) and \
            (self.last_ema_50 > self.last_ema_150 and not self.buy) and \
            (slowk > 80 and slowd > 80) and \
            (slowk > slowd and self.last_slowk) and \
            (self.last_slowk < self.last_slowd):
            print('Buy!')
            self.place_order('buy')
            self.buy = True
            self.sell = False

        elif (ema_50 > ema_150 and self.last_ema_50) and \
            (self.last_ema_50 > self.last_ema_150 and not self.sell):
            print('Sell!')
            self.place_order('sell')
            self.buy = False
            self.sell = True

        self.last_ema_50 = ema_50
        self.last_ema_150 = ema_150
        self.last_slowk = slowk
        self.last_slowd = slowd


    def streaming(self):
        ubwa = unicorn_binance_websocket_api.BinanceWebSocketApiManager(exchange="binance.com")
        ubwa.create_stream([f'kline_{self.interval}'], [self.symbol])
        
        while True:
            message = ubwa.pop_stream_data_from_stream_buffer()
            if message:
                try:
                    data = json.loads(message)
                    kline = data['data']['k']
                except KeyError: pass
                else: self.on_message(kline)
                finally: time.sleep(2)



if __name__ == '__main__':
    stream = Stream(SYMBOL, INTERVAL)
    stream.streaming()