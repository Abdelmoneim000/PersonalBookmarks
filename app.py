from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, Response
from flask_socketio import SocketIO
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import time
import requests


# Flask setup
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
    """Scrapes Instagram saved posts dynamically, extracting captions and images from the saved posts page."""
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
        saved_posts_data = {}
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Find post containers
            post_elements = driver.find_elements(By.XPATH, "//article//a[contains(@href, '/p/')]//img")

            for img_element in post_elements:
                try:
                    caption = img_element.get_attribute("alt") or "No caption"  # Get the caption from the alt attribute
                    image_url = img_element.get_attribute("src")  # Get the image URL
                    post_link = img_element.find_element(By.XPATH, "../../..").get_attribute("href")  # Navigate up to the <a> tag for the link

                    # Add to the dictionary with caption as key
                    if caption not in saved_posts_data:  # Avoid duplicates
                        saved_posts_data[caption] = {"image": image_url, "link": post_link}
                except Exception as e:
                    print(f"Error processing post: {e}")

            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        return saved_posts_data

    except Exception as e:
        print(f"Error: {e}")
        return {}
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

@app.route('/fetch-image/<path:image_url>')
def fetch_image(image_url):
    """Fetch image from Instagram and serve it through the Flask server."""
    try:
        # Fetch the image from the external URL
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            return Response(response.content, mimetype=response.headers['Content-Type'])
        else:
            return "Image not found", 404
    except Exception as e:
        return f"Error fetching image: {e}", 500




@app.route("/dashboard")
def dashboard():
    """Dashboard to view scraped data."""
    return render_template("dashboard.html", user_data=user_data)

if __name__ == "__main__":
    socketio.run(app, debug=True)
