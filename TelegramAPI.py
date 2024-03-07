import json
import time
import requests

from os import getcwd
from os.path import splitext, join, basename
from urllib.parse import urlparse

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


    def is_url(self, url: Union[str, bytes]) -> bool:
        """Check if the given string is a URL. Returns True if the input is an URL, and False otherwise."""
        if isinstance(url, bytes):
            return False
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)


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


    def poll_updates(self, polling_interval: int=1):
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


    def download_attachment(self, file_id: str, file_name: str, download_path: str) -> bool:
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


    def post_media_group(self, chat_id: Union[str, int], mtype: str, media: list, caption: str = None, disable_notification: bool = False, protect_content: bool = False,
                         reply_to_message_id: int = None, byte: bool = False):
        """
        CAUTION: This function is currently designed for internal use within other functions, specifically for sending multiple media items. It was not intended for direct user utilization.
        If you want to send mixed items as a group, use send_document endpoint instead.
        """
        files = {}
        media_group = []

        for i, item in enumerate(media, start=1):
            if self.is_url(item):
                media_group.append({'type': mtype, 'media': item})
            else:
                if byte:
                    files.update({f'file{i}': (f'file{i}', item, 'application/octet-stream')})
                else:
                    files.update({f'file{i}': (basename(item), open(item, 'rb'))})
                media_group.append({'type': mtype, 'media': f'attach://file{i}'})

        # When you are uploading as sendMediaGroup, it doesn't accept the caption in the traditional way.
        # Fucking stupid but what can you do.
        if caption:
            if media_group:
                media_group[0]['caption'] = caption
            elif files:
                files[0]['caption'] = caption

        return self.post(
            url = f'https://api.telegram.org/bot{self.token}/sendMediaGroup',
            chat_id = chat_id,
            media_group = media_group,
            media_files = files,
            disable_notification = disable_notification,
            protect_content = protect_content,
            reply_to_message_id = reply_to_message_id,
            byte = byte
        )


    def send_document(self, chat_id: Union[int, str], document: Union[str, bytes, list], caption: str = None, thumbnail: str = None, parse_mode: str = None, byte: bool = False,
                    disable_content_type_detection: bool = False, disable_notification: bool = False, protect_content: bool = False, reply_to_message_id: int = None):
        """
        Sends a document or a list of documents to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - document: Path to the document file or a list of paths to the document files to be sent. Pass a file_id as a string to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a string for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        - caption: Caption for the document, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this audio message will reply to.
        - thumbnail: Path to a thumbnail image for the document.
        - parse_mode: Mode for parsing entities in the document caption. 'Markdown' or 'HTML'.
        - disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent document message from forwarding and saving.
        - byte: Set this to True if you are passing a file from memory as a bytes-like variable.

        Example:
        bot.send_document(chat_id='@example_channel', document='/path/to/document.pdf', caption='Check out this document!', thumbnail='/path/to/thumbnail.jpg', disable_content_type_detection=False)
        """
        if isinstance(document, (str, bytes)):
            return self.post(
                url = f'https://api.telegram.org/bot{self.token}/sendDocument',
                chat_id = chat_id,
                document = document,
                caption = caption,
                thumbnail = thumbnail,
                parse_mode = parse_mode,
                disable_content_type_detection = disable_content_type_detection,
                disable_notification = disable_notification,
                protect_content = protect_content,
                reply_to_message_id = reply_to_message_id,
                byte = byte
            )
        elif isinstance(document, list):
            return self.post_media_group(chat_id = chat_id, mtype = 'document', media = document, caption = caption, reply_to_message_id = reply_to_message_id, disable_notification = disable_notification, protect_content = protect_content, byte=byte)


    def send_audio(self, chat_id: Union[int, str], audio: Union[str, bytes, list], caption: str = None, reply_to_message_id: int = None, parse_mode: str = None, byte: bool = False,
                duration: int = None, performer: str = None, title: str = None, thumbnail: Union[str, bytes] = None, disable_notification: bool = False, protect_content: bool = False):
        """
        Sends an audio file or a list of audio files to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - audio: Path to the audio file or a list of paths to the audio files to be sent. Pass a file_id as a string to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a string for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        - caption: Caption for the audio file, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this audio message will reply to.
        - parse_mode: Mode for parsing entities in the audio caption. 'Markdown' or 'HTML'.
        - duration: Duration of the audio file in seconds.
        - performer: Performer of the audio file.
        - title: Title of the audio file.
        - thumbnail: Path to a thumbnail image for the audio file.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent audio message from forwarding and saving.
        - byte: Set this to True if you are passing a file from memory as a bytes-like variable.

        Example:
        bot.send_audio(chat_id='@example_channel', audio='/path/to/audio.mp3', caption='Check out this audio!', reply_to_message_id=123456789, duration=180, performer='Artist', title='Song Title', disable_notification=False)
        """
        if isinstance(audio, (str, bytes)):
            return self.post(
                url = f'https://api.telegram.org/bot{self.token}/sendAudio',
                chat_id = chat_id,
                audio = audio,
                caption = caption,
                reply_to_message_id = reply_to_message_id,
                parse_mode = parse_mode,
                duration = duration,
                performer = performer,
                title = title,
                thumbnail = thumbnail,
                disable_notification = disable_notification,
                protect_content = protect_content,
                byte = byte
            )
        elif isinstance(audio, list):
            return self.post_media_group(chat_id = chat_id, mtype = 'audio', media = audio, caption = caption, reply_to_message_id = reply_to_message_id, disable_notification = disable_notification, protect_content = protect_content, byte=byte)


    def send_video(self, chat_id: Union[int, str], video: Union[str, bytes, list], caption: str = None, reply_to_message_id: int = None, parse_mode: str = None,
                disable_notification: bool = False, protect_content: bool = False, has_spoiler: bool = False, duration: int = None, width: int = None,
                height: int = None, thumbnail: str = None, supports_streaming: bool = False, byte: bool = False):
        """
        Sends a video or a list of videos to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - video: Path to the video file or a list of paths to the video files to be sent. Pass a file_id as a string to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a string for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        - caption: Caption for the video, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this video message will reply to.
        - parse_mode: Mode for parsing entities in the video caption. 'Markdown' or 'HTML'.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent video message from forwarding and saving.
        - has_spoiler: Indicates whether the video has spoiler content.
        - duration: Duration of the video in seconds.
        - width: Width of the video in pixels.
        - height: Height of the video in pixels.
        - thumbnail: Path to a thumbnail image for the video.
        - supports_streaming: Pass True if the uploaded video is suitable for streaming.
        - byte: Set this to True if you are passing a file from memory as a bytes-like variable.

        Example:
        bot.send_video(chat_id='@example_channel', video='/path/to/video.mp4', caption='Check out this video!', reply_to_message_id=123456789, has_spoilers=True)
        """
        if isinstance(video, (str, bytes)):
            return self.post(
                url = f'https://api.telegram.org/bot{self.token}/sendVideo',
                chat_id = chat_id,
                video = video,
                caption = caption,
                reply_to_message_id = reply_to_message_id,
                parse_mode = parse_mode,
                disable_notification = disable_notification,
                protect_content = protect_content,
                supports_streaming = supports_streaming,
                has_spoiler = has_spoiler,
                duration = duration,
                width = width,
                height = height,
                thumbnail = thumbnail,
                byte = byte
            )
        elif isinstance(video, list):
            return self.post_media_group(chat_id = chat_id, mtype = 'video', media = video, caption = caption, reply_to_message_id = reply_to_message_id, disable_notification = disable_notification, protect_content = protect_content, byte=byte)


    def send_photo(self, chat_id: Union[int, str], photo: Union[str, bytes, list], caption: str = None, reply_to_message_id: int = None, parse_mode: str = None, disable_notification: bool = False,
                   protect_content: bool = False, has_spoiler: bool = False, byte: bool = False):
        """
        Sends a photo to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - photos: Path to the image files to be sent. Pass a file_id as a string to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a string for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        - caption: Photo caption, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this photo message will reply to.
        - parse_mode: Mode for parsing entities in the photo caption. 'Markdown' or 'HTML'.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent photo message from forwarding and saving.
        - has_spoiler: Pass True if the photo needs to be covered with a spoiler animation
        - byte: Set this to True if you are passing a file from memory as a bytes-like variable.

        Example:
        bot.send_photo(chat_id='@example_channel', photo='/path/to/photo.jpg', caption='Check out this photo!', reply_to_message_id=123456789, has_spoiler=True)
        """
        if isinstance(photo, (str, bytes)):
            return self.post(
                url = f'https://api.telegram.org/bot{self.token}/sendPhoto',
                chat_id = chat_id,
                photo = photo,
                caption = caption,
                reply_to_message_id = reply_to_message_id,
                parse_mode = parse_mode,
                disable_notification = disable_notification,
                protect_content = protect_content,
                has_spoiler = has_spoiler,
                byte = byte
            )
        elif isinstance(photo, list):
            return self.post_media_group(chat_id = chat_id, mtype = 'photo', media = photo, caption = caption, reply_to_message_id = reply_to_message_id, disable_notification = disable_notification, protect_content = protect_content, byte=byte)


    def send_contact(self, chat_id: Union[str, int], phone_number: str, first_name: str, last_name: str = None, vcard: str = None, disable_notification: bool = False, protect_content: bool = False):
        """
        Sends a contact to the specified chat or channel.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - phone_number: Contact's phone number.
        - first_name: Contact's first name.
        - last_name: Contact's last name.
        - vcard: Additional data about the contact in the form of a vCard, 0-2048 bytes.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.

        Example:
        bot.send_contact(chat_id='ID or @name', phone_number='+1234567890', first_name='John', last_name='Doe', vcard='vCardData', disable_notification=True, protect_content=True)
        """
        return self.post(
            url = f'https://api.telegram.org/bot{self.token}/sendContact',
            chat_id = chat_id,
            contact_number = phone_number,
            contact_first_name = first_name,
            contact_last_name = last_name,
            contact_vcard = vcard,
            disable_notification = disable_notification,
            protect_content = protect_content
        )


    def send_location(self, chat_id:Union[int, str], latitude: float, longitude: float, horizontal_accuracy: float = None, live_period: int = None, heading: int = None,
                      proximity_alert_radius: int = None, reply_to_message_id: int = None, disable_notification: bool = False, protect_content: bool = False):
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
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - reply_to_message_id: Quotes and replies to the message ID.
        - protect_content: Protects the contents of the sent message from forwarding and saving.

        Example:
        bot.send_location(chat_id='ID or @channel', latitude=37.7749, longitude=-122.4194, horizontal_accuracy=50, live_period=300, heading=90, proximity_alert_radius=1000, disable_notification=True, reply_to_message_id=123456789)
        """
        return self.post(
            url = f'https://api.telegram.org/bot{self.token}/sendLocation',
            chat_id = chat_id,
            latitude = latitude,
            longitude = longitude,
            horizontal_accuracy = horizontal_accuracy,
            live_period = live_period,
            heading = heading,
            proximity_alert_radius = proximity_alert_radius,
            reply_to_message_id = reply_to_message_id,
            disable_notification = disable_notification,
            protect_content = protect_content
        )


    def send_voice(self, chat_id: Union[int, str], voice: Union[str, bytes], duration: int = None, caption: str = None, parse_mode: str = None, reply_to_message_id: str = None, disable_notification: bool = False,
                   protect_content: bool = False, byte: bool = False):
        """
        Sends a voice message to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - voice: Path to the audio file to be sent. Pass a file_id as a string to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a string for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        - duration: Duration of the voice message in seconds. If the file you uploaded is 10 seconds long, and you enter 5 as the duration, only the first 5 seconds will be sent.
        - caption: Voice message caption, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this voice message will reply to.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent voice message from forwarding and saving.
        - byte: Set this to True if you are passing a file from memory as a bytes-like variable.

        Example:
        bot.send_voice(chat_id='ID or @channel', voice='/path/to/voice.ogg', duration=10, caption='Check out this voice message!', reply_to_message_id=123456789, disable_notification=True)
        """
        return self.post(
            url = f'https://api.telegram.org/bot{self.token}/sendVoice',
            chat_id = chat_id,
            voice = open(voice, 'rb'),
            duration = duration,
            caption = caption,
            parse_mode = parse_mode,
            reply_to_message_id = reply_to_message_id,
            disable_notification = disable_notification,
            protect_content = protect_content,
            byte = byte
        )


    def send_message(self, chat_id:Union[str, int], text: str, reply_to_message_id: int = None, parse_mode: str = None, no_webpage: bool = False, disable_notification: bool = False, protect_content: bool = False):
        """
        Sends a text message to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - text: The text of the message to be sent.
        - reply_to_message_id: The message ID to which this message will reply to.
        - parse_mode: Mode for parsing entities in the message text. 'Markdown' or 'HTML'.
        - no_webpage: Set this flag to disable the generation of the webpage preview.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.

        Example:
        bot.send_message(chat_id='ID or @channel', text='*Hello, World!*', parse_mode='Markdown', no_webpage=True, disable_notification=True)
        """
        return self.post(
            url = f'https://api.telegram.org/bot{self.token}/sendMessage',
            chat_id = chat_id,
            text = text,
            reply_to_message_id = reply_to_message_id,
            parse_mode = parse_mode,
            no_webpage = no_webpage,
            disable_notification = disable_notification,
            protect_content = protect_content
        )


    def delete_message(self, chat_id: Union[int, str], message_id: Union[int, str]):
        """
        Deletes the given message from the chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - message_id: The ID of the message you wish to delete.

        Example:
        bot.delete_message(chat_id = 123456789, message_id = 1235)
        """
        return self.post(url = f'https://api.telegram.org/bot{self.token}/deleteMessage', chat_id = chat_id, message_id = message_id)


    def edit_message(self, chat_id: Union[int, str], message_id: Union[int, str], text: str, parse_mode: str = None, no_webpage: bool = False):
        """
        Updates the given message with the new text.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - message_id: The ID of the message you wish to edit.
        - text: The text of the message to be sent.

        Example:
        bot.edit_message(chat_id = 123456789, message_id = 1235, text = 'This is an updated text!')
        """
        return self.post(
            url = f'https://api.telegram.org/bot{self.token}/editMessageText',
            chat_id = chat_id,
            message_id = message_id,
            text = text,
            parse_mode = parse_mode,
            no_webpage = no_webpage
        )


    def post(self, url, chat_id, message_id=None, text=None, caption=None, reply_to_message_id=None, parse_mode=None, disable_notification=None, protect_content=None,
             no_webpage=None, contact_number=None, contact_first_name=None, contact_last_name=None, contact_vcard=None, voice=None, duration=None,
             latitude=None, longitude=None, horizontal_accuracy=None, live_period=None, heading=None, proximity_alert_radius=None, photo = None, has_spoiler = None,
             video = None, width = None, height = None, thumbnail = None, supports_streaming = None, disable_content_type_detection = None, document = None,
             audio = None, performer = None, title = None, media_group = None, media_files = None, byte = None):
        """
        CAUTION: This function serves as the centralized point for sending requests in support of other functions. 
        Please refrain from attempting to use this endpoint independently. Utilize the designated functions instead; this one is not meant for direct user utilization.
        """
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
        if message_id: # For deleting a message
            params.update({'message_id': message_id})
        
        # Some extra params for tweaking and finetuning
        if disable_notification: # Sends the message silently. Users will receive a notification with no sound.
            params.update({'disable_notification': True})
        if no_webpage: # Set this flag to disable generation of the webpage preview
            params.update({'disable_web_page_preview': True})
        if protect_content: # Protects the contents of the sent message from forwarding and saving
            params.update({'protect_content': True})
        if has_spoiler: # Covers the media with a spoiler animation
            params.update({'has_spoiler': True})
        if duration: # Sets the duration for videos and voices
            params.update({'duration': duration})
        if width: # For videos
            params.update({'width': width})
        if height: # Also for videos
            params.update({'height': height})
        if thumbnail: # For videos and documents
            if byte:
                files.update({'thumbnail': ('xxx', thumbnail, 'application/octet-stream')})
            else:
                files.update({'thumbnail': open(thumbnail, 'rb')})
            
        if supports_streaming: # For videos
            params.update({'supports_streaming': True})
        if disable_content_type_detection: # For Documents
            params.update({'disable_content_type_detection': True})
        if performer: # Audio Artist
            params.update({'performer': performer})
        if title: # Audio Name
            params.update({'title': title})
        
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

        # Dealing with medias etc
        if voice:
            files.update({'voice': voice})
        if voice and byte:
            files.update({'voice': ('xxx', voice, 'application/octet-stream')})
        
        if self.is_url(photo):
            params.update({'photo': photo})
        elif photo:
            if byte:
                files.update({'photo': ('xxx', document, 'application/octet-stream')})
            else:
                files.update({'photo': open(photo, 'rb')})
        
        if self.is_url(video):
            params.update({'video': video})
        elif video:
            if byte:
                files.update({'video': ('xxx', video, 'application/octet-stream')})
            else:
                files.update({'video': open(video, 'rb')})
        
        if self.is_url(document):
            params.update({'document': document})
        elif document:
            if byte:
                files.update({'document': ('xxx', document, 'application/octet-stream')})
            else:
                files.update({'document': open(document, 'rb')})

        if self.is_url(audio):
            params.update({'audio': audio})            
        elif audio:
            if byte:
                files.update({'audio': ('xxx', audio, 'application/octet-stream')})
            else:
                files.update({'audio': open(audio, 'rb')})

        if media_group:
            params.update({'media': json.dumps(media_group)})
        if media_files:
            files.update(media_files)

        response = requests.post(url, params=params, files=files)
        return self.parser.process(json.loads(response.text))