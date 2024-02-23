import time
import requests

from os import getcwd
from os.path import splitext, join
from datetime import datetime, timezone
from typing import Union

from TelegramParser import Parser


class TelegramAPI:
    def __init__(self, token):
        self.token = token
        self.base_download_url = f'https://api.telegram.org/file/bot{token}'
        self.base_url = f'https://api.telegram.org/bot{token}'
        self.current_directory = join(getcwd(), '')
        self.last_update_id = None
        self.parser = Parser()
        self.my_id = 639236393


    def convert_timestamp(self, timestamp:Union[str, int]):
        """
        Converts a Unix timestamp to the user's local time in the format 'dd/mm/YYYY HH:MM:SS'.

        Parameters:
        - timestamp: Unix timestamp to be converted.

        Returns:
        - Formatted local time string.

        Example:

        for message in bot.poll_updates():
            print(f'Date: {bot.convert_timestamp(message.date)}')
        
        # Output: '23/02/2022 10:19:00'
        """
        if timestamp:
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
            return dt.astimezone().strftime('%d/%m/%Y %H:%M:%S')


    def get_updates(self):
        """Gets the latest updates from the /getUpdates endpoint. This function is made for the poll_updates() function."""
        url = f'{self.base_url}/getUpdates'
        params = {'offset': self.last_update_id + 1} if self.last_update_id else {}
        response = requests.get(url, params=params)
        updates = response.json().get('result', [])
        if updates:
            self.last_update_id = updates[-1]['update_id']
        return updates


    def poll_updates(self, polling_interval:int=1):
        """
        Continuously polls for the latest updates and yields the processed results.

        Parameters:
        - polling_interval: Time interval in seconds between polling for updates.

        Yields:
        - Processed updates using the parser.

        Example:
        for message in bot.poll_updates(polling_interval=2):
            print(f'Received Message: {message.text}')
        """
        while True:
            updates = self.get_updates()
            for update in updates:
                yield self.parser.process(update)
            time.sleep(polling_interval)


    def download_attachment(self, file_id:str, file_name:str, download_path:str) -> bool:
        """
        Downloads an attachment identified by its file ID from Telegram and saves it to the specified path.

        Parameters:
        - file_id: Identifier for this file, which can be used to download or reuse the file.
        - file_name: However you wish to name the file.
        - download_path: Full path of where you want this file to be saved.

        Returns:
        - True if the file is downloaded successfully, False otherwise.

        Example:
        bot.download_attachment(file_id='123456789', file_name='example_file', download_path='/path/to/download/')
        """
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

    
    def send_message(self, chat_id:Union[str, int], text:str, reply_to_message_id:int=None, parse_mode:str=None, no_webpage:bool=False, silent:bool=False, protect_content:bool=False) -> str:
        """
        Sends a text message to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - text: The text of the message to be sent.
        - reply_to_message_id: The message ID to which this message will reply to.
        - parse_mode: Mode for parsing entities in the message text. 'Markdown' or 'HTML'.
        - no_webpage: Set this flag to disable the generation of the webpage preview.
        - silent: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.

        Returns:
        - JSON response from the Telegram API.

        Example:
        bot.send_message(chat_id='ID or @channel', text='*Hello, World!*', parse_mode='Markdown', no_webpage=True, silent=True)
        """
        return self.send(
            url=f'https://api.telegram.org/bot{self.token}/sendMessage',
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            no_webpage=no_webpage,
            silent=silent,
            protect_content=protect_content
        )


    def send_contact(self, chat_id:Union[str, int], phone_number:str, first_name:str, last_name:str=None, vcard:str=None, silent:bool=False, protect_content:bool=False) -> str:
        """
        Sends a contact to the specified chat or channel.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - phone_number: Contact's phone number.
        - first_name: Contact's first name.
        - last_name: Contact's last name.
        - vcard: Additional data about the contact in the form of a vCard, 0-2048 bytes.
        - silent: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.

        Example:
        bot.send_contact(chat_id='ID or @name', phone_number='+1234567890', first_name='John', last_name='Doe', vcard='vCardData', silent=True, protect_content=True)
        """
        return self.send(f'https://api.telegram.org/bot{self.token}/sendContact',
                         chat_id = chat_id,
                         contact_number = phone_number,
                         contact_first_name = first_name,
                         contact_last_name = last_name,
                         contact_vcard = vcard,
                         silent = silent,
                         protect_content = protect_content
                         )


    def send_location(self, chat_id:Union[int, str], latitude:float, longitude:float, horizontal_accuracy:float=None, live_period:int=None, heading:int=None,
                      proximity_alert_radius:int=None, reply_to_message_id:int=None, silent:bool=False, protect_content:bool=False) -> str:
        """
        Sends a location to the specified chat or channel.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - latitude: Latitude of the location.
        - longitude: Longitude of the location.
        - horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500.
        - live_period: Period in seconds for which the location will be updated; should be between 60 and 86400.
        - heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        - proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        - silent: Sends the message silently. Users will receive a notification with no sound.
        - reply_to_message_id: Quotes and replies to the message ID.
        - protect_content: Protects the contents of the sent voice message from forwarding and saving.

        Example:
        bot.send_location(chat_id='ID or @channel', latitude=37.7749, longitude=-122.4194, horizontal_accuracy=50, live_period=300, heading=90, proximity_alert_radius=1000, silent=True, reply_to_message_id=123456789)
        """
        return self.send(
            url=f'https://api.telegram.org/bot{self.token}/sendLocation',
            chat_id = chat_id,
            latitude = latitude,
            longitude = longitude,
            horizontal_accuracy = horizontal_accuracy,
            live_period = live_period,
            heading = heading,
            proximity_alert_radius = proximity_alert_radius,
            reply_to_message_id = reply_to_message_id,
            silent = silent,
            protect_content = protect_content
        )


    def send_voice(self, chat_id:str, voice:str, duration:int=None, caption:str=None, parse_mode:str=None, reply_to_message_id:str=None, silent:bool=False, protect_content:bool=False) -> str:
        """
        Sends a voice message to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - voice: Path to the audio file to be sent. Pass a file_id as a string to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a string for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        - duration: Duration of the voice message in seconds. If the file you uploaded is 10 seconds long, and you enter 5 as the duration, only the first 5 seconds will be sent.
        - caption: Voice message caption, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this voice message will reply to.
        - silent: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent voice message from forwarding and saving.

        Example:
        bot.send_voice(chat_id='ID or @channel', voice_path='/path/to/voice.ogg', duration=10, caption='Check out this voice message!', reply_to_message_id=123456789, silent=False)
        """
        return self.send(
            f'https://api.telegram.org/bot{self.token}/sendVoice',
            chat_id=chat_id, voice=open(voice, 'rb'),
            voice_duration=duration,
            caption=caption,
            parse_mode=parse_mode,
            reply_to_message_id=reply_to_message_id,
            silent=silent,
            protect_content=protect_content
            )


    # in progress
    def send(self, url, chat_id, text=None, caption=None, reply_to_message_id=None, parse_mode=None, silent=None, protect_content=None,
             no_webpage=None, contact_number=None, contact_first_name=None, contact_last_name=None, contact_vcard=None, voice=None, voice_duration=None,
             latitude=None, longitude=None, horizontal_accuracy=None, live_period=None, heading=None, proximity_alert_radius=None):
        
        # a necessity for every request. we build it upon here
        params = {'chat_id': chat_id}
        files = {}

        if text: # The message
            params.update({'text': text})
        if caption: # The caption for media
            params.update({'caption': caption})
        if parse_mode: # Either Markdown or HTML
            params.update({'parse_mode': parse_mode})
        if reply_to_message_id: # The message ID to which message you will quote/reply to
            params.update({'reply_to_message_id': reply_to_message_id})
        
        # Some extra params for tweaking and finetuning
        if silent: # Sends the message silently. Users will receive a notification with no sound.
            params.update({'disable_notification': True})
        if no_webpage: # Set this flag to disable generation of the webpage preview
            params.update({'disable_web_page_preview': True})
        if protect_content: # Protects the contents of the sent message from forwarding and saving
            params.update({'protect_content': True})
        
        # Contact card information
        if contact_number and contact_first_name:
            params.update({'phone_number': contact_number})
            params.update({'first_name': contact_first_name})
            if contact_last_name:
                params.update({'last_name': contact_last_name})
            if contact_vcard:
                params.update({'vcard': contact_vcard})

        # Geo information for sending locations
        if latitude and longitude:
            params.update({'latitude': latitude, 'longitude': longitude})
            if horizontal_accuracy:
                params.update({'horizontal_accuracy': horizontal_accuracy})
            if live_period:
                params.update({'live_period': live_period})
            if heading:
                params.update({'heading': heading})
            if proximity_alert_radius:
                params.update({'proximity_alert_radius': proximity_alert_radius})

        # Voice message information
        if voice:
            files.update({'voice': voice})
            if voice_duration:
                params.update({'duration': voice_duration})

        response = requests.post(url, params=params, files=files)
        print(response)
        return response.json
