from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import random
import traceback
import logging
import time

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

class Scraping:
    @staticmethod
    def get_page_with_requests(url):
        headers_pool = [
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "it-IT,it;q=0.9",
                "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "it,en-US;q=0.7,en;q=0.3",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
            }
        ]
        chosen_headers = random.choice(headers_pool)
        response = ""
        try:
            if HAS_CLOUDSCRAPER:
                scraper = cloudscraper.create_scraper(
                    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
                    delay=random.uniform(2, 5)
                )
                resp = scraper.get(url, headers=chosen_headers, timeout=30)
                response = resp.text
            else:
                session = requests.Session()
                session.headers.update(chosen_headers)
                # Prima richiesta alla home per ottenere i cookie
                parsed = __import__('urllib.parse', fromlist=['urlparse']).urlparse(url)
                home_url = f"{parsed.scheme}://{parsed.netloc}/"
                try:
                    session.get(home_url, timeout=10)
                    time.sleep(random.uniform(1, 3))
                except Exception:
                    pass
                response = session.get(url, timeout=30).text
        except (ValueError, Exception) as e:
            logging.error(f"Error in requests/cloudscraper: {e}")
            traceback.print_exc()
        return BeautifulSoup(response, 'lxml')

    @staticmethod
    def get_page_with_selenium(url):
        response = ""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.binary_location = "/usr/bin/chromium"
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--lang=it-IT')
            ua = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            ])
            
            # Use undetected_chromedriver if available
            try:
                import undetected_chromedriver as uc
                uc_options = uc.ChromeOptions()
                uc_options.binary_location = "/usr/bin/chromium"
                uc_options.add_argument('--headless=new')
                uc_options.add_argument('--no-sandbox')
                uc_options.add_argument('--disable-dev-shm-usage')
                uc_options.add_argument('--window-size=1920,1080')
                uc_options.add_argument('--lang=it-IT')
                uc_options.add_argument(f"user-agent={ua}")
                driver = uc.Chrome(options=uc_options, driver_executable_path="/usr/bin/chromedriver", browser_executable_path="/usr/bin/chromium")
            except ImportError:
                chrome_options.add_argument(f"user-agent={ua}")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                driver = webdriver.Chrome(options=chrome_options)

            driver.set_page_load_timeout(45)
            driver.get(url)
            # Attende che il body sia presente e poi un breve delay per JS dinamico
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(random.uniform(2, 4))
            except Exception:
                pass
            response = driver.page_source
        except (ValueError, Exception) as e:
            logging.error(f"Error in selenium: {e}")
            traceback.print_exc()
        finally:
            if driver:
                driver.quit()
        return BeautifulSoup(response, 'lxml')


scraping = Scraping()
