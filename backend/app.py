import contextlib
import json
import os
import time
from dataclasses import asdict, dataclass

import requests
import undetected_chromedriver as uc
from flask import Flask, Response, jsonify, redirect, render_template, request, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
CORS(app)  # Enable CORS
socketio = SocketIO(app)


# Stored scraped data
scraped_data = {}


@dataclass
class Pin:
    url: str
    title: str | None
    description: str | None
    image_url: str | None
    image_alt: str | None
    by: str | None
    likes: str | None
    video_src: str | None
    video_poster: str | None


# Utility to set up WebDriver
def setup_driver():
    # options = uc.ChromeOptions()
    # options.add_argument("start-maximized")
    # options.add_argument("disable-infobars")
    # options.add_argument("--disable-notifications")
    # options.add_argument("disable-popup-blocking")
    # options.binary_location = "/run/current-system/sw/bin/brave"
    #
    return webdriver.Firefox()


def scrape_pinterest(email, password):
    """Scrapes Pinterest saved pins."""
    driver = setup_driver()
    pins_list = []
    try:
        driver.get("https://www.pinterest.com/login")

        wait = WebDriverWait(driver, 60)

        email_field = wait.until(EC.element_to_be_clickable((By.ID, "email")))
        email_field.send_keys(email)
        password_field = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        password_field.send_keys(password)
        login_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[data-test-id='registerFormSubmitButton']")
            )
        )
        login_button.click()

        wait.until(
             EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-test-id='header-profile']"))
        ).click()


        driver.get(f"{driver.current_url}_pins/")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='pin']")))
        pins = [
            pin.find_element(By.TAG_NAME, "a").get_attribute("href")
            for pin in driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='pin']")
        ]

        results = []
        for pin in pins:
            wait = WebDriverWait(driver, 2)  # don't move this outside
            driver.get(pin)  # type: ignore
            
            pin_url = driver.current_url
            pin_title = None
            description = None
            image_url = None
            image_alt = None
            by = None
            likes = None
            video_src = None
            video_poster = None

            with contextlib.suppress(TimeoutException):
                pin_title = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[itemprop='name']"))
                ).text

            with contextlib.suppress(TimeoutException):
                description = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "span[data-test-id='richPinInformation-description']")
                    )
                ).text
                description = description.replace("\n ...more", "")

            # high quality images are presented last in the dom
            for img in reversed(
                driver.find_elements(
                    By.CSS_SELECTOR, "div[data-test-id='visual-content-container'] img"
                )
            ):
                if img.get_attribute("src"):
                    image_url = img.get_attribute("src")
                    image_alt = img.get_attribute("alt")
                    break

            for video in reversed(
                driver.find_elements(
                    By.CSS_SELECTOR, "div[data-test-id='visual-content-container'] video"
                )
            ):
                if video.get_attribute("src"):
                    video_src = video.get_attribute("src")
                    video_poster = video.get_attribute("poster")
                    break

            with contextlib.suppress(NoSuchElementException):
                by = driver.find_element(
                    By.CSS_SELECTOR, "a[data-test-id='creator-avatar-link']"
                ).get_attribute("href")

            with contextlib.suppress(NoSuchElementException):
                likes = driver.find_element(
                    By.CSS_SELECTOR, "div[data-test-id='reactions-count-button']"
                ).text

            # pins_list.append(
            #     # Pin(
            #     #     title=pin_title,
            #     #     url=pin_url,
            #     #     description=description,
            #     #     image_url=image_url,
            #     #     image_alt=image_alt,
            #     #     by=by,
            #     #     likes=likes,
            #     #     video_src=video_src,
            #     #     video_poster=video_poster,
            #     # )
                
            # )
            results.append(
                {
                        "title": pin_title,
                        "image_url": image_url,
                        "url": pin_url,
                        "caption": description,
                        "image_alt": image_alt,
                        "by": by,
                        "likes": likes,
                        "video_src": video_src,
                        "video_poster": video_poster
                }
            )

            print("Pin",results)
        return results    
    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()

    return results


# Instagram Scraper Function
def scrape_instagram(username, password):
    """Scrapes Instagram saved posts dynamically, extracting captions, images, and post URLs."""
    driver = setup_driver()
    scraped_posts = []  # List to store scraped post data as dictionaries

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # Log in using username and password
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(10)  # Wait for page load

        # Navigate to saved posts
        saved_posts_url = f"https://www.instagram.com/{username}/saved/all-posts/"
        driver.get(saved_posts_url)
        time.sleep(5)

        # Scroll to load all posts
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Find post containers
            post_elements = driver.find_elements(
                By.XPATH, "//article//a[contains(@href, '/p/')]//img"
            )

            for img_element in post_elements:
                try:
                    # Extract required attributes
                    image_url = img_element.get_attribute("src")  # Image URL
                    image_alt = (
                        img_element.get_attribute("alt") or "No caption"
                    )  # Caption from alt attribute
                    post_link = img_element.find_element(
                        By.XPATH, "../../.."
                    ).get_attribute("href")  # Post link

                    # Create a dictionary matching the front-end format
                    post_data = {
                        "title": image_alt,  # Title is the same as caption
                        "description": image_alt,  # Description is also the caption
                        "image_url": image_url,  # Image URL
                        "image_alt": image_alt,  # Alt text
                        "url": post_link,  # Post link
                    }

                    # Avoid duplicates
                    if post_data not in scraped_posts:
                        scraped_posts.append(post_data)

                except Exception as e:
                    print(f"Error processing post: {e}")

            if len(scraped_posts) >= 10:  # Limit to 10 posts
                break

            # Scroll down to load more content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        return scraped_posts  # Return the list of dictionaries

    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        driver.quit()


