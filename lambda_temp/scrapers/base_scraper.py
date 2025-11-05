# scrapers/base_scraper.py
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class BaseScraper(ABC):
    """Base class for all job board scrapers"""
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Setup headless Chrome driver with anti-detection"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Anti-detection measures
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
        })
    
    @abstractmethod
    def scrape(self, keywords, location):
        """Must be implemented by each scraper"""
        pass
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
