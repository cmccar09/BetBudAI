#!/usr/bin/env python3
"""
AUTOMATED DAILY RESULTS SCRAPER
================================
Fully automated Racing Post scraper with robust error handling.
Runs daily to fetch all race results for the learning loop.

Features:
- Headless Chrome automation
- Proper resource cleanup
- Error recovery
- Database integration
- Zero manual work

Usage:
    python automated_daily_results_scraper.py           # Today's results
    python automated_daily_results_scraper.py 2026-02-03  # Specific date
"""

import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from decimal import Decimal
import time
import sys
import json
import atexit

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

class RacingPostScraper:
    def __init__(self):
        self.driver = None
        self.scraped_races = []
        self.total_runners = 0
        atexit.register(self.cleanup)  # Ensure cleanup on exit
    
    def init_driver(self):
        """Initialize Chrome WebDriver with robust options"""
        if self.driver:
            return  # Already initialized
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
    
    def cleanup(self):
        """Ensure driver is properly closed"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def parse_odds(self, odds_text):
        """Convert fractional odds to decimal"""
        if not odds_text or odds_text == '-':
            return None
        
        odds_text = odds_text.strip().upper()
        
        if 'EVS' in odds_text:
            return 2.0
        
        if '/' in odds_text:
            try:
                parts = odds_text.split('/')
                num = float(parts[0])
                den = float(parts[1])
                return round((num / den) + 1, 2)
            except:
                return None
        
        return None
    
    def get_race_urls(self, date_str):
        """Get all race URLs for a specific date"""
        try:
            self.init_driver()
            
            url = f"https://www.racingpost.com/results/{date_str}"
            self.driver.get(url)
            
            # Wait for race links to load
            time.sleep(3)
            
            # Find all result links
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/results/"]')
            race_urls = set()
            
            for link in links:
                href = link.get_attribute('href')
                if href and '/results/' in href and date_str in href:
                    # Filter to actual race result pages (contain race IDs)
                    parts = href.split('/')
                    if len(parts) >= 6 and parts[-1].isdigit():
                        race_urls.add(href)
            
            return list(race_urls)
        
        except Exception as e:
            print(f"Error getting race URLs: {e}")
            return []
    
    def scrape_race(self, url):
        """Scrape a single race and return results"""
        try:
            self.driver.get(url)
            
            # Wait for table
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'rp-horseTable')))
            time.sleep(3)  # Longer wait for dynamic content
            
            # Extract race info from URL
            parts = url.split('/')
            course_id = parts[-4]
            course_name = parts[-3]
            
            # Find table
            table = self.driver.find_element(By.CLASS_NAME, 'rp-horseTable')
            rows = table.find_elements(By.TAG_NAME, 'tr')
            
            results = []
            
            for row in rows:
                try:
                    row_class = row.get_attribute('class') or ''
                    if 'header' in row_class.lower():
                        continue
                    
                    # Position - try table cells first
                    position = None
                    try:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if cells and len(cells) > 0:
                            pos_text = cells[0].text.strip()
                            # Check if it looks like a position
                            if pos_text:
                                # Remove any non-numeric characters
                                pos_clean = ''.join(c for c in pos_text if c.isdigit())
                                if pos_clean:
                                    position = pos_clean
                    except:
                        pass
                    
                    if not position:
                        continue
                    
                    # Horse name - look for links
                    horse_name = None
                    try:
                        links = row.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            text = link.text.strip()
                            # Horse names are usually longer than 2 chars and don't contain numbers
                            if text and len(text) > 2 and not text.isdigit():
                                horse_name = text
                                break
                    except:
                        pass
                    
                    if not horse_name:
                        # Try spans as fallback
                        try:
                            spans = row.find_elements(By.TAG_NAME, 'span')
                            for span in spans:
                                text = span.text.strip()
                                if text and len(text) > 3 and not text.isdigit() and '/' not in text:
                                    horse_name = text
                                    break
                        except:
                            pass
                    
                    if not horse_name:
                        continue
                    
                    # Odds (SP)
                    odds = None
                    try:
                        spans = row.find_elements(By.TAG_NAME, 'span')
                        for span in spans:
                            text = span.text.strip()
                            if '/' in text or 'EVS' in text.upper():
                                odds = self.parse_odds(text)
                                break
                    except:
                        pass
                    
                    results.append({
                        'position': position,
                        'horse_name': horse_name,
                        'odds': odds
                    })
                
                except Exception as e:
                    continue
            
            if results:
                self.scraped_races.append({
                    'url': url,
                    'course_id': course_id,
                    'course_name': course_name,
                    'runners': len(results),
                    'winner': results[0]['horse_name'] if results else None
                })
                
                self.total_runners += len(results)
            
            return results
        
        except Exception as e:
            return []
    
    def update_database(self, race_results, date_str):
        """Match results with database picks and update outcomes"""
        updated_count = 0
        
        try:
            # Query picks for this date
            response = table.scan(
                FilterExpression='contains(#raceId, :date)',
                ExpressionAttributeNames={'#raceId': 'raceId'},
                ExpressionAttributeValues={':date': date_str}
            )
            
            picks = response.get('Items', [])
            
            for pick in picks:
                horse_name = pick.get('horseName')
                if not horse_name:
                    continue
                
                # Find matching result
                for race_url, results in race_results.items():
                    for result in results:
                        if result['horse_name'].lower() == horse_name.lower():
                            # Update outcome
                            outcome = 'won' if result['position'] == '1' else 'lost'
                            
                            table.update_item(
                                Key={
                                    'raceId': pick['raceId'],
                                    'timestamp': pick['timestamp']
                                },
                                UpdateExpression='SET outcome = :outcome, actual_position = :pos',
                                ExpressionAttributeValues={
                                    ':outcome': outcome,
                                    ':pos': result['position']
                                }
                            )
                            
                            updated_count += 1
                            break
            
            return updated_count
        
        except Exception as e:
            print(f"Database update error: {e}")
            return 0
    
    def run(self, date_str=None):
        """Main execution"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        print("=" * 80)
        print(f"AUTOMATED DAILY RESULTS SCRAPER")
        print("=" * 80)
        print(f"Date: {date_str}")
        print("=" * 80)
        
        try:
            # Get race URLs
            print("\n1. Fetching race list...")
            race_urls = self.get_race_urls(date_str)
            print(f"   Found {len(race_urls)} races")
            
            if not race_urls:
                print("   [!] No races found for this date")
                return
            
            # Scrape each race
            print(f"\n2. Scraping {len(race_urls)} races...")
            all_results = {}
            
            for idx, url in enumerate(race_urls, 1):
                try:
                    print(f"   [{idx}/{len(race_urls)}] {url.split('/')[-3]}...", end=' ')
                    results = self.scrape_race(url)
                    if results:
                        all_results[url] = results
                        winner = results[0]['horse_name']
                        print(f"OK {len(results)} runners (Winner: {winner})")
                    else:
                        print("[!] No data")
                except Exception as e:
                    print(f"[X] {str(e)[:50]}")
                
                # Brief pause between races
                time.sleep(1)
            
            # Update database
            print(f"\n3. Updating database...")
            updated = self.update_database(all_results, date_str)
            print(f"   Updated {updated} picks")
            
            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Races scraped:     {len(self.scraped_races)}/{len(race_urls)}")
            print(f"Total runners:     {self.total_runners}")
            print(f"Database updates:  {updated}")
            print("=" * 80)
            
            # Save results
            output = {
                'date': date_str,
                'total_races': len(race_urls),
                'scraped_races': len(self.scraped_races),
                'total_runners': self.total_runners,
                'database_updates': updated,
                'races': self.scraped_races
            }
            
            filename = f"results_{date_str}.json"
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"\n[OK] Results saved to: {filename}")
        
        finally:
            self.cleanup()

if __name__ == '__main__':
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    scraper = RacingPostScraper()
    scraper.run(date_arg)
