import undetected_chromedriver as uc
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Path to cookies and localStorage JSON file
DATA_FILE = "session_data.json"

# Selenium WebDriver setup
def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    # Uncomment for headless mode
    # options.add_argument("--headless")
    return uc.Chrome(options=options)

def login_tiktok(driver):
    # Navigate to TikTok login page
    driver.get("https://www.tiktok.com/login")

    driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div/div/div/div[3]/div[2]').click()
    driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[1]/form/div[1]/a').click()

    # Wait for the login page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))

    # Enter your TikTok username and password
    username_input = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
    time.sleep(30)
    password_input = driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[1]/form/div[2]/div/input')
    time.sleep(5)
    username_input.send_keys("ab2arabi222@gmail.com")
    password_input.send_keys("LOokylooky7&")

    # Submit the login form
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    # Wait for the user to be logged in
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-e2e='user-avatar']")))

def save_session_data(driver):
    # Get cookies and localStorage data
    cookies = driver.get_cookies()
    localStorage = driver.execute_script("return window.localStorage;")

    # Save the data to a JSON file
    with open(DATA_FILE, "w") as f:
        json.dump({"cookies": cookies, "localStorage": localStorage}, f)

def load_session_data(driver):
    try:
        # Load the session data from the JSON file
        with open(DATA_FILE, "r") as f:
            session_data = json.load(f)

        # Set cookies and localStorage
        for cookie in session_data["cookies"]:
            # Modify the cookie domain to match the current website
            cookie["domain"] = ".tiktok.com"
            driver.add_cookie(cookie)
        driver.execute_script("window.localStorage.clear();")
        for key, value in session_data["localStorage"].items():
            driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")

        # Navigate to TikTok
        driver.get("https://www.tiktok.com")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-e2e='user-avatar']")))
        print("Session data loaded successfully.")
    except FileNotFoundError:
        print("No saved session data found. Logging in again.")
        login_tiktok(driver)
        save_session_data(driver)

if __name__ == "__main__":
    driver = setup_driver()
    load_session_data(driver)
    time.sleep(60)

    # Your code to interact with TikTok goes here
    # ...

    driver.quit()