from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import os
import csv
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------------
# ENV VARIABLES (SECURE)
# -----------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# -----------------------------------
# FILTERS
# -----------------------------------
ALLOWED_LOCATIONS = [
    "hyderabad",
    "bengaluru",
    "bangalore",
    "mumbai",
    "delhi",
    "noida"
]

ROLE_KEYWORDS = [
    "data science",
    "data scientist",
    "software engineer",
    "software developer",
    "sde"
]

INTERN_KEYWORDS = [
    "intern",
    "internship",
    "student",
    "trainee",
    "apprentice",
    "apprenticeship"
]

# -----------------------------------
# LOAD COMPANIES FROM CSV
# -----------------------------------
def load_companies(csv_path="list.csv"):
    companies = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row["Company"].strip()
            url = row["Career Portal URL"].strip()
            companies.append((company, url))
    return companies

# -----------------------------------
# TELEGRAM ALERT
# -----------------------------------
def send_telegram_alert(row):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    message = (
        f"🚀 *New Internship Found!*\n\n"
        f"🏢 *Company:* {row[0]}\n"
        f"💼 *Role:* {row[1]}\n"
        f"📍 *Location:* {row[2]}\n"
        f"🔗 [Apply Here]({row[3]})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    requests.post(url, data=payload)

# -----------------------------------
# GOOGLE SHEETS SETUP
# -----------------------------------
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDS = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", SCOPE
)

client = gspread.authorize(CREDS)
sheet = client.open("Internship Tracker").sheet1

# -----------------------------------
# SELENIUM SETUP
# -----------------------------------
def get_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# -----------------------------------
# SCRAPER
# -----------------------------------
def scrape_company(company_name, url, wait_time=6):
    print(f"🔍 Scraping {company_name}")
    driver = get_driver()
    driver.get(url)
    time.sleep(wait_time)

    results = []
    visited = set()
    job_links = driver.find_elements(By.TAG_NAME, "a")

    for job in job_links:
        href = job.get_attribute("href")
        text = job.text or ""

        if not href or href in visited:
            continue

        visited.add(href)

        combined_text = f"{text} {href}".lower()

        # Internship filter
        if not any(k in combined_text for k in INTERN_KEYWORDS):
            continue

        # Role filter
        if not any(r in combined_text for r in ROLE_KEYWORDS):
            continue

        # Open job page
        driver.execute_script("window.open(arguments[0]);", href)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)

        #page_text = driver.page_source.lower()
        #matched_city = None

        #for city in ALLOWED_LOCATIONS:
         #   if city in page_text:
          #      matched_city = city.title()
           #     break

        #driver.close()
        #driver.switch_to.window(driver.window_handles[0])

        #if not matched_city:
         #   continue
        page_text = driver.page_source.lower()

        matched_city = "All Locations"

        driver.close()
        driver.switch_to.window(driver.window_handles[0])


        results.append([
            company_name,
            text.strip() if text.strip() else "Internship Role",
            matched_city,
            href,
            url,
            datetime.today().strftime("%Y-%m-%d"),
            "Not Applied"
        ])

    driver.quit()
    print(f"✅ Found {len(results)} valid internships at {company_name}")
    return results

# -----------------------------------
# GOOGLE SHEETS APPEND (DEDUP + TELEGRAM)
# -----------------------------------
def append_to_sheet(data):
    if not data:
        print("ℹ️ No data to add")
        return

    existing = sheet.get_all_values()
    existing_set = set(tuple(row[:4]) for row in existing[1:])

    new_rows = []
    for row in data:
        key = tuple(row[:4])
        if key not in existing_set:
            new_rows.append(row)
            send_telegram_alert(row)

    if new_rows:
        sheet.append_rows(new_rows)
        print(f"📊 Added {len(new_rows)} new rows to Google Sheets")
    else:
        print("ℹ️ No new unique internships found")

# -----------------------------------
# MAIN RUNNER
# -----------------------------------
def run_bot():
    test_url = "PASTE_YOUR_ACTUAL_INTERNSHIP_LINK_HERE"
    driver = get_driver()
    driver.get(test_url)
    time.sleep(5)

    print(driver.title)
    print(driver.current_url)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    driver.quit()


# -----------------------------------
if __name__ == "__main__":
    run_bot()
