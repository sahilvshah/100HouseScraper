#!/usr/bin/env python3
"""
100 House NJ Apartment Scraper with Anti-Detection
Solutions for 403 Forbidden errors
"""

import requests
import re
import smtplib
import os
import time
import random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup

# Try to import pyjson5 for better JavaScript parsing
try:
    import pyjson5
    HAS_PYJSON5 = True
except ImportError:
    HAS_PYJSON5 = False

# Email configuration
EMAIL_FROM = os.getenv('EMAIL_FROM', 'your_email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your_app_password')
EMAIL_TO = os.getenv('EMAIL_TO', 'mail84.sahil@gmail.com')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Anti-detection measures
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0'
]

def get_session_with_retries():
    """Create a session with anti-detection measures"""
    session = requests.Session()
    
    # Random user agent
    user_agent = random.choice(USER_AGENTS)
    
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    return session

def make_request_with_retries(session, url, max_retries=3):
    """Make request with retries and delays"""
    for attempt in range(max_retries):
        try:
            # Random delay between requests
            if attempt > 0:
                delay = random.uniform(2, 5)
                print(f"⏳ Waiting {delay:.1f} seconds before retry {attempt + 1}...")
                time.sleep(delay)
            
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                print(f"🚫 403 Forbidden on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    # Try with different user agent
                    session.headers['User-Agent'] = random.choice(USER_AGENTS)
                    continue
            else:
                print(f"⚠️ HTTP {response.status_code} on attempt {attempt + 1}")
                
        except requests.RequestException as e:
            print(f"🔴 Request error on attempt {attempt + 1}: {str(e)}")
            
        if attempt < max_retries - 1:
            delay = random.uniform(3, 8)
            print(f"⏳ Waiting {delay:.1f} seconds before next attempt...")
            time.sleep(delay)
    
    return None

def try_alternative_endpoints():
    """Try alternative ways to access the data"""
    
    alternative_urls = [
        "https://100housejc.securecafe.com/onlineleasing/100house/oleapplication.aspx?stepname=floorplan",
        "https://100housejc.securecafe.com/onlineleasing/100house/",
        "https://www.100housejc.com/floorplans/",
        "https://www.100housejc.com/availability/"
    ]
    
    session = get_session_with_retries()
    
    for url in alternative_urls:
        print(f"🔍 Trying: {url}")
        response = make_request_with_retries(session, url)
        
        if response and response.status_code == 200:
            print(f"✅ Success with: {url}")
            return response
        
        # Small delay between different URLs
        time.sleep(random.uniform(1, 3))
    
    return None

def extract_floorplans_manually(js_obj_str):
    """Manual extraction fallback if pyjson5 is unavailable"""
    floorplans = []
    
    fp_pattern = r'\{\s*id:\s*(\d+).*?\}'
    fp_matches = re.finditer(fp_pattern, js_obj_str, re.DOTALL)
    
    for match in fp_matches:
        fp_str = match.group(0)
        floorplan = {}
        
        id_match = re.search(r'id:\s*(\d+)', fp_str)
        if id_match:
            floorplan['id'] = int(id_match.group(1))
        
        name_match = re.search(r'name:\s*["\']([^"\']+)["\']', fp_str)
        if name_match:
            floorplan['name'] = name_match.group(1)
        
        beds_match = re.search(r'beds:\s*(\d+)', fp_str)
        if beds_match:
            floorplan['beds'] = int(beds_match.group(1))
        
        baths_match = re.search(r'baths:\s*([\d.]+)', fp_str)
        if baths_match:
            floorplan['baths'] = float(baths_match.group(1))
        
        url_match = re.search(r'availableUnitsURL:\s*["\']([^"\']*)["\']', fp_str)
        if url_match:
            floorplan['availableUnitsURL'] = url_match.group(1)
        
        count_match = re.search(r'availableCount:\s*(\d+)', fp_str)
        if count_match:
            floorplan['availableCount'] = int(count_match.group(1))
        
        if floorplan:
            floorplans.append(floorplan)
    
    return floorplans

def get_available_apartments():
    """Main function to scrape available 2BR/2BA apartments with anti-detection"""
    
    try:
        print("🔍 Fetching apartment data...")
        
        # Try main URL first with retries
        session = get_session_with_retries()
        url = "https://100housejc.securecafe.com/onlineleasing/100house/oleapplication.aspx?stepname=floorplan"
        
        response = make_request_with_retries(session, url)
        
        # If main URL fails, try alternatives
        if not response:
            print("🔄 Trying alternative endpoints...")
            response = try_alternative_endpoints()
        
        if not response:
            return None, "All endpoints returned 403 Forbidden or failed"
        
        print("✅ Successfully fetched page data")
        
        # Extract JavaScript pageData object
        pattern = r'var pageData = ({.*?});'
        match = re.search(pattern, response.text, re.DOTALL)
        
        if not match:
            return None, "Could not find apartment data in response"
        
        page_data_str = match.group(1)
        
        # Parse the JavaScript object
        page_data = None
        
        if HAS_PYJSON5:
            try:
                page_data = pyjson5.decode(page_data_str)
            except Exception:
                pass
        
        if not page_data:
            floorplans = extract_floorplans_manually(page_data_str)
            page_data = {'floorplans': floorplans}
        
        floorplans = page_data.get('floorplans', [])
        
        if not floorplans:
            return None, "No floorplan data found"
        
        # Filter for 2BR/2BA units
        target_floorplans = [fp for fp in floorplans 
                           if fp.get('beds') == 2 and fp.get('baths') == 2.0]
        
        if not target_floorplans:
            return [], "No 2BR/2BA apartments found"
        
        print(f"✅ Found {len(target_floorplans)} 2BR/2BA floorplan(s)")
        
        # Get apartment details for each floorplan
        all_apartments = []
        
        for floorplan in target_floorplans:
            floorplan_name = floorplan.get('name', 'Unknown')
            available_units_url = floorplan.get('availableUnitsURL', '')
            
            # Extract URL from JavaScript location.href statement
            url_match = re.search(r"location\.href='([^']+)'", available_units_url)
            if url_match:
                units_url = url_match.group(1)
            elif available_units_url:
                units_url = available_units_url
            else:
                continue
            
            print(f"🔍 Checking {floorplan_name} apartments...")
            
            # Add delay between requests
            time.sleep(random.uniform(1, 3))
            
            try:
                units_response = make_request_with_retries(session, units_url)
                
                if not units_response:
                    print(f"⚠️ Failed to fetch {floorplan_name} listings")
                    continue
                
                soup = BeautifulSoup(units_response.content, 'html.parser')
                apartment_rows = soup.find_all('tr', class_='AvailUnitRow')
                
                for row in apartment_rows:
                    apt_cell = row.find('td', {'data-label': 'Apartment'})
                    rent_cell = row.find('td', {'data-label': 'Rent'})
                    
                    if apt_cell and rent_cell:
                        apt_number = apt_cell.get_text(strip=True).replace('#', '').strip()
                        rent = rent_cell.get_text(strip=True)
                        
                        all_apartments.append({
                            'apartment': apt_number,
                            'floorplan': floorplan_name,
                            'rent': rent
                        })
                
            except Exception as e:
                print(f"⚠️ Error checking {floorplan_name}: {str(e)}")
        
        return all_apartments, None
        
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def create_email_content(apartments, error_msg=None):
    """Create HTML email content"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if error_msg:
        subject = "🚨 100 House NJ Scraper - Error Report"
        html_content = f"""
        <html>
        <body>
            <h2>🚨 100 House NJ Apartment Scraper - Error</h2>
            <p><strong>Time:</strong> {timestamp}</p>
            <p><strong>Error:</strong> {error_msg}</p>
            <p>The scraper encountered an issue. This might be due to:</p>
            <ul>
                <li>Website blocking automated requests (403 Forbidden)</li>
                <li>Website structure changes</li>
                <li>Temporary network issues</li>
            </ul>
            <p>The script will try again at the next scheduled time.</p>
        </body>
        </html>
        """
        text_content = f"Error at {timestamp}: {error_msg}"
        
    elif not apartments:
        subject = "🏠 100 House NJ - No Apartments Available"
        html_content = f"""
        <html>
        <body>
            <h2>🏠 100 House NJ Apartment Report</h2>
            <p><strong>Time:</strong> {timestamp}</p>
            <p><strong>Status:</strong> No 2BR/2BA apartments currently available</p>
            <p>Keep checking! New apartments may become available soon.</p>
        </body>
        </html>
        """
        text_content = f"No apartments available at {timestamp}"
        
    else:
        subject = f"🏠 100 House NJ - {len(apartments)} Apartment(s) Available!"
        
        apartment_rows = ""
        for i, apt in enumerate(apartments, 1):
            apartment_rows += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px;">{i}</td>
                <td style="padding: 10px; font-weight: bold;">#{apt['apartment']}</td>
                <td style="padding: 10px;">{apt['floorplan']}</td>
                <td style="padding: 10px; color: #2e8b57;">{apt['rent']}</td>
            </tr>
            """
        
        html_content = f"""
        <html>
        <body>
            <h2>🏠 100 House NJ Apartment Report</h2>
            <p><strong>Time:</strong> {timestamp}</p>
            <p><strong>Found {len(apartments)} available 2BR/2BA apartment(s):</strong></p>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f57534; color: white;">
                        <th style="padding: 12px; text-align: left;">#</th>
                        <th style="padding: 12px; text-align: left;">Apartment</th>
                        <th style="padding: 12px; text-align: left;">Floorplan</th>
                        <th style="padding: 12px; text-align: left;">Rent</th>
                    </tr>
                </thead>
                <tbody>
                    {apartment_rows}
                </tbody>
            </table>
            
            <p><a href="https://100housejc.com" style="color: #f57534;">Visit 100 House NJ Website</a></p>
        </body>
        </html>
        """
        
        text_content = f"Found {len(apartments)} apartments at {timestamp}:\n"
        for i, apt in enumerate(apartments, 1):
            text_content += f"{i}. Apartment #{apt['apartment']} ({apt['floorplan']}) - {apt['rent']}\n"
    
    return subject, html_content, text_content

def send_email(apartments, error_msg=None):
    """Send email with apartment results"""
    if not EMAIL_FROM or not EMAIL_PASSWORD:
        print("❌ Email credentials not configured")
        return False
    
    try:
        subject, html_content, text_content = create_email_content(apartments, error_msg)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {EMAIL_TO}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def main():
    """Main function for scheduled execution"""
    print("🏠 100 House NJ Apartment Scraper (Anti-Detection)")
    print(f"📅 Running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Add initial random delay to avoid pattern detection
    initial_delay = random.uniform(1, 10)
    print(f"⏳ Initial delay: {initial_delay:.1f} seconds")
    time.sleep(initial_delay)
    
    apartments, error_msg = get_available_apartments()
    
    if error_msg:
        print(f"❌ Error: {error_msg}")
        send_email(None, error_msg)
    else:
        if apartments:
            print(f"✅ Found {len(apartments)} apartment(s)")
            for apt in apartments:
                print(f"   🏠 #{apt['apartment']} ({apt['floorplan']}) - {apt['rent']}")
        else:
            print("❌ No apartments available")
        
        send_email(apartments)
    
    print("-" * 50)
    print("✅ Script completed")

if __name__ == "__main__":
    main()