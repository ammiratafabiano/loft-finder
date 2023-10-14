import requests
from bs4 import BeautifulSoup

headers= {
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
  "Accept-Encoding": "gzip, deflate", 
  "Accept-Language": "it-IT,it;q=0.9", 
  "Upgrade-Insecure-Requests": "1", 
  "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
}

url="https://www.immobiliare.it/vendita-case/palermo/?localiMinimo=3&prezzoMinimo=60000&prezzoMassimo=220000&superficieMinima=90&fasciaPiano[]=20&fasciaPiano[]=30&criterio=dataModifica&ordine=desc"
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')
rawList = soup.find_all('li', class_='nd-list__item in-realEstateResults__item')
for rawAdv in rawList:
  temp = rawAdv.a
  if temp != None:
    url = temp['href']
    prize = rawAdv.find('li', class_='in-feat__item--main').get_text(separator=' ')
    print(url, prize)