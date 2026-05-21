#!/usr/bin/env python3
"""
Get yesterday's Racing Post results
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

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
racingpost_table = dynamodb.Table('RacingPostRaces')

def parse_odds(odds_text):
    """Convert fractional odds to decimal"""
    if not odds_text or odds_text == '-':
        return None
    
    odds_text = odds_text.strip().upper()
    
    if 'EVS' in odds_text:
        return 2.0
    
    if '/' in odds_text:
        try:
            parts = odds_text.split('/')
            return round((float(parts[0]) / float(parts[1])) + 1, 2)
        except:
            return None
    return None

def scrape_yesterday():
    """Scrape yesterday's races"""
    
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    
    # Setup Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = None
    scraped_count = 0
    
    try:
        print(f"\n{'='*60}")
        print(f"RACING POST SCRAPER - YESTERDAY ({date_str})")
        print(f"{'='*60}\n")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)
        
        # Get race list
        print(f"1. Fetching race list for {date_str}...")
        driver.get(f"https://www.racingpost.com/results/{date_str}")
        time.sleep(3)
        
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/results/"]')
        race_urls = set()
        
        for link in links:
            href = link.get_attribute('href')
            if href and date_str in href:
                parts = href.split('/')
                if len(parts) >= 6 and parts[-1].isdigit():
                    race_urls.add(href)
        
        race_urls = list(race_urls)
        print(f"   Found {len(race_urls)} races\n")
        
        if not race_urls:
            print("   No races found for yesterday")
            return 0
        
        # Scrape each race
        print("2. Scraping races...")
        for idx, url in enumerate(race_urls, 1):
            try:
                parts = url.split('/')
                course_name = parts[-3].replace('-', ' ').title()
                race_id = parts[-1]
                
                print(f"   [{idx}/{len(race_urls)}] {course_name}...", end=' ')
                
                driver.get(url)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'rp-horseTable')))
                time.sleep(2)
                
                # Get table
                table_elem = driver.find_element(By.CLASS_NAME, 'rp-horseTable')
                rows = table_elem.find_elements(By.TAG_NAME, 'tr')
                
                runners = []
                winner_name = None
                
                for row in rows:
                    try:
                        if 'header' in (row.get_attribute('class') or '').lower():
                            continue
                        
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if not cells:
                            continue
                        
                        # Position
                        pos_text = cells[0].text.strip()
                        position = ''.join(c for c in pos_text if c.isdigit())
                        
                        # Horse name
                        horse_name = None
                        links = row.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            text = link.text.strip()
                            if text and len(text) > 2 and not text.isdigit():
                                horse_name = text
                                break
                        
                        if not horse_name:
                            continue
                        
                        # Track winner
                        if position == '1':
                            winner_name = horse_name
                        
                        # Odds
                        odds = None
                        spans = row.find_elements(By.TAG_NAME, 'span')
                        for span in spans:
                            text = span.text.strip()
                            if '/' in text or 'EVS' in text.upper():
                                odds = parse_odds(text)
                                break
                        
                        runners.append({
                            'position': position or '',
                            'horse_name': horse_name,
                            'odds': Decimal(str(odds)) if odds else None
                        })
                    
                    except Exception as e:
                        continue
                
                # Save to DynamoDB
                if runners:
                    # Create composite key matching scheduled scraper format
                    race_key = f"{course_name}_{date_str.replace('-', '')}_{race_id}"
                    
                    item = {
                        'raceKey': race_key,
                        'scrapeTime': datetime.now().isoformat(),
                        'raceDate': date_str,
                        'courseName': course_name,
                        'raceId': race_id,
                        'url': url,
                        'hasResults': True,
                        'runnerCount': len(runners),
                        'runners': runners,
                        'winner': winner_name or 'Unknown'
                    }
                    
                    racingpost_table.put_item(Item=item)
                    scraped_count += 1
                    print(f"OK [RESULTS] Winner: {winner_name}")
                else:
                    print("SKIP (no data)")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                continue
        
        return scraped_count
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        return 0
    
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    scraped = scrape_yesterday()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Races scraped: {scraped}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
