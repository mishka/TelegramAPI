from requests import post
from urllib.parse import quote as qt

def telegram_text(txt, token, chat_id):
    post('https://api.telegram.org/bot' + token + '/sendMessage?chat_id=' + chat_id + '&text=' + qt(txt))

def telegram_pic(file, token, chat_id, caption = None):
    if caption:
        post('https://api.telegram.org/bot' + token + '/sendPhoto?chat_id=' + chat_id + '&caption=' + qt(caption), files = {'photo': file})
    else:
        post('https://api.telegram.org/bot' + token + '/sendPhoto?chat_id=' + chat_id, files = {'photo': file})

def telegram_video(file, token, chat_id, caption = None):
    if caption:
        post('https://api.telegram.org/bot' + token + '/sendVideo?chat_id=' + chat_id + '&caption=' + qt(caption), files = {'video': file})
    else:
        post('https://api.telegram.org/bot' + token + '/sendVideo?chat_id=' + chat_id, files = {'video': file})

def telegram_doc(file, token, chat_id, caption = None):
    if caption:
        post('https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + chat_id + '&caption=' + qt(caption), files = {'document': file})
    else:
        post('https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + chat_id, files = {'document': file})
