from __future__ import annotations

import re
import logging
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

def process_content(content:str) -> list[str]:
    pattern = r"■--------------------------------------------------------------------\n(.*?)\n--------------------------------------------------------------------■"
    matches = re.findall(pattern, content, re.DOTALL)
    return matches

    




def main():
    mail_dealer = MailDealer(
        username='vietnamrpa',
        password='nsk159753',
        logger=logging.getLogger('MailDealer'),
    )
    mail_box = '専用アドレス・飯田GH/≪ベトナム納期≫東栄(FAX・メール)'
    mails = mail_dealer.get_mails(
        mail_box=mail_box,
        tab_name='対応完了',
    )
    # Filter mail
    mails = [mail for mail in mails if mail.get('subject').startswith('【東栄住宅】 工程表更新のお知らせ')]
    # Process email
    for mail in mails[:5]:
        content = mail_dealer.read_mail(
            mail_box = mail_box,
            mail_id = mail.get('id')
        )
        datas = process_content(content)
        for data in datas:
            print('------')
            print(data)

            
            
            


if __name__ == '__main__':
    main()
