from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _thumbnail(data: Any) -> dict[str, Any]:
    return data if isinstance(data, dict) else {}


@dataclass(slots=True)
class Message:
    # General IDs
    update_id: int | None = None
    message_id: int | None = None

    # From section
    from_id: int | None = None
    from_is_bot: bool | None = None
    from_first_name: str | None = None
    from_username: str | None = None
    from_last_name: str | None = None

    # Chat section
    chat_id: int | None = None
    chat_first_name: str | None = None
    chat_username: str | None = None
    chat_title: str | None = None
    chat_type: str | None = None

    # Dates and basic context
    date: int | None = None
    edit_date: int | None = None
    text: str | None = None
    caption: str | None = None
    media_group_id: str | None = None
    reply_to_message_id: int | None = None
    message_thread_id: int | None = None
    is_topic_message: bool | None = None
    entities: list[dict[str, Any]] | None = None
    caption_entities: list[dict[str, Any]] | None = None

    # Media and attachments
    video: Video | None = None
    photo: Photo | None = None
    voice: Voice | None = None
    audio: Audio | None = None
    sticker: Sticker | None = None
    contact: Contact | None = None
    location: Location | None = None
    document: Document | None = None
    animation: Animation | None = None
    video_note: VideoNote | None = None

    # Update metadata
    update_type: str | None = None

    # Everything Telegram sent, so new fields are never lost
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    raw_message: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def id(self) -> int | None:
        """Alias for message_id, for convenience."""
        return self.message_id


