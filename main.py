import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class FacebookScraper:
    """Handles Facebook scraping operations."""

    def __init__(self, username, password, driver=None):
        """
        Initializes the scraper with user credentials and WebDriver.
        
        Args:
            username (str): Facebook username.
            password (str): Facebook password.
            driver: Selenium WebDriver instance (optional).
        """
        self.username = username
        self.password = password
        self.driver = driver or webdriver.Firefox()

    def login(self):
        """Logs into Facebook using the provided credentials."""
        self.driver.get("https://www.facebook.com/login")
        time.sleep(5)
        
        self.driver.find_element(By.ID, "email").send_keys(self.username)
        self.driver.find_element(By.ID, "pass").send_keys(self.password)
        self.driver.find_element(By.ID, "pass").send_keys(Keys.RETURN)
        time.sleep(10)  # Wait for login to complete

    def navigate_to_saved_posts(self):
        """Navigates to the Facebook saved posts page."""
        self.driver.get("https://www.facebook.com/saved/")
        time.sleep(10)  # Wait for page to load

    def scrape_saved_posts(self, unwanted_keywords):
        """
        Scrapes saved posts, excluding unwanted titles.

        Args:
            unwanted_keywords (list): List of keywords to exclude.

        Returns:
            list: Filtered saved posts' titles.
        """
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6"
        )
        span_texts = [element.text for element in elements]
        return self._filter_unwanted(span_texts, unwanted_keywords)

    def get_links(self, css_selector):
        """
        Extracts href links from <a> tags based on a given CSS selector.

        Args:
            css_selector (str): The CSS selector for the <a> tags to target.

        Returns:
            list: A list of extracted href links.
        """
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            links = [element.get_attribute("href") for element in elements if element.get_attribute("href")]
            return links
        except Exception as e:
            print(f"Error extracting links: {e}")
            return []
        
    @staticmethod
    def _filter_unwanted(span_texts, unwanted_keywords):
        """Filters out unwanted titles from the list."""
        return [text for text in span_texts if text not in unwanted_keywords]

    def close(self):
        """Closes the WebDriver."""
        self.driver.quit()


def main():
    """
    Main function to execute the Facebook scraper.

    Replace 'username' and 'password' with actual Facebook credentials.
    """
    USERNAME = "your_username"
    PASSWORD = "your_password"
    UNWANTED_KEYWORDS = ["مجموعاتي", "للاستخدام لاحقًا", "إنشاء مجموعة جديدة", "إضافة إلى المجموعة"]

    scraper = FacebookScraper(USERNAME, PASSWORD)
    A_TAG_CSS_SELECTOR = (
        "a.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf.xcfux6l."
        "x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r.x11i5rnm."
        "xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8.x1hl2dhg."
        "xggy1nq.x1a2a7pz.x1heor9g.x1sur9pj.xkrqix3.x1s688f"
    )
    try:
        scraper.login()
        scraper.navigate_to_saved_posts()
        saved_posts = scraper.scrape_saved_posts(UNWANTED_KEYWORDS)
        links = scraper.get_links(A_TAG_CSS_SELECTOR)
        print("Filtered Saved Posts:", saved_posts)
        print("Extracted Links:", links)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

    # USERNAME = "01032296137"
    # PASSWORD = "Ha1711@@"
    # UNWANTED_KEYWORDS = ["مجموعاتي", "للاستخدام لاحقًا", "إنشاء مجموعة جديدة", "إضافة إلى المجموعة"]
