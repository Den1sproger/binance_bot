import time
import json

import websocket
import requests
import talib
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
        self.client = Client(api_key=API_KEY, api_secret=SECRET_KEY, testnet=True)
        self.buy = False
        self.sell = True
        self.last_ema_50 = None
        self.last_ema_150 = None
        self.last_number_of_trades = 0


    def get_prices(self) -> list[list[float]]:
        url = f'https://api.binance.com/api/v3/klines?symbol={self.symbol}&interval={self.interval}'
        r = requests.get(url)
        data = []
        for i in range(2, 5):    # high price, low price, close price
            item = [float(kline[i]) for kline in r.json()]
            data.append(item)

        return data   # prices


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


    def update_price_list(self, kline: dict,
                          delete_index: int = -1) -> None:
        count = 0
        for i in ['h', 'l', 'c']:            # high price, low price, close price
            self.prices_data[count].pop(delete_index)
            self.prices_data[count].append(float(kline.get(i)))
            count += 1


    def on_message(self, ws, message):  # getting data from websockets
        return_data = json.loads(message)
        kline = return_data.get('k')
        number_of_trades = int(kline.get('n'))

        if self.last_number_of_trades > number_of_trades:
            self.update_price_list(kline, delete_index=0)
        else:
            self.update_price_list(kline)
        
        ema_50 = talib.EMA(np.array(self.prices_data[2]), timeperiod=50)[-1]
        ema_150 = talib.EMA(np.array(self.prices_data[2]), timeperiod=150)[-1]
        print(f'50: {ema_50}')
        print(f'150 {ema_150}\n')

        slowk, slowd = talib.STOCH(
            high=np.array(self.prices_data[0]),
            low=np.array(self.prices_data[1]),
            close=np.array(self.prices_data[2]),
            fastk_period=5, slowk_period=5, slowd_period=5
        )
        
        print('k ==> ', slowk[-1])
        print('d ==> ', slowd[-1])
        
        self.last_number_of_trades = number_of_trades
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