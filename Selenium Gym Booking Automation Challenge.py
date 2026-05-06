from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import WebDriverOrWebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import datetime
import time

#load environment variables
load_dotenv()
# Initialization
ACCOUNT_EMAIL = os.getenv("ACCOUNT_EMAIL")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

# Configure chrome to stay open using the Chrome option
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

# Give Selenium its own user profile.
# create a directory in project folder to store Chrome Profile information with:
user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

# Tell your Chrome Driver to use the directory you specified to store a "profile".
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://appbrewery.github.io/gym/")



# function to log in into the account
def login():
    # find and click login button
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "login-button"))
    )
    login_button.click()

    # find email field and enter credentials
    email_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "email-input"))
    )
    email_input.clear() #clear in case this is a retry call
    email_input.send_keys(ACCOUNT_EMAIL)
    # find password field and enter credentials and use enter key to log in
    password_input = driver.find_element(By.ID, "password-input")
    password_input.clear() #clear in case this is a retry call
    password_input.send_keys(ACCOUNT_PASSWORD, Keys.ENTER)
    time.sleep(2)

    # 2. Use find elements to check for the SUCCESS element!
    success_indicators = driver.find_elements(By.ID, "my-bookings-link")

    # 3. The Logic Check
    if len(success_indicators) == 0:
        # The list is empty. We are not logged in.
        raise Exception("Login failed: Could not find the bookings link.")
    else:
        # The list has an item! We are officially in.
        print("✓ Login successful!")

# function to get current date from site
def get_current_date():
    site_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#schedule-page h1"))
        ).text.split('(')[1].split(')')[0].split(' ')[1]

    today_date = datetime.datetime.strptime(site_date, "%m/%d/%Y").date()
    return today_date

# function to format date
def get_class_date(day, reference_date):
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    target_day = days.index(day.lower())
    # Calculate how many days we need to add to reach Tuesday (which is day 1)
    # Math: Target Day (1) - Today's Day
    days_ahead = target_day - reference_date.weekday()
    # if it is currently tuesday, or it is already past tuesday this week
    if days_ahead <= 0:
        days_ahead += 7

    # get next tuesday date with timedelta
    formatted_date = reference_date + datetime.timedelta(days=days_ahead)
    return formatted_date

# function to book a class
def book_class(target_day, today_date):
    # The days you want to work out this week


    locator_date = get_class_date(target_day, today_date).strftime("%Y-%m-%d-1800")
    display_date = get_class_date(target_day, today_date).strftime("%B %d")
    session = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"#book-button-spin-{locator_date}"))
    )
    button_text = session.text.lower()

    if "booked" in button_text:
        print(f"✓ Already booked: Spin Class on {target_day}, {display_date}")
        return "already_booked"
    elif "waitlisted" in button_text:
        print(f"✓ Already on waitlist: Spin Class on {target_day}, {display_date}")
        return "already_booked"
    else:
        # Click it!
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(session))
        session.click()
        # Verify it!
        import time
        time.sleep(1.5)
        new_text = session.text.lower()

        if "booked" in new_text:

            print(f"✓ {new_text}: Spin Class on {target_day}, {display_date}")
            return "booked"
        elif "waitlisted" in new_text:
            print(f"✓ {new_text}: Spin Class on {target_day}, {display_date}")
            return "waitlisted"
        else:
            raise Exception("Click swallowed")

# function to verify all booked classes
def verification(t_booked):

    # VERIFICATION

    my_bookings = driver.find_element(By.ID, "my-bookings-link")
    my_bookings.click()
    time.sleep(1.5)

    on_my_bookings = driver.find_elements(By.CSS_SELECTOR, "#my-bookings-page  h1")
    if len(on_my_bookings)>0:

        booked  = driver.find_elements(By.CSS_SELECTOR, "div[data-booking-status='confirmed']")
        waitlisted = driver.find_elements(By.CSS_SELECTOR, "div[data-booking-status='waitlisted']")

        actual_bookings = 0
        # Count Booked
        for item in booked:
            text = item.text.lower()
            # Check for the day and the time(in the time format of the site)
            if ("tue" in text or "thu" in text) and ("6:00" in text):
                print(f"  ✓ Verified: {" ".join(text.split('\n')[:2])} (booked)")
                actual_bookings += 1

        # Count Waitlisted
        for item in waitlisted:
            text = item.text.lower()
            if ("tue" in text or "thu" in text) and ("6:00" in text):
                print(f"  ✓ Verified: {" ".join(text.split('\n')[:2])} (Waitlist)")
                actual_bookings += 1

        # The Final Check
        verification_result = f"""
        --- VERIFICATION RESULT ---
        Expected: {t_booked} bookings
        Found: {actual_bookings} bookings
        """
        print(verification_result)
        if actual_bookings == t_booked:
            print("✅ SUCCESS: All bookings verified!")
        else:
            # abs() ensures we don't get a negative number if actual_bookings is greater than total_successful
            missing_bookings = abs(t_booked - actual_bookings)
            print(f"❌ MISMATCH: Difference of {missing_bookings} bookings")
    else:
        raise Exception("Not on page")

# function to retry incase network of failure
def retry(function, tries = 7,**kwargs):
    for attempt in range(tries):
        try:
            print(f"Try {attempt + 1}: {function}")
            return function(**kwargs)

            break
        except Exception as e:
            time.sleep(attempt*0.5)

    else:
        print("critical failure")

# Manager function
def bot():
    retry(login)
    workout_days = ["Tuesday", "Thursday"]
    today = get_current_date()

    classes_booked = 0
    waitlists_joined = 0
    already_booked = 0

    for day in workout_days:
         result = retry(book_class,  target_day = day, today_date = today)

         if result == "already_booked":
             already_booked += 1
         elif result == "booked":
             classes_booked += 1
         elif result == "waitlisted":
             waitlists_joined += 1

    total_successful = classes_booked + waitlists_joined + already_booked

    retry(verification, t_booked=total_successful)



bot()