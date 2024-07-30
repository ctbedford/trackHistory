#!/home/tyler/GithubStuff/trackHistory/venv/bin/python3
import logging
from browser_history import get_history
import time
import sqlite3
from urllib.parse import urlparse
import re
from collections import defaultdict
import sys
import traceback
from datetime import datetime

# Set up logging
logging.basicConfig(filename='/home/tyler/GithubStuff/trackHistory/browsing-history-tracker.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


def categorize_url(url):
    domain = urlparse(url).netloc
    categories = {
        r'(youtube|vimeo|dailymotion)': 'Video',
        r'(facebook|twitter|instagram|linkedin)': 'Social Media',
        r'(gmail|outlook|yahoo)': 'Email',
        r'(amazon|ebay|aliexpress)': 'Shopping',
        r'(nytimes|bbc|cnn)': 'News',
        r'(stackoverflow|github|gitlab)': 'Programming',
        r'(wikipedia|britannica)': 'Education'
    }
    for pattern, category in categories.items():
        if re.search(pattern, domain):
            return category
    return 'Other'


last_url = None
last_timestamp = None
time_spent = defaultdict(int)


def process_browser_history():
    global last_url, last_timestamp
    conn = None
    try:
        db_path = '/home/tyler/GithubStuff/trackHistory/browsing_history.db'
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (timestamp TEXT, url TEXT, title TEXT, category TEXT, time_spent INTEGER)''')

        outputs = get_history()
        his = outputs.histories

        if not his:
            logging.warning(
                "No browser history found. Ensure a supported browser is installed and running.")
            return False

        current_time = int(time.time())

        for h in his:
            if len(h) >= 2:
                timestamp, url = h[:2]
                title = ''  # browser_history doesn't provide titles
                category = categorize_url(url)

                logging.info(f"Processing URL: {url} (Category: {category})")

                # Calculate time spent on the last URL
                if last_url and last_timestamp:
                    time_diff = int(timestamp.timestamp()) - last_timestamp
                    time_spent[last_url] += time_diff

                # Insert new record
                c.execute('''INSERT INTO history 
                             (timestamp, url, title, category, time_spent) 
                             VALUES (?, ?, ?, ?, ?)''',
                          (timestamp.isoformat(), url, title, category, 0))  # Initialize time_spent as 0

                last_url = url
                last_timestamp = int(timestamp.timestamp())

        # Update time spent for the last visited URL
        if last_url and last_timestamp:
            final_time_diff = current_time - last_timestamp
            time_spent[last_url] += final_time_diff
            c.execute('''UPDATE history 
                         SET time_spent = ? 
                         WHERE url = ? AND timestamp = ?''',
                      (time_spent[last_url], last_url, datetime.fromtimestamp(last_timestamp).isoformat()))

        conn.commit()
        logging.info("Successfully processed and updated browser history.")
        return True
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
    except Exception as e:
        logging.error(f"Error processing browser history: {e}")
    finally:
        if conn:
            conn.close()
    return False


def main():
    logging.info("Starting browser history tracking process.")
    while True:
        success = process_browser_history()
        if not success:
            logging.warning(
                "Failed to process browser history. Retrying in 60 seconds.")
        time.sleep(60)  # Wait for 60 seconds before the next check


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Browser history tracking stopped by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error in main function: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)
