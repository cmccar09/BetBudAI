"""
Test Selenium scraper - check actual page structure
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    url = 'https://www.racingpost.com/results/8/carlisle/2026-02-03/4803334'
    print(f"Loading: {url}\n")
    
    driver.get(url)
    time.sleep(5)
    
    # Save page source
    with open('selenium_page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    
    print("Saved page source to selenium_page_source.html\n")
    
    # Try to find the table
    try:
        table = driver.find_element(By.CLASS_NAME, 'rp-horseTable')
        print("Found table with class 'rp-horseTable'\n")
        
        # Get all rows
        rows = table.find_elements(By.TAG_NAME, 'tr')
        print(f"Found {len(rows)} rows\n")
        
        # Check first few rows for structure
        for i, row in enumerate(rows[:3], 1):
            print(f"Row {i}:")
            print(f"  HTML: {row.get_attribute('outerHTML')[:200]}")
            
            # Try to find elements
            cells = row.find_elements(By.TAG_NAME, 'td')
            print(f"  Cells: {len(cells)}")
            
            spans = row.find_elements(By.TAG_NAME, 'span')
            print(f"  Spans: {len(spans)}")
            
            if spans:
                for j, span in enumerate(spans[:3], 1):
                    print(f"    Span {j}: class='{span.get_attribute('class')}' text='{span.text[:30]}'")
            print()
            
    except Exception as e:
        print(f"Error finding table: {e}")
    
finally:
    driver.quit()
