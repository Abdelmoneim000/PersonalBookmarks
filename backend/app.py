import contextlib
import time
from dataclasses import dataclass

import undetected_chromedriver as uc
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
socketio = SocketIO(app)


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
    options = webdriver.FirefoxOptions()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("disable-popup-blocking")

    options.binary_location = "/run/current-system/sw/bin/firefox"
    driver = webdriver.Firefox(
        options=options
    )  # Replace with appropriate driver (e.g., Chrome or Edge)
    return driver


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
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[data-test-id='header-profile']")
            )
        ).click()

        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//h2[text()='All Pins']"))
        ).click()

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='pin']"))
        )
        pins = [
            pin.find_element(By.TAG_NAME, "a").get_attribute("href")
            for pin in driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='pin']")
        ]

        for pin in pins:
            wait = WebDriverWait(driver, 2)  # don't move this outside
            driver.get(pin)

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
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div[itemprop='name']")
                    )
                ).text

            with contextlib.suppress(TimeoutException):
                description = wait.until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "span[data-test-id='richPinInformation-description']",
                        )
                    )
                ).text
                description = description.replace("\n ...more", "")

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
                    By.CSS_SELECTOR,
                    "div[data-test-id='visual-content-container'] video",
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

            pins_list.append(
                Pin(
                    title=pin_title,
                    url=pin_url,
                    description=description,
                    image_url=image_url,
                    image_alt=image_alt,
                    by=by,
                    likes=likes,
                    video_src=video_src,
                    video_poster=video_poster,
                )
            )

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()

    return [pin.__dict__ for pin in pins_list]


# Instagram Scraper Function
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
        time.sleep(10)

        # Navigate to saved posts
        saved_posts_url = f"https://www.instagram.com/{username}/saved/all-posts/"
        driver.get(saved_posts_url)
        time.sleep(5)

        # Scroll to load all posts
        saved_posts = set()
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            elements = driver.find_elements(By.XPATH, "//article//a")
            for el in elements:
                saved_posts.add(el.get_attribute("href"))

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        return list(saved_posts)

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
                img = post.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                results.append({"title": title, "link": link, "image": img})
                print(f"Extracted data: {title}, {link}, {img}")
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
            result = {
                "user_link": "",
                "tweet_link": "",
                "text": "",
                "photos": [],
                "videos": [],
            }

            # Extract user profile link
            avatar_container = tweet.find_element(
                By.CSS_SELECTOR, "div[data-testid='Tweet-User-Avatar']"
            )
            result["user_link"] = avatar_container.find_element(
                By.TAG_NAME, "a"
            ).get_attribute("href")

            # Extract tweet text
            text_container = tweet.find_element(
                By.CSS_SELECTOR, "div[data-testid='tweetText']"
            )
            result["text"] = text_container.text

            # Extract tweet link
            result["tweet_link"] = (
                tweet.find_element(By.CSS_SELECTOR, "div[data-testid='User-Name'] time")
                .find_element(By.XPATH, "..")
                .get_attribute("href")
            )

            # Extract media (photos/videos)
            mediums = tweet.find_elements(
                By.CSS_SELECTOR, "div[data-testid='tweetPhoto']"
            )
            for media in mediums:
                with contextlib.suppress(Exception):
                    if image := media.find_element(By.TAG_NAME, "img"):
                        result["photos"].append(
                            {
                                "src": image.get_attribute("src"),
                                "alt": image.get_attribute("alt"),
                            }
                        )
                with contextlib.suppress(Exception):
                    if video := media.find_element(By.TAG_NAME, "video"):
                        result["videos"].append(
                            {
                                "src": video.get_attribute("src"),
                                "poster": video.get_attribute("poster"),
                            }
                        )

            results.append(result)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()

    return results


# REST API Endpoints
@app.route("/")
def health_check():
    return jsonify({"status": "API is running"}), 200


@app.route("/start-scraping", methods=["POST"])
def start_scraping():
    """Starts scraping based on user inputs."""
    data = request.json
    platform = data.get("platform")
    username = data.get("username")
    password = data.get("password")

    if not platform or not username or not password:
        return jsonify({"error": "Missing required fields"}), 400

    scraped_data = []
    if platform == "Twitter":
        scraped_data = scrape_twitter(username, password)
    elif platform == "Pinterest":
        scraped_data = scrape_pinterest(username, password)  # Define Pinterest function
    elif platform == "Instagram":
        scraped_data = scrape_instagram(username, password)  # Define Instagram function
    elif platform == "Facebook":
        scraped_data = scrape_facebook(username, password)  # Define Facebook function
    else:
        return jsonify({"error": "Unsupported platform"}), 400

    return jsonify({"platform": platform, "data": scraped_data}), 200


if __name__ == "__main__":
    app.run(debug=True)
