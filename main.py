import sys
import concurrent.futures
import re
import logging
import concurrent
import pandas as pd
import datetime
from bot import MailDealer,Touei,WebAccess
from bot import touei

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler('bot.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(),
    ],
)

def process_schedu_email_content(content:str) -> list[str]:
    buildings = []
    def split_raw_buildings(content) -> list[str]:    
        pattern = r"■--------------------------------------------------------------------\n(.*?)\n--------------------------------------------------------------------■"
        matches = re.findall(pattern, content, re.DOTALL)
        return matches
    def extract_data_building(building: str):   
        sumary_regex = r"(.+?)\s*[\u3000\s](\d+)件"
        building_regex = r"\((\d+)\)" 
        sumary_match = re.search(sumary_regex, building)
        if sumary_match:
            department = sumary_match.group(1)
            project_count = int(sumary_match.group(2))
            department = re.sub(r"（.*?）", "", department)
        else:
            department, project_count = None, 0
        project_ids = re.findall(building_regex, building)
        return {
            "construction": department,
            "quantity": project_count,
            "details": project_ids
        }
        
    matches = split_raw_buildings(content)
    for match in matches:
        building = extract_data_building(match)
        buildings.append(building)
    return buildings

TAB_NAME = "新着"
MAIL_BOX = '専用アドレス・飯田GH/≪ベトナム納期≫東栄(FAX・メール)'
TASK = "鋼製野縁"
FIELDS = ['確定納期', '案件番号', '物件名','配送先住所']
PROCESS_CONSTRUCTIONS = ["仙台施工","郡山施工","浜松施工","東海施工","関西施工","岡山施工","広島施工","福岡施工","熊本施工","東京施工","神奈川施工"]