@dataclass(slots=True)
class Sticker:
    width: int | None = None
    height: int | None = None
    emoji: str | None = None
    set_name: str | None = None
    is_animated: bool | None = None
    is_video: bool | None = None
    sticker_type: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    thumbnail_file_id: str | None = None
    thumbnail_file_unique_id: str | None = None
    thumbnail_file_size: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def type(self) -> str | None:
        return self.sticker_type

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Sticker:
        data = data or {}
        thumbnail = _thumbnail(data.get("thumbnail") or data.get("thumb"))
        return cls(
            width=data.get("width"),
            height=data.get("height"),
            emoji=data.get("emoji"),
            set_name=data.get("set_name"),
            is_animated=data.get("is_animated"),
            is_video=data.get("is_video"),
            sticker_type=data.get("type"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            thumbnail_file_id=thumbnail.get("file_id"),
            thumbnail_file_unique_id=thumbnail.get("file_unique_id"),
            thumbnail_file_size=thumbnail.get("file_size"),
            thumbnail_width=thumbnail.get("width"),
            thumbnail_height=thumbnail.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class Animation:
    file_name: str | None = None
    mime_type: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    thumbnail_file_id: str | None = None
    thumbnail_file_unique_id: str | None = None
    thumbnail_file_size: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Animation:
        data = data or {}
        thumbnail = _thumbnail(data.get("thumbnail") or data.get("thumb"))
        return cls(
            file_name=data.get("file_name"),
            mime_type=data.get("mime_type"),
            duration=data.get("duration"),
            width=data.get("width"),
            height=data.get("height"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            thumbnail_file_id=thumbnail.get("file_id"),
            thumbnail_file_unique_id=thumbnail.get("file_unique_id"),
            thumbnail_file_size=thumbnail.get("file_size"),
            thumbnail_width=thumbnail.get("width"),
            thumbnail_height=thumbnail.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class Video:
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    thumbnail_file_id: str | None = None
    thumbnail_file_unique_id: str | None = None
    thumbnail_file_size: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def unique_id(self) -> str | None:
        """Backwards-compatible alias for file_unique_id."""
        return self.file_unique_id

    @property
    def video_size(self) -> int | None:
        """Backwards-compatible alias for file_size."""
        return self.file_size

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Video:
        data = data or {}
        thumbnail = _thumbnail(data.get("thumbnail") or data.get("thumb"))
        return cls(
            duration=data.get("duration"),
            width=data.get("width"),
            height=data.get("height"),
            file_name=data.get("file_name"),
            mime_type=data.get("mime_type"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            thumbnail_file_id=thumbnail.get("file_id"),
            thumbnail_file_unique_id=thumbnail.get("file_unique_id"),
            thumbnail_file_size=thumbnail.get("file_size"),
            thumbnail_width=thumbnail.get("width"),
            thumbnail_height=thumbnail.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class Document:
    file_name: str | None = None
    mime_type: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    thumbnail_file_id: str | None = None
    thumbnail_file_unique_id: str | None = None
    thumbnail_file_size: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        data = data or {}
        thumbnail = _thumbnail(data.get("thumbnail") or data.get("thumb"))
        return cls(
            file_name=data.get("file_name"),
            mime_type=data.get("mime_type"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            thumbnail_file_id=thumbnail.get("file_id"),
            thumbnail_file_unique_id=thumbnail.get("file_unique_id"),
            thumbnail_file_size=thumbnail.get("file_size"),
            thumbnail_width=thumbnail.get("width"),
            thumbnail_height=thumbnail.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class VideoNote:
    duration: int | None = None
    length: int | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    thumbnail_file_id: str | None = None
    thumbnail_file_unique_id: str | None = None
    thumbnail_file_size: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VideoNote:
        data = data or {}
        thumbnail = _thumbnail(data.get("thumbnail") or data.get("thumb"))
        return cls(
            duration=data.get("duration"),
            length=data.get("length"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            thumbnail_file_id=thumbnail.get("file_id"),
            thumbnail_file_unique_id=thumbnail.get("file_unique_id"),
            thumbnail_file_size=thumbnail.get("file_size"),
            thumbnail_width=thumbnail.get("width"),
            thumbnail_height=thumbnail.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class Audio:
    duration: int | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    performer: str | None = None
    title: str | None = None
    thumbnail_file_id: str | None = None
    thumbnail_file_unique_id: str | None = None
    thumbnail_file_size: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Audio:
        data = data or {}
        thumbnail = _thumbnail(data.get("thumbnail") or data.get("thumb"))
        return cls(
            duration=data.get("duration"),
            file_name=data.get("file_name"),
            mime_type=data.get("mime_type"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            performer=data.get("performer"),
            title=data.get("title"),
            thumbnail_file_id=thumbnail.get("file_id"),
            thumbnail_file_unique_id=thumbnail.get("file_unique_id"),
            thumbnail_file_size=thumbnail.get("file_size"),
            thumbnail_width=thumbnail.get("width"),
            thumbnail_height=thumbnail.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class Photo:
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Photo:
        data = data or {}
        return cls(
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            width=data.get("width"),
            height=data.get("height"),
            raw=data,
        )


@dataclass(slots=True)
class Voice:
    duration: int | None = None
    mime_type: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    file_size: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Voice:
        data = data or {}
        return cls(
            duration=data.get("duration"),
            mime_type=data.get("mime_type"),
            file_id=data.get("file_id"),
            file_unique_id=data.get("file_unique_id"),
            file_size=data.get("file_size"),
            raw=data,
        )


@dataclass(slots=True)
class Contact:
    phone_number: str | None = None
    first_name: str | None = None
    user_id: int | None = None
    last_name: str | None = None
    vcard: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Contact:
        data = data or {}
        return cls(
            phone_number=data.get("phone_number"),
            first_name=data.get("first_name"),
            user_id=data.get("user_id"),
            last_name=data.get("last_name"),
            vcard=data.get("vcard"),
            raw=data,
        )


@dataclass(slots=True)
class Location:
    latitude: float | None = None
    longitude: float | None = None
    live_period: int | None = None
    heading: int | None = None
    horizontal_accuracy: float | None = None
    proximity_alert_radius: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Location:
        data = data or {}
        return cls(
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            live_period=data.get("live_period"),
            heading=data.get("heading"),
            horizontal_accuracy=data.get("horizontal_accuracy"),
            proximity_alert_radius=data.get("proximity_alert_radius"),
            raw=data,
        )
