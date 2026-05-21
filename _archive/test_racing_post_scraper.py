"""
Test Racing Post scraper with a known race

This tests the scraper against a specific race URL to verify parsing logic.
"""

import requests
from bs4 import BeautifulSoup

def test_racing_post_structure():
    """Test what Racing Post HTML structure looks like"""
    
    # Test with today's date
    date_str = '2026-02-03'
    url = f'https://www.racingpost.com/results/{date_str}'
    
    print(f"\n{'='*80}")
    print(f"Testing Racing Post Results Page Structure")
    print(f"{'='*80}\n")
    print(f"URL: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)} bytes\n")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save HTML for inspection
            with open('racing_post_sample.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("✓ HTML saved to: racing_post_sample.html\n")
            
            # Find common elements
            print("Looking for common elements:")
            print("-" * 80)
            
            # Look for race cards/results
            links = soup.find_all('a', href=True)
            race_links = [link for link in links if '/results/' in link.get('href', '')]
            print(f"Links with '/results/': {len(race_links)}")
            
            if race_links:
                print("\nSample race links:")
                for link in race_links[:5]:
                    print(f"  {link.get('href')}")
            
            # Look for tables
            tables = soup.find_all('table')
            print(f"\nTables found: {len(tables)}")
            
            # Look for common class patterns
            all_classes = set()
            for element in soup.find_all(class_=True):
                classes = element.get('class', [])
                all_classes.update(classes)
            
            rp_classes = [cls for cls in all_classes if 'rp-' in cls or 'race' in cls.lower()]
            if rp_classes:
                print(f"\nRacing Post specific classes found: {len(rp_classes)}")
                print("Sample classes:")
                for cls in list(rp_classes)[:10]:
                    print(f"  {cls}")
            
            print(f"\n{'='*80}")
            print("Test complete - check racing_post_sample.html for structure")
            print(f"{'='*80}\n")
            
        else:
            print(f"✗ Failed to fetch page (status {response.status_code})")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    test_racing_post_structure()
