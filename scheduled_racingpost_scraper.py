#!/usr/bin/env python3
"""
SCHEDULED RACING POST SCRAPER
Runs every 30 minutes (12pm-8pm) to collect race data and results
Saves to dedicated RacingPostRaces DynamoDB table
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
import json
import sys

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

def scrape_todays_races():
    """Scrape all today's races (both upcoming and completed)"""
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Setup Chrome with robust options
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
        print(f"RACING POST SCRAPER - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)
        
        # Get race list
        print("1. Fetching race list...")
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
            print("   No races found")
            return 0
        
        # Scrape each race
        print("2. Scraping races...")
        for idx, url in enumerate(race_urls, 1):
            try:
                parts = url.split('/')
                course_id = parts[-4]
                course_name = parts[-3]
                race_id = parts[-1]
                
                print(f"   [{idx}/{len(race_urls)}] {course_name}...", end=' ')
                
                driver.get(url)
                time.sleep(2)
                
                # Extract race time from page
                race_time = None
                try:
                    time_elem = driver.find_element(By.CSS_SELECTOR, 'span.rp-raceTimeCourseName__time, .rp-raceTimeCourseName__time')
                    race_time = time_elem.text.strip()
                except:
                    # Try alternative selector
                    try:
                        time_elem = driver.find_element(By.XPATH, "//span[contains(@class, 'time')]")
                        race_time = time_elem.text.strip()
                    except:
                        pass
                
                # Get results table - try multiple selectors
                table_elem = None
                try:
                    table_elem = driver.find_element(By.CSS_SELECTOR, 'table.rp-horseTable, .rp-horseTable, table[data-test-selector="table-raceResult"]')
                except:
                    try:
                        table_elem = driver.find_element(By.TAG_NAME, 'table')
                    except:
                        print("[No table]")
                        continue
                
                if not table_elem:
                    print("[No table]")
                    continue
                
                rows = table_elem.find_elements(By.TAG_NAME, 'tr')
                
                runners = []
                has_results = False
                
                for row in rows:
                    try:
                        # Skip header rows
                        if 'header' in (row.get_attribute('class') or '').lower():
                            continue
                        
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) < 3:  # Need at least position, horse name, and some other data
                            continue
                        
                        # Position (usually first cell)
                        pos_cell = cells[0]
                        pos_text = pos_cell.text.strip()
                        
                        # Extract numeric position
                        position = ''
                        for char in pos_text:
                            if char.isdigit():
                                position += char
                            elif position:  # Stop at first non-digit after we found digits
                                break
                        
                        if position:
                            has_results = True
                        
                        # Horse name - look for links in the row
                        horse_name = None
                        horse_links = row.find_elements(By.CSS_SELECTOR, 'a[href*="/horse/"], a.rp-horseTable__horse__name')
                        
                        if horse_links:
                            horse_name = horse_links[0].text.strip()
                        
                        # Fallback: look for any substantial text in 2nd or 3rd cell
                        if not horse_name:
                            for cell_idx in [1, 2]:
                                if cell_idx < len(cells):
                                    text = cells[cell_idx].text.strip()
                                    # Must be at least 3 chars, not all numbers
                                    if len(text) >= 3 and not text.isdigit() and not '/' in text:
                                        horse_name = text
                                        break
                        
                        if not horse_name:
                            continue
                        
                        # Odds - look for fractional format or "EVS"
                        odds = None
                        for cell in cells:
                            cell_text = cell.text.strip()
                            if '/' in cell_text or 'EVS' in cell_text.upper():
                                odds = parse_odds(cell_text)
                                break
                        
                        # Jockey - usually a link with href containing "/jockey/"
                        jockey = None
                        jockey_links = row.find_elements(By.CSS_SELECTOR, 'a[href*="/jockey/"]')
                        if jockey_links:
                            jockey = jockey_links[0].text.strip()
                        
                        runners.append({
                            'horse_name': horse_name,
                            'position': position if position else 'running',
                            'odds': Decimal(str(odds)) if odds else None,
                            'jockey': jockey
                        })
                    
                    except Exception as e:
                        # Skip problematic rows silently
                        continue
                
                if runners:
                    # Save to DynamoDB
                    race_key = f"{course_name}_{date_str.replace('-', '')}_{race_time.replace(':', '') if race_time else race_id}"
                    
                    item = {
                        'raceKey': race_key,
                        'scrapeTime': datetime.now().isoformat(),
                        'raceDate': date_str,
                        'courseId': course_id,
                        'courseName': course_name,
                        'raceTime': race_time or 'unknown',
                        'raceId': race_id,
                        'url': url,
                        'hasResults': has_results,
                        'runnerCount': len(runners),
                        'runners': runners,
                        'winner': runners[0]['horse_name'] if has_results and runners else None
                    }
                    
                    racingpost_table.put_item(Item=item)
                    
                    status = "RESULTS" if has_results else "PREVIEW"
                    winner_info = f"Winner: {runners[0]['horse_name']}" if has_results else f"{len(runners)} runners"
                    print(f"OK [{status}] {winner_info}")
                    
                    scraped_count += 1
                else:
                    print("[No data]")
                
                time.sleep(1)
            
            except Exception as e:
                print(f"[ERROR: {str(e)[:40]}]")
                continue
        
        return scraped_count
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    """Main execution"""
    try:
        scraped = scrape_todays_races()
        
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Races scraped: {scraped}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Log to file
        with open('scraper_log.txt', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Scraped {scraped} races\n")
        
        return 0
    
    except Exception as e:
        print(f"\nERROR: {e}")
        with open('scraper_log.txt', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - ERROR: {e}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
