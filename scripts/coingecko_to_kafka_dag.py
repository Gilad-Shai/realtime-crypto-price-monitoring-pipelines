import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1&sparkline=false"

response = requests.get(COINGECKO_URL)
crypto_data = response.json()


for coin in crypto_data:
    if coin['name'] == "Bitcoin":
        print(coin)

