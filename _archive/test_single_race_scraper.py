#!/usr/bin/env python3
"""
Test script to scrape a SINGLE race from Racing Post
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def parse_odds(odds_text):
    """Convert fractional odds to decimal"""
    if not odds_text or odds_text == '-':
        return None
    
    odds_text = odds_text.strip()
    
    if 'EVS' in odds_text.upper():
        return 2.0
    
    if '/' in odds_text:
        try:
            parts = odds_text.split('/')
            numerator = float(parts[0])
            denominator = float(parts[1])
            return round((numerator / denominator) + 1, 2)
        except:
            return None
    
    return None

def scrape_single_race(url):
    """Scrape one race and return results"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize driver
    print("Initializing Chrome WebDriver...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    results = []
    
    try:
        print(f"\nLoading: {url}")
        driver.get(url)
        
        # Wait for table to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'rp-horseTable')))
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        print("Page loaded. Extracting data...")
        
        # Find the table
        table = driver.find_element(By.CLASS_NAME, 'rp-horseTable')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        
        print(f"Found {len(rows)} total rows")
        
        for idx, row in enumerate(rows):
            try:
                # Skip header rows
                row_class = row.get_attribute('class') or ''
                if 'header' in row_class.lower():
                    continue
                
                # Extract position (try multiple methods)
                position = None
                try:
                    pos_elem = row.find_element(By.CSS_SELECTOR, 'span[data-test-selector="text-position"]')
                    position = pos_elem.text.strip()
                except:
                    try:
                        pos_elem = row.find_element(By.CLASS_NAME, 'rp-horseTable__pos')
                        position = pos_elem.text.strip()
                    except:
                        # Try finding first column with a number
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if cells:
                            text = cells[0].text.strip()
                            if text and (text.isdigit() or text in ['1','2','3','4','5','6','7','8','9','10']):
                                position = text
                
                if not position:
                    continue  # Skip rows without position
                
                # Extract horse name
                horse_name = None
                try:
                    horse_elem = row.find_element(By.CSS_SELECTOR, 'a[data-test-selector="link-horseName"]')
                    horse_name = horse_elem.text.strip()
                except:
                    try:
                        horse_elem = row.find_element(By.CLASS_NAME, 'rp-horseTable__horse__name')
                        links = horse_elem.find_elements(By.TAG_NAME, 'a')
                        if links:
                            horse_name = links[0].text.strip()
                    except:
                        # Try any link in the row
                        links = row.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            text = link.text.strip()
                            if text and len(text) > 2:  # Reasonable horse name length
                                horse_name = text
                                break
                
                if not horse_name:
                    continue
                
                # Extract odds
                odds = None
                try:
                    odds_elem = row.find_element(By.CSS_SELECTOR, 'span[data-test-selector="text-sp"]')
                    odds_text = odds_elem.text.strip()
                    odds = parse_odds(odds_text)
                except:
                    # Try finding fractional odds pattern
                    spans = row.find_elements(By.TAG_NAME, 'span')
                    for span in spans:
                        text = span.text.strip()
                        if '/' in text or 'EVS' in text.upper():
                            odds = parse_odds(text)
                            break
                
                # Extract jockey
                jockey = None
                try:
                    jockey_elem = row.find_element(By.CSS_SELECTOR, 'a[data-test-selector="link-jockeyName"]')
                    jockey = jockey_elem.text.strip()
                except:
                    pass
                
                # Extract trainer
                trainer = None
                try:
                    trainer_elem = row.find_element(By.CSS_SELECTOR, 'a[data-test-selector="link-trainerName"]')
                    trainer = trainer_elem.text.strip()
                except:
                    pass
                
                runner = {
                    'position': position,
                    'horse_name': horse_name,
                    'odds': odds,
                    'jockey': jockey,
                    'trainer': trainer
                }
                
                results.append(runner)
                print(f"  {position}. {horse_name} @ {odds}")
                
            except Exception as e:
                print(f"  Error parsing row {idx}: {str(e)}")
                continue
        
    finally:
        driver.quit()
    
    return results

if __name__ == '__main__':
    # Test with Carlisle 13:30 race
    test_url = "https://www.racingpost.com/results/8/carlisle/2026-02-03/4803335"
    
    print("=" * 80)
    print("SINGLE RACE SCRAPER TEST")
    print("=" * 80)
    
    results = scrape_single_race(test_url)
    
    print("\n" + "=" * 80)
    print(f"RESULTS: Scraped {len(results)} runners")
    print("=" * 80)
    
    # Save to JSON
    output = {
        'url': test_url,
        'runners_count': len(results),
        'results': results
    }
    
    with open('single_race_test.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to: single_race_test.json")
    print("\nWinner:", results[0]['horse_name'] if results else "No results")
