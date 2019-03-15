# Welcome!
You can text yourself from a telegram bot using this method.

## Dependencies
- curl

## Creating a telegram bot
You can create a bot through [@BotFather](https://telegram.me/BotFather)

## Finding chat ID
You can learn about your chat ID by messaging `/my_id` to the [@get_id_bot](https://telegram.me/get_id_bot) on telegram.

## Usage
```python
from telegram_api import *

BOT_TOKEN = 'your bot token here'
CHAT_ID = 'your chat id here'
PATH = '/home/username/Documents/'

# \n works in messages/captions
telegram_text('This sends a message', CHAT_ID, TELEGRAM_TOKEN)

# if you don't want to write a caption, just leave it empty
telegram_file('Caption here', 'example.zip', PATH, CHAT_ID, BOT_TOKEN)
telegram_image('Caption here', 'somepic.jpg', PATH, CHAT_ID, BOT_TOKEN)
telegram_video('Caption here', 'somevideo.mp4', PATH, CHAT_ID, BOT_TOKEN)
```
