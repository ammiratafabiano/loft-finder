import requests
from bs4 import BeautifulSoup

headers= {
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
  "Accept-Encoding": "gzip, deflate", 
  "Accept-Language": "it-IT,it;q=0.9", 
  "Upgrade-Insecure-Requests": "1", 
  "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
}

url = "https://www.idealista.it/vendita-case/palermo-palermo/con-prezzo_220000,prezzo-min_60000,dimensione_90,trilocali-3,quadrilocali-4,5-locali-o-piu,piani-intermedi,ultimo-piano,/?ordine=pubblicazione-desc"
#proxies = {
#"http": 'http://151.63.46.97:8118'
#}
#response = requests.get(url,headers=headers, proxies=proxies, stream=True)
#print(response.raw._connection.sock.getsockname())
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')
raw = soup.find_all('article', class_='item')
for el in raw:
  	urlItem = el.find('a', class_='item-link')
  	if urlItem:
	    url = urlItem['href']
	    prize = el.find('span', class_='item-price').get_text()
	    print(url,prize)