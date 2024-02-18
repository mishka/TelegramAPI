# Welcome!
You can run a Telegram bot, get all the message data in a parsed way, download any attachments, and send messages and attachments using this library.

I felt the need to code something like this because I grew tired of all the popular libraries' version updates and constant rewrites.

I don't have time to relearn the libraries and read docs whenever I build bots.

If you need to automate a bot and get something done quickly, this library is what you are searching for.

It is currently in progress. I've written the parsing and downloading the attachments so far. I will be working on sending data back whenever I have free time to do so.

## Dependencies
- requests

## Creating a telegram bot
You can create a bot through [@BotFather](https://telegram.me/BotFather)

## Finding the chat ID
You can learn about your chat ID by messaging `/my_id` to the [@get_id_bot](https://telegram.me/get_id_bot) on telegram.

## Example Usage  

**All the available methods are shown below for receiving the parsed data. I will be writing a proper documentation once I am done with coding the whole thing.**

```python
from TelegramAPI import TelegramAPI

telegram = TelegramAPI('Your Token Here')

for message in telegram.poll_updates():
    print('-----------------------------------------')
    print(f'Update ID: {message.update_id}')
    print(f'Message ID: {message.message_id}')
    print()
    print(f'From ID: {message.from_id}')
    print(f'From is Bot: {message.from_is_bot}')
    print(f'From First Name: {message.from_first_name}')
    print(f'From Username: {message.from_username}')
    print()
    print(f'Chat ID: {message.chat_id}')
    print(f'Chat First Name: {message.chat_first_name}')
    print(f'Chat Username: {message.chat_username}')
    print(f'Chat Type: {message.chat_type}')
    print()
    print(f'Date: {telegram.convert_timestamp(message.date)}')
    print(f'Edited Date: {telegram.convert_timestamp(message.edit_date)}')
    print(f'Text: {message.text}')
    print(f'Caption: {message.caption}')
    print(f'Media Group ID: {message.media_group_id}')
    print()
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
        print()
        print(f'Sticker Thumbnail File_ID: {message.sticker.thumbnail_file_id}')
        print(f'Sticker Thumbnail File Unique ID: {message.sticker.thumbnail_file_unique_id}')
        print(f'Sticker Thumbnail File Size: {message.sticker.thumbnail_file_size}')
        print(f'Sticker Thumbnail Width: {message.sticker.thumbnail_width}')
        print(f'Sticker Thumbnail Height: {message.sticker.thumbnail_height}')
        print()
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
        print()
        print(f'Animation Thumbnail File_ID: {message.animation.thumbnail_file_id}')
        print(f'Animation Thumbnail File Unique ID: {message.animation.thumbnail_file_unique_id}')
        print(f'Animation Thumbnail File Size: {message.animation.thumbnail_file_size}')
        print(f'Animation Thumbnail Width: {message.animation.thumbnail_width}')
        print(f'Animation Thumbnail Height: {message.animation.thumbnail_height}')
        print()
    if message.video:
        telegram.download_attachment(message.video.file_id, message.video.file_name, telegram.current_directory)
        print(f'Video Width: {message.video.width}')
        print(f'Video Height: {message.video.height}')
        print(f'Video Filename: {message.video.file_name}')
        print(f'Video Mime Type: {message.video.mime_type}')
        print(f'Video File ID: {message.video.file_id}')
        print(f'Video Unique ID: {message.video.unique_id}')
        print(f'Video Video Size: {message.video.video_size}')
        print()
        print(f'Video Thumbnail File_ID: {message.video.thumbnail_file_id}')
        print(f'Video Thumbnail File Unique ID: {message.video.thumbnail_file_unique_id}')
        print(f'Video Thumbnail File Size: {message.video.thumbnail_file_size}')
        print(f'Video Thumbnail Width: {message.video.thumbnail_width}')
        print(f'Video Thumbnail Height: {message.video.thumbnail_height}')
        print()
    if message.document:
        telegram.download_attachment(message.document.file_id, message.document.file_name, telegram.current_directory)
        print(f'Document Filename: {message.document.file_name}')
        print(f'Document Mime Type: {message.document.mime_type}')
        print(f'Document File ID: {message.document.file_id}')
        print(f'Document File Unique ID: {message.document.file_unique_id}')
        print(f'Document File Size: {message.document.file_size}')
        print()
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
        print()
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
        print()
    if message.photo:
        telegram.download_attachment(message.photo.file_id, message.photo.file_unique_id, telegram.current_directory)
        print(f'Photo File ID: {message.photo.file_id}')
        print(f'Photo File Unique ID: {message.photo.file_unique_id}')
        print(f'Photo File Size: {message.photo.file_size}')
        print(f'Photo Width: {message.photo.width}')
        print(f'Photo Height: {message.photo.height}')
        print()
    if message.voice:
        telegram.download_attachment(message.voice.file_id, message.voice.file_unique_id, telegram.current_directory)
        print(f'Voice Duration: {message.voice.duration}')
        print(f'Voice Mime Type: {message.voice.mime_type}')
        print(f'Voice File ID: {message.voice.file_id}')
        print(f'Voice File Unique ID: {message.voice.file_unique_id}')
        print(f'Voice File Size: {message.voice.file_size}')
        print()
    if message.contact:
        print(f'Contact Phone Number: {message.contact.phone_number}')
        print(f'Contact First Name: {message.contact.first_name}')
        print(f'Contact User ID: {message.contact.user_id}')
        print()
    if message.location:
        print(f'Location Latitude: {message.location.latitude}')
        print(f'Location Longitude: {message.location.longitude}')
        print(f'Location Live Period: {message.location.live_period}')
        print(f'Location Heading: {message.location.heading}')
        print(f'Location Horizontal Accuracy: {message.location.horizontal_accuracy}')
```
