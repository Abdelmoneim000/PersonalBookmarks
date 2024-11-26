from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class FacebookScraper:
    """
    A class to scrape Facebook saved posts, extracting titles and links.
    """

    def __init__(self, username, password, driver=None):
        self.username = username
        self.password = password
        self.driver = driver or webdriver.Firefox()

    def login(self):
        """
        Logs into Facebook using the provided username and password.
        """
        self.driver.get("https://www.facebook.com/login")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        self.driver.find_element(By.ID, "email").send_keys(self.username)
        self.driver.find_element(By.ID, "pass").send_keys(self.password)
        self.driver.find_element(By.ID, "pass").send_keys(Keys.RETURN)
        time.sleep(10)

    def scrape_saved_posts(self):
        """
        Scrapes Facebook saved posts, extracting links and titles.

        Returns:
            list of dict: A list of dictionaries containing `title` and `link`.
        """
        try:
            # Navigate to saved posts
            self.driver.get("https://www.facebook.com/saved/")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.x1i10hfl.xjbqb8w.x1ejq31n")
                )
            )

            # CSS selectors for <a> and <span> elements
            link_selector = (
                "a.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf."
                "xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r."
                "x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8."
                "x1hl2dhg.xggy1nq.x1a2a7pz.x1heor9g.x1sur9pj.xkrqix3.x1s688f"
            )
            title_selector = "span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6"

            # Locate all link elements
            links = self.driver.find_elements(By.CSS_SELECTOR, link_selector)

            # Extract titles and links
            saved_posts = []
            for link in links:
                href = link.get_attribute("href")
                try:
                    title_element = link.find_element(By.CSS_SELECTOR, title_selector)
                    title = title_element.text
                    saved_posts.append({"title": title.strip(), "link": href})

                except Exception:
                    continue

            return saved_posts

        except Exception as e:
            print(f"Error while scraping: {e}")
            return []

    def close(self):
        """
        Closes the browser and ends the WebDriver session.
        """
        self.driver.quit()


def main():
    # Replace these with your Facebook credentials
    USERNAME = "username"
    PASSWORD = "password@@"

    # Initialize the scraper
    scraper = FacebookScraper(USERNAME, PASSWORD)

    try:
        # Log in to Facebook
        scraper.login()

        # Scrape saved posts for titles and links
        saved_posts = scraper.scrape_saved_posts()

        # Display results
        print("Extracted Saved Posts:")
        for post in saved_posts:
            if post['title']:  # Only print if the title is not empty
                print(f"Title: {post['title']}\nLink: {post['link']}\n")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        scraper.close()


if __name__ == "__main__":
    main()

