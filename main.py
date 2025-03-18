from __future__ import annotations
from datetime import datetime
import re
import os
import logging
import concurrent.futures
import itertools
import pandas as pd
from bot import MailDealer
from bot import Touei
from bot import WebAccess

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
            "department": department,
            "project_count": project_count,
            "project_ids": project_ids
        }
        
    matches = split_raw_buildings(content)
    for match in matches:
        building = extract_data_building(match)
        buildings.append(building)
    return buildings


    
file_path = 'result.xlsx'

process_building = ["仙台施工","郡山施工","浜松施工","東海施工","関西施工","岡山施工","広島施工","福岡施工","熊本施工","東京施工","神奈川施工"]

fields=['確定納期', '案件番号', '物件名','配送先住所']

mail_dealer = MailDealer(
    username='vietnamrpa',
    password='nsk159753',
    headless=True,
    timeout=5,
    logger=logging.getLogger('MailDealer'),
)

# touei= Touei(
#     username="c0032",
#     password="nsk159753",
#     headless=True,
#     logger=logging.getLogger('Touei'),
# )

# web_access = WebAccess(
#     username="2909",
#     password="159753",
#     headless=True,
#     logger=logging.getLogger('WebAccess'),
# )

MAX_THREAD = 5    

TAB_NAME = "すべて"

MAIL_BOX = '専用アドレス・飯田GH/≪ベトナム納期≫東栄(FAX・メール)'

def main():
    mailbox: pd.DataFrame = mail_dealer.mailbox(
        mail_box = MAIL_BOX,
        tab_name = TAB_NAME,
    )   
    # Lọc các mail có cột '件名' bắt đầu bằng "【東栄住宅】 工程表更新のお知らせ"
    mailbox = mailbox[mailbox['件名'].str.startswith("【東栄住宅】 工程表更新のお知らせ", na=False)]
    # 
    for ID in mailbox['ID'].to_list():
        content = mail_dealer.read_mail(
            mail_box=MAIL_BOX,
            mail_id=ID,
            tab_name=TAB_NAME,
        )
        buildings = process_schedu_email_content(content)
        print("OK")
    

if __name__ == '__main__':    
    main()
