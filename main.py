from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common import exceptions
import sqlite3
import time
from datetime import datetime
import subprocess
import os


driver = webdriver.Chrome(ChromeDriverManager().install())

url = "https://twitter.com/search?q=Israel&src=typed_query&f=live"
driver.get(url)

con = sqlite3.connect('tweets.db')
cur = con.cursor()

TMP_SCREENSHOT_FILE_NAME = "shot.png"
TMP_SCREENSHOT_FILE_NAME_COMPRESSED = "shot_compressed.png"

def create_db():
    cur.execute(f'''CREATE TABLE IF NOT EXISTS Tweets
                   (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tweet_timestamp DATETIME,
                    sender_id TEXT,
                    sender_display_name TEXT,
                    message BLOB,
                    message_lang TEXT,
                    screenshot BLOB,
                    likes INTEGER,
                    comments INTEGER,
                    tweet_href TEXT);''')
    con.commit()

def hide_element(xpath):
    footer = driver.find_element(By.XPATH, xpath)
    driver.execute_script(f'arguments[0].style.display="none"', footer)

def remove_footer():
    xpath = '//*[@id="layers"]/div'
    hide_element(xpath)

def compress(quality = 1):
    _exec = r'C:\Users\Shlomi\Downloads\pngquant-windows\pngquant\pngquant.exe'

    if os.path.exists(TMP_SCREENSHOT_FILE_NAME_COMPRESSED):
        os.remove(TMP_SCREENSHOT_FILE_NAME_COMPRESSED)

    p = subprocess.Popen([_exec, "--quality", str(quality), "--ext", "_compressed.png", TMP_SCREENSHOT_FILE_NAME])
    p.wait()

create_db()

remove_footer()
tweets_xpath = '/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/*'


inner_tweet_sender_id_xpath = './div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[2]/div/span'
inner_tweet_sender_display_name_xpath = './div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[1]/div[1]/span/span'
inner_tweet_likes = './/div[contains(@aria-label, "Like")]'
inner_tweet_id = ".//a[contains(@href, '/status/')]"

inner_tweet_message = './/div[@lang]'

id_queue = []

while True:
    tweets = WebDriverWait(driver, 10).until(lambda x: x.find_elements(By.XPATH, tweets_xpath))
    time.sleep(3)
    new_ids = []
    for tweet in tweets:
        id = tweet.id
        new_ids.append(id)
        if id not in id_queue:
            id_queue.append(id)

            tweet.screenshot(TMP_SCREENSHOT_FILE_NAME)
            compress()

            driver.execute_script("arguments[0].style.border='3px red solid'", tweet)

            _sender_id = tweet.find_element(By.XPATH, inner_tweet_sender_id_xpath).text
            _sender_display_name = tweet.find_element(By.XPATH, inner_tweet_sender_display_name_xpath).text

            try:
                _datetime_element = WebDriverWait(driver, 20).until(lambda x: x.find_element(By.XPATH, "//time"))
                _datetime = _datetime_element.get_attribute("datetime")
            except exceptions.StaleElementReferenceException as e:
                _datetime = None

            try:
                _message = tweet.find_element(By.XPATH, inner_tweet_message)
                _message_lang = _message.get_attribute("lang")
                _message_text = _message.text
            except exceptions.NoSuchElementException as e:
                _message = None
                _message_lang = None
                _message_text = None

            try:
                _likes = tweet.find_element(By.XPATH, inner_tweet_likes).text
            except exceptions.NoSuchElementException:
                _likes = None

            try:
                _tweet_id = tweet.find_element(By.XPATH, inner_tweet_id)
                _tweet_href = _tweet_id.get_attribute("href")
            except exceptions.NoSuchElementException:
                _tweet_id = None

            _utc_time_now = datetime.utcnow()

            with open(TMP_SCREENSHOT_FILE_NAME_COMPRESSED, "rb") as file:
                _screenshot_binary = sqlite3.Binary(file.read())
                cur.execute("INSERT INTO Tweets (timestamp, tweet_timestamp, sender_id, message, screenshot, message_lang, sender_display_name, tweet_href) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", [_utc_time_now, _datetime, _sender_id, _message_text, _screenshot_binary, _message_lang, _sender_display_name, _tweet_href])
                con.commit()
            driver.execute_script("arguments[0].style.border=''", tweet)
            time.sleep(1)
    for id in id_queue:
        if id not in new_ids:
            id_queue.remove(id)
    print(f"Tweets: {len(tweets)}")
