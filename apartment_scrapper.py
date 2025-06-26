#!/usr/bin/env python3
"""
100 House NJ Apartment Scraper
Finds available 2BR/2BA apartments and displays them in terminal
"""

import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
import os
import smtplib
from email.mime.text import MIMEText

# Try to import pyjson5 for better JavaScript parsing
try:
    import pyjson5
    HAS_PYJSON5 = True
except ImportError:
    HAS_PYJSON5 = False

def extract_floorplans_manually(js_obj_str):
    """Manual extraction fallback if pyjson5 is unavailable"""
    floorplans = []
    
    # Find all floorplan objects in the JavaScript
    fp_pattern = r'\{\s*id:\s*(\d+).*?\}'
    fp_matches = re.finditer(fp_pattern, js_obj_str, re.DOTALL)
    
    for match in fp_matches:
        fp_str = match.group(0)
        floorplan = {}
        
        # Extract key properties using regex
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

def send_email(subject, body, to_email):
    """Send an email with the given subject and body to the specified address."""
    from_email = os.environ.get("EMAIL_USER")
    app_password = os.environ.get("EMAIL_PASS")
    if not from_email or not app_password:
        print("❌ Email credentials not set in environment variables.")
        return
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, app_password)
            server.sendmail(from_email, [to_email], msg.as_string())
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def get_available_apartments(email_results=False):
    """Main function to scrape available 2BR/2BA apartments"""
    
    # Setup HTTP session with proper headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    })
    
    try:
        # Step 1: Fetch the main floorplan page
        print("🔍 Fetching apartment data...")
        url = "https://100housejc.securecafe.com/onlineleasing/100house/oleapplication.aspx?stepname=floorplan"
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Step 2: Extract JavaScript pageData object
        pattern = r'var pageData = ({.*?});'
        match = re.search(pattern, response.text, re.DOTALL)
        
        if not match:
            print("❌ Could not find apartment data")
            return
        
        page_data_str = match.group(1)
        
        # Step 3: Parse the JavaScript object
        page_data = None
        
        if HAS_PYJSON5:
            try:
                page_data = pyjson5.decode(page_data_str)
            except Exception:
                pass
        
        if not page_data:
            # Fallback to manual parsing
            floorplans = extract_floorplans_manually(page_data_str)
            page_data = {'floorplans': floorplans}
        
        floorplans = page_data.get('floorplans', [])
        
        if not floorplans:
            print("❌ No floorplan data found")
            return
        
        # Step 4: Filter for 2BR/2BA units
        target_floorplans = [fp for fp in floorplans 
                           if fp.get('beds') == 2 and fp.get('baths') == 2.0]
        
        if not target_floorplans:
            print("❌ No 2BR/2BA apartments found")
            return
        
        print(f"✅ Found {len(target_floorplans)} 2BR/2BA floorplan(s)")
        
        # Step 5: Get apartment details for each floorplan
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
            
            try:
                # Fetch apartment listings page
                units_response = session.get(units_url, timeout=30)
                units_response.raise_for_status()
                
                # Parse apartment data from HTML
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
        
        # Step 6: Display results
        display_results(all_apartments, email_results=email_results)
        
    except requests.RequestException as e:
        print(f"❌ Network error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def display_results(apartments, email_results=False):
    """Display the results in a formatted manner and optionally email them."""
    output = []
    output.append("\n" + "="*60)
    output.append("🏠 100 HOUSE NJ - AVAILABLE APARTMENTS")
    output.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("="*60)
    
    if apartments:
        output.append(f"Found {len(apartments)} available 2BR/2BA apartment(s):\n")
        for i, apt in enumerate(apartments, 1):
            output.append(f"{i}. 🏠 Apartment #{apt['apartment']}")
            output.append(f"   📋 Floorplan: {apt['floorplan']}")
            output.append(f"   💰 Rent: {apt['rent']}")
            output.append("")
    else:
        output.append("❌ No apartments currently available")
    output.append("="*60)
    result_str = "\n".join(output)
    print(result_str)
    if email_results:
        send_email(
            subject="100 House NJ - Available 2BR/2BA Apartments",
            body=result_str,
            to_email="mal84.sahil@gmail.com"
        )

def main():
    """Entry point with dependency check"""
    print("🏠 100 House NJ Apartment Scraper")
    print("📋 Searching for 2BR/2BA apartments...")
    if not HAS_PYJSON5:
        print("💡 For better parsing, install pyjson5: pip install pyjson5")
    print("-" * 40)
    # Email results if running in GitHub Actions
    email_results = os.environ.get("EMAIL_RESULTS", "false").lower() == "true"
    get_available_apartments(email_results=email_results)

if __name__ == "__main__":
    main()