# Internship Automation Bot 🚀

A Python-based automation bot that scrapes internship opportunities from multiple company career pages, applies smart filters (role + location), stores results in Google Sheets, and sends Telegram alerts for new opportunities.

Built using **Selenium**, **Google Sheets API**, and **Telegram Bot API**.

---

## ✨ Features

- 🔍 Scrapes internships from real company career pages (JS-heavy sites)
- 🎯 Filters by role:
  - Data Science
  - Software Engineer
  - Software Developer
- 📍 Filters by location:
  - Hyderabad
  - Bengaluru / Bangalore
  - Mumbai
  - Delhi
  - Noida
- 📊 Automatically updates a Google Sheet
- 🔔 Sends Telegram alerts only for **new internships**
- 🔁 Deduplication (no repeated entries)
- 🕒 Can be scheduled to run automatically using cron (Linux)

---

## 🛠 Tech Stack

- Python 3.10+
- Selenium + ChromeDriver
- Google Sheets API
- Telegram Bot API
- Headless Chrome

---

## 📂 Project Structure

├── internship_bot.py
├── service_account.json # (NOT committed, local only)
├── .gitignore
├── README.md
├── requirements.txt


---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/LaveUI/internship-automation-bot.git
cd internship-automation-bot

### Create and activate virtual environment

python3 -m venv .venv
source .venv/bin/activate

### Requirements

pip install -r requirements.txt
or
uv add -r requirements.txt


### Setup bot for personal use

Get Chat / Group ID

Send a message to your bot (or Telegram group)

Open:

https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates


Copy chat.id


export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_or_group_id"

#copy and paste this on terminal


#run this script

python internship_bot.py
