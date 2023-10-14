import requests
from bs4 import BeautifulSoup

headers = {
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	"Accept-Encoding": "gzip, deflate",
	"Accept-Language": "it-IT,it;q=0.9",
	"Upgrade-Insecure-Requests": "1",
	"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
}
headers = {
    'authority': 'cdn.cookielaw.org',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
    'sec-ch-ua-mobile': '?1',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Mobile Safari/537.36',
    'sec-ch-ua-platform': '"Android"',
    'accept': '*/*',
    'origin': 'https://www.casa.it',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.casa.it/vendita/residenziale/milano/con-da-privati/',
    'accept-language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7'
}

url="https://www.casa.it/vendita/residenziale/milano/con-da-privati?priceMin=100000&priceMax=260000&mqMin=60&sortType=date_desc"
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')
print(response.text)
raw = soup.find_all('article', class_='srp-card')
for el in raw:
  if el.a != None:
    url = el.a['href']
    prize = el.find('div', class_='info-features__price').get_text()
    print(url,prize)