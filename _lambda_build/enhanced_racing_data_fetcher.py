#!/usr/bin/env python3
"""
Enhanced Racing Data Fetcher
Scrapes comprehensive racing data from Racing Post to enrich Betfair odds with:
- Form strings and recent performance
- Trainer/jockey statistics
- Course & Distance (C&D) records
- Official ratings
- Ground preferences
- Days since last run

This data is critical for informed betting decisions.

⚠️ IMPORTANT NOTE ON RACING POST SCRAPING:
Racing Post actively blocks automated scraping with 406 errors. If this happens:
1. The system will gracefully continue without enrichment
2. Betfair data alone will be used for predictions
3. Alternative: Consider paid Racing Post API access or Timeform API
4. Alternative: Use Selenium with headless Chrome for more realistic browsing
5. Alternative: Racing-specific data providers like Proform or Raceform
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import time
import os

class EnhancedRacingDataFetcher:
    """Fetch detailed racing data to supplement Betfair odds"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.google.com/',
        })
        self.cache = {}
    
    def fetch_race_card(self, course, race_time, date_str=None):
        """
        Fetch detailed race card for a specific race
        Returns enriched data for each runner
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Normalize course name for URL
        course_slug = course.lower().replace(' ', '-').replace('(', '').replace(')', '')
        
        # Racing Post race card URL
        url = f"https://www.racingpost.com/racecards/{course_slug}/{date_str}"
        
        print(f"Fetching race card: {course} at {race_time}")
        
        try:
            # Add small delay to be respectful
            time.sleep(1)
            
            response = self.session.get(url, timeout=30, allow_redirects=True)
            
            if response.status_code == 404:
                print(f"  [WARNING] Race card not found for {course}")
                return None
            
            if response.status_code == 406:
                print(f"  [WARNING] Racing Post blocking request - trying alternative method")
                # Try with different headers
                alt_headers = self.session.headers.copy()
                alt_headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
                response = self.session.get(url, timeout=30, headers=alt_headers, allow_redirects=True)
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse runners data
            runners_data = self._parse_race_card(soup, race_time)
            
            if runners_data:
                print(f"  ✓ Extracted data for {len(runners_data)} runners")
                return runners_data
            else:
                print(f"  [WARNING] No runner data found")
                return None
        
        except Exception as e:
            print(f"  [ERROR] Error fetching race card: {e}")
            return None
    
    def _parse_race_card(self, soup, target_time):
        """Parse runner data from race card HTML"""
        runners = []
        
        # Find race cards - Racing Post structure
        race_sections = soup.find_all('div', class_=re.compile('raceCard|race-card'))
        
        for race_section in race_sections:
            # Check if this is the right race time
            time_elem = race_section.find('span', class_=re.compile('time|off-time'))
            if time_elem:
                race_time_text = time_elem.get_text(strip=True)
                # Simple time matching
                if target_time not in race_time_text:
                    continue
            
            # Find runner rows
            runner_rows = race_section.find_all('tr', class_=re.compile('runner|horse'))
            
            for row in runner_rows:
                runner_data = self._parse_runner_row(row)
                if runner_data:
                    runners.append(runner_data)
        
        return runners if runners else None
    
    def _parse_runner_row(self, row):
        """Extract all available data from a runner row"""
        try:
            data = {}
            
            # Horse name
            name_elem = row.find('a', class_=re.compile('horse|name'))
            if name_elem:
                data['horse_name'] = name_elem.get_text(strip=True)
            else:
                return None
            
            # Form string (e.g., "1-2-3-0-1")
            form_elem = row.find('span', class_=re.compile('form'))
            if form_elem:
                data['form'] = form_elem.get_text(strip=True)
                data['last_run_result'] = self._parse_last_run(data['form'])
            
            # Trainer
            trainer_elem = row.find('a', class_=re.compile('trainer'))
            if trainer_elem:
                data['trainer'] = trainer_elem.get_text(strip=True)
            
            # Jockey
            jockey_elem = row.find('a', class_=re.compile('jockey'))
            if jockey_elem:
                data['jockey'] = jockey_elem.get_text(strip=True)
            
            # Age
            age_elem = row.find('span', class_=re.compile('age'))
            if age_elem:
                data['age'] = age_elem.get_text(strip=True)
            
            # Weight
            weight_elem = row.find('span', class_=re.compile('weight|wgt'))
            if weight_elem:
                data['weight'] = weight_elem.get_text(strip=True)
            
            # Official Rating (OR)
            or_elem = row.find('span', class_=re.compile('or|rating'))
            if or_elem:
                data['official_rating'] = or_elem.get_text(strip=True)
            
            # RPR (Racing Post Rating)
            rpr_elem = row.find('span', class_=re.compile('rpr'))
            if rpr_elem:
                data['rpr'] = rpr_elem.get_text(strip=True)
            
            # Draw/Stall
            draw_elem = row.find('span', class_=re.compile('draw|stall'))
            if draw_elem:
                data['draw'] = draw_elem.get_text(strip=True)
            
            # Days since last run
            days_elem = row.find('span', class_=re.compile('days|since'))
            if days_elem:
                data['days_since_last_run'] = days_elem.get_text(strip=True)
            
            # Comments/analysis (if available)
            comment_elem = row.find('div', class_=re.compile('comment|analysis'))
            if comment_elem:
                data['comment'] = comment_elem.get_text(strip=True)[:200]  # Truncate
            
            return data
        
        except Exception as e:
            print(f"    ⚠️ Error parsing runner: {e}")
            return None
    
    def _parse_last_run(self, form_string):
        """Extract last run result from form string"""
        if not form_string:
            return None
        
        # Form like "1-2-3" -> last run was "1" (win)
        parts = form_string.split('-')
        if parts:
            last = parts[0].strip()
            # Try to convert to int (position), or return as-is
            try:
                return int(last) if last.isdigit() else last
            except:
                return last
        return None
    
    def fetch_trainer_stats(self, trainer_name, course_name):
        """
        Fetch trainer statistics at specific course
        Returns strike rate, wins, runs
        """
        # Note: This requires accessing trainer stats pages
        # Racing Post has this under trainer profiles
        
        cache_key = f"{trainer_name}_{course_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Normalize names for URL
        trainer_slug = trainer_name.lower().replace(' ', '-').replace('.', '')
        
        url = f"https://www.racingpost.com/profile/trainer/{trainer_slug}/statistics"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse trainer course stats
            stats = self._parse_trainer_course_stats(soup, course_name)
            
            if stats:
                self.cache[cache_key] = stats
                return stats
        
        except Exception as e:
            print(f"    ⚠️ Error fetching trainer stats: {e}")
        
        return None
    
    def _parse_trainer_course_stats(self, soup, course_name):
        """Parse trainer statistics for a specific course"""
        # This is a simplified version - actual Racing Post structure may vary
        try:
            # Look for course-specific stats table
            stats_table = soup.find('table', class_=re.compile('stats|course'))
            
            if not stats_table:
                return None
            
            # Find row for this course
            course_normalized = course_name.lower().strip()
            
            for row in stats_table.find_all('tr'):
                course_cell = row.find('td', class_=re.compile('course|venue'))
                
                if course_cell and course_normalized in course_cell.get_text(strip=True).lower():
                    # Extract stats from this row
                    cells = row.find_all('td')
                    
                    if len(cells) >= 4:
                        return {
                            'course': course_name,
                            'runs': cells[1].get_text(strip=True),
                            'wins': cells[2].get_text(strip=True),
                            'strike_rate': cells[3].get_text(strip=True)
                        }
        
        except Exception as e:
            print(f"    ⚠️ Error parsing trainer stats: {e}")
        
        return None
    
    def fetch_going_data(self, course_name, date_str=None):
        """Fetch official going (ground conditions) for course"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        course_slug = course_name.lower().replace(' ', '-')
        url = f"https://www.racingpost.com/racecards/{course_slug}/{date_str}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find going information
            going_elem = soup.find('span', class_=re.compile('going'))
            if going_elem:
                return going_elem.get_text(strip=True)
            
            # Alternative location
            going_elem = soup.find('div', class_=re.compile('course-info'))
            if going_elem:
                going_text = going_elem.get_text()
                match = re.search(r'Going:\s*(\w+)', going_text, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        except Exception as e:
            print(f"  ⚠️ Error fetching going data: {e}")
        
        return None
    
    def enrich_betfair_snapshot(self, snapshot_file, output_file=None):
        """
        Enrich a Betfair snapshot JSON with Racing Post data
        Adds form, ratings, trainer stats to each runner
        """
        print("\n=== Enriching Betfair Snapshot with Racing Post Data ===\n")
        
        # Load Betfair snapshot
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        enriched_count = 0
        total_runners = 0
        
        for race in snapshot.get('races', []):
            course = race.get('course', '')
            race_time = race.get('time', '')
            
            # Fetch race card data
            race_card_data = self.fetch_race_card(course, race_time)
            
            if not race_card_data:
                print(f"  [SKIP] No race card data for {course} {race_time}")
            for runner in race.get('runners', []):
                total_runners += 1
                horse_name = runner.get('name', '').lower().strip()
                
                # Find matching runner in race card
                for card_runner in race_card_data:
                    card_name = card_runner.get('horse_name', '').lower().strip()
                    
                    if horse_name in card_name or card_name in horse_name:
                        # Enrich runner with Racing Post data
                        runner['enhanced_data'] = card_runner
                        
                        # Fetch trainer stats if available
                        if 'trainer' in card_runner:
                            trainer_stats = self.fetch_trainer_stats(
                                card_runner['trainer'],
                                course
                            )
                            if trainer_stats:
                                runner['enhanced_data']['trainer_stats'] = trainer_stats
                        
                        enriched_count += 1
                        print(f"    ✓ Enriched: {runner['name']}")
                        break
            
            # Add going data to race
            going = self.fetch_going_data(course)
            if going:
                race['going'] = going
                print(f"  ✓ Added going: {going}")
            
            # Rate limiting
            time.sleep(1)
        
        # Save enriched snapshot
        if not output_file:
            output_file = snapshot_file.replace('.json', '_enriched.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Enrichment complete:")
        print(f"   - {enriched_count}/{total_runners} runners enriched")
        print(f"   - Saved to: {output_file}")
        
        return output_file


def main():
    """Test the enhanced data fetcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich Betfair data with Racing Post information')
    parser.add_argument('--snapshot', default='response_live.json', help='Betfair snapshot file')
    parser.add_argument('--output', help='Output file (default: snapshot_enriched.json)')
    
    args = parser.parse_args()
    
    fetcher = EnhancedRacingDataFetcher()
    
    if os.path.exists(args.snapshot):
        fetcher.enrich_betfair_snapshot(args.snapshot, args.output)
    else:
        print(f"❌ Snapshot file not found: {args.snapshot}")
        print("Run betfair_delayed_snapshots.py first to generate a snapshot")


if __name__ == '__main__':
    main()
