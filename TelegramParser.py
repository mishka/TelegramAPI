from __future__ import annotations

from typing import Any

from TelegramTypes import (
    Animation,
    Audio,
    Contact,
    Document,
    Location,
    Message,
    Photo,
    Sticker,
    Video,
    VideoNote,
    Voice,
)

MESSAGE_UPDATE_KEYS = (
    "message",
    "edited_message",
    "channel_post",
    "edited_channel_post",
    "business_message",
    "edited_business_message",
)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _photo_data(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value:
        last = value[-1]
        return last if isinstance(last, dict) else {}
    return {}


class Parser:
    def process(self, update: Any) -> Any:
        """
        Parses one raw Telegram update, or a complete Bot API response.

        Message updates are returned as Message objects. Non-message updates
        (callback queries, inline queries, etc.) are also returned as Message
        objects, with update_type set and the untouched update available in
        `.raw`.
        """
        if not isinstance(update, dict):
            return update

        # A complete Bot API response, e.g. {"ok": True, "result": ...}
        if "result" in update and not any(key in update for key in MESSAGE_UPDATE_KEYS):
            return self.parse_result(update.get("result"))

        update_id = update.get("update_id")
        for key in MESSAGE_UPDATE_KEYS:
            data = update.get(key)
            if isinstance(data, dict):
                return self.parse_message(
                    data,
                    update_id=update_id,
                    update_type=key,
                    raw_update=update,
                )

        update_type = next((key for key in update if key != "update_id"), "unknown")
        return Message(update_id=update_id, update_type=update_type, raw=update)

    def parse_message(
        self,
        data: dict[str, Any],
        update_id: int | None = None,
        update_type: str = "message",
        raw_update: dict[str, Any] | None = None,
    ) -> Message:
        if not isinstance(data, dict):
            return data

        from_data = _dict(data.get("from"))
        chat_data = _dict(data.get("chat"))
        reply_data = _dict(data.get("reply_to_message"))

        sticker_data = _dict(data.get("sticker"))
        animation_data = _dict(data.get("animation"))
        video_data = _dict(data.get("video"))
        document_data = _dict(data.get("document"))
        video_note_data = _dict(data.get("video_note"))
        audio_data = _dict(data.get("audio"))
        voice_data = _dict(data.get("voice"))
        contact_data = _dict(data.get("contact"))
        location_data = _dict(data.get("location"))

        photo_data = _photo_data(data.get("photo"))
        photo = Photo.from_dict(photo_data) if photo_data else None

        return Message(
            update_id=update_id,
            message_id=data.get("message_id"),
            from_id=from_data.get("id"),
            from_is_bot=from_data.get("is_bot"),
            from_first_name=from_data.get("first_name"),
            from_username=from_data.get("username"),
            from_last_name=from_data.get("last_name"),
            chat_id=chat_data.get("id"),
            chat_first_name=chat_data.get("first_name"),
            chat_username=chat_data.get("username"),
            chat_title=chat_data.get("title"),
            chat_type=chat_data.get("type"),
            date=data.get("date"),
            edit_date=data.get("edit_date"),
            text=data.get("text"),
            caption=data.get("caption"),
            media_group_id=data.get("media_group_id"),
            reply_to_message_id=reply_data.get("message_id"),
            message_thread_id=data.get("message_thread_id"),
            is_topic_message=data.get("is_topic_message"),
            entities=data.get("entities"),
            caption_entities=data.get("caption_entities"),
            video=Video.from_dict(video_data) if video_data else None,
            photo=photo,
            voice=Voice.from_dict(voice_data) if voice_data else None,
            audio=Audio.from_dict(audio_data) if audio_data else None,
            sticker=Sticker.from_dict(sticker_data) if sticker_data else None,
            contact=Contact.from_dict(contact_data) if contact_data else None,
            location=Location.from_dict(location_data) if location_data else None,
            document=Document.from_dict(document_data) if document_data else None,
            animation=Animation.from_dict(animation_data) if animation_data else None,
            video_note=VideoNote.from_dict(video_note_data) if video_note_data else None,
            update_type=update_type,
            raw=raw_update if raw_update is not None else data,
            raw_message=data,
        )

    def parse_result(self, result: Any) -> Any:
        """
        Parses the value of a Bot API "result" field.

        A single message becomes a Message, a list of messages (sendMediaGroup)
        becomes a list of Messages, and other values (deleteMessage, getMe,
        MessageId, booleans, etc.) are returned unchanged.
        """
        if isinstance(result, dict):
            if "message_id" in result:
                return self.parse_message(result)
            return result
        if isinstance(result, list):
            return [self.parse_message(item) for item in result if isinstance(item, dict)]
        return result
