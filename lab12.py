## MASON RUDIN m285640
## Lab 12 - scrape Rotten Tomatoes "Movies in Theaters" (newest first) with Selenium + BeautifulSoup,
## put movie name / critic score / audience score / release date in a DataFrame,
## then INSERT every row into the Movies table from lab12.sql

import re
import time
from datetime import datetime
from urllib import robotparser

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from mydb import db

URL = "https://www.rottentomatoes.com/browse/movies_in_theaters/sort:newest"
USER_AGENT = "SD321 student scraper"
LOAD_MORE_CLICKS = 3        # the page shows ~28 movies, each "Load more" click adds ~30 more

# CSS selectors for the parts of the page we care about
TILE = "a[data-qa='discovery-media-list-item-caption']"            # one per movie
TITLE = "[data-qa='discovery-media-list-item-title']"
CRITIC = "[slot='criticsScore']"                                    # Tomatometer
AUDIENCE = "[slot='audienceScore']"                                 # Popcornmeter
DATE = "[data-qa='discovery-media-list-item-start-date']"           # "Opens ..." / "Re-releasing ..."
LOAD_MORE = "button[data-qa='dlp-load-more-button']"


print(1)
## Check robots.txt first to make sure we are allowed to scrape this page
robots = robotparser.RobotFileParser("https://www.rottentomatoes.com/robots.txt")
robots.read()
if not robots.can_fetch(USER_AGENT, URL):
    raise SystemExit("robots.txt does not allow scraping " + URL)
print("robots.txt allows scraping", URL)


print(2)
## Selenium opens the page in Chrome so the JavaScript runs and the movie tiles get built
driver = webdriver.Chrome()                 # opens a Chrome window (webdriver.Firefox() for Firefox)
driver.get(URL)

# Wait up to 10 seconds for JavaScript to build at least one movie tile
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, TILE)))

# Click "Load more" a few times to get more movies on the page
for i in range(LOAD_MORE_CLICKS):
    buttons = driver.find_elements(By.CSS_SELECTOR, LOAD_MORE)
    if not buttons or not buttons[0].is_displayed():    # no button means no more movies
        break
    count = len(driver.find_elements(By.CSS_SELECTOR, TILE))
    # click with JavaScript so a cookie banner or ad sitting on top of the button can't block the click
    driver.execute_script("arguments[0].click();", buttons[0])
    try:
        # wait until the new movies show up on the page
        WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, TILE)) > count)
    except TimeoutException:
        break
    time.sleep(1)                           # be polite: one request per second

page = BeautifulSoup(driver.page_source, "html.parser")    # the HTML AFTER JavaScript ran
driver.quit()


print(3)
## Pull the 4 fields out of every movie tile with BeautifulSoup

def get_text(tile, selector):
    """Text inside the tag, or "" if the tile doesn't have that tag"""
    tag = tile.select_one(selector)
    return tag.get_text(strip=True) if tag else ""

def to_score(text):
    """'74%' -> 74.  A movie with no score yet has '' -> None (goes in the table as NULL)"""
    digits = text.replace("%", "").strip()
    return int(digits) if digits.isdigit() else None

def to_date(text):
    """'Opens Nov 20, 2026' / 'Opened Jul 03, 2026' / 'Re-releasing Nov 22, 2026' -> date(2026, 11, 20)
    Only the date is kept because the table only has a DATE column."""
    match = re.search(r"([A-Z][a-z]{2})[a-z]*\.? (\d{1,2}), (\d{4})", text)
    if not match:
        return None
    return datetime.strptime(" ".join(match.groups()), "%b %d %Y").date()

rows = []
for tile in page.select(TILE):
    name = get_text(tile, TITLE)
    if not name:
        continue
    rows.append({
        "MName":         name[:40].strip(), # MName is VARCHAR(40), so cut longer titles to 40 characters
        "CriticScore":   to_score(get_text(tile, CRITIC)),
        "AudienceScore": to_score(get_text(tile, AUDIENCE)),
        "ReleaseDate":   to_date(get_text(tile, DATE)),
    })


print(4)
## Put the rows in a DataFrame. dtype=object keeps missing scores as None instead of NaN,
## because MySQLdb knows None means NULL but doesn't know what to do with NaN
df = pd.DataFrame(rows, columns=["MName", "CriticScore", "AudienceScore", "ReleaseDate"], dtype=object)
df = df.drop_duplicates(subset="MName")     # MName is the primary key, so each name can only be in once
print(df.to_string())
print(df.shape)


print(5)
## INSERT each row of the DataFrame into the Movies table.
## ON DUPLICATE KEY UPDATE means running the lab again updates the scores
## instead of erroring because the movie name (primary key) is already in the table.
query = """INSERT INTO Movies (MName, CriticScore, AudienceScore, ReleaseDate)
           VALUES (%s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE CriticScore = VALUES(CriticScore),
                                   AudienceScore = VALUES(AudienceScore),
                                   ReleaseDate = VALUES(ReleaseDate)"""

saved = 0
for row in df.itertuples(index=False):
    column_info, data, insert_id, error = db.query(query, list(row))
    if error:
        print("Could not insert", row.MName, "->", error)
    else:
        saved += 1
print(saved, "of", len(df), "movies saved to the Movies table")


print(6)
## Read the table back to check what got stored
movies, error = db.querydf("SELECT * FROM Movies ORDER BY ReleaseDate DESC, MName")
if error:
    print(error)
else:
    print(movies.to_string())

db.close()
