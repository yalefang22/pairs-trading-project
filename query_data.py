import pandas as pd
from pymongo import MongoClient
import numpy as np
import datetime
from upload_data import *

# d1 = "2021-10-10"
# d2 = "2021-12-6"
client = MongoClient("mongodb+srv://yalfan22:yale2004@cluster0.qszrw.mongodb.net/test", connect=False)
db = client.pairs_trading

btc = db.btc
eth = db.eth
ltc = db.ltc
bch = db.bch
xrp = db.xrp


def find_best_pairs(date1, date2):
    from values import find_correlation, find_cointegration
    coin_symbols = ["Bitcoin", "Ethereum", "Litecoin", "Ripple", "Bitcoin Cash"]
    index = []
    values_to_return = []
    for i in range(len(coin_symbols)-1):
        for j in range(i+1, len(coin_symbols)):
            prices1 = np.array(get_data(date1, date2, coin_symbols[i])[0])
            prices2 = np.array(get_data(date1, date2, coin_symbols[j])[0])
            # print("prices 1 %s %s" % (len(prices1), coin_symbols[i]))
            # print("prices 2 %s %s" % (len(prices2), coin_symbols[j]))
            values_to_return.append([coin_symbols[i], coin_symbols[j],
                                     find_correlation(prices1, prices2),
                                     round(find_cointegration(prices1, prices2)[1], 6)])
    df = pd.DataFrame(values_to_return, columns=['Coin1', 'Coin2', 'Correlation', 'Cointegration P-Value'])

    return df


def get_dates(start_date, end_date):
    start_date = datetime.datetime.fromisoformat(start_date)
    end_date = datetime.datetime.fromisoformat(end_date)
    day_count = (end_date - start_date).days + 1
    dates_array = []
    for single_date in (start_date + datetime.timedelta(n) for n in range(day_count)):
        dates_array.append(single_date)
    """d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    # d1 = '{d.month} {d.day} {d.year}'.format(d=d1)
    d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")
    # d2 = '{d.month} {d.day} {d.year}'.format(d=d2)
    dates = coin.find({'Date': {"$gte":  d1, "$lte":  d2}})
    dates_array = []
    for i in dates:
        dates_array.append(i['Date'])"""
    return dates_array


def get_dates_string_daily(dates):
    string_dates = []
    for i in range(len(dates)):
        string_dates.append('{d.month}-{d.day}-{d.year}'.format(d=dates[i]))
    return string_dates


def get_data(date1, date2, coin_string):
    coin_symbols = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Litecoin": "LTC-USD",
        "Ripple": "XRP-USD",
        "Bitcoin Cash": "BCH-USD"
    }
    coin = string_to_coin(coin_string)
    check_dates(coin_symbols[coin_string])
    average_prices, opens, highs, lows, closes, volumes, open_interest = [], [], [], [], [], [], []

    # avg1, open1, high1, low1, close1, volume1
    # avg2, open2, high2, low2, close2, volume2

    d1 = datetime.datetime.fromisoformat(date1)
    # d1 = '{d.month} {d.day} {d.year}'.format(d=d1)
    d2 = datetime.datetime.fromisoformat(date2)
    # d2 = '{d.month} {d.day} {d.year}'.format(d=d2)
    data_range = coin.find({'Date': {"$gte": d1, "$lte": d2}})
    for i in data_range:
        average_prices.append(i['Average'])
        opens.append(i['Open'])
        highs.append(i['High'])
        lows.append(i['Low'])
        closes.append(i['Close'])
        volumes.append(i['Volume'])
        open_interest.append(0)
    """average_prices.reverse()
    opens.reverse()
    highs.reverse()
    lows.reverse()
    closes.reverse()
    volumes.reverse()"""
    return average_prices, opens, highs, lows, closes, volumes, open_interest


def get_data_dataframe(d1, d2, coin_string):
    # get dates
    dates = np.array(get_dates(d1, d2))
    # dates = np.flip(dates)

    # get values
    avg1, open1, high1, low1, close1, volume1, open_interest = np.array(get_data(d1, d2, coin_string))

    # make array
    arr = np.array([dates, open1, high1, low1, close1, volume1, open_interest], dtype=object)
    arr = arr.T

    # make data frame
    df = pd.DataFrame(arr,  columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest'])
    df.set_index('Date', inplace=True, drop=True)
    return df


def string_to_coin(coin_string):
    coin = {
        "Bitcoin": btc,
        "Ethereum": eth,
        "Litecoin": ltc,
        "Bitcoin Cash": bch,
        "Ripple": xrp
    }[coin_string]
    return coin


def check_dates(coin_string):
    coins = {
        "BTC-USD": btc,
        "ETH-USD": eth,
        "LTC-USD": ltc,
        "XRP-USD": xrp,
        "BCH-USD": bch
    }
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    coin = coins[coin_string]
    last_date = coin.find().limit(1).sort([('$natural', -1)])[0]['Date'].date()
    first_date = coin.find()[0]['Date'].date()
    # print(last_date)
    # print(first_date)
    if last_date.strftime('%Y-%m-%d') != today and first_date.strftime("%Y-%m-%d") != today:
        print("updated %s date!" % coin_string)
        update_csv_db(coin_string, last_date, coin)

