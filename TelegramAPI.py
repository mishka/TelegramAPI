import time
import requests

from os import getcwd
from os.path import splitext, join
from datetime import datetime, timezone

from TelegramParser import Parser


class TelegramAPI:
    def __init__(self, token):
        self.base_download_url = f'https://api.telegram.org/file/bot{token}'
        self.base_url = f'https://api.telegram.org/bot{token}'
        self.current_directory = join(getcwd(), '')
        self.last_update_id = None
        self.parser = Parser()


    def convert_timestamp(self, timestamp):
        if timestamp:
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
            return dt.astimezone().strftime('%d/%m/%Y %H:%M:%S')


    def get_updates(self):
        url = f'{self.base_url}/getUpdates'
        params = {'offset': self.last_update_id + 1} if self.last_update_id else {}
        response = requests.get(url, params=params)
        updates = response.json().get('result', [])
        if updates:
            self.last_update_id = updates[-1]['update_id']
        return updates


    def poll_updates(self, polling_interval=1):
        while True:
            updates = self.get_updates()
            for update in updates:
                yield self.parser.process(update)
            time.sleep(polling_interval)


    def download_attachment(self, file_id, file_name, download_path):
        response = requests.get(self.base_url + '/GetFile', params={'file_id': file_id})
        file_info = response.json()

        if not file_info['ok']:
            print(f'Error getting file information: {file_info["description"]}')
            return False

        file_path = (file_info.get('result')).get('file_path')
        download_url = self.base_download_url + f'/{file_path}'
        response = requests.get(download_url)

        if response.status_code == 200:
            try:
                _, file_extension = splitext(file_path)
                # If the document name is: name + ext. Then the downloaded file becomes name + ext + ext. That's why.
                file_name, _ = splitext(file_name) 
                download_path_with_extension = f"{download_path}{file_name}{file_extension}"

                with open(download_path_with_extension, 'wb') as file:
                    file.write(response.content)
                    print(f'File downloaded successfully to {download_path_with_extension}')
                    return True
            except Exception as e:
                print(f'There was an error while trying to write the file: {str(e)}')
                return False
        else:
            print(f"Error downloading file: {response.status_code} - {response.text}")
            return False
