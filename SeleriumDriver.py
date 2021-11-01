from enum import Enum

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

_chrome_driver_path = r'C:\Users\Shlomi\Desktop\Projects\chromedriver_win32\chromedriver.exe'
_brave_path = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'


# option.add_argument("--incognito")

class Browser(Enum):
    BRAVE = "brave"
    CHROME = "chrome"
    FIREFOX = "firefox"


def get_driver(browser: Browser, tor: bool = False, headless: bool = False):
    match browser:
        case Browser.BRAVE:
            option = webdriver.ChromeOptions()
            option.binary_location = _brave_path
            if tor:
                option.add_argument("--tor")
            if headless:
                option.add_argument("--headless")
            driver = webdriver.Chrome(executable_path=_chrome_driver_path, chrome_options=option)
            return driver
        case Browser.CHROME:
            driver = webdriver.Chrome(ChromeDriverManager().install())
            return driver
        case Browser.FIREFOX:
            print("Firefox not supported right now")
