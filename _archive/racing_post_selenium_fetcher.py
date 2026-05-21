#!/usr/bin/env python3
"""
Racing Post Selenium Fetcher
Uses headless Chrome to bypass anti-scraping measures
Install: pip install selenium webdriver-manager
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

class SeleniumRacingPostFetcher:
    """Fetch Racing Post data using Selenium to bypass blocks"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome driver"""
        if self.driver:
            return
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def fetch_race_card(self, course, date_str=None):
        """Fetch race card using Selenium"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        course_slug = course.lower().replace(' ', '-').replace('(', '').replace(')', '')
        url = f"https://www.racingpost.com/racecards/{course_slug}/{date_str}"
        
        try:
            self._init_driver()
            
            print(f"Fetching race card via Selenium: {course}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Give JavaScript time to render
            time.sleep(2)
            
            # Get page source and parse
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract race data (same parsing logic as original)
            races = self._parse_races(soup)
            
            print(f"  ✓ Found {len(races)} races")
            return races
        
        except Exception as e:
            print(f"  ✗ Selenium fetch error: {e}")
            return None
    
    def _parse_races(self, soup):
        """Parse race data from page"""
        races = []
        
        # Find race sections (adjust selectors based on actual Racing Post HTML)
        race_cards = soup.find_all('div', class_=['RC-runnerRow', 'raceCard'])
        
        for card in race_cards:
            race_data = {
                'runners': []
            }
            
            # Extract runner info
            runners = card.find_all('tr', class_=['RC-runnerRow', 'runner'])
            for runner in runners:
                runner_data = self._parse_runner(runner)
                if runner_data:
                    race_data['runners'].append(runner_data)
            
            if race_data['runners']:
                races.append(race_data)
        
        return races
    
    def _parse_runner(self, runner_elem):
        """Extract runner details"""
        try:
            data = {}
            
            # Horse name
            name_elem = runner_elem.find('a', class_=['RC-runnerName', 'horseName'])
            if name_elem:
                data['horse_name'] = name_elem.get_text(strip=True)
            
            # Form
            form_elem = runner_elem.find('span', class_='RC-form')
            if form_elem:
                data['form'] = form_elem.get_text(strip=True)
            
            # Trainer
            trainer_elem = runner_elem.find('a', class_='RC-trainer')
            if trainer_elem:
                data['trainer'] = trainer_elem.get_text(strip=True)
            
            # Jockey
            jockey_elem = runner_elem.find('a', class_='RC-jockey')
            if jockey_elem:
                data['jockey'] = jockey_elem.get_text(strip=True)
            
            # OR (Official Rating)
            or_elem = runner_elem.find('span', class_='RC-or')
            if or_elem:
                data['official_rating'] = or_elem.get_text(strip=True)
            
            return data if data else None
        
        except Exception as e:
            return None
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup"""
        self.close()


def main():
    """Test Selenium fetcher"""
    import sys
    
    fetcher = SeleniumRacingPostFetcher(headless=True)
    
    try:
        # Test with today's races
        course = sys.argv[1] if len(sys.argv) > 1 else "southwell"
        races = fetcher.fetch_race_card(course)
        
        if races:
            print(f"\n✅ Successfully fetched {len(races)} races")
            print(json.dumps(races[0], indent=2))
        else:
            print("❌ No races found")
    
    finally:
        fetcher.close()


if __name__ == '__main__':
    main()
