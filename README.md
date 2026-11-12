# Welcome!
You can run a Telegram bot, get all the message data in a parsed way, download any attachments, and send messages and attachments using this library.  

If you need to automate a bot and get something done quickly, this library is what you are searching for.  

The file sending is unexceptionally simplified. You only need to enter the file path, a valid URL that telegram can fetch it from, bytes already in memory, or an open file object.  
   
It is currently in progress; however, it can already achieve the following:
- Polling messages, with server-side long polling
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
  - Sticker
  - Animation
  - Video note
  - Media Groups
- Inline keyboards, callback answers, and chat actions
- Forward, copy, edit, delete, pin, and unpin messages
- Download attachments to disk or to memory, with your own file names
- Webhooks and bot/chat/file information
- Clear exceptions instead of silent failures
  
# Basics
## Dependencies
- Python 3.10 or newer
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

All message and media sending methods return parsed `Message` objects. Media group sends return a list of `Message` objects.  
`copy_message` returns a dictionary such as `{'message_id': 123}`, and methods that only confirm success, including `send_chat_action`, return Telegram's raw result, usually `True`.

## Importing the library and setting up your telegram object
```python
from TelegramAPI import TelegramAPI

telegram = TelegramAPI('Enter your bot token here. You can obtain it through @BotFather on telegram.')
```

The constructor also accepts a custom `requests.Session`, timeouts, and the number of automatic flood-wait retries:

```python
import requests

session = requests.Session()
telegram = TelegramAPI(
    'Enter your bot token here.',
    session = session,
    timeout = 30,
    upload_timeout = 120,
    max_flood_retries = 3
)
```

`timeout` applies to normal API calls. `upload_timeout` applies to requests that contain files.  
You can also use the client as a context manager, or call `close()` yourself:

```python
with TelegramAPI('Enter your bot token here.') as telegram:
    telegram.send_message(chat_id = 'Your ID here', text = 'Hi!')

telegram = TelegramAPI('Enter your bot token here.')
telegram.close()
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

`parse_mode` accepts `'Markdown'`, `'MarkdownV2'`, or `'HTML'`. You can pass `entities` or `link_preview_options` directly:

```python
telegram.send_message(
    chat_id = 'Your ID here',
    text = 'Hello, World!',
    parse_mode = 'HTML',
    link_preview_options = {'is_disabled': True}
    )
