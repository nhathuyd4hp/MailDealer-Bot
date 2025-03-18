from __future__ import annotations
import concurrent.futures
import re
import logging
import concurrent
import pandas as pd
from bot import mail_dealer,touei,web_access

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8',
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


MAX_THREAD = 5
TAB_NAME = "すべて"
MAIL_BOX = '専用アドレス・飯田GH/≪ベトナム納期≫東栄(FAX・メール)'
JOB = "鋼製野縁"
FIELDS = ['確定納期', '案件番号', '物件名','配送先住所']
PROCESS_CONSTRUCTIONS = ["仙台施工","郡山施工","浜松施工","東海施工","関西施工","岡山施工","広島施工","福岡施工","熊本施工","東京施工","神奈川施工"]

def main():
    mailbox: pd.DataFrame = mail_dealer.mailbox(
        mail_box = MAIL_BOX,
        tab_name = TAB_NAME,
    )   
    # Lọc các mail có cột '件名' bắt đầu bằng "【東栄住宅】 工程表更新のお知らせ"
    mailbox = mailbox[mailbox['件名'].str.startswith("【東栄住宅】 工程表更新のお知らせ", na=False)]
    # Loop
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
        construction_ids = [detail for construction in constructions for detail in construction.get("details", [])]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for id in construction_ids:
                future_timeline = executor.submit(touei.get_schedule, id=id, job=JOB)
                future_information = executor.submit(web_access.get_information, construction_id=id, fields=FIELDS)
                timeline = future_timeline.result()
                information = future_information.result()
    
            
            print("OK")
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        del touei
        del web_access
        del mail_dealer
