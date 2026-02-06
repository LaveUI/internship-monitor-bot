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
# ENV
# -----------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MAX_LINKS_PER_COMPANY = 30      # hard cap
MAX_VALID_RESULTS = 10          # stop early if found enough

BLOCKED_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "medium.com",
    "blog",
    "about",
    "help",
    "privacy",
    "terms"
]

ALLOWED_JOB_DOMAINS = [
    "amazon.jobs",
    "careers.google.com",
    "jobs.careers.microsoft.com",
    "nvidia.wd5.myworkdayjobs.com",
    "jobs.sap.com",
    "careers.adobe.com"
]



INDIA_LOCATIONS = [
    "india", "bengaluru", "bangalore", "hyderabad",
    "pune", "mumbai", "delhi", "noida",
    "chennai", "gurgaon", "gurugram"
]

ROLE_KEYWORDS = [
    "software engineer", "software developer", "sde",
    "data science", "data scientist", "machine learning"
]

INTERN_KEYWORDS = [
    "intern", "internship", "apprentice", "apprenticeship", "student"
]

# -----------------------------------
# LOAD COMPANIES
# -----------------------------------
def load_companies(csv_path="list.csv"):
    companies = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append((row["Company"].strip(), row["Career Portal URL"].strip()))
    return companies

# -----------------------------------
# TELEGRAM
# -----------------------------------
def send_telegram_alert(company, link):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    message = (
        f"🚀 *New Internship Link Detected!*\n\n"
        f"🏢 *Company:* {company}\n"
        f"🔗 [View Job]({link})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    requests.post(url, data=payload)


def is_valid_job(driver):
    text = driver.page_source.lower()

    if not any(loc in text for loc in INDIA_LOCATIONS):
        return False

    if not any(role in text for role in ROLE_KEYWORDS):
        return False

    if not any(i in text for i in INTERN_KEYWORDS):
        return False

    return True


# -----------------------------------
# GOOGLE SHEETS
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
# SELENIUM
# -----------------------------------
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# -----------------------------------
# GENERIC MONITOR
# -----------------------------------
def monitor_company(company, url):
    print(f"🔍 Monitoring {company}")
    driver = get_driver()
    driver.get(url)
    time.sleep(8)

    valid_links = set()
    visited = set()
    checked = 0

    for a in driver.find_elements(By.TAG_NAME, "a"):
        if checked >= MAX_LINKS_PER_COMPANY:
            break
        if len(valid_links) >= MAX_VALID_RESULTS:
            break

        href = a.get_attribute("href")
        if not href or href in visited:
            continue

        visited.add(href)
        href_l = href.lower()

        # 🚫 Block junk & social domains
        if any(bad in href_l for bad in BLOCKED_DOMAINS):
            continue

        # ✅ Allow only known career/job domains
        if not any(domain in href_l for domain in ALLOWED_JOB_DOMAINS):
            continue

        # 🔍 Must look like a job detail URL
        if not any(k in href_l for k in ["job", "jobs", "intern", "opening", "position"]):
            continue

        # 🚫 Skip pagination / filters
        if any(x in href_l for x in ["search?", "page=", "filter", "category"]):
            continue

        checked += 1

        # Open job page
        driver.execute_script("window.open(arguments[0]);", href)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)

        try:
            if is_valid_job(driver):
                valid_links.add(href)
        except Exception:
            pass

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    driver.quit()
    print(
        f"🇮🇳 Found {len(valid_links)} valid India SDE/DS internships "
        f"at {company} (checked {checked} links)"
    )
    return valid_links




# -----------------------------------
# DEDUP + SAVE
# -----------------------------------
def save_new_links(company, links):
    existing = sheet.get_all_values()
    existing_links = set(row[3] for row in existing[1:])

    new_rows = []

    for link in links:
        if link not in existing_links:
            new_rows.append([
                company,
                "Internship",
                "N/A",
                link,
                datetime.today().strftime("%Y-%m-%d"),
                "Not Applied"
            ])
            send_telegram_alert(company, link)

    if new_rows:
        sheet.append_rows(new_rows)
        print(f"📊 Added {len(new_rows)} new internships")
    else:
        print("ℹ️ No new internships found")

# -----------------------------------
# MAIN
# -----------------------------------
def run_bot():
    print("🚀 Internship Monitor Started\n")

    companies = load_companies()

    for company, url in companies:
        try:
            links = monitor_company(company, url)
            save_new_links(company, links)
            time.sleep(5)
        except Exception as e:
            print(f"❌ Failed for {company}: {e}")

    print("\n🎯 Monitoring Complete")

# -----------------------------------
if __name__ == "__main__":
    run_bot()
