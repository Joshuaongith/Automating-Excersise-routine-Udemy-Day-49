from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import datetime

#load environment variables
load_dotenv()
# Initialization
ACCOUNT_EMAIL = os.getenv("ACCOUNT_EMAIL")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

# Configure Selenium to stay open using the Chrome option
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

# Give Selenium its own user profile.
# Have your script create a directory in your project folder to store your Chrome Profile information with:
user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

# Tell your Chrome Driver to use the directory you specified to store a "profile".
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

driver = webdriver.Chrome(options=chrome_options)

driver.get("https://appbrewery.github.io/gym/")

# Login into the account
# find and click login button
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "login-button"))
)
login_button.click()

# find email field and enter credentials
email_input = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "email-input"))
)
email_input.send_keys(ACCOUNT_EMAIL)
# find password field and enter credentials and use enter key to log in
password_input = driver.find_element(By.ID, "password-input")
password_input.send_keys(ACCOUNT_PASSWORD, Keys.ENTER)

def get_class_date(day):
    today = datetime.date.today()
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    target_day = days.index(day.lower())
    # Calculate how many days we need to add to reach Tuesday (which is day 1)
    # Math: Target Day (1) - Today's Day
    days_ahead = target_day - today.weekday()
    # if it is currently tuesday, or it is already past tuesday this week
    if days_ahead <= 0:
        days_ahead += 7

    # get next tuesday date with timedelta
    formatted_date = today + datetime.timedelta(days=days_ahead)
    return formatted_date


# Global Trackers ---
classes_booked = 0
waitlists_joined = 0
already_booked = 0
failed_or_skipped = 0

# The days you want to work out this week
target_days = ["Tuesday", "Thursday"]

for day in target_days:
    locator_date = get_class_date(day).strftime("%Y-%m-%d-1800")
    display_date = get_class_date(day).strftime("%B %d")
    session = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"#book-button-spin-{locator_date}"))
    )

    button_text = session.text.lower()

    if "booked" in button_text:
        print(f"✓ Already booked: Spin Class on {day}, {display_date}")
        already_booked += 1

    elif "waitlisted" in button_text:
        print(f"✓ Already on waitlist: Spin Class on {day}, {display_date}")
        already_booked += 1
    else:
        try:
            # Click it!
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(session))
            session.click()

            # Verify it!
            import time

            time.sleep(1.5)
            new_text = session.text.lower()

            if "booked" in new_text:
                classes_booked += 1
                print(f"✓ {new_text}: Spin Class on {day}, {display_date}")
            elif "waitlisted" in new_text:
                waitlists_joined += 1
                print(f"✓ {new_text}: Spin Class on {day}, {display_date}")

        except TimeoutException:
            # If the button was unclickable, or the site crashed
            print("Error: Could not click the button.")
            failed_or_skipped += 1

# --- 3. The Mathematical Report ---
# Derive the total successful interactions exactly like you suggested:
total_successful = classes_booked + waitlists_joined + already_booked

summary_report = f"""
--- BOOKING SUMMARY ---
Classes booked: {classes_booked}
Waitlists joined: {waitlists_joined}
Already booked/waitlisted: {already_booked}
Total Tuesday 6pm classes processed: {total_successful}
"""
print(summary_report)

# Only show failures if they actually happened!
if failed_or_skipped > 0:
    print(f"⚠️ Failed/Skipped: {failed_or_skipped}")

