import json
import time

import websocket


def on_message(ws, message):
    data = json.loads(message)

    count = 1
    for cryptocurrency in data:
        symbol, last_price = cryptocurrency["s"], cryptocurrency["c"]
        print(f"{count}. {symbol} -- {last_price}")
        count += 1
    time.sleep(5)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### connected ###")


def main():
    url = 'wss://stream.binance.com:9443/ws/!ticker@arr'
    wsa = websocket.WebSocketApp(
        url, on_message=on_message,
        on_error = on_error,
        on_close = on_close
    )
    wsa.on_open = on_open
    wsa.run_forever()


if __name__ == '__main__':
    main()
