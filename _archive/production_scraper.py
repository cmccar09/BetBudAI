#!/usr/bin/env python3
"""
PRODUCTION RACING POST SCRAPER
Simple, reliable, single-driver approach
"""
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from decimal import Decimal
import time
import sys
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

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

def scrape_all_races(date_str):
    """Scrape all races for a date - simple single-driver approach"""
    
    # Setup Chrome
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = None
    all_results = {}
    
    try:
        print(f"\nScraping results for {date_str}")
        print("=" * 60)
        
        # Initialize driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        wait = WebDriverWait(driver, 15)
        
        # Get race list
        print("\n1. Fetching race list...")
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
            print("No races found!")
            return {}
        
        # Scrape each race
        print("2. Scraping races...")
        for idx, url in enumerate(race_urls, 1):
            try:
                course = url.split('/')[-3]
                print(f"   [{idx}/{len(race_urls)}] {course}...", end=' ')
                
                driver.get(url)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'rp-horseTable')))
                time.sleep(3)
                
                table_elem = driver.find_element(By.CLASS_NAME, 'rp-horseTable')
                rows = table_elem.find_elements(By.TAG_NAME, 'tr')
                
                results = []
                for row in rows:
                    try:
                        if 'header' in (row.get_attribute('class') or '').lower():
                            continue
                        
                        # Get position
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if not cells:
                            continue
                        
                        pos_text = cells[0].text.strip()
                        position = ''.join(c for c in pos_text if c.isdigit())
                        
                        if not position:
                            continue
                        
                        # Get horse name
                        horse_name = None
                        links = row.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            text = link.text.strip()
                            if text and len(text) > 2 and not text.isdigit():
                                horse_name = text
                                break
                        
                        if not horse_name:
                            continue
                        
                        # Get odds
                        odds = None
                        spans = row.find_elements(By.TAG_NAME, 'span')
                        for span in spans:
                            text = span.text.strip()
                            if '/' in text or 'EVS' in text.upper():
                                odds = parse_odds(text)
                                break
                        
                        results.append({
                            'position': position,
                            'horse_name': horse_name,
                            'odds': odds
                        })
                    
                    except:
                        continue
                
                if results:
                    all_results[url] = results
                    winner = results[0]['horse_name']
                    print(f"OK ({len(results)} runners, Winner: {winner})")
                else:
                    print("[No data]")
                
                time.sleep(1)  # Brief pause between races
            
            except Exception as e:
                print(f"[ERROR: {str(e)[:40]}]")
                continue
        
        return all_results
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def update_database(results, date_str):
    """Update DynamoDB with results"""
    print("\n3. Updating database...")
    updated = 0
    
    try:
        # Get picks for this date
        response = table.scan(
            FilterExpression='contains(#raceId, :date)',
            ExpressionAttributeNames={'#raceId': 'raceId'},
            ExpressionAttributeValues={':date': date_str}
        )
        
        picks = response.get('Items', [])
        print(f"   Found {len(picks)} picks to match")
        
        for pick in picks:
            horse_name = pick.get('horseName')
            if not horse_name:
                continue
            
            # Find in results
            for url, runners in results.items():
                for runner in runners:
                    if runner['horse_name'].lower() == horse_name.lower():
                        outcome = 'won' if runner['position'] == '1' else 'lost'
                        
                        table.update_item(
                            Key={
                                'raceId': pick['raceId'],
                                'timestamp': pick['timestamp']
                            },
                            UpdateExpression='SET outcome = :outcome, actual_position = :pos',
                            ExpressionAttributeValues={
                                ':outcome': outcome,
                                ':pos': runner['position']
                            }
                        )
                        
                        updated += 1
                        print(f"   - Updated: {horse_name} (pos {runner['position']}, {outcome})")
                        break
        
        return updated
    
    except Exception as e:
        print(f"   Database error: {e}")
        return 0

def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    
    print("\n" + "=" * 60)
    print("RACING POST RESULTS SCRAPER")
    print("=" * 60)
    
    # Scrape
    results = scrape_all_races(date_str)
    
    if not results:
        print("\nNo results scraped")
        return
    
    # Update database
    updated = update_database(results, date_str)
    
    # Summary
    total_runners = sum(len(r) for r in results.values())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Races scraped:      {len(results)}")
    print(f"Total runners:      {total_runners}")
    print(f"Database updates:   {updated}")
    print("=" * 60)
    
    # Save to file
    output = {
        'date': date_str,
        'races': len(results),
        'runners': total_runners,
        'updated': updated,
        'details': {
            url: [{'pos': r['position'], 'horse': r['horse_name'], 'odds': r['odds']} 
                  for r in runners]
            for url, runners in results.items()
        }
    }
    
    filename = f"results_{date_str}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[OK] Saved to {filename}\n")

if __name__ == '__main__':
    main()
