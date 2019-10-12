from requests import post
from urllib.parse import quote as qt

def telegram(token, chat_id, text = None, file = None, filetype = None):
    if text and file == None:
        post(f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={qt(text)}&parse_mode=markdown')
    elif file and filetype and text == None:
        post(f'https://api.telegram.org/bot{token}/send{filetype}?chat_id={chat_id}', files = {filetype.lower(): file})
    elif text and file and filetype:
        post(f'https://api.telegram.org/bot{token}/send{filetype}?chat_id={chat_id}&caption={qt(text)}&parse_mode=markdown', files = {filetype.lower(): file})
