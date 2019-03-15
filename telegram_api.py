import subprocess

def telegram_text(message, chat_id, token):
    print('Sending: ' + message)
    subprocess.call('curl -s -o /dev/null -X POST https://api.telegram.org/bot' + token + '/sendMessage -d chat_id=' + chat_id + ' -d text="' + message + '"', shell=True)

def telegram_image(caption, filename, path, chat_id, token):
    print('Uploading: ' + filename)
    subprocess.call('curl -s -o /dev/null -X POST https://api.telegram.org/bot' + token + '/sendPhoto -F chat_id=' + chat_id + ' -F caption="' + caption + '" -F photo=@' + path + '\'' + filename + '\'', shell=True)

def telegram_video(caption, filename, path, chat_id, token):
    print('Uploading: ' + filename)
    subprocess.call('curl -s -o /dev/null -X POST https://api.telegram.org/bot' + token + '/sendVideo -F chat_id=' + chat_id + ' -F caption="' + caption + '" -F video=@' + path + '\'' + filename + '\'', shell=True)

def telegram_file(caption, filename, path, chat_id, token):
    print('Uploading: ' + filename)
    subprocess.call('curl -s -o /dev/null -X POST https://api.telegram.org/bot' + token + '/sendDocument -F chat_id=' + chat_id + ' -F caption="' + caption + '" -F document=@' + path + '\'' + filename + '\'', shell=True)