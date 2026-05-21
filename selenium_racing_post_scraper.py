"""
Selenium-Based Racing Post Results Scraper

Fully automated results fetching using Selenium to handle JavaScript-rendered content.
Zero manual work required.

Usage:
    python selenium_racing_post_scraper.py                # Fetch today's results
    python selenium_racing_post_scraper.py 2026-02-03     # Fetch specific date
    python selenium_racing_post_scraper.py --update-db    # Update database with results

Requirements:
    pip install selenium webdriver-manager
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
import re
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

class SeleniumRacingPostScraper:
    def __init__(self, headless=True):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        print("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def __del__(self):
        """Cleanup WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def parse_odds(self, odds_text):
        """Convert odds text to decimal (e.g., '9/2' -> 5.5)"""
        try:
            odds_text = odds_text.strip().upper()
            
            # Handle fractional odds (e.g., "9/2")
            if '/' in odds_text:
                parts = odds_text.split('/')
                numerator = float(parts[0])
                denominator = float(parts[1])
                return round((numerator / denominator) + 1, 2)
            
            # Handle decimal odds (e.g., "5.5")
            elif '.' in odds_text or odds_text.isdigit():
                return float(odds_text)
            
            # Handle EVS (evens)
            elif 'EVS' in odds_text or 'EVENS' in odds_text:
                return 2.0
            
            return None
            
        except:
            return None
    
    def get_race_urls_for_date(self, date_str):
        """Get all race result URLs for a specific date"""
        url = f'https://www.racingpost.com/results/{date_str}'
        
        print(f"\nFetching race list for {date_str}...")
        print(f"URL: {url}")
        
        self.driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Find all race result links
        try:
            # Look for links with /results/ in href
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            race_urls = []
            
            for link in links:
                href = link.get_attribute('href')
                if href and '/results/' in href and date_str in href:
                    # Filter out non-race links
                    if 'winning-times' not in href and '#' not in href:
                        if href not in race_urls:
                            race_urls.append(href)
            
            print(f"Found {len(race_urls)} race URLs")
            return race_urls
            
        except Exception as e:
            print(f"Error finding race URLs: {e}")
            return []
    
    def scrape_race_result(self, race_url):
        """Scrape a single race result page"""
        print(f"\n{'='*80}")
        print(f"Scraping: {race_url}")
        
        self.driver.get(race_url)
        
        # Wait for the results table to load
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'rp-horseTable')))
            time.sleep(2)  # Extra time for dynamic content
        except Exception as e:
            print(f"Error waiting for page load: {e}")
            return None
        
        race_data = {
            'url': race_url,
            'course': None,
            'race_time': None,
            'race_class': None,
            'going': None,
            'winner': None,
            'runners': []
        }
        
        try:
            # Extract course from URL
            # Format: /results/8/carlisle/2026-02-03/4803334
            url_parts = race_url.split('/')
            if len(url_parts) > 4:
                race_data['course'] = url_parts[4].replace('-', ' ').title()
            
            # Get race title/time from page
            try:
                title = self.driver.find_element(By.TAG_NAME, 'h1').text
                
                # Extract time (e.g., "3:35")
                time_match = re.search(r'(\d{1,2}:\d{2})', title)
                if time_match:
                    race_data['race_time'] = time_match.group(1)
                
                # Extract class
                class_match = re.search(r'Class (\d)', title, re.IGNORECASE)
                if class_match:
                    race_data['race_class'] = f"Class {class_match.group(1)}"
                    
            except Exception as e:
                print(f"  Warning: Could not extract title: {e}")
            
            # Find results table - try multiple selectors
            try:
                table = self.driver.find_element(By.CLASS_NAME, 'rp-horseTable')
                rows = table.find_elements(By.TAG_NAME, 'tr')
                
                print(f"  Found {len(rows)} rows total")
                
                for row in rows:
                    try:
                        # Skip header rows
                        if 'rp-horseTable__header' in row.get_attribute('class'):
                            continue
                        
                        # Try to find position - multiple possible locations
                        position = None
                        try:
                            # Try data-test-selector first
                            pos_elem = row.find_element(By.CSS_SELECTOR, 'span[data-test-selector="text-position"]')
                            position = pos_elem.text.strip()
                        except:
                            try:
                                # Try class-based selector
                                pos_elem = row.find_element(By.CLASS_NAME, 'rp-horseTable__pos')
                                position = pos_elem.text.strip()
                            except:
                                # Try finding first span with numeric text
                                spans = row.find_elements(By.TAG_NAME, 'span')
                                for span in spans:
                                    text = span.text.strip()
                                    if text and (text.isdigit() or text in ['1', '2', '3', '4', '5', '6', '7', '8', '9']):
                                        position = text
                                        break
                        
                        if not position:
                            continue  # Skip rows without position
                        
                        # Horse name - try multiple selectors
                        horse_name = None
                        try:
                            horse_elem = row.find_element(By.CSS_SELECTOR, 'a[data-test-selector="link-horseName"]')
                            horse_name = horse_elem.text.strip()
                        except:
                            try:
                                horse_elem = row.find_element(By.CLASS_NAME, 'rp-horseTable__horse__name')
                                horse_name = horse_elem.text.strip()
                            except:
                                # Try any link in the row
                                links = row.find_elements(By.TAG_NAME, 'a')
                                if links:
                                    horse_name = links[0].text.strip()
                        
                        if not horse_name:
                            continue
                        
                        # Odds (SP - Starting Price)
                        odds = None
                        try:
                            odds_elem = row.find_element(By.CSS_SELECTOR, 'span[data-test-selector="text-sp"]')
                            odds_text = odds_elem.text.strip()
                            odds = self.parse_odds(odds_text)
                        except:
                            try:
                                # Look for fractional odds pattern in any span
                                spans = row.find_elements(By.TAG_NAME, 'span')
                                for span in spans:
                                    text = span.text.strip()
                                    if '/' in text or 'EVS' in text:
                                        odds = self.parse_odds(text)
                                        break
                            except:
                                pass
                        
                        # Jockey
                        jockey = None
                        try:
                            jockey_elem = row.find_element(By.CSS_SELECTOR, 'a[data-test-selector="link-jockeyName"]')
                            jockey = jockey_elem.text.strip()
                        except:
                            pass
                        
                        # Trainer
                        trainer = None
                        try:
                            trainer_elem = row.find_element(By.CSS_SELECTOR, 'a[data-test-selector="link-trainerName"]')
                            trainer = trainer_elem.text.strip()
                        except:
                            pass
                        
                        runner_data = {
                            'position': position,
                            'horse_name': horse_name,
                            'odds': odds,
                            'jockey': jockey,
                            'trainer': trainer
                        }
                        
                        race_data['runners'].append(runner_data)
                        
                        # Set winner
                        if position == '1':
                            race_data['winner'] = horse_name
                            print(f"  Winner: {horse_name} @ {odds}")
                        
                    except Exception as e:
                        print(f"  Error parsing runner: {e}")
                        continue
                
            except Exception as e:
                print(f"  Error finding results table: {e}")
        
        except Exception as e:
            print(f"  Error scraping race: {e}")
            return None
        
        if race_data['runners']:
            print(f"  ✓ Scraped {len(race_data['runners'])} runners from {race_data['course']} {race_data['race_time']}")
            return race_data
        else:
            print(f"  ✗ No runners found")
            return None
    
    def fetch_all_results(self, date_str=None):
        """Fetch all results for a date"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{'='*80}")
        print(f"FETCHING ALL RESULTS FOR {date_str}")
        print(f"{'='*80}")
        
        # Get race URLs
        race_urls = self.get_race_urls_for_date(date_str)
        
        if not race_urls:
            print("No race URLs found")
            return []
        
        # Scrape each race
        results = []
        
        for i, race_url in enumerate(race_urls, 1):
            print(f"\n[{i}/{len(race_urls)}]")
            
            race_data = self.scrape_race_result(race_url)
            
            if race_data:
                results.append(race_data)
            
            # Be respectful to the server
            time.sleep(2)
        
        print(f"\n{'='*80}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"Successfully scraped: {len(results)}/{len(race_urls)} races")
        
        return results
    
    def match_and_update_database(self, results, date_str):
        """Match results with database and update"""
        # Get our picks
        response = table.query(
            KeyConditionExpression='bet_date = :date',
            FilterExpression='show_in_ui = :ui',
            ExpressionAttributeValues={
                ':date': date_str,
                ':ui': True
            }
        )
        
        our_picks = response['Items']
        
        print(f"\n{'='*80}")
        print(f"MATCHING RESULTS WITH DATABASE")
        print(f"{'='*80}")
        print(f"Our picks: {len(our_picks)}")
        print(f"Scraped results: {len(results)}\n")
        
        matched = 0
        updated = 0
        
        for pick in our_picks:
            pick_course = pick.get('course', '').lower().strip()
            pick_time = pick.get('race_time', '')
            pick_horse = pick.get('horse_name', '').lower().strip()
            
            # Extract time from ISO format (2026-02-03T15:35:00.000Z -> 15:35)
            if 'T' in pick_time:
                pick_time = pick_time.split('T')[1][:5]
            
            # Find matching race
            for result in results:
                result_course = result.get('course', '').lower().strip()
                result_time = result.get('race_time', '')
                
                # Check if course and time match
                course_match = (pick_course in result_course or result_course in pick_course)
                time_match = (result_time == pick_time)
                
                if course_match and time_match:
                    matched += 1
                    
                    # Find our horse in the results
                    winner = result.get('winner', '').lower()
                    
                    outcome = 'loss'
                    profit = -30.0
                    winning_odds = None
                    
                    # Check if our horse won
                    for runner in result.get('runners', []):
                        runner_name = runner['horse_name'].lower()
                        
                        # Flexible matching (handles (IRE), spacing differences, etc.)
                        if (pick_horse in runner_name or runner_name in pick_horse or
                            pick_horse.replace(' ', '') == runner_name.replace(' ', '')):
                            
                            if runner['position'] == '1':
                                outcome = 'win'
                                winning_odds = runner.get('odds')
                                if winning_odds:
                                    profit = (winning_odds * 30) - 30
                                break
                    
                    # Update database
                    try:
                        table.update_item(
                            Key={
                                'bet_date': date_str,
                                'bet_id': pick['bet_id']
                            },
                            UpdateExpression='SET outcome = :outcome, profit_loss = :profit, '
                                           'actual_winner = :winner, result_updated = :updated',
                            ExpressionAttributeValues={
                                ':outcome': outcome,
                                ':profit': Decimal(str(profit)),
                                ':winner': result.get('winner'),
                                ':updated': 'yes'
                            }
                        )
                        
                        updated += 1
                        
                        status = "WIN" if outcome == 'win' else "LOSS"
                        print(f"✓ {pick_time} {pick_course:15} {pick_horse:20} {status} {profit:+.0f} EUR")
                        
                    except Exception as e:
                        print(f"✗ Error updating {pick_horse}: {e}")
                    
                    break  # Found match, move to next pick
        
        print(f"\n{'='*80}")
        print(f"DATABASE UPDATE COMPLETE")
        print(f"{'='*80}")
        print(f"Matched: {matched}/{len(our_picks)} picks")
        print(f"Updated: {updated} entries")
        
        return updated

def main():
    import sys
    
    # Parse command line args
    date_str = datetime.now().strftime('%Y-%m-%d')
    update_db = True
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--help' or arg == '-h':
            print(__doc__)
            return
        elif arg == '--no-update':
            update_db = False
        else:
            date_str = arg
    
    print(f"\n{'='*80}")
    print(f"SELENIUM RACING POST SCRAPER")
    print(f"{'='*80}")
    print(f"Date: {date_str}")
    print(f"Update database: {update_db}")
    print(f"{'='*80}\n")
    
    # Create scraper
    scraper = SeleniumRacingPostScraper(headless=True)
    
    try:
        # Fetch results
        results = scraper.fetch_all_results(date_str)
        
        # Save results to JSON
        output_file = f"race_results_{date_str}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        
        # Update database
        if update_db and results:
            updated = scraper.match_and_update_database(results, date_str)
            
            if updated > 0:
                print(f"\n✓ Successfully updated {updated} results in database")
                print("\nRun learning: python complete_race_learning.py learn")
            else:
                print("\n⚠ No database entries updated")
                print("Possible reasons:")
                print("  - Course/time names don't match exactly")
                print("  - No picks made for these races")
                print("  - Results already recorded")
        
    finally:
        # Cleanup
        del scraper
    
    print(f"\n{'='*80}")
    print("DONE")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
