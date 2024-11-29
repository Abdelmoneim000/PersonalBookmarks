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
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        self.driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        time.sleep(10)

    def scrape_saved_posts(self):
        """
        Scrapes Facebook saved posts, extracting titles, links, and images.

        Returns:
            list of dict: A list of dictionaries containing `title`, `link`, and `image`.
        """
        try:
            # Navigate to saved posts
            self.driver.get("https://www.facebook.com/saved/")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "x1yztbdb"))
            )
            posts = self.driver.find_elements(By.CLASS_NAME, "x1yztbdb")

            results = []
            for post in posts:
                try:
                    title = post.find_element(By.CSS_SELECTOR, "span[dir='auto'] span").text
                    
                    link = post.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    img = post.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                    
                    results.append({
                        "title": title,
                        "link": link,
                        "image": img
                    })
                except Exception as e:
                    print(f"خطأ في استخراج البيانات: {e}")  

            return results

        except Exception as e:
            print(f"Error while scraping: {e}")
            return []

    def close(self):
        """
        Closes the browser and ends the WebDriver session.
        """
        self.driver.quit()


def main():
    USERNAME = "your_username"
    PASSWORD = "your_password"

    scraper = FacebookScraper(USERNAME, PASSWORD)

    try:
        scraper.login()

        saved_posts = scraper.scrape_saved_posts()

        print("Extracted Saved Posts:")
        for post in saved_posts:
            print(f"Title: {post['title']}\nLink: {post['link']}\nImage: {post['image']}\n")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

