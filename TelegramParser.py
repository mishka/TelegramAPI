from TelegramTypes import Message, Video, Document, VideoNote
from TelegramTypes import Audio, Photo, Voice, Contact, Location
from TelegramTypes import Sticker, Animation

class Parser:
    def process(self, message):
            # GET one
            message_data = message.get('message', {})
            # GET but if the content is updated/edited
            if not message_data:
                message_data = message.get('edited_message', {})
            # POST one
            if not message_data:
                message_data = message.get('result', {})
                # ducktape fix for sendMediaGroup.

                # if you upload 3 items, you get 3 responses back within a list.
                # for now i send the first one back.
                # i will have to scale this out for messages with many items within
                if str(message_data).startswith('['):
                    message_data = message_data[-1]

            if type(message_data) == bool:
                return

            from_data = message_data.get('from', {})
            chat_data = message_data.get('chat', {})
            video_data = message_data.get('video', {})
            photo_data = message_data.get('photo', {})
            document_data = message_data.get('document', {})
            voice_data = message_data.get('voice', {})
            video_note_data = message_data.get('video_note', {})
            audio_data = message_data.get('audio', {})
            contact_data = message_data.get('contact', {})
            location_data = message_data.get('location', {})
            sticker_data = message_data.get('sticker', {})
            animation_data = message_data.get('animation', {})
            
            update_id = message.get('update_id')
            message_id = message_data.get('message_id')
            
            from_user_id = from_data.get('id')
            from_is_bot = from_data.get('is_bot')
            from_first_name = from_data.get('first_name')
            from_username = from_data.get('username')
            
            chat_id = chat_data.get('id')
            chat_first_name = chat_data.get('first_name')
            chat_username = chat_data.get('username')
            chat_type = chat_data.get('type')

            date = message_data.get('date')
            text = message_data.get('text')
            caption = message_data.get('caption')
            edit_date = message_data.get('edit_date')
            media_group_id = message_data.get('media_group_id')
            
            # Parse Sticker Data
            if sticker_data:
                sticker_width = sticker_data.get('width')
                sticker_height = sticker_data.get('height')
                sticker_emoji = sticker_data.get('emoji')
                sticker_set_name = sticker_data.get('set_name')
                sticker_is_animated = sticker_data.get('is_animated')
                sticker_is_video = sticker_data.get('is_video')
                sticker_type = sticker_data.get('type')
                sticker_file_id = sticker_data.get('file_id')
                sticker_file_unique_id = sticker_data.get('file_unique_id')
                sticker_file_size = sticker_data.get('file_size')
                
                sticker_thumbnail_data = sticker_data.get('thumbnail')
                sticker_thumbnail_file_id = sticker_thumbnail_data.get('file_id')
                sticker_thumbnail_file_unique_id = sticker_thumbnail_data.get('file_unique_id')
                sticker_thumbnail_file_size = sticker_thumbnail_data.get('file_size')
                sticker_thumbnail_width = sticker_thumbnail_data.get('width')
                sticker_thumbnail_height = sticker_thumbnail_data.get('height')

                sticker = Sticker(sticker_width, sticker_height, sticker_emoji, sticker_set_name, sticker_is_animated,
                                  sticker_is_video, sticker_type, sticker_file_id, sticker_file_unique_id,
                                  sticker_file_size, sticker_thumbnail_file_id, sticker_thumbnail_file_unique_id,
                                  sticker_thumbnail_file_size, sticker_thumbnail_width, sticker_thumbnail_height)
            else:
                sticker = None

            # Parse GIFs
            if animation_data:
                animation_file_name = animation_data.get('file_name')
                animation_mime_type = animation_data.get('mime_type')
                animation_duration = animation_data.get('duration')
                animation_width = animation_data.get('width')
                animation_height = animation_data.get('height')
                animation_file_id = animation_data.get('file_id')
                animation_file_unique_id = animation_data.get('file_unique_id')
                animation_file_size = animation_data.get('file_size')
                
                animation_thumbnail_data = animation_data.get('thumbnail')
                animation_thumbnail_file_id = animation_thumbnail_data.get('file_id')
                animation_thumbnail_file_unique_id = animation_thumbnail_data.get('file_unique_id')
                animation_thumbnail_file_size = animation_thumbnail_data.get('file_size')
                animation_thumbnail_width = animation_thumbnail_data.get('width')
                animation_thumbnail_height = animation_thumbnail_data.get('height')

                animation = Animation(animation_file_name, animation_mime_type, animation_duration, animation_width,
                                      animation_height, animation_file_id, animation_file_unique_id, animation_file_size,
                                      animation_thumbnail_file_id, animation_thumbnail_file_unique_id, animation_thumbnail_file_size,
                                      animation_thumbnail_width, animation_thumbnail_height)
            else:
                animation = None

            # Parse Video Data
            if video_data:
                video_duration = video_data.get('duration')
                video_width = video_data.get('width')
                video_height = video_data.get('height')
                video_file_name = video_data.get('file_name')
                video_mime_type = video_data.get('mime_type')
                video_file_id = video_data.get('file_id')
                video_unique_id = video_data.get('file_unique_id')
                video_size = video_data.get('file_size')

                video_thumbnail_data = video_data.get('thumbnail', {})
                video_thumbnail_file_id = video_thumbnail_data.get('file_id')
                video_thumbnail_file_unique_id = video_thumbnail_data.get('file_unique_id')
                video_thumbnail_file_size = video_thumbnail_data.get('file_size')
                video_thumbnail_width = video_thumbnail_data.get('width')
                video_thumbnail_height = video_thumbnail_data.get('height')
                
                video = Video(video_duration, video_width, video_height, video_file_name, video_mime_type,
                            video_file_id, video_unique_id, video_size, video_thumbnail_file_id, video_thumbnail_file_unique_id,
                            video_thumbnail_file_size, video_thumbnail_width, video_thumbnail_height)
            else:
                video = None

            # Parse Document Files
            if document_data:
                document_file_name = document_data.get('file_name')
                document_mime_type = document_data.get('mime_type')
                document_file_id = document_data.get('file_id')
                document_file_unique_id = document_data.get('file_unique_id')
                document_file_size = document_data.get('file_size')
                document_thumbnail_data = document_data.get('thumbnail', {})
                
                document_thumbnail_file_id = document_thumbnail_data.get('file_id')
                document_thumbnail_file_unique_id = document_thumbnail_data.get('file_unique_id')
                document_thumbnail_file_size = document_thumbnail_data.get('file_size')
                document_thumbnail_width = document_thumbnail_data.get('width')
                document_thumbnail_height = document_thumbnail_data.get('height')

                document = Document(document_file_name, document_mime_type, document_file_id, document_file_unique_id,
                                    document_file_size, document_thumbnail_file_id, document_thumbnail_file_unique_id,
                                    document_thumbnail_file_size, document_thumbnail_width, document_thumbnail_height)
            else:
                document = None

            # Parse the circle video thing
            if video_note_data:
                video_note_duration = video_note_data.get('duration')
                video_note_length = video_note_data.get('length')
                video_note_file_id = video_note_data.get('file_id')
                video_note_file_unique_id = video_note_data.get('file_unique_id')
                video_note_file_size = video_note_data.get('file_size')
                video_note_thumbnail_data = video_note_data.get('thumbnail', {})
                
                video_note_thumbnail_file_id = video_note_thumbnail_data.get('file_id')
                video_note_thumbnail_file_unique_id = video_note_thumbnail_data.get('file_unique_id')
                video_note_thumbnail_file_size = video_note_thumbnail_data.get('file_size')
                video_note_thumbnail_width = video_note_thumbnail_data.get('width')
                video_note_thumbnail_height = video_note_thumbnail_data.get('height')

                video_note = VideoNote(video_note_duration, video_note_length, video_note_file_id, video_note_file_unique_id,
                                    video_note_file_size, video_note_thumbnail_file_id, video_note_thumbnail_file_unique_id,
                                    video_note_thumbnail_file_size, video_note_thumbnail_width, video_note_thumbnail_height)
            else:
                video_note = None

            # Parse audio files
            if audio_data:
                audio_duration = audio_data.get('duration')
                audio_file_name = audio_data.get('file_name')
                audio_mime_type = audio_data.get('mime_type')
                audio_file_id = audio_data.get('file_id')
                audio_file_unique_id = audio_data.get('file_unique_id')
                audio_file_size = audio_data.get('file_size')

                audio = Audio(audio_duration, audio_file_name, audio_mime_type, audio_file_id, audio_file_unique_id, audio_file_size)
            else:
                audio = None

            # Parse Photos
            if photo_data:
                photo_data = photo_data[-1] # we get the last entry which is the highest quality
                photo_file_id = photo_data.get('file_id')
                photo_file_unique_id = photo_data.get('file_unique_id')
                photo_file_size = photo_data.get('file_size')
                photo_width = photo_data.get('width')
                photo_height = photo_data.get('height')

                photo = Photo(photo_file_id, photo_file_unique_id, photo_file_size, photo_width, photo_height)
            else:
                photo = None

            # Parse Voice Messages
            if voice_data:
                voice_duration = voice_data.get('duration')
                voice_mime_type = voice_data.get('mime_type')
                voice_file_id = voice_data.get('file_id')
                voice_file_unique_id = voice_data.get('file_unique_id')
                voice_file_size = voice_data.get('file_size')

                voice = Voice(voice_duration, voice_mime_type, voice_file_id, voice_file_unique_id, voice_file_size)
            else:
                voice = None

            # Parse Shared Contacts
            if contact_data:
                contact_phone_number = contact_data.get('phone_number')
                contact_first_name = contact_data.get('first_name')
                contact_user_id = contact_data.get('user_id')

                contact = Contact(contact_phone_number, contact_first_name, contact_user_id)

            else:
                contact = None

            # Parse Location Data
            if location_data:
                location_latitude = location_data.get('latitude')
                location_longitude = location_data.get('longitude')
                location_live_period = location_data.get('live_period')
                location_heading = location_data.get('heading')
                location_horizontal_accuracy = location_data.get('horizontal_accuracy')

                location = Location(location_latitude, location_longitude, location_live_period, location_heading, location_horizontal_accuracy)
            else:
                location = None

            return Message(update_id, message_id, from_user_id, from_is_bot, from_first_name, from_username,
                            chat_id, chat_first_name, chat_username, chat_type, date, edit_date, text, caption, media_group_id,
                            video, photo, voice, audio, sticker, contact, location, document, animation, video_note)