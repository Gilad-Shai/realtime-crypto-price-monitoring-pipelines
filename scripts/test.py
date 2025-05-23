import requests


coin_input = input("Please Chose A Coin: ")
test = "bitcoin"

url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1&sparkline=false"

response = requests.get(url)
deta = response.json()

for coin in deta:
    if coin['name'] == coin_input:
        print(coin)