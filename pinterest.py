import contextlib
from dataclasses import dataclass
from getpass import getpass

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-notifications")
options.add_argument("disable-popup-blocking")

options.binary_location = "/home/body20002/.nix-profile/bin/brave"

email = input("Email: ")
password = getpass()

driver = webdriver.Firefox()


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


wait.until(EC.element_to_be_clickable((By.XPATH, "//h2[text()='All Pins']"))).click()

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='pin']")))
pins = [
    pin.find_element(By.TAG_NAME, "a").get_attribute("href")
    for pin in driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='pin']")
]

print(pins)


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


pins_list = []

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

driver.quit()

# do whatever you want :)
print(pins_list)
print(len(pins_list))
