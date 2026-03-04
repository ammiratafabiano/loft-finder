from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import random
import traceback
import logging

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

class Scraping:
    @staticmethod
    def get_page_with_requests(url):
        headers = [
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "it-IT,it;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            }
        ]
        response = ""
        try:
            if HAS_CLOUDSCRAPER:
                scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'darwin', 'mobile': False})
                response = scraper.get(url, headers=random.choice(headers)).text
            else:
                response = requests.get(url, headers=random.choice(headers)).text
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
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
            
            # Use undetected_chromedriver if available
            try:
                import undetected_chromedriver as uc
                # uc gestisce autonomamente il bypass dell'automazione,
                # non supporta add_experimental_option
                uc_options = uc.ChromeOptions()
                uc_options.binary_location = "/usr/bin/chromium"
                uc_options.add_argument('--headless=new')
                uc_options.add_argument('--no-sandbox')
                uc_options.add_argument('--disable-dev-shm-usage')
                uc_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
                driver = uc.Chrome(options=uc_options, driver_executable_path="/usr/bin/chromedriver", browser_executable_path="/usr/bin/chromium")
            except ImportError:
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                driver = webdriver.Chrome(options=chrome_options)
                
            driver.set_page_load_timeout(30)
            driver.get(url)
            response = driver.page_source
        except (ValueError, Exception) as e:
            logging.error(f"Error in selenium: {e}")
            traceback.print_exc()
        finally:
            if driver:
                driver.quit()
        return BeautifulSoup(response, 'lxml')


scraping = Scraping()
