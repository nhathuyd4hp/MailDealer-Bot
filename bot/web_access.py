import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

class WebAccess:
    def __init__(
        self,
        username: str,
        password: str,
        timeout: int = 10,
        headless:bool=False,
        logger_name: str = __name__,
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
        self.logger = logging.getLogger(logger_name)
        self.browser = webdriver.Chrome(options=options)
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, timeout)
        self.username = username
        self.password = password
        # Trạng thái đăng nhập
        self.authenticated = self.__authentication(username, password)
        
    def __del__(self):
        if hasattr(self,"browser"):
            self.browser.quit()
        
    def __authentication(self,username:str,password:str) -> bool:
        try:
            self.browser.get("https://webaccess.nsk-cad.com")
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"input[type='text']"))
            ).send_keys(username)
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"input[type='password']"))
            ).send_keys(password)
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"button[class='btn login']"))
            ).click()
            self.logger.info('✅ Xác thực thành công!')
            return True
        except Exception as e:
            self.logger.error(f'❌ Xác thực thất bại! {e}.')
            return False
    def __switch_tab(self,tab:str) -> bool:
        try:
            a = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,f"a[title='{tab}']")
                )
            )
            href = a.get_attribute("href")
            self.browser.get(href)
            return True
        except Exception as e:
            self.logger.error(e)
            return False
        
    def get_information(self,construction_id:str,fields:list[str] = None) -> pd.DataFrame:
        try:
            self.__switch_tab("受注一覧")
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,"button[type='reset']")
                )
            ).click()
            date_picker = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,"input[name='search_fix_deliver_date_from']")
                )
            )
            date_picker.clear()
            date_picker.send_keys(Keys.ESCAPE)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,"input[name='search_construction_no']")
                )
            ).send_keys(construction_id)
            
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,"button[type='submit']")
                )
            ).click()
            try:
                time.sleep(5)
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH,"//td[text()='検索結果はありません']")
                    )
                )
                self.logger.warning(f'❌ Construction:{construction_id} không có dữ liệu')
                return pd.DataFrame(columns=fields)
            except TimeoutException:
                time.sleep(1)
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,"input[id='checkAll']")
                    )
                ).click()
                
                
                if not fields:
                    self.wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR,"input[id='checkAll']")
                        )
                    ).click()
                else:
                    for field in fields:
                        xpath = f"//label[text()='{field}']//input[@type='checkbox']"
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH,xpath)
                            )
                        ).click()
                    
                    
                data_tables = self.wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,"div[class='dataTables_scroll']")
                    )
                )
                # Columns            
                dataTables_scrollHead = data_tables.find_element(By.CSS_SELECTOR,"div[class='dataTables_scrollHead']")
                spans = dataTables_scrollHead.find_elements(By.TAG_NAME,'span')
                columns = [span.text for span in spans]

                df = pd.DataFrame(columns=columns)
                # Row
                dataTables_scrollBody = data_tables.find_element(By.CSS_SELECTOR,"div[class='dataTables_scrollBody']")
                dataTables_scrollBody_tbody = dataTables_scrollBody.find_element(By.TAG_NAME,'tbody')
                dataTables_scrollBody_tbody_trs = dataTables_scrollBody_tbody.find_elements(By.TAG_NAME,'tr')
                for tr in dataTables_scrollBody_tbody_trs:
                    tds = tr.find_elements(By.TAG_NAME,'td')
                    row = [td.text for td in tds][1:]
                    df.loc[len(df)] = row  
                self.logger.info(f'✅ Lấy dữ liệu construction:{construction_id} thành công')
                return df
        
        except Exception as e:
            self.logger.error(e)
            return pd.DataFrame(columns=fields)
            
        


__all__ = [WebAccess]

        
    
    

        