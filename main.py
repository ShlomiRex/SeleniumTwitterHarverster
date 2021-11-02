from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common import exceptions
import time
from datetime import datetime

from Utils import compress_png_lossy, PNGQUANT_NotFound
from db import Database

import SeleriumDriver
import logging

FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger()

TMP_SCREENSHOT_FILE_NAME = "shot.png"
TMP_SCREENSHOT_FILE_NAME_COMPRESSED = "shot_compressed.png"

tweets_xpath = '/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/*'
tweets_holder_xpath = '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/*'

inner_tweet_sender_id_xpath = './div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[2]/div/span'
inner_tweet_sender_display_name_xpath = './div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[1]'
inner_tweet_likes = './/div[contains(@aria-label, "Like")]'
inner_tweet_id = ".//a[contains(@href, '/status/')]"
inner_tweet_verified_account = './/div[6]/div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[1]/div[2]/svg[@aria-label="Verified account"]'
inner_tweet_message = './/div[@lang]'
inner_tweet_display_name_and_verified_and_id = './/div/div/article/div/div/div/div[2]/div[2]/div[1]'
inner_tweet_inner_top_verified_account = './/*[local-name() = "svg" and @aria-label="Verified account"]'

id_queue = []


class TwitterHarvester:
    def __init__(self, search_what):
        self.db = Database()
        self.db.create_db()

        self.driver = SeleriumDriver.get_driver(SeleriumDriver.Browser.BRAVE, tor=False, headless=False)

        #url = "https://twitter.com/search?q=Israel&src=typed_query&f=live"
        url = f"https://twitter.com/search?q={search_what}&src=typed_query&f=live"
        self.driver.get(url)

        #self.__remove_footer()
        #self.__remove_header()

    def __get_tweets(self):
        tweets = WebDriverWait(self.driver, 10).until(lambda x: x.find_elements(By.XPATH, tweets_holder_xpath))
        return tweets


    def __process_tweet(self, tweet):

        # try:
        #     self.driver.execute_script("arguments[0].style.border='3px red solid'", tweet)
        # except exceptions.StaleElementReferenceException:
        #     # We don't do anything, it's only visual, not data.
        #     pass

        try:
            tweet.screenshot(TMP_SCREENSHOT_FILE_NAME)
            try:
                compress_png_lossy(TMP_SCREENSHOT_FILE_NAME)
                _screenshot_path = TMP_SCREENSHOT_FILE_NAME_COMPRESSED
            except PNGQUANT_NotFound:
                _screenshot_path = None
                self.driver.quit()
                return

        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _screenshot_path = None

        try:
            _sender_id = tweet.find_element(By.XPATH, inner_tweet_sender_id_xpath).text
            logger.info(f"Sender ID: {_sender_id}")
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _sender_id = None

        try:
            _sender_display_name = tweet.find_element(By.XPATH, inner_tweet_sender_display_name_xpath).text
            logger.info(f"Sender display name: {_sender_display_name}")
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _sender_display_name = None

        try:
            _datetime_element = WebDriverWait(self.driver, 10).until(
                lambda x: x.find_element(By.XPATH, "//time"))
            _tweet_timestamp = _datetime_element.get_attribute("datetime")
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _tweet_timestamp = None

        try:
            _message = tweet.find_element(By.XPATH, inner_tweet_message)
            _message_lang = _message.get_attribute("lang")
            _message_text = _message.text
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _message = None
            _message_lang = None
            _message_text = None

        try:
            _likes = tweet.find_element(By.XPATH, inner_tweet_likes).text
            if _likes == '':
                _likes = 0
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _likes = 0

        try:
            _tweet_id = tweet.find_element(By.XPATH, inner_tweet_id)
            _tweet_href = _tweet_id.get_attribute("href")
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _tweet_href = None

        try:
            _inner_tweet_top_div = tweet.find_element(By.XPATH,
                                                      inner_tweet_display_name_and_verified_and_id)
            _inner_tweet_top_div.find_element(By.XPATH, inner_tweet_inner_top_verified_account)
            _verified_account = True
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            _verified_account = False

        _utc_time_now = datetime.utcnow()

        self.db.insert_tweet(timestamp=str(_utc_time_now), tweet_timestamp=_tweet_timestamp,
                             sender_id=_sender_id, message=_message_text, message_lang=_message_lang,
                             sender_display_name=_sender_display_name, tweet_href=_tweet_href,
                             screenshot_img_path=_screenshot_path, likes=_likes,
                             verified_account=_verified_account)



        try:
            # Delete the tweet
            self.driver.execute_script("arguments[0].remove()", tweet)
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            tweets = WebDriverWait(self.driver, 10).until(lambda x: x.find_elements(By.XPATH, tweets_xpath))
            self.driver.execute_script("arguments[0].remove()", tweets[0])
            # Scroll by amount of tweet height
            #_scroll_y = tweet.rect["height"]
            #self.driver.execute_script(f"window.scrollBy(0, {_scroll_y})")

        #self.driver.execute_script("arguments[0].style.border=''", tweet)

        time.sleep(1)

    def __hide_element(self, xpath):
        # element = driver.find_element(By.XPATH, xpath)
        element = WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath)))
        self.driver.execute_script(f'arguments[0].style.display="none"', element)

    def __remove_footer(self):
        xpath = '//*[@id="layers"]/div'
        self.__hide_element(xpath)

    def __remove_header(self):
        xpath = '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]'
        self.__hide_element(xpath)

    def run(self):
        while True:
            # Tweets feed gets refreshed. So we ask again for the tweets.
            tweets = self.__get_tweets()
            num_tweets = len(tweets)

            logger.info(f"Processing batch of {num_tweets} tweets")

            new_ids = []
            tweet_num = 1
            for tweet in tweets:
                _id = tweet.id
                new_ids.append(_id)
                if _id not in id_queue:
                    id_queue.append(_id)
                    logger.info(f"Processing tweet: {tweet_num}")
                    tweet_num += 1
                    self.__process_tweet(tweet)

            for _id in id_queue:
                if _id not in new_ids:
                    id_queue.remove(_id)


if __name__ == "__main__":
    harvester = TwitterHarvester("Israel")
    harvester.run()
