import csv
from binance.client import Client
from binance.enums import HistoricalKlinesType

client = Client("", "")

timeframes = ['1m','3m', '5m']
pairs = ['ETHUSDT','BTCUSDT','DOGEUSDT','LINKUSDT']
#pairs = ['DOGEUSDT','ADAUSDT','MATICUSDT']
for pair in pairs:
    for time in timeframes:
        csvfile = open(f"./data/{pair}-2021-2022-{time}.csv", 'w', newline='')
        candlestick_writer = csv.writer(csvfile, delimiter=',')


        candlesticks = client.get_historical_klines(pair, time, "17 June, 2022", "17 Sept, 2022",klines_type=HistoricalKlinesType.FUTURES)

        for candlestick in candlesticks:
            candlestick[0] = candlestick[0] / 1000 # divide timestamp to ignore miliseconds
            print(candlestick[0])
            candlestick_writer.writerow(candlestick)


        csvfile.close()
##print(Client.KLINE_INTERVAL_1MINUTE)