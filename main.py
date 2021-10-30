from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common import exceptions
import time
from datetime import datetime

from Utils import compress_png_lossy, PNGQUANT_NotFound
from db import Database

import SeleriumDriver

# You can choose the browser and tools for the driver. Example: Chrome, Firefox, Safari, Brave, Brave + Tor, Firefox + Tor and more.

#driver = SeleriumDriver.get_brave_tor_driver()
driver = SeleriumDriver.get_chrome_driver()


url = "https://twitter.com/search?q=Israel&src=typed_query&f=live"
driver.get(url)

TMP_SCREENSHOT_FILE_NAME = "shot.png"
TMP_SCREENSHOT_FILE_NAME_COMPRESSED = "shot_compressed.png"


def hide_element(xpath):
    footer = driver.find_element(By.XPATH, xpath)
    driver.execute_script(f'arguments[0].style.display="none"', footer)


def remove_footer():
    xpath = '//*[@id="layers"]/div'
    hide_element(xpath)


class TwitterHarverster:
    def __init__(self):
        self.db = Database()
        self.db.create_db()
        remove_footer()

tweets_xpath = '/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/*'

inner_tweet_sender_id_xpath = './div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[2]/div/span'
inner_tweet_sender_display_name_xpath = './div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[1]/div[1]/span/span'
inner_tweet_likes = './/div[contains(@aria-label, "Like")]'
inner_tweet_id = ".//a[contains(@href, '/status/')]"

inner_tweet_message = './/div[@lang]'

id_queue = []

harverster = TwitterHarverster()

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
            try:
                compress_png_lossy(TMP_SCREENSHOT_FILE_NAME)
            except PNGQUANT_NotFound:
                driver.quit()
                break

            driver.execute_script("arguments[0].style.border='3px red solid'", tweet)

            try:
                _sender_id = tweet.find_element(By.XPATH, inner_tweet_sender_id_xpath).text
            except exceptions.NoSuchElementException:
                _sender_id = None
                # Something is wrong.


            try:
                _sender_display_name = tweet.find_element(By.XPATH, inner_tweet_sender_display_name_xpath).text
            except exceptions.NoSuchElementException:
                _sender_display_name = None
                # Something is wrong. Why can't we find the sender name?

            try:
                _datetime_element = WebDriverWait(driver, 20).until(lambda x: x.find_element(By.XPATH, "//time"))
                _tweet_timestamp = _datetime_element.get_attribute("datetime")
            except exceptions.StaleElementReferenceException as e:
                _tweet_timestamp = None

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
                _tweet_href = None

            _utc_time_now = datetime.utcnow()

            harverster.db.insert_tweet(timestamp=str(_utc_time_now), tweet_timestamp=_tweet_timestamp, sender_id=_sender_id, message=_message_text, message_lang=_message_lang, sender_display_name=_sender_display_name, tweet_href=_tweet_href, screenshot_img_path=TMP_SCREENSHOT_FILE_NAME_COMPRESSED, likes=_likes)

            driver.execute_script("arguments[0].style.border=''", tweet)
            time.sleep(1)
    for id in id_queue:
        if id not in new_ids:
            id_queue.remove(id)
    print(f"Tweets: {len(tweets)}")
