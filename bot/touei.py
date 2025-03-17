import re
import time
import logging
from selenium import webdriver
from datetime import datetime,timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException


def style_to_day(style:str) -> int | None:
    try:
        width_match = re.search(r"width: calc\((.*?)\);", style)
        width_expression = width_match.group(1)
        length_match = re.findall(r"\d+", width_expression)
        width = int(length_match[0])
        return int((width + 15) / 77)
    except:
        return None

class Touei:
    def __init__(
        self,
        username: str,
        password: str,
        timeout: int = 10,
        headless:bool=False,
        logger: logging.Logger = logging.getLogger(__name__)
    ):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-notifications')
        if headless: 
            options.add_argument('--headless=new')
        # Disable log
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')  #
        options.add_argument('--silent')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Attribute
        self.logger = logger
        self.browser = webdriver.Chrome(options=options)
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, timeout)
        self.username = username
        self.password = password
        # Trạng thái đăng nhập
        self.authenticated = self.__authentication(username, password)

    def __authentication(self, username: str, password: str) -> bool:
        self.browser.get('https://sk.touei.co.jp/')
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='userId']"),
                ),
            ).send_keys(username)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='pcPassword']"),
                ),
            ).send_keys(password)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='login']"),
                ),
            ).click()
            return True
        except Exception:
            return False

    def __switch_bar(self, bar: str) -> bool:
        try:
            xpath = f"//a[@class='gpcInfoLink' and text()='{bar}']"
            a = self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath)),
            )
            href = a.get_attribute('href')
            self.browser.get(href)
            return True
        except Exception:
            return False
        
    def timeline(self,id:str,job:str) -> dict | None:
        self.__switch_bar("▼ 工程表")
        schedule = {}
        try:
            id_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"input[name='genbaCode']"))
            )
            id_field.send_keys(id)
            search_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,"input[id='search']")
                )
            )
            search_btn.click()
            # Reload Table
            time.sleep(5)
            # ----- #
            schedules:list[WebElement] = self.browser.find_elements(By.CSS_SELECTOR,"input[value='工程表']")
            if len(schedules) != 1:
                self.logger.warning("No building found or multiple buildings found.")
                return None
            time.sleep(1)
            schedules[0].click()
            # --------------- #
            calendar_area : WebElement = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"div[id='calendar_area']"))
            )
            timeline: list[WebElement] = calendar_area.find_elements(By.TAG_NAME,'div')
            
            time.sleep(1)
            koteihyo_area:WebElement = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"div[id='koteihyo_area']"))
            )
            
            koteihyo_area_goto_areas = koteihyo_area.find_elements(By.CSS_SELECTOR,"div[class='goto_area']")
            for no_stage, stage in enumerate(koteihyo_area_goto_areas):
                # koteihyo_area_goto_area_one_day_area là danh sách các job trong ngày hôm đó
                koteihyo_area_goto_area_one_day_areas: list[WebElement] = stage.find_elements(By.CSS_SELECTOR,"div[class='one_day_area   ']")
                for index,koteihyo_area_goto_area_one_day_area in enumerate(koteihyo_area_goto_area_one_day_areas):
                    try:
                        found_job = koteihyo_area_goto_area_one_day_area.find_element(By.CSS_SELECTOR,f"span[title='{job}']")
                        job_duration = style_to_day(found_job.get_attribute("style"))
                        start_date = datetime.strptime(timeline[index].get_attribute('title'), "%Y/%m/%d")
                        schedule[no_stage+1] = {
                            "start":start_date,
                            "end":start_date+timedelta(job_duration),
                        }
                        break
                    except NoSuchElementException:
                        continue

            return schedule
        except Exception as e:
            self.logger.error(e)
            return None
            
            
__all__ = [Touei]