def run(outputFile:str,timeout:int=10,headless:bool=False):
    touei = Touei(
        username="c0032",
        password="nsk159753",
        headless=headless,
        timeout=timeout,
        logger_name="Touei",
    ) 
    web_access = WebAccess(
        username="2909",
        password="159753",
        headless=headless,
        timeout=timeout,
        logger_name="WebAccess",
    )
    mail_dealer = MailDealer(
        username='vietnamrpa',
        password='nsk159753',
        headless=headless,
        timeout=timeout,
        logger_name="MailDealer",
    )

    
    logger = logging.getLogger("Main")
    
    mailbox: pd.DataFrame = mail_dealer.mailbox(
        mail_box = MAIL_BOX,
        tab_name = TAB_NAME,
    )   
    # Chuyển cột 日付 thành datetime "%y/%m/%d %H:%M"
    mailbox["日付"] = pd.to_datetime(mailbox["日付"], format="%y/%m/%d %H:%M", errors="coerce")
    # Lọc các mail có cột '件名' bắt đầu bằng "【東栄住宅】 工程表更新のお知らせ"
    mailbox = mailbox[mailbox['件名'].str.startswith("【東栄住宅】 工程表更新のお知らせ", na=False)]
    # Chỉ xử lí các mail hôm nay
    mailbox = mailbox[mailbox['日付'].dt.date == datetime.date.today()]  
    # Result
    result = pd.DataFrame(
        columns=['案件番号','物件名','CODE','NOUKI TOEUI','NOUKI WEBACCESS','NOUKI DIFF','RESULT',"NOTE"],
        dtype=object,
    )
    # Duyệt từng Mail
    for ID in mailbox['ID'].to_list():
        content = mail_dealer.read_mail(
            mail_box=MAIL_BOX,
            mail_id=ID,
            tab_name=TAB_NAME,
        )
        constructions:list[dict] = process_schedu_email_content(content)
        # Chỉ lấy các element có key construction nằm trong PROCESS_CONSTRUCTIONS cần xử lí
        constructions:list[dict] = [item for item in constructions if any(keyword in item.get("construction", "") for keyword in PROCESS_CONSTRUCTIONS)]
        # Lấy các constructions_id cần xử lí
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for construction in constructions:
                for construction_id in construction.get("details"):
                    future_timeline = executor.submit(touei.get_schedule, construction_id=construction_id, task=TASK)
                    future_information = executor.submit(web_access.get_information, construction_id=construction_id, fields=FIELDS)
                    job_timeline = future_timeline.result()
                    web_access_information = future_information.result()
                    if job_timeline == None:
                        result.loc[len(result)] = [None,None,construction_id,None,None,None,False,"KHÔNG LẤY ĐƯỢC THÔNG TIN Ở TOEUI"]
                        continue
                    if web_access_information.empty:
                        result.loc[len(result)] = [None,None,construction_id,None,None,None,False,"KHÔNG LẤY ĐƯỢC THÔNG TIN Ở WEB ACCESS"]
                        continue
                    if construction.get("construction").startswith("東京施工"):
                        # Nếu địa chỉ trong access (cột 配送先住所) không chứa 1 trong những giá trị này ignore_region thì result ghi: vùng không cần làm-> bot không làm các bước tiếp theo
                        ignore_region = ['甲府市、','富士吉田市、','都留市、',"山梨市、",'大月市、',"韮崎市、","南アルプス市、","北杜市、","甲斐市、","笛吹市、","上野原市、","甲州市、","中央市"]
                        配送先住所:list = web_access_information['配送先住所'].to_list()
                        if not any(region in address for region in ignore_region for address in 配送先住所):
                            if web_access_information.empty:
                                result.loc[len(result)] = [None,None,construction_id,None,None,None,False,"IGNORE"]
                            else:
                                for index, row in web_access_information.iterrows():
                                    touei_endtime:datetime.datetime = job_timeline.get(index+1).get("end")
                                    web_access_endtime = None
                                    try:
                                        web_access_endtime = datetime.datetime.strptime(row['確定納期'],"%y/%m/%d")
                                    except Exception:
                                        pass
                                    result.loc[len(result)] = [row['案件番号'],row['物件名'],construction_id,touei_endtime.strftime("%Y-%m-%d"),web_access_endtime.strftime("%Y-%m-%d"),0,False,"IGNORE"]
                            continue
                    if construction.get("construction").startswith("神奈川施工"):
                        ignore_region = ['静岡県']
                        配送先住所:list = web_access_information['配送先住所'].to_list()
                        if not any(region in address for region in ignore_region for address in 配送先住所):
                            if web_access_information.empty:
                                result.loc[len(result)] = [None,None,construction_id,None,None,None,False,"IGNORE"]
                            else:
                                for index, row in web_access_information.iterrows():
                                    touei_endtime:datetime.datetime = job_timeline.get(index+1).get("end")
                                    web_access_endtime = None
                                    try:
                                        web_access_endtime = datetime.datetime.strptime(row['確定納期'],"%y/%m/%d")
                                    except Exception:
                                        pass
                                    result.loc[len(result)] = [row['案件番号'],row['物件名'],construction_id,touei_endtime.strftime("%Y-%m-%d"),web_access_endtime.strftime("%Y-%m-%d"),0,False,"IGNORE"]
                            continue
                    for 案件番号 in web_access_information['案件番号']:
                        result_一括操作 = mail_dealer.一括操作(
                            案件ID=案件番号,
                            このメールと同じ親番号のメールをすべて関連付ける=True,
                        )
                        for index, row in web_access_information.iterrows():
                            touei_endtime:datetime.datetime = job_timeline.get(index+1).get("end")
                            web_access_endtime = None
                            try:
                                web_access_endtime = datetime.datetime.strptime(row['確定納期'],"%y/%m/%d")
                            except Exception:
                                pass
                            result.loc[len(result)] = [
                                案件番号,
                                row['物件名'],
                                construction_id,
                                touei_endtime.strftime("%Y-%m-%d"),
                                web_access_endtime.strftime("%Y-%m-%d") if web_access_endtime != None else web_access_endtime,
                                (web_access_endtime-touei_endtime) if web_access_endtime != None else None,
                                result_一括操作[0],
                                result_一括操作[1],
                            ]
    result.drop_duplicates(inplace=True)
    result.to_excel(outputFile,index=False)
    logger.info(f"Kết quả: {outputFile}")
    
if __name__ == '__main__':
    run(
        outputFile="test_v2.xlsx",
        timeout=5,
        headless=False,
    )
    
        
        
