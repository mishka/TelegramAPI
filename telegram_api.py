from requests import post
from urllib.parse import quote as qt

class telegram(object):
    def __init__(self,token):
        self.token = token
    
    def telegram_text(self,text, chat_id):
        post('https://api.telegram.org/bot' + self.token + '/sendMessage?chat_id=' + chat_id + '&text=' + qt(text))

    def telegram_pic(self,file, chat_id, caption = None):
        if caption:
            post('https://api.telegram.org/bot' + self.token + '/sendPhoto?chat_id=' + chat_id + '&caption=' + qt(caption), files = {'photo': file})
        else:
            post('https://api.telegram.org/bot' + self.token + '/sendPhoto?chat_id=' + chat_id, files = {'photo': file})

    def telegram_video(self,file, chat_id, caption = None):
        if caption:
            post('https://api.telegram.org/bot' + self.token + '/sendVideo?chat_id=' + chat_id + '&caption=' + qt(caption), files = {'video': file})
        else:
            post('https://api.telegram.org/bot' + token + '/sendVideo?chat_id=' + chat_id, files = {'video': file})

    def telegram_doc(self,file, chat_id, caption = None):
        if caption:
            post('https://api.telegram.org/bot' + self.token + '/sendDocument?chat_id=' + chat_id + '&caption=' + qt(caption), files = {'document': file})
        else:
            post('https://api.telegram.org/bot' + self.token + '/sendDocument?chat_id=' + chat_id, files = {'document': file})
