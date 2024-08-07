# Welcome!
You can run a Telegram bot, get all the message data in a parsed way, download any attachments, and send messages and attachments using this library.  

If you need to automate a bot and get something done quickly, this library is what you are searching for.  

The file sending is unexceptionally simplified. You only need to enter the file path, or a valid URL that telegram can fetch it from.
  
It is currently in progress; however, it can already achieve the following:
- Polling messages
- Message information is parsed in a pythonic way
- Endpoints which are covered for sending messages:
  - Text
  - Contact
  - Location
  - Document
  - Photo
  - Video
  - Audio
  - Voice
  - Contact
  - Sticker
  - Media Groups
- Delete messages
- Edit messages
  
# Basics
## Dependencies
- requests
## Creating a bot
You can create a bot through [@BotFather](https://telegram.me/BotFather)

## Finding the chat ID
You can learn about your chat ID by messaging `/my_id` to the [@get_id_bot](https://telegram.me/get_id_bot) on telegram.
Or, you can send your bot a message, and access this URL to see the updates coming through to your bot to see your user ID: https://api.telegram.org/YourTokenHere/getUpdates

## Projects that rely on this API!
- [A YouTube mp3 downloader bot that runs on memory!](https://github.com/mishka/TelegramMusicBot)

# Some Code Examples

**As you write function names in your IDE, you will see the available parameters for all of them.  
They are all documented alongside with their functionality and accepted data types.  
These are just some basic examples to give you an idea about the library.**

## Importing the library and setting up your telegram object
```python
from TelegramAPI import TelegramAPI

telegram = TelegramAPI('Enter your bot token here. You can obtain it through @BotFather on telegram.')
```

## Sending a text message
```python
telegram.send_message(
    chat_id = 'Your ID here',
    text = 'You can visit my GitHub account here: github.com/mishka',
    no_webpage = True,
    disable_notification = True
    )
```

## Sending a contact
```python
telegram.send_contact(
    chat_id = 'Your ID here',
    first_name = 'First name of the contact',
    last_name = 'Last name of the contact',
    phone_number = '+1234567890'
    )
```

## Sending a location
```python
telegram.send_location(
    chat_id = 'Your ID here',
    latitude = 29.9792,
    longitude = 31.1342,
    horizontal_accuracy = 50,
    heading = 90
    )
```

## Sending a voice
```python
telegram.send_voice(
    chat_id = 'Your ID here',
    voice = 'path to voice file or valid url',
    duration = 7,
    caption = 'Check out this voice message!'
    )
```

## Sending an audio
```python
# Sending a single audio
telegram.send_audio(
    chat_id = 'Your ID here',
    audio = 'path to audio file or valid url',
    performer = 'Artist Name',
    title = 'Song Name',
    thumbnail = '/path/to/album/cover/picture'
    )
```

## Sending multiple audios
```python
# Sending more than one audio
# It currently does not support metadata when it is sent in groups
telegram.send_audio(
    chat_id = 'Your ID here',
    audio = ['song path 1', 'song path 2', 'song path 3']
    )
```

## Sending a photo
```python
telegram.send_photo(
    chat_id = 'Your ID here',
    caption = 'Check this cool picture!',
    photo = 'path to file or a valid url',
    has_spoilers = True
    )
```

## Sending multiple photos
```python
telegram.send_photo(
    chat_id = 'Your ID here',
    caption = 'Check these cool pictures!',
    photo = ['path to photo', 'photo url'],
    protect_content = True
    )
```

## Sending a video
```python
telegram.send_video(
    chat_id = 'Your ID here',
    caption = 'Check this cool video!',
    video = 'path to file or a valid url',
    supports_streaming = True
    )
```

## Sending multiple videos
```python
telegram.send_video(
    chat_id = 'Your ID here',
    caption = 'Check these cool videos!',
    video = ['path to video', 'video url'],
    protect_content = True
    )
```

## Sending a document
```python
telegram.send_document(
    chat_id = 'Your ID here',
    caption = 'Check this cool document!',
    video = 'path to file or valid url',
    protect_content = True
    )
```

## Sending multiple documents
```python
# If you want to send many files, use this method.
telegram.send_document(
    chat_id = 'Your ID here',
    caption = 'Check these cool files!',
    video = ['audio file path', 'photo url', 'video file path', 'a custom file url'],
    protect_content = True
    )
```

## Deleting a message
```python
from time import sleep

message = telegram.send_message(chat_id = 'ID', text = 'Hi!')
sleep(5)
telegram.delete_message(chat_id = 'ID', message_id = message.id)
```

## Editing a message
```python
telegram.send_message(
    chat_id = 098765,
    message_id = 123456,
    text = 'Hi!',
    parse_mode = 'Markdown'
    )
```

## Replying to messages or commands from users
```python
# I am thinking about adding decorators to this library, and further simplying this process.
# For now, you can poll the updates, and listen to them in a loop. and add conditions inside that loop.

for message in telegram.poll_updates(polling_interval=1):
    if message.text.startswith('/ping'):
        telegram.send_message(
            chat_id = message.from_id,
            text = '*pong!*'
            reply_to_message_id = message.message_id,
            parse_mode = 'Markdown'
        )
```

## Polling, accessing the parsed data, and downloading attachments!
```python
# You can see all the available information that comes with user messages below.

# You can set the polling interval while setting it up. Default value is 1.
for message in telegram.poll_updates(polling_interval=5): 
    print(f'Update ID: {message.update_id}')
    print(f'Message ID: {message.message_id}')

    print(f'From ID: {message.from_id}')
    print(f'From is Bot: {message.from_is_bot}')
    print(f'From First Name: {message.from_first_name}')
    print(f'From Username: {message.from_username}')

    print(f'Chat ID: {message.chat_id}')
    print(f'Chat First Name: {message.chat_first_name}')
    print(f'Chat Username: {message.chat_username}')
    print(f'Chat Type: {message.chat_type}')

    print(f'Date: {telegram.convert_timestamp(message.date)}')
    print(f'Edited Date: {telegram.convert_timestamp(message.edit_date)}')
    print(f'Text: {message.text}')
    print(f'Caption: {message.caption}')
    print(f'Media Group ID: {message.media_group_id}')

    if message.sticker:
        telegram.download_attachment(message.sticker.file_id, message.sticker.file_unique_id, telegram.current_directory)

        print(f'Sticker Width: {message.sticker.width}')
        print(f'Sticker Height: {message.sticker.height}')
        print(f'Sticker Emoji: {message.sticker.emoji}')
        print(f'Sticker Set Name: {message.sticker.set_name}')
        print(f'Sticker Is Animated: {message.sticker.is_animated}')
        print(f'Sticker Is Video: {message.sticker.is_video}')
        print(f'Sticker Type: {message.sticker.sticker_type}')
        print(f'Sticker File ID: {message.sticker.file_id}')
        print(f'Sticker Unique ID: {message.sticker.file_unique_id}')
        print(f'Sticker Size: {message.sticker.file_size}')

        print(f'Sticker Thumbnail File_ID: {message.sticker.thumbnail_file_id}')
        print(f'Sticker Thumbnail File Unique ID: {message.sticker.thumbnail_file_unique_id}')
        print(f'Sticker Thumbnail File Size: {message.sticker.thumbnail_file_size}')
        print(f'Sticker Thumbnail Width: {message.sticker.thumbnail_width}')
        print(f'Sticker Thumbnail Height: {message.sticker.thumbnail_height}')

    if message.animation:
        telegram.download_attachment(message.animation.file_id, message.animation.file_unique_id, telegram.current_directory)

        print(f'Animation File Name: {message.animation.file_name}')
        print(f'Animation Mime Type: {message.animation.mime_type}')
        print(f'Animation Duration: {message.animation.duration}')
        print(f'Animation Width: {message.animation.width}')
        print(f'Animation Height: {message.animation.height}')
        print(f'Animation File ID: {message.animation.file_id}')
        print(f'Animation Unique ID: {message.animation.file_unique_id}')
        print(f'Animation Size: {message.animation.file_size}')

        print(f'Animation Thumbnail File_ID: {message.animation.thumbnail_file_id}')
        print(f'Animation Thumbnail File Unique ID: {message.animation.thumbnail_file_unique_id}')
        print(f'Animation Thumbnail File Size: {message.animation.thumbnail_file_size}')
        print(f'Animation Thumbnail Width: {message.animation.thumbnail_width}')
        print(f'Animation Thumbnail Height: {message.animation.thumbnail_height}')

    if message.video:
        telegram.download_attachment(message.video.file_id, message.video.file_name, telegram.current_directory)

        print(f'Video Width: {message.video.width}')
        print(f'Video Height: {message.video.height}')
        print(f'Video Filename: {message.video.file_name}')
        print(f'Video Mime Type: {message.video.mime_type}')
        print(f'Video File ID: {message.video.file_id}')
        print(f'Video Unique ID: {message.video.unique_id}')
        print(f'Video Video Size: {message.video.video_size}')

        print(f'Video Thumbnail File_ID: {message.video.thumbnail_file_id}')
        print(f'Video Thumbnail File Unique ID: {message.video.thumbnail_file_unique_id}')
        print(f'Video Thumbnail File Size: {message.video.thumbnail_file_size}')
        print(f'Video Thumbnail Width: {message.video.thumbnail_width}')
        print(f'Video Thumbnail Height: {message.video.thumbnail_height}')

    if message.document:
        telegram.download_attachment(message.document.file_id, message.document.file_name, telegram.current_directory)

        print(f'Document Filename: {message.document.file_name}')
        print(f'Document Mime Type: {message.document.mime_type}')
        print(f'Document File ID: {message.document.file_id}')
        print(f'Document File Unique ID: {message.document.file_unique_id}')
        print(f'Document File Size: {message.document.file_size}')

        if message.document.thumbnail_file_id:
            print(f'Document Thumbnail File ID: {message.document.thumbnail_file_id}')
            print(f'Document Thumbnail File Unique ID: {message.document.thumbnail_file_unique_id}')
            print(f'Document Thumbnail File Size: {message.document.thumbnail_file_size}')
            print(f'Document Thumbnail Width: {message.document.thumbnail_width}')
            print(f'Document Thumbnail Height: {message.document.thumbnail_height}')

    if message.video_note:
        telegram.download_attachment(message.video_note.file_id, message.video_note.file_unique_id, telegram.current_directory)

        print(f'Video Note Duration: {message.video_note.duration}')
        print(f'Video Note Length: {message.video_note.length}')
        print(f'Video Note File ID: {message.video_note.file_id}')
        print(f'Video Note File Unique ID: {message.video_note.file_unique_id}')
        print(f'Video Note File Size: {message.video_note.file_size}')

        print(f'Video Note Thumbnail File ID: {message.video_note.thumbnail_file_id}')
        print(f'Video Note Thumbnail File Unique ID: {message.video_note.thumbnail_file_unique_id}')
        print(f'Video Note Thumbnail File Size: {message.video_note.thumbnail_file_size}')
        print(f'Video Note Thumbnail Width: {message.video_note.thumbnail_width}')
        print(f'Video Note Thumbnail Height: {message.video_note.thumbnail_height}')

    if message.audio:
        telegram.download_attachment(message.audio.file_id, message.audio.file_name, telegram.current_directory)

        print(f'Audio Duration: {message.audio.duration}')
        print(f'Audio File Name: {message.audio.file_name}')
        print(f'Audio Mime Type: {message.audio.mime_type}')
        print(f'Audio File ID: {message.audio.file_id}')
        print(f'Audio File Unique ID: {message.audio.file_unique_id}')
        print(f'Audio File Size: {message.audio.file_size}')

    if message.photo:
        telegram.download_attachment(message.photo.file_id, message.photo.file_unique_id, telegram.current_directory)

        print(f'Photo File ID: {message.photo.file_id}')
        print(f'Photo File Unique ID: {message.photo.file_unique_id}')
        print(f'Photo File Size: {message.photo.file_size}')
        print(f'Photo Width: {message.photo.width}')
        print(f'Photo Height: {message.photo.height}')

    if message.voice:
        telegram.download_attachment(message.voice.file_id, message.voice.file_unique_id, telegram.current_directory)

        print(f'Voice Duration: {message.voice.duration}')
        print(f'Voice Mime Type: {message.voice.mime_type}')
        print(f'Voice File ID: {message.voice.file_id}')
        print(f'Voice File Unique ID: {message.voice.file_unique_id}')
        print(f'Voice File Size: {message.voice.file_size}')

    if message.contact:
        print(f'Contact Phone Number: {message.contact.phone_number}')
        print(f'Contact First Name: {message.contact.first_name}')
        print(f'Contact User ID: {message.contact.user_id}')

    if message.location:
        print(f'Location Latitude: {message.location.latitude}')
        print(f'Location Longitude: {message.location.longitude}')
        print(f'Location Live Period: {message.location.live_period}')
        print(f'Location Heading: {message.location.heading}')
        print(f'Location Horizontal Accuracy: {message.location.horizontal_accuracy}')
```
