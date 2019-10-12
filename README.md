# Welcome!
You can text yourself from a telegram bot using this method.

## Dependencies
- requests

## Creating a telegram bot
You can create a bot through [@BotFather](https://telegram.me/BotFather)

## Finding the chat ID
You can learn about your chat ID by messaging `/my_id` to the [@get_id_bot](https://telegram.me/get_id_bot) on telegram.

## Important note on filetypes
[Current available filetypes:](https://core.telegram.org/bots/api#available-methods)  
**Audio**, **Voice**  
**Photo**, **Video**, **Animation**  
**Document**  
 


## Usage  


**You MUST define the filetype if you're uploading a file.**

```python
from telegram_api import *

TOKEN = 'your bot token here'
CHAT_ID = 'your chat id here'

# Just to send a text message, simply;
telegram(text = 'hi', token = TOKEN, chat_id = CHAT_ID)

# Upload a file without text/caption;
telegram(file = open('test.pdf', 'rb'), filetype = 'Document', token = TOKEN, chat_id = CHAT_ID)

# Upload a file with text/caption;
telegram(text = 'a test file', file = open('test.mp4', 'rb'), filetype = 'Video', token = TOKEN, chat_id = CHAT_ID)
```