# Facebook Scraper Functions
def login_to_facebook(driver, username, password):
    """Logs into Facebook."""
    driver.get("https://www.facebook.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys(username)
    driver.find_element(By.ID, "pass").send_keys(password)
    driver.find_element(By.ID, "pass").send_keys(Keys.RETURN)
    time.sleep(10)


def scrape_facebook_saved_posts(driver):
    """Scrapes Facebook saved posts."""
    try:
        driver.get("https://www.facebook.com/saved/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "x1yztbdb"))
        )
        posts = driver.find_elements(By.CLASS_NAME, "x1yztbdb")

        results = []
        for post in posts:
            try:
                title = post.find_element(By.CSS_SELECTOR, "span[dir='auto'] span").text
                link = post.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                image_url = post.find_element(By.CSS_SELECTOR, "img").get_attribute(
                    "src"
                )
                # post_data = {
                #         "title": image_alt,  # Title is the same as caption
                #         "description": image_alt,  # Description is also the caption
                #         "image_url": image_url,  # Image URL
                #         "image_alt": image_alt,  # Alt text
                #         "url": post_link,  # Post link
                # }
                results.append(
                    {
                        "title": title,
                        "image_url": image_url,
                        "url": link,
                    }
                )
                # results.append({"title": title, "link": link, "image_url": image_url})
                print(f"Extracted data for post: {title}, {link}, {image_url}")
            except Exception as e:
                print(f"Error extracting data: {e}")

        return results

    except Exception as e:
        print(f"Error while scraping: {e}")
        return []


def scrape_facebook(username, password):
    """Wrapper to log in and scrape Facebook saved posts."""
    driver = setup_driver()
    try:
        login_to_facebook(driver, username, password)
        return scrape_facebook_saved_posts(driver)
    finally:
        driver.quit()


# Twitter Scraper Function
def scrape_twitter(email, password):
    """Scrapes bookmarks from Twitter (X)."""
    driver = setup_driver()
    results = []

    try:
        driver.get("https://x.com/i/flow/login")
        wait = WebDriverWait(driver, 60)

        # Enter email
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        email_field.send_keys(email)
        email_field.send_keys(Keys.RETURN)
        time.sleep(10)

        # Enter password
        password_field = wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(10)

        # Navigate to bookmarks
        driver.get("https://x.com/i/bookmarks")

        container = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[aria-label='Timeline: Bookmarks']")
            )
        )
        tweets = container.find_elements(By.TAG_NAME, "article")
        time.sleep(5)  # Let the tweets load

        for tweet in tweets:
            title = ""
            link = ""
            image_url = []

            # Extract tweet text
            with contextlib.suppress(Exception):
                text_container = tweet.find_element(
                    By.CSS_SELECTOR, "div[data-testid='tweetText']"
                )
                title = text_container.text

            # Extract tweet link
            with contextlib.suppress(Exception):
                link = (
                    tweet.find_element(
                        By.CSS_SELECTOR, "div[data-testid='User-Name'] time"
                    )
                    .find_element(By.XPATH, "..")
                    .get_attribute("href")
                )

            # Extract media (photos)
            with contextlib.suppress(Exception):
                mediums = tweet.find_elements(
                    By.CSS_SELECTOR, "div[data-testid='tweetPhoto'] img"
                )
                for media in mediums:
                    image_url.append(media.get_attribute("src"))

            # Append result
            results.append(
                {
                    "title": title,
                    "image_url": image_url,
                    "url": link,
                }
            )

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()

    return results


def load_data_from_json():
    if os.path.exists("scraper_data.json"):
        try:
            with open("scraper_data.json", "r") as f:  # Open in read mode
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
    return {}


def save_data_to_json(data):
    with open("./scraper_data.json", "w") as f:
        json.dump(data, f, indent=4)
        print("Data saved to scraper_data.json")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start-scraping")
def start_scraping():
    return render_template("start_scraping.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    global scraper_data  # Reference the global variable
    if request.method == "POST":
        search_query = request.form.get("search_query")
        if search_query:
            # Filter data based on search query
            filtered_data = {
                platform: [
                    pin for pin in pins if search_query.lower() in str(pin).lower()
                ]
                for platform, pins in scraped_data.items()
            }
        else:
            filtered_data = scraper_data
        return render_template("dashboard.html", data=filtered_data)

    # Load data into the global variable
    scraper_data = load_data_from_json()
    return render_template("dashboard.html", data=scraper_data)


@app.route("/scrape", methods=["POST"])
def scrape_and_render():
    platform = request.form.get("platform")
    username = request.form.get("username")
    password = request.form.get("password")

    if not platform or not username or not password:
        return render_template("start_scraping.html", error="Missing required fields")

    # Perform scraping based on platform
    if platform == "Twitter":
        pins = scrape_twitter(username, password)
    elif platform == "Pinterest":
        pins = scrape_pinterest(username, password)
    elif platform == "Instagram":
        pins = scrape_instagram(username, password)
    elif platform == "Facebook":
        pins = scrape_facebook(username, password)
    else:
        return render_template("start_scraping.html", error="Unsupported platform")

    # Update the global scraped_data dictionary
    global scraped_data
    scraped_data[platform] = pins

    # Save the data to a JSON file
    save_data_to_json(scraped_data)

    # Redirect to the dashboard
    return redirect(url_for("dashboard"))


@app.route("/fetch-image/<path:image_url>")
def fetch_image(image_url):
    """Fetch image from Instagram and serve it through the Flask server."""
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            return Response(response.content, mimetype=response.headers["Content-Type"])
        else:
            return "Image not found", 404
    except Exception as e:
        return f"Error fetching image: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
