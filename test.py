"""
 Use cookies to make a request to TikTok. This script was made for testing case.
"""
import json
import requests

# Load cookies from the JSON file
with open("cookies.json", "r") as file:
    cookies = json.load(file)

# Convert cookies into a format usable by the requests library
cookies_dict = {key: value for key, value in cookies.items()}

# Example URL: TikTok login or profile page
url = "https://www.tiktok.com"

# Start a session with the cookies
session = requests.Session()
session.cookies.update(cookies_dict)

# Make a request to TikTok
response = session.get(url)

# Check the response
if response.status_code == 200:
    print("Successfully loaded TikTok page!")
    print(response.text[:500])  # Print a snippet of the page
else:
    print(f"Failed to load page. Status Code: {response.status_code}")
