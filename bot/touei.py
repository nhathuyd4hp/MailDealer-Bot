import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
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
        duration = int((width + 15) / 77)
        return duration - 1
    except:
        return None

class Touei:
    def __init__(
        self,
        username: str,
        password: str,
        timeout: int = 10,
        headless:bool=False,
        logger_name: str = __name__
    ):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-notifications')
        if headless: 
            options.add_argument('--headless=new')
        # Disable log
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')  #
        options.add_argument('--silent')
        options.add_argument("--incognito")  
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Attribute
        self.logger = logging.getLogger(logger_name)
        self.browser = webdriver.Chrome(options=options)
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, timeout)
        self.username = username
        self.password = password
        # Trạng thái đăng nhập
        self.authenticated = self.__authentication(username, password)
        
    def __del__(self):
        if hasattr(self,"browser") and isinstance(self.browser,WebDriver):
            self.browser.quit()
        
    def __authentication(self, username: str, password: str) -> bool:
        time.sleep(0.5)
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
            if not hasattr(self,"authenticated") or not self.authenticated:
                self.logger.info('✅ Xác thực thành công!')
            return True
        except Exception as e:
            self.logger.error(f'❌ Xác thực thất bại! {e}.')
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
        
    def get_schedule(self,construction_id:str,task:str) -> dict | None:
        self.__authentication(self.username,self.password)
        self.__switch_bar("▼ 工程表")
        schedule = {}
        try:
            id_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"input[name='genbaCode']"))
            )
            id_field.send_keys(construction_id)
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
                self.logger.warning(f"❌ Không tìm thấy construction: {construction_id} hoặc tìm thấy nhiều hơn 1")
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
                koteihyo_area_goto_area_one_day_areas: list[WebElement] = stage.find_elements(
                    By.CSS_SELECTOR,
                    "div[class='one_day_area   '],div[class='one_day_area kokaiHaniBack  '],div[class='one_day_area   today'],div[class='one_day_area  unKokaiHaniBack ']"
                )
                for index,koteihyo_area_goto_area_one_day_area in enumerate(koteihyo_area_goto_area_one_day_areas):
                    try:
                        found_job = koteihyo_area_goto_area_one_day_area.find_element(By.CSS_SELECTOR,f"span[title='{task}']")
                        job_duration = style_to_day(found_job.get_attribute("style"))
                        start_date = datetime.strptime(timeline[index].get_attribute('title'), "%Y/%m/%d")
                        schedule[no_stage+1] = {
                            "start":start_date,
                            "end":start_date+timedelta(job_duration),
                        }
                        break
                    except NoSuchElementException:
                        continue
            if schedule == {}:
                self.logger.info(f"Không có task:{task} trong Construction:{construction_id}")
                return None
            self.logger.info(f'✅ Lấy lịch trình: {construction_id} task:{task} thành công!')
            return schedule
        except Exception as e:
            self.logger.error(f'❌ Lấy lịch trình: {construction_id} task:{task} thất bại! {e}')
            return None
            
    
       
__all__ = [Touei]