import time
import json

import websocket
import talib
import requests
import numpy as np

from config import API_KEY, SECRET_KEY
from binance.client import Client



SYMBOL = 'BTCUSDT'
INTERVAL = '1m'


class Stream:
    """Streaming data about the latest prices via websockets"""
    

    def __init__(self, symbol: str, interval: str) -> None:
        self.symbol = symbol
        self.interval = interval
        self.closing_data = self.get_closing_prices()     # list with the last prices
        self.client = Client(api_key=API_KEY, api_secret=SECRET_KEY)
        self.buy = False
        self.sell = True
        self.last_ema_50 = None
        self.last_ema_150 = None


    def get_closing_prices(self) -> list[float]:
        url = f'https://api.binance.com/api/v3/klines?symbol={self.symbol}&interval={self.interval}'
        r = requests.get(url)
        data = [float(item[4]) for item in r.json()]
        return data   # close prices


    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):             # for websockets
        print("### closed ###")

    def on_open(self, ws):
        print("### connected ###")

        
    def place_order(self, order_type: str) -> None:     # buy or sell
        if order_type.lower() == 'buy':
            order = self.client.create_order(symbol=SYMBOL, side='buy', type='MARKET')
            print('Open position', order)
        elif order_type.lower() == 'sell':
            order = self.client.create_order(symbol=SYMBOL, side='sell', type='MARKET')
            print('Close position', order)


    def on_message(self, ws, message):  # getting data from websockets
        return_data = json.loads(message)
        last_price = return_data.get("k").get("c")
        self.closing_data.append(float(last_price))
        self.closing_data.pop(0)

        ema_50 = talib.EMA(np.array(self.closing_data), timeperiod=50)[-1]
        ema_150 = talib.EMA(np.array(self.closing_data), timeperiod=150)[-1]

        if (ema_50 < ema_150 and self.last_ema_50) and \
            (self.last_ema_50 > self.last_ema_150 and not self.buy):
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

        time.sleep(1)


    def get_data(self):
        url = f'wss://stream.binance.com:9443/ws/{self.symbol.lower()}@kline_{self.interval}'
        wsa = websocket.WebSocketApp(
            url, on_message=self.on_message,
            on_error = self.on_error,
            on_close = self.on_close
        )
        wsa.on_open = self.on_open
        wsa.run_forever()



if __name__ == '__main__':
    stream = Stream(SYMBOL, INTERVAL)
    stream.get_data()




