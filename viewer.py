import sqlite3
import time
import sys
import os

use_notifications = False  # Initialize before the try block

try:
    import notify2
    use_notifications = True
except ImportError:
    print("notify2 or dbus not available. Desktop notifications will be disabled.")

DB_PATH = '/home/tyler/GithubStuff/trackHistory/browsing_history.db'
NOTIFICATION_COOLDOWN = 60  # Minimum seconds between notifications


def get_db_last_modified():
    return os.path.getmtime(DB_PATH)


def view_recent_history():
    global use_notifications
    if use_notifications:
        try:
            notify2.init('Browser History Tracker')
        except Exception as e:
            print(f"Failed to initialize notifications: {e}")
            use_notifications = False

    last_url = None
    last_notification_time = 0
    last_db_modified = get_db_last_modified()

    while True:
        current_db_modified = get_db_last_modified()

        if current_db_modified > last_db_modified:
            print("Database updated. Checking for new entries...")
            last_db_modified = current_db_modified

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row  # This allows accessing columns by name
            c = conn.cursor()
            c.execute(
                "SELECT timestamp, url, category FROM history ORDER BY timestamp DESC LIMIT 1")
            row = c.fetchone()
            conn.close()

            if row and row['url'] != last_url:
                print(
                    f"New entry - Time: {row['timestamp']}, URL: {row['url']}, Category: {row['category']}")

                current_time = time.time()
                if use_notifications and (current_time - last_notification_time) > NOTIFICATION_COOLDOWN:
                    try:
                        notification = notify2.Notification(
                            "New Browser History Entry",
                            f"URL: {row['url']}\nCategory: {row['category']}"
                        )
                        notification.show()
                        last_notification_time = current_time
                    except Exception as e:
                        print(f"Failed to show notification: {e}")

                last_url = row['url']
        else:
            print("No new updates to the database.")

        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    try:
        view_recent_history()
    except KeyboardInterrupt:
        print("\nViewer stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
