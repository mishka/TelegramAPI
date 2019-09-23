# Welcome!
You can text yourself from a telegram bot using this method.

## Dependencies
- requests

## Creating a telegram bot
You can create a bot through [@BotFather](https://telegram.me/BotFather)

## Finding the chat ID
You can learn about your chat ID by messaging `/my_id` to the [@get_id_bot](https://telegram.me/get_id_bot) on telegram.

## Usage

Captions are optional, you can just upload files without them as well.

```python
from telegram_api import *

TOKEN = 'your bot token here'
CHAT_ID = 'your chat id here'

telegram_text(text = 'hi', token = TOKEN, chat_id = CHAT_ID)
telegram_doc(caption = 'test file', file = open('test.pdf', 'rb'), token = TOKEN, chat_id = CHAT_ID)
telegram_pic(caption = 'test picture', file = open('test.jpg', 'rb'), token = TOKEN, chat_id = CHAT_ID)
telegram_video(caption = 'test video', file = open('test.mp4', 'rb'), token = TOKEN, chat_id = CHAT_ID)
```
