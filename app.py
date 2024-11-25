from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Store user-scraped data
user_data = {}

# Selenium WebDriver setup
def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options)

def scrape_instagram(username, password):
    """Scrapes Instagram saved posts dynamically by scrolling to load all content."""
    driver = setup_driver()
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # Log in using username and password
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(10)  # Adjust based on load time

        # Navigate to saved posts
        saved_posts_url = f"https://www.instagram.com/{username}/saved/all-posts/"
        driver.get(saved_posts_url)
        time.sleep(5)

        # Scroll to load all posts
        saved_posts = set()  # Using a set to avoid duplicates
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Find post links and add them to the set
            elements = driver.find_elements(By.XPATH, "//article//a")
            for el in elements:
                saved_posts.add(el.get_attribute("href"))

            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # Wait for new content to load

            # Check new scroll height and compare it with the last height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Stop scrolling if no new content is loaded
            last_height = new_height

        return list(saved_posts)  # Convert set back to list

    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        driver.quit()



# Flask Routes
@app.route("/")
def index():
    """Home page to select platform."""
    return render_template("index.html")

@app.route("/start-scraping", methods=["POST"])
def start_scraping():
    """Starts scraping based on user inputs."""
    platform = request.form["platform"]
    username_or_email = request.form["username"]  # Updated name attribute
    password = request.form["password"]

    # Perform scraping in a thread
    def run_scraping():
        data = []
        if platform == "Instagram":
            data = scrape_instagram(username_or_email, password)  # Pass the updated variable

        # Save data to user_data
        user_data[platform] = data
        print(data)
        # Notify client scraping is complete
        socketio.emit("scraping_complete", {"platform": platform, "data": data})

    thread = threading.Thread(target=run_scraping)
    thread.start()

    return jsonify({"status": "scraping_started"})

@app.route("/dashboard")
def dashboard():
    """Dashboard to view scraped data."""
    return render_template("dashboard.html", user_data=user_data)

if __name__ == "__main__":
    socketio.run(app, debug=True)
