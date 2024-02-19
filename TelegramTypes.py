class Message:
    def __init__(self, update_id, message_id, from_user_id, from_is_bot, from_first_name, from_username,
                 chat_id, chat_first_name, chat_username, chat_type, date, edit_date, text, caption, media_group_id,
                 video, photo, voice, audio, sticker, contact, location, document, animation, video_note):
        # general IDs
        self.update_id = update_id
        self.message_id = message_id

        # from section
        self.from_id = from_user_id
        self.from_is_bot = from_is_bot
        self.from_first_name = from_first_name
        self.from_username = from_username

        # chat section
        self.chat_id = chat_id
        self.chat_first_name = chat_first_name
        self.chat_username = chat_username
        self.chat_type = chat_type

        # dates and basic context
        self.date = date
        self.text = text
        self.caption = caption
        self.edit_date = edit_date

        # if the post is part of a media group
        self.media_group_id = media_group_id
        
        # medias and attachments
        self.video = video
        self.photo = photo
        self.voice = voice
        self.audio = audio
        self.sticker = sticker
        self.contact = contact
        self.location = location
        self.document = document
        self.animation = animation
        self.video_note = video_note


class Sticker:
    def __init__(self, width, height, emoji, set_name, is_animated, is_video, sticker_type,
                 file_id, file_unique_id, file_size, thumbnail_file_id, thumbnail_file_unique_id,
                 thumbnail_file_size, thumbnail_width, thumbnail_height):
        self.width = width
        self.height = height
        self.emoji = emoji
        self.set_name = set_name
        self.is_animated = is_animated
        self.is_video = is_video
        self.sticker_type = sticker_type
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size
        self.thumbnail_file_id = thumbnail_file_id
        self.thumbnail_file_unique_id = thumbnail_file_unique_id
        self.thumbnail_file_size = thumbnail_file_size
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height


class Animation:
    def __init__(self, file_name, mime_type, duration, width, height, file_id, file_unique_id,
                 file_size, thumbnail_file_id, thumbnail_file_unique_id, thumbnail_file_size,
                 thumbnail_width, thumbnail_height):
        self.file_name = file_name
        self.mime_type = mime_type
        self.duration = duration
        self.width = width
        self.height = height
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size
        self.thumbnail_file_id = thumbnail_file_id
        self.thumbnail_file_unique_id = thumbnail_file_unique_id
        self.thumbnail_file_size = thumbnail_file_size
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height
        

class Video:
    def __init__(self, duration, width, height, file_name, mime_type, file_id, unique_id, size, thumbnail_file_id,
                 thumbnail_file_unique_id, thumbnail_file_size, thumbnail_width, thumbnail_height):
        self.duration = duration
        self.width = width 
        self.height = height
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_id = file_id
        self.unique_id = unique_id
        self.video_size = size
        self.thumbnail_file_id = thumbnail_file_id
        self.thumbnail_file_unique_id = thumbnail_file_unique_id
        self.thumbnail_file_size = thumbnail_file_size
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height


class Document:
    def __init__(self, file_name, mime_type, file_id, file_unique_id, file_size, thumbnail_file_id,
                 thumbnail_file_unique_id, thumbnail_file_size, thumbnail_width, thumbnail_height):
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size
        self.thumbnail_file_id = thumbnail_file_id
        self.thumbnail_file_unique_id = thumbnail_file_unique_id
        self.thumbnail_file_size = thumbnail_file_size
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height


class VideoNote:
    def __init__(self, duration, length, file_id, file_unique_id, file_size, thumbnail_file_id,
                 thumbnail_file_unique_id, thumbnail_file_size, thumbnail_width, thumbnail_height):
        self.duration = duration
        self.length = length
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size
        self.thumbnail_file_id = thumbnail_file_id
        self.thumbnail_file_unique_id = thumbnail_file_unique_id
        self.thumbnail_file_size = thumbnail_file_size
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height


class Audio:
    def __init__(self, duration, file_name, mime_type, file_id, file_unique_id, file_size):
        self.duration = duration
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size


class Photo:
    def __init__(self, file_id, file_unique_id, file_size, width, height):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size
        self.width = width
        self.height = height


class Voice:
    def __init__(self, duration, mime_type, file_id, file_unique_id, file_size):
        self.duration = duration
        self.mime_type = mime_type
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size


class Contact:
    def __init__(self, phone_number, first_name, user_id):
        self.phone_number = phone_number
        self.first_name = first_name
        self.user_id = user_id


class Location:
    def __init__(self, latitude, longitude, live_period, heading, horizontal_accuracy):
        self.latitude = latitude
        self.longitude = longitude
        self.live_period = live_period
        self.heading = heading
        self.horizontal_accuracy = horizontal_accuracy