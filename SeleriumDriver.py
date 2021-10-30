from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

_chrome_driver_path = r'C:\Users\Shlomi\Desktop\Projects\chromedriver_win32\chromedriver.exe'
_brave_path = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'

# option.add_argument("--incognito")
# option.add_argument("--headless")


def get_chrome_driver():
    driver = webdriver.Chrome(ChromeDriverManager().install())
    return driver


def get_brave_tor_driver():
    option = webdriver.ChromeOptions()
    option.binary_location = _brave_path
    option.add_argument("--tor")  # Launch in Tor mode

    driver = webdriver.Chrome(executable_path=_chrome_driver_path, chrome_options=option)

    return driver