```

## Sending a message with an inline keyboard
```python
telegram.send_message(
    chat_id = 'Your ID here',
    text = 'Choose an option:',
    reply_markup = {
        'inline_keyboard': [
            [
                {'text': 'Open GitHub', 'url': 'https://github.com/mishka'},
                {'text': 'Say hello', 'callback_data': 'hello'}
            ]
        ]
    }
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
telegram.send_audio(
    chat_id = 'Your ID here',
    audio = ['song path 1', 'song path 2', 'song path 3']
    )
```

A list of more than one file is sent as a media group. This applies to `send_audio`, `send_video`, `send_photo`, and `send_document`.  
Lists larger than 10 are split into multiple groups automatically. You can give each uploaded file its own name with `file_names`:

```python
telegram.send_audio(
    chat_id = 'Your ID here',
    audio = [b'first audio bytes', b'second audio bytes'],
    file_names = ['First song.mp3', 'Second song.mp3'],
    caption = 'Two songs'
    )
```

You can also use `(source, file_name)` tuples or dictionaries to give each media group item its own metadata:

```python
telegram.send_audio(
    chat_id = 'Your ID here',
    audio = [
        ('song 1.mp3', 'First song.mp3'),
        {
            'media': 'song 2.mp3',
            'title': 'Second song',
            'performer': 'Artist Name',
            'duration': 180
        },
        'https://example.com/song3.mp3'
    ],
    caption = 'Three songs',
    parse_mode = 'HTML'
    )
```

If the list contains exactly one item, it is sent as a normal single message, so single-file metadata still works.  
For groups, put per-file metadata inside the tuple or dictionary; top-level single-file metadata such as `duration` or `thumbnail` is only used for single sends.

## Sending a photo
```python
telegram.send_photo(
    chat_id = 'Your ID here',
    caption = 'Check this cool picture!',
    photo = 'path to file or a valid url',
    has_spoiler = True
    )
```

## Sending multiple photos
```python
telegram.send_photo(
    chat_id = 'Your ID here',
    caption = 'Check these cool pictures!',
    photo = [
        ('first.jpg', 'First picture.jpg'),
        {'media': 'second.jpg', 'caption': 'Second picture'},
        'https://example.com/third.jpg'
    ],
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
    video = [
        'path to video',
        {'media': 'https://example.com/video.mp4', 'caption': 'From the internet'}
    ],
    protect_content = True
    )
```

## Sending a document
```python
telegram.send_document(
    chat_id = 'Your ID here',
    caption = 'Check this cool document!',
    document = 'path to file or valid url',
    protect_content = True
    )
```

## Sending multiple documents
```python
telegram.send_document(
    chat_id = 'Your ID here',
    caption = 'Check these cool files!',
    document = [
        'audio file path',
        'photo url',
        'video file path',
        {
            'media': 'custom file url',
            'caption': 'A custom file',
            'disable_content_type_detection': True
        }
    ],
    protect_content = True
    )
```

## Sending a sticker
```python
telegram.send_sticker(
    chat_id = 'Your ID here',
    sticker = 'path to sticker file, valid url, or file_id'
    )
```

`emoji` is optional and is only used for stickers that are being uploaded for the first time.

## Sending an animation
```python
telegram.send_animation(
    chat_id = 'Your ID here',
    animation = 'path to animation file or valid url',
    caption = 'Look at this animation!',
    duration = 5,
    width = 480,
    height = 270,
    has_spoiler = False
    )
```

Telegram treats a video as an animation when it is muted or when it is a GIF. A video with an audio track may come back as a normal video message.

## Sending a video note
```python
telegram.send_video_note(
    chat_id = 'Your ID here',
    video_note = 'path to circular video or valid url',
    duration = 10,
    length = 240
    )
```

## Uploading bytes from memory
You no longer need a temporary file to send something that is already in memory. `bytes`, `bytearray`, and `memoryview` are detected automatically:

```python
with open('song.mp3', 'rb') as file:
    telegram.send_audio(
        chat_id = 'Your ID here',
        audio = file,
        file_name = 'Song.mp3'
    )

png_bytes = b'\x89PNG\r\n\x1a\n...'
telegram.send_photo(
    chat_id = 'Your ID here',
    photo = png_bytes,
    file_name = 'chart.png'
    )

zip_bytes = b'PK\x03\x04...'
telegram.send_document(
    chat_id = 'Your ID here',
    document = zip_bytes,
    file_name = 'archive.zip'
    )
```

File objects that you pass in are never closed by the library; you keep ownership of them.  
`byte = True` is still accepted for backwards compatibility, but it does nothing now because bytes are detected automatically.

When you do not provide a name, the library uses a sensible default for the endpoint (`audio.mp3`, `video.mp4`, `photo.jpg`, `document.bin`, and so on). For in-memory bytes, the content is also inspected, so a PNG upload becomes `photo.png` instead of `photo.jpg`.

## URLs, paths, file IDs, and file names
A string is handled in this order:
1. An `http://` or `https://` URL is passed to Telegram as a URL.
2. An existing path is opened and streamed to Telegram.
3. A string that looks like a Telegram `file_id` is passed without uploading it again.
4. Anything else raises `FileNotFoundError`.

```python
telegram.send_photo(chat_id = 'Your ID here', photo = 'https://example.com/photo.jpg')
telegram.send_photo(chat_id = 'Your ID here', photo = message.photo.file_id)
telegram.send_photo(chat_id = 'Your ID here', photo = '/path/to/photo.jpg')
```

For path uploads, the file's base name is used unless you pass `file_name`. For URLs, Telegram uses the URL. For bytes, use `file_name`, `file_names`, `thumbnail_file_name`, or `certificate_file_name`.

## Showing a chat action
```python
telegram.send_chat_action(chat_id = 'Your ID here', action = 'typing')
```

Useful actions include `'typing'`, `'upload_photo'`, `'upload_video'`, `'record_voice'`, `'upload_document'`, and `'find_location'`.

## Forwarding, copying, deleting, and editing messages

```python
telegram.forward_message(
    chat_id = 'Destination ID',
    from_chat_id = 'Source ID',
    message_id = 12345
    )

telegram.copy_message(
    chat_id = 'Destination ID',
    from_chat_id = 'Source ID',
    message_id = 12345,
    caption = 'Copied!'
    )
```

`copy_message` returns the new `message_id` in a dictionary.  
`forward_message` returns the new `Message` object.

```python
telegram.delete_message(chat_id = 'Your ID here', message_id = 1235)
telegram.delete_messages(chat_id = 'Your ID here', message_ids = [1235, 1236])
```

```python
telegram.edit_message(
    chat_id = 'Your ID here',
    message_id = 1235,
    text = 'This is an updated text!',
    parse_mode = 'Markdown'
    )

telegram.edit_message_caption(
    chat_id = 'Your ID here',
    message_id = 1235,
    caption = 'This is an updated caption!'
    )

telegram.edit_message_reply_markup(
    chat_id = 'Your ID here',
    message_id = 1235,
    reply_markup = {'inline_keyboard': []}
    )
```

## Pinning and unpinning messages
```python
telegram.pin_chat_message(
    chat_id = 'Your ID here',
    message_id = 1235,
    disable_notification = True
    )

telegram.unpin_chat_message(chat_id = 'Your ID here', message_id = 1235)

# Unpin the most recent pinned message.
telegram.unpin_chat_message(chat_id = 'Your ID here')
```

## Answering callback queries
```python
for update in telegram.poll_updates(allowed_updates = ['callback_query']):
    callback = update.raw.get('callback_query')
    if not callback:
        continue

    telegram.answer_callback_query(
        callback_query_id = callback['id'],
        text = 'Done!',
        show_alert = False
        )
```

## Downloading attachments
`download_attachment` uses the `file_id` from a received message. It writes the file to disk by default and returns the full path:

```python
message = telegram.send_document(
    chat_id = 'Your ID here',
    document = '/path/to/report.pdf'
    )

saved_path = telegram.download_attachment(
    file_id = message.document.file_id,
    file_name = 'downloaded-report.pdf',
    download_path = '/path/to/downloads/'
    )
```

Pass `as_bytes = True` to keep the file in memory instead:

```python
content = telegram.download_attachment(
    file_id = message.document.file_id,
    as_bytes = True
    )
```

Downloads are streamed in chunks. You can change the chunk size and timeout, and 429/5xx responses are retried automatically:

```python
content = telegram.download_attachment(
    file_id = message.document.file_id,
    as_bytes = True,
    chunk_size = 128 * 1024,
    timeout = 60
    )
```

If you do not pass `download_path`, `telegram.current_directory` is used. You can change that attribute at any time.

## Getting bot, chat, and file information
```python
me = telegram.get_me()
print(me['id'], me['username'])

chat = telegram.get_chat(chat_id = '@example_channel')
print(chat['title'])

# `message` is a message you received earlier.
file_info = telegram.get_file(file_id = message.document.file_id)
print(file_info['file_path'])
```

## Raw updates, polling, and parsed data
`get_updates` returns the raw updates from Telegram and advances the internal offset for you:

```python
updates = telegram.get_updates(
    long_poll_timeout = 30,
    allowed_updates = ['message', 'callback_query'],
    limit = 100
    )

for update in updates:
    print(f'Update ID: {update["update_id"]}')
```

`poll_updates` is a generator that parses each update into a `Message` object:

```python
for message in telegram.poll_updates(
    polling_interval = 1,
    long_poll_timeout = 30,
    max_retries = None,
    allowed_updates = ['message']
    ):
    print(f'Update ID: {message.update_id}')
    print(f'Message ID: {message.message_id}')
    print(f'Update type: {message.update_type}')
    print(f'Text: {message.text}')
```

With long polling enabled (the default), Telegram holds the request for up to `long_poll_timeout` seconds, so `polling_interval` is only used when you set `long_poll_timeout = 0`.  
`max_retries` limits consecutive network/server failures. Permanent errors such as an invalid token or a webhook conflict are raised immediately.

Non-message updates such as callback queries are also returned as `Message` objects. Their `update_type` is set, and the untouched update is available in `.raw`.  
The old aliases `message.id`, `sticker.type`, `video.unique_id`, and `video.video_size` are still available.

## Polling, accessing the parsed data, and downloading attachments!
```python
for message in telegram.poll_updates(polling_interval = 5):
    print(f'Update ID: {message.update_id}')
    print(f'Message ID: {message.message_id}')
    print(f'Update Type: {message.update_type}')

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
        telegram.download_attachment(
            message.sticker.file_id,
            message.sticker.file_unique_id,
            telegram.current_directory
            )

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

        print(f'Sticker Thumbnail File ID: {message.sticker.thumbnail_file_id}')
        print(f'Sticker Thumbnail File Unique ID: {message.sticker.thumbnail_file_unique_id}')
        print(f'Sticker Thumbnail File Size: {message.sticker.thumbnail_file_size}')
        print(f'Sticker Thumbnail Width: {message.sticker.thumbnail_width}')
        print(f'Sticker Thumbnail Height: {message.sticker.thumbnail_height}')

    if message.animation:
        telegram.download_attachment(
            message.animation.file_id,
            message.animation.file_name,
            telegram.current_directory
            )

        print(f'Animation File Name: {message.animation.file_name}')
        print(f'Animation Mime Type: {message.animation.mime_type}')
        print(f'Animation Duration: {message.animation.duration}')
        print(f'Animation Width: {message.animation.width}')
        print(f'Animation Height: {message.animation.height}')
        print(f'Animation File ID: {message.animation.file_id}')
        print(f'Animation Unique ID: {message.animation.file_unique_id}')
        print(f'Animation Size: {message.animation.file_size}')

        print(f'Animation Thumbnail File ID: {message.animation.thumbnail_file_id}')
        print(f'Animation Thumbnail File Unique ID: {message.animation.thumbnail_file_unique_id}')
        print(f'Animation Thumbnail File Size: {message.animation.thumbnail_file_size}')
        print(f'Animation Thumbnail Width: {message.animation.thumbnail_width}')
        print(f'Animation Thumbnail Height: {message.animation.thumbnail_height}')

    if message.video:
        telegram.download_attachment(
            message.video.file_id,
            message.video.file_name,
            telegram.current_directory
            )

        print(f'Video Width: {message.video.width}')
        print(f'Video Height: {message.video.height}')
        print(f'Video Filename: {message.video.file_name}')
        print(f'Video Mime Type: {message.video.mime_type}')
        print(f'Video File ID: {message.video.file_id}')
        print(f'Video Unique ID: {message.video.unique_id}')
        print(f'Video Video Size: {message.video.video_size}')

        print(f'Video Thumbnail File ID: {message.video.thumbnail_file_id}')
        print(f'Video Thumbnail File Unique ID: {message.video.thumbnail_file_unique_id}')
        print(f'Video Thumbnail File Size: {message.video.thumbnail_file_size}')
        print(f'Video Thumbnail Width: {message.video.thumbnail_width}')
        print(f'Video Thumbnail Height: {message.video.thumbnail_height}')

    if message.document:
        telegram.download_attachment(
            message.document.file_id,
            message.document.file_name,
            telegram.current_directory
            )

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
        telegram.download_attachment(
            message.video_note.file_id,
            message.video_note.file_unique_id,
            telegram.current_directory
            )

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
        telegram.download_attachment(
            message.audio.file_id,
            message.audio.file_name,
            telegram.current_directory
            )

        print(f'Audio Duration: {message.audio.duration}')
        print(f'Audio File Name: {message.audio.file_name}')
        print(f'Audio Mime Type: {message.audio.mime_type}')
        print(f'Audio File ID: {message.audio.file_id}')
        print(f'Audio File Unique ID: {message.audio.file_unique_id}')
        print(f'Audio File Size: {message.audio.file_size}')

    if message.photo:
        telegram.download_attachment(
            message.photo.file_id,
            message.photo.file_unique_id,
            telegram.current_directory
            )

        print(f'Photo File ID: {message.photo.file_id}')
        print(f'Photo File Unique ID: {message.photo.file_unique_id}')
        print(f'Photo File Size: {message.photo.file_size}')
        print(f'Photo Width: {message.photo.width}')
        print(f'Photo Height: {message.photo.height}')

    if message.voice:
        telegram.download_attachment(
            message.voice.file_id,
            message.voice.file_unique_id,
            telegram.current_directory
            )

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

    # Everything Telegram sent, including fields this library does not parse yet.
    print(f'Raw message: {message.raw_message}')
    print(f'Raw update: {message.raw}')
```

## Webhooks
```python
telegram.set_webhook(
    url = 'https://example.com/webhook',
    certificate = '/path/to/certificate.pem',
    allowed_updates = ['message', 'callback_query'],
    secret_token = 'your-secret-token',
    max_connections = 40,
    drop_pending_updates = False
    )

print(telegram.get_webhook_info())

telegram.delete_webhook(drop_pending_updates = True)
```

The `certificate` parameter accepts a path, bytes, or an open file object. When uploading from memory, use `certificate_file_name` to choose the name.  
A webhook and `poll_updates` cannot be used at the same time; call `delete_webhook()` before switching back to polling.

## Errors
All Telegram errors are raised as exceptions:

```python
from TelegramAPI import TelegramAPI, TelegramAPIError, TelegramNetworkError, TelegramTimeoutError

telegram = TelegramAPI('Enter your bot token here.')

try:
    telegram.send_message(chat_id = 'Your ID here', text = 'Hello!')
except TelegramAPIError as error:
    print(f'Method: {error.method}')
    print(f'Error code: {error.error_code}')
    print(f'Description: {error.description}')
    print(f'Parameters: {error.parameters}')
```

`TelegramTimeoutError` is a subclass of `TelegramNetworkError`, which is a subclass of `TelegramAPIError`.  
Rate-limited requests (`429`) are retried automatically up to `max_flood_retries` times, respecting Telegram's `retry_after` value. Upload streams are rewound before a retry; a non-seekable stream is not retried with empty data.

## Helper methods
```python
telegram.is_url('https://example.com')  # True
telegram.is_url('/path/to/file')        # False

print(telegram.convert_timestamp(message.date))
# Output: '23/02/2022 10:19:00'
```
