from __future__ import annotations

import json
import logging
import mimetypes
import os
import random
import re
import time
from collections.abc import Sequence
from contextlib import ExitStack
from datetime import datetime, timezone
from typing import Any, BinaryIO, Literal, TypeAlias, cast
from urllib.parse import urlparse

import requests

from TelegramParser import Parser

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

ChatId: TypeAlias = int | str
ParseMode: TypeAlias = Literal["Markdown", "MarkdownV2", "HTML"]
MediaSource: TypeAlias = str | bytes | bytearray | memoryview | os.PathLike[str] | BinaryIO
MediaGroupItem: TypeAlias = MediaSource | tuple[MediaSource, str | None] | dict[str, Any]

_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}={0,2}$")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
_SINGLE_ITEM_EXTRA_KEYS = {
    "caption",
    "parse_mode",
    "caption_entities",
    "has_spoiler",
    "show_caption_above_media",
    "duration",
    "width",
    "height",
    "supports_streaming",
    "performer",
    "title",
    "disable_content_type_detection",
}


class TelegramAPIError(Exception):
    """Raised when Telegram returns an error, or returns an invalid response."""

    def __init__(
        self,
        method: str,
        error_code: int | None = None,
        description: str = "",
        parameters: dict[str, Any] | None = None,
        response: dict[str, Any] | None = None,
    ):
        self.method = method
        self.error_code = error_code
        self.description = description
        self.parameters = parameters or {}
        self.response = response
        if error_code is not None:
            message = f"{method} failed ({error_code}): {description}"
        else:
            message = f"{method} failed: {description}"
        super().__init__(message)


class TelegramNetworkError(TelegramAPIError):
    """Raised when the connection to Telegram fails."""


class TelegramTimeoutError(TelegramNetworkError):
    """Raised when a request to Telegram times out."""


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _json_param(value: Any) -> Any:
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _form_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _safe_filename(name: Any) -> str:
    name = str(name).replace("\\", "/").rsplit("/", 1)[-1]
    name = _CONTROL_CHARS_RE.sub("_", name).strip()
    if name in ("", ".", ".."):
        return "file"
    return name


def _looks_like_file_id(value: str) -> bool:
    return bool(_FILE_ID_RE.fullmatch(value))


def _sniff_extension(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"
    if data.startswith(b"ID3"):
        return ".mp3"
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return ".mp3"
    if data.startswith(b"OggS"):
        return ".ogg"
    if data.startswith(b"fLaC"):
        return ".flac"
    if data.startswith(b"#!AMR"):
        return ".amr"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return ".webm"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in (b"M4A ", b"M4B ", b"M4P "):
            return ".m4a"
        return ".mp4"
    if data.startswith(b"%PDF-"):
        return ".pdf"
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return ".zip"
    return None


def _filename_for_bytes(data: bytes, default_name: str) -> str:
    extension = _sniff_extension(data)
    if not extension:
        return default_name
    base, current = os.path.splitext(default_name)
    if current.lower() == extension.lower():
        return default_name
    return f"{base}{extension}"


class TelegramAPI:
    def __init__(
        self,
        token: str,
        session: requests.Session | None = None,
        timeout: float | tuple[float, float] = (10, 30),
        upload_timeout: float | tuple[float, float] = (10, 120),
        max_flood_retries: int = 3,
    ):
        if not isinstance(token, str) or not token.strip():
            raise ValueError("A Telegram bot token is required.")

        self.token = token.strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.base_download_url = f"https://api.telegram.org/file/bot{self.token}"
        self.current_directory = os.path.join(os.getcwd(), "")
        self.last_update_id: int | None = None
        self.parser = Parser()

        self.session = session or requests.Session()
        self._owns_session = session is None
        self.timeout = timeout
        self.upload_timeout = upload_timeout
        self.max_flood_retries = max_flood_retries

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    def __enter__(self) -> TelegramAPI:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def _redact(self, text: str) -> str:
        if self.token and self.token in text:
            return text.replace(self.token, "<redacted>")
        return text

    def _call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | tuple[float, float] | None = None,
    ) -> Any:
        if timeout is None:
            timeout = self.upload_timeout if files else self.timeout

        url = f"{self.base_url}/{method}"
        form = {key: _form_value(value) for key, value in (data or {}).items() if value is not None}
        upload_positions = self._upload_positions(files) if files else {}

        attempts = 0
        while True:
            try:
                response = self.session.post(url, data=form, files=files or None, timeout=timeout)
            except requests.Timeout as exc:
                raise TelegramTimeoutError(
                    method, description=self._redact(f"Request timed out: {exc}")
                ) from exc
            except requests.RequestException as exc:
                raise TelegramNetworkError(
                    method, description=self._redact(f"Network error: {exc}")
                ) from exc

            try:
                payload = response.json()
            except ValueError as exc:
                text = (response.text or "")[:500]
                raise TelegramAPIError(
                    method, response.status_code, f"Invalid JSON response: {text}"
                ) from exc

            if isinstance(payload, dict) and payload.get("ok"):
                return payload.get("result")

            payload = payload if isinstance(payload, dict) else {}
            error_code = payload.get("error_code", response.status_code)
            description = (
                payload.get("description")
                or (response.text or "")[:500]
                or "Unknown Telegram error"
            )
            parameters = payload.get("parameters") or {}

            if error_code == 429 and attempts < self.max_flood_retries:
                if files and not self._rewind_uploads(files, upload_positions):
                    logger.warning(
                        "%s was rate limited, but an upload stream cannot be rewound; "
                        "not retrying.",
                        method,
                    )
                else:
                    wait = min(float(parameters.get("retry_after", 1)), 60.0)
                    logger.warning("%s was rate limited; retrying in %.1f seconds.", method, wait)
                    time.sleep(wait)
                    attempts += 1
                    continue

            raise TelegramAPIError(method, error_code, description, parameters, payload)

    def _upload_positions(self, files: dict[str, Any]) -> dict[str, int] | None:
        positions: dict[str, int] = {}
        for key, entry in files.items():
            if not isinstance(entry, tuple) or len(entry) < 2:
                continue
            payload = entry[1]
            if isinstance(payload, (bytes, bytearray, memoryview)):
                continue
            tell = getattr(payload, "tell", None)
            seek = getattr(payload, "seek", None)
            if tell is None or seek is None:
                return None
            try:
                positions[key] = tell()
            except (OSError, ValueError):
                return None
        return positions

    def _rewind_uploads(
        self, files: dict[str, Any], positions: dict[str, int] | None
    ) -> bool:
        if positions is None:
            return False
        for key, entry in files.items():
            if not isinstance(entry, tuple) or len(entry) < 2:
                continue
            payload = entry[1]
            if isinstance(payload, (bytes, bytearray, memoryview)):
                continue
            try:
                payload.seek(positions[key])
            except (KeyError, OSError, ValueError):
                return False
        return True

    def _parse_result(self, result: Any) -> Any:
        return self.parser.parse_result(result)

    def _long_poll_timeout(self, long_poll_timeout: int) -> tuple[float, float]:
        connect = self.timeout[0] if isinstance(self.timeout, tuple) else self.timeout
        return (connect, float(long_poll_timeout + 5))

    def _resolve_source(
        self,
        source: MediaSource,
        file_name: str | None = None,
        default_name: str = "file",
        default_mime: str | None = None,
    ) -> tuple[Any, ...]:
        if file_name is not None:
            file_name = _safe_filename(os.fspath(file_name)) if isinstance(file_name, os.PathLike) else str(file_name)

        if isinstance(source, (bytes, bytearray, memoryview)):
            data = bytes(source)
            name = _safe_filename(file_name or _filename_for_bytes(data, default_name))
            mime = mimetypes.guess_type(name)[0] or default_mime or "application/octet-stream"
            return ("upload", name, data, mime, None)

        if hasattr(source, "read"):
            raw_name = getattr(source, "name", "") or ""
            if not isinstance(raw_name, str) or raw_name.startswith("<"):
                raw_name = ""
            name = _safe_filename(file_name or (os.path.basename(raw_name) if raw_name else default_name))
            mime = mimetypes.guess_type(name)[0] or default_mime or "application/octet-stream"
            return ("upload", name, source, mime, None)

        if isinstance(source, os.PathLike):
            source = os.fspath(source)

        if isinstance(source, str):
            if self.is_url(source):
                return ("field", source)
            if os.path.isfile(source):
                handle = open(source, "rb")
                name = _safe_filename(file_name or os.path.basename(source))
                mime = mimetypes.guess_type(name)[0] or default_mime or "application/octet-stream"
                return ("upload", name, handle, mime, handle.close)
            if _looks_like_file_id(source):
                return ("field", source)
            raise FileNotFoundError(
                f"File not found: {source!r}. If this is a Telegram file_id, it must contain no "
                "path separators or dots and be at least 20 characters long."
            )

        raise TypeError(f"Unsupported media source: {type(source).__name__}")

    def _add_upload(
        self,
        data: dict[str, Any],
        files: dict[str, Any],
        stack: ExitStack,
        field: str,
        source: MediaSource,
        file_name: str | None,
        default_name: str,
        default_mime: str | None = None,
    ) -> None:
        resolved = self._resolve_source(source, file_name, default_name, default_mime)
        if resolved[0] == "field":
            data[field] = resolved[1]
            return

        _, name, payload, mime, closer = resolved
        if closer is not None:
            stack.callback(closer)
        files[field] = (name, payload, mime)

    def _normalize_single_item(
        self, item: MediaGroupItem
    ) -> tuple[MediaSource, str | None, dict[str, Any]]:
        if isinstance(item, dict):
            item = dict(item)
            source = item.pop("media", None)
            name = item.pop("file_name", None)
            item.pop("type", None)
            if source is None:
                raise ValueError("The media item must contain a media source.")
            extra = {key: value for key, value in item.items() if key in _SINGLE_ITEM_EXTRA_KEYS}
            return cast(MediaSource, source), cast(str | None, name), extra
        if isinstance(item, (tuple, list)) and len(item) == 2:
            return cast(MediaSource, item[0]), cast(str | None, item[1]), {}
        return cast(MediaSource, item), None, {}

    def _send_media_group(
        self,
        mtype: str,
        media: Sequence[MediaGroupItem],
        file_names: Sequence[str] | None,
        base_data: dict[str, Any],
        caption: str | None,
        caption_extra: dict[str, Any] | None,
        default_name: str,
        default_mime: str | None,
    ) -> list[Any]:
        items = list(media)
        results: list[Any] = []

        for start in range(0, len(items), 10):
            chunk = items[start : start + 10]
            with ExitStack() as stack:
                files: dict[str, Any] = {}
                group: list[dict[str, Any]] = []

                for index, item in enumerate(chunk):
                    field = f"file{index + 1}"
                    entry: dict[str, Any] = {"type": mtype}
                    source: Any = item
                    item_name: str | None = None
                    item_caption: str | None = None
                    extra: dict[str, Any] = {}

                    if isinstance(item, dict):
                        item = dict(item)
                        source = item.pop("media", None)
                        if "type" in item:
                            entry["type"] = item.pop("type")
                        item_name = item.pop("file_name", None)
                        item_caption = item.pop("caption", None)
                        extra = item
                    elif isinstance(item, (tuple, list)) and len(item) == 2:
                        source, item_name = item

                    if source is None:
                        raise ValueError("Every media group item must contain a media source.")
                    if file_names is not None and start + index < len(file_names):
                        item_name = item_name or file_names[start + index]

                    resolved = self._resolve_source(source, item_name, default_name, default_mime)
                    if resolved[0] == "field":
                        entry["media"] = resolved[1]
                    else:
                        _, name, payload, mime, closer = resolved
                        if closer is not None:
                            stack.callback(closer)
                        files[field] = (name, payload, mime)
                        entry["media"] = f"attach://{field}"

                    entry.update(extra)
                    if isinstance(entry.get("caption_entities"), str):
                        try:
                            entry["caption_entities"] = json.loads(entry["caption_entities"])
                        except json.JSONDecodeError:
                            pass
                    if item_caption is not None:
                        entry["caption"] = item_caption
                    group.append(entry)

                if caption and "caption" not in group[0]:
                    group[0]["caption"] = caption
                    if caption_extra:
                        for key, value in _clean(caption_extra).items():
                            if key == "caption_entities" and isinstance(value, str):
                                try:
                                    value = json.loads(value)
                                except json.JSONDecodeError:
                                    pass
                            group[0].setdefault(key, value)

                data = dict(base_data)
                data["media"] = json.dumps(group, ensure_ascii=False)
                result = self._call("sendMediaGroup", data, files)

            parsed = self._parse_result(result)
            if isinstance(parsed, list):
                results.extend(parsed)
            else:
                results.append(parsed)

        return results

    def is_url(self, url: Any) -> bool:
        """Check if the given value is an HTTP(S) URL."""
        if not isinstance(url, str):
            return False
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def convert_timestamp(self, timestamp: int | float | str | None):
        """
        Converts a Unix timestamp to the user's local time in the format 'dd/mm/YYYY HH:MM:SS'.

        Parameters:
        - timestamp: Unix timestamp to be converted.

        Returns:
        - Formatted local time string.

        Example:

        for message in bot.poll_updates():
            print(f'Date: {bot.convert_timestamp(message.date)}')

        # Output: '23/02/2022 10:19:00'
        """
        if timestamp is None:
            return None
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        dt = datetime.fromtimestamp(timestamp, timezone.utc)
        return dt.astimezone().strftime("%d/%m/%Y %H:%M:%S")

    def get_updates(
        self,
        long_poll_timeout: int = 30,
        allowed_updates: Sequence[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Gets the latest updates from the /getUpdates endpoint.

        Uses Telegram server-side long-polling (timeout param) so the
        server holds the connection open for up to `long_poll_timeout`
        seconds before returning an empty list — much more efficient than
        tight short-polling loops.

        The client-side requests timeout is set slightly higher than the
        Telegram timeout so we never hang indefinitely on a dead connection.
        """
        updates = self._fetch_updates(
            self.last_update_id, long_poll_timeout, allowed_updates, limit
        )
        if updates:
            self.last_update_id = updates[-1].get("update_id", self.last_update_id)
        return updates

    def _fetch_updates(
        self,
        last_update_id: int | None,
        long_poll_timeout: int,
        allowed_updates: Sequence[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        data: dict[str, Any] = {"timeout": long_poll_timeout, "limit": limit}
        if last_update_id is not None:
            data["offset"] = last_update_id + 1
        if allowed_updates is not None:
            data["allowed_updates"] = _json_param(list(allowed_updates))

        result = self._call(
            "getUpdates",
            data,
            timeout=self._long_poll_timeout(long_poll_timeout),
        )
        if not isinstance(result, list):
            return []
        return [update for update in result if isinstance(update, dict)]

    def poll_updates(
        self,
        polling_interval: int = 2,
        long_poll_timeout: int = 30,
        max_retries: int | None = None,
        allowed_updates: Sequence[str] | None = None,
        limit: int = 100,
    ):
        """
        Continuously polls for the latest updates and yields the processed results.

        Parameters:
        - polling_interval: Short sleep between polls when NOT using long-polling
          (unused when long_poll_timeout > 0).
        - long_poll_timeout: Seconds Telegram holds the connection open server-side.
          Set to 0 to disable long-polling and revert to short-polling.
        - max_retries: Maximum number of consecutive connection retries
          before giving up (None = unlimited).
        - allowed_updates: Optional list of update types Telegram should deliver.
        - limit: Maximum number of updates to fetch per request (1-100).

        Yields:
        - Processed updates using the parser.

        Example:
        for message in bot.poll_updates():
            print(f'Received Message: {message.text}')
        """
        retries = 0
        backoff_interval = max(float(polling_interval), 0.5)
        last_error: Exception | None = None

        while max_retries is None or retries < max_retries:
            try:
                updates = self._fetch_updates(
                    self.last_update_id, long_poll_timeout, allowed_updates, limit
                )
            except TelegramTimeoutError:
                # The long-poll window expired, or the network was briefly slow.
                # This is not a real error — loop again without incrementing retries.
                continue
            except TelegramNetworkError as exc:
                retries += 1
                last_error = exc
                logger.warning(
                    "Connection error: %s. Retry %s/%s.",
                    exc,
                    retries,
                    max_retries if max_retries is not None else "∞",
                )
                time.sleep(backoff_interval + random.uniform(0, 0.5))
                backoff_interval = min(backoff_interval * 2, 60.0)
                continue
            except TelegramAPIError as exc:
                if (
                    exc.error_code is not None
                    and exc.error_code < 500
                    and exc.error_code != 429
                ):
                    raise
                retries += 1
                last_error = exc
                logger.warning(
                    "Telegram error: %s. Retry %s/%s.",
                    exc,
                    retries,
                    max_retries if max_retries is not None else "∞",
                )
                time.sleep(backoff_interval + random.uniform(0, 0.5))
                backoff_interval = min(backoff_interval * 2, 60.0)
                continue

            retries = 0
            backoff_interval = max(float(polling_interval), 0.5)

            if not updates:
                if long_poll_timeout == 0:
                    time.sleep(polling_interval)
                continue

            for update in updates:
                update_id = update.get("update_id")
                try:
                    parsed = self.parser.process(update)
                except Exception:
                    logger.exception(
                        "Failed to parse update %s; skipping it.", update_id
                    )
                    if update_id is not None:
                        self.last_update_id = update_id
                    continue

                yield parsed

                if update_id is not None:
                    self.last_update_id = update_id

        if last_error is not None:
            raise TelegramNetworkError(
                "poll_updates",
                description=f"Maximum retry limit reached: {last_error}",
            )

    def get_me(self) -> dict[str, Any]:
        """Returns basic information about the bot."""
        return self._call("getMe")

    def get_chat(self, chat_id: ChatId) -> dict[str, Any]:
        """Returns information about a chat."""
        return self._call("getChat", {"chat_id": chat_id})

    def get_file(self, file_id: str) -> dict[str, Any]:
        """Returns basic information about a file and a temporary download path."""
        return self._call("getFile", {"file_id": file_id})

    def download_attachment(
        self,
        file_id: str,
        file_name: str | None = None,
        download_path: str | None = None,
        as_bytes: bool = False,
        chunk_size: int = 64 * 1024,
        timeout: float | tuple[float, float] | None = None,
    ) -> str | bytes:
        """
        Downloads an attachment identified by its file ID from Telegram.

        Parameters:
        - file_id: Identifier for this file, which can be used to download or reuse the file.
        - file_name: However you wish to name the file. If omitted, Telegram's name is used.
        - download_path: Directory where the file should be saved. Defaults to the current directory.
        - as_bytes: Return the file content in RAM as bytes instead of writing it to disk.
        - chunk_size: Number of bytes to read per chunk while streaming.
        - timeout: Optional requests timeout.

        Returns:
        - The full saved path when writing to disk, or bytes when as_bytes=True.

        Example:
        bot.download_attachment(file_id='123456789', file_name='example_file', download_path='/path/to/download/')
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        file_info = self.get_file(file_id)
        file_path = file_info.get("file_path") if isinstance(file_info, dict) else None
        if not file_path:
            raise TelegramAPIError(
                "getFile", description=f"No file_path returned for file_id {file_id!r}."
            )

        download_url = f"{self.base_download_url}/{file_path}"
        timeout = timeout or self.timeout

        if as_bytes:
            bytes_response = self._download_response(download_url, timeout)
            try:
                buffer = bytearray()
                for chunk in bytes_response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        buffer.extend(chunk)
                return bytes(buffer)
            except requests.RequestException as exc:
                raise TelegramNetworkError(
                    "download", description=self._redact(f"Download failed: {exc}")
                ) from exc
            finally:
                bytes_response.close()

        directory = download_path or self.current_directory
        os.makedirs(directory, exist_ok=True)

        server_name = os.path.basename(file_path)
        name = _safe_filename(file_name if file_name else server_name)
        if not os.path.splitext(name)[1]:
            server_extension = os.path.splitext(file_path)[1]
            if server_extension:
                name += server_extension

        final_path = os.path.join(directory, name)
        part_path = f"{final_path}.part"

        response: requests.Response | None = None
        try:
            response = self._download_response(download_url, timeout)
            with open(part_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
            os.replace(part_path, final_path)
            return final_path
        except requests.RequestException as exc:
            raise TelegramNetworkError(
                "download", description=self._redact(f"Download failed: {exc}")
            ) from exc
        finally:
            if response is not None:
                response.close()
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except OSError:
                    pass

    def _download_response(
        self, url: str, timeout: float | tuple[float, float]
    ) -> requests.Response:
        attempts = 0
        while True:
            try:
                response = self.session.get(url, stream=True, timeout=timeout)
            except requests.Timeout as exc:
                raise TelegramTimeoutError(
                    "download", description=self._redact(f"Download timed out: {exc}")
                ) from exc
            except requests.RequestException as exc:
                raise TelegramNetworkError(
                    "download", description=self._redact(f"Download failed: {exc}")
                ) from exc

            if response.status_code == 429 and attempts < self.max_flood_retries:
                retry_after = 1
                try:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                except (TypeError, ValueError):
                    pass
                response.close()
                wait = min(float(retry_after), 60.0)
                logger.warning("Download was rate limited; retrying in %.1f seconds.", wait)
                time.sleep(wait)
                attempts += 1
                continue

            if response.status_code >= 500 and attempts < self.max_flood_retries:
                response.close()
                wait = min(2.0**attempts, 60.0)
                logger.warning("Download server error; retrying in %.1f seconds.", wait)
                time.sleep(wait)
                attempts += 1
                continue

            try:
                response.raise_for_status()
            except requests.RequestException as exc:
                response.close()
                raise TelegramNetworkError(
                    "download", description=self._redact(f"Download failed: {exc}")
                ) from exc
            return response

    def send_message(
        self,
        chat_id: ChatId,
        text: str,
        reply_to_message_id: int | None = None,
        parse_mode: ParseMode | None = None,
        no_webpage: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
        entities: list[dict[str, Any]] | str | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        message_thread_id: int | None = None,
        allow_sending_without_reply: bool | None = None,
        link_preview_options: dict[str, Any] | str | None = None,
    ):
        """
        Sends a text message to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - text: The text of the message to be sent.
        - reply_to_message_id: The message ID to which this message will reply to.
        - parse_mode: Mode for parsing entities in the message text. 'Markdown', 'MarkdownV2', or 'HTML'.
        - no_webpage: Set this flag to disable the generation of the webpage preview.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.
        - entities: List of special entities that appear in the message text.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - message_thread_id: Identifier of the message thread for forum topics.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.
        - link_preview_options: Options for the link preview.

        Example:
        bot.send_message(chat_id='ID or @channel', text='*Hello, World!*', parse_mode='Markdown', no_webpage=True, disable_notification=True)
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_to_message_id": reply_to_message_id,
                "parse_mode": parse_mode,
                "entities": _json_param(entities),
                "disable_notification": disable_notification,
                "protect_content": protect_content,
                "reply_markup": _json_param(reply_markup),
                "message_thread_id": message_thread_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "link_preview_options": _json_param(link_preview_options),
            }
        )
        if no_webpage and "link_preview_options" not in data:
            data["disable_web_page_preview"] = True
        return self._parse_result(self._call("sendMessage", data))

    def send_contact(
        self,
        chat_id: ChatId,
        phone_number: str,
        first_name: str,
        last_name: str | None = None,
        vcard: str | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
    ):
        """
        Sends a contact to the specified chat or channel.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - phone_number: Contact's phone number.
        - first_name: Contact's first name.
        - last_name: Contact's last name.
        - vcard: Additional data about the contact in the form of a vCard, 0-2048 bytes.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.
        - reply_to_message_id: The message ID to which this message will reply to.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.

        Example:
        bot.send_contact(chat_id='ID or @name', phone_number='+1234567890', first_name='John', last_name='Doe', vcard='vCardData', disable_notification=True, protect_content=True)
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name,
                "vcard": vcard,
                "disable_notification": disable_notification,
                "protect_content": protect_content,
                "reply_to_message_id": reply_to_message_id,
                "message_thread_id": message_thread_id,
                "reply_markup": _json_param(reply_markup),
            }
        )
        return self._parse_result(self._call("sendContact", data))

    def send_location(
        self,
        chat_id: ChatId,
        latitude: float,
        longitude: float,
        horizontal_accuracy: float | None = None,
        live_period: int | None = None,
        heading: int | None = None,
        proximity_alert_radius: int | None = None,
        reply_to_message_id: int | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a location to the specified chat or channel.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - latitude: Latitude of the location.
        - longitude: Longitude of the location.
        - horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500.
        - live_period: Period in seconds for which the location will be updated; should be between 60 and 86400.
        - heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        - proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - reply_to_message_id: Quotes and replies to the message ID.
        - protect_content: Protects the contents of the sent message from forwarding and saving.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_location(chat_id='ID or @channel', latitude=37.7749, longitude=-122.4194, horizontal_accuracy=50, live_period=300, heading=90, proximity_alert_radius=1000, disable_notification=True, reply_to_message_id=123456789)
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "latitude": latitude,
                "longitude": longitude,
                "horizontal_accuracy": horizontal_accuracy,
                "live_period": live_period,
                "heading": heading,
                "proximity_alert_radius": proximity_alert_radius,
                "reply_to_message_id": reply_to_message_id,
                "disable_notification": disable_notification,
                "protect_content": protect_content,
                "message_thread_id": message_thread_id,
                "reply_markup": _json_param(reply_markup),
                "allow_sending_without_reply": allow_sending_without_reply,
            }
        )
        return self._parse_result(self._call("sendLocation", data))

    def send_voice(
        self,
        chat_id: ChatId,
        voice: MediaSource,
        duration: int | None = None,
        caption: str | None = None,
        parse_mode: ParseMode | None = None,
        reply_to_message_id: int | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        byte: bool = False,
        file_name: str | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a voice message to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - voice: Path to the voice file, bytes, a file-like object, an HTTP URL, or a file_id.
        - duration: Duration of the voice message in seconds. If the file you uploaded is 10 seconds long, and you enter 5 as the duration, only the first 5 seconds will be sent.
        - caption: Voice message caption, 0-1024 characters after entities parsing.
        - parse_mode: Mode for parsing entities in the voice caption. 'Markdown', 'MarkdownV2', or 'HTML'.
        - reply_to_message_id: The message ID to which this voice message will reply to.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent voice message from forwarding and saving.
        - byte: Kept for backwards compatibility. Bytes are detected automatically.
        - file_name: Name shown to users when uploading from memory.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - caption_entities: List of special entities that appear in the caption.
        - show_caption_above_media: Pass True to show the caption above the media.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_voice(chat_id='ID or @channel', voice='/path/to/voice.ogg', duration=10, caption='Check out this voice message!', reply_to_message_id=123456789, disable_notification=True)
        """
        if isinstance(voice, list):
            raise TypeError("send_voice does not support lists of files.")

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "duration": duration,
                    "caption": caption,
                    "parse_mode": parse_mode,
                    "reply_to_message_id": reply_to_message_id,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "caption_entities": _json_param(caption_entities),
                    "show_caption_above_media": show_caption_above_media,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            files: dict[str, Any] = {}
            self._add_upload(data, files, stack, "voice", voice, file_name, "voice.ogg", "audio/ogg")
            result = self._call("sendVoice", data, files)

        return self._parse_result(result)

    def send_audio(
        self,
        chat_id: ChatId,
        audio: MediaSource | list[MediaGroupItem],
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        parse_mode: ParseMode | None = None,
        byte: bool = False,
        duration: int | None = None,
        performer: str | None = None,
        title: str | None = None,
        thumbnail: MediaSource | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        file_name: str | None = None,
        thumbnail_file_name: str | None = None,
        file_names: Sequence[str] | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends an audio file or a list of audio files to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - audio: Path, bytes, file-like object, HTTP URL, file_id, or a list of those.
        - caption: Caption for the audio file, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this audio message will reply to.
        - parse_mode: Mode for parsing entities in the audio caption. 'Markdown', 'MarkdownV2', or 'HTML'.
        - byte: Kept for backwards compatibility. Bytes are detected automatically.
        - duration: Duration of the audio file in seconds.
        - performer: Performer of the audio file.
        - title: Title of the audio file.
        - thumbnail: Path, bytes, URL, or file_id of a thumbnail image for the audio file.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent audio message from forwarding and saving.
        - file_name: Name shown to users when uploading from memory.
        - thumbnail_file_name: Name of the thumbnail when uploading from memory.
        - file_names: Names for list uploads, in the same order as `audio`.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - caption_entities: List of special entities that appear in the caption.
        - show_caption_above_media: Pass True to show the caption above the media.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_audio(chat_id='@example_channel', audio='/path/to/audio.mp3', caption='Check out this audio!', reply_to_message_id=123456789, duration=180, performer='Artist', title='Song Title', disable_notification=False)
        """
        if isinstance(audio, list) and len(audio) > 1:
            base_data = _clean(
                {
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            caption_extra = _clean(
                {
                    "parse_mode": parse_mode,
                    "caption_entities": caption_entities,
                    "show_caption_above_media": show_caption_above_media,
                }
            )
            return self._send_media_group(
                "audio",
                audio,
                file_names,
                base_data,
                caption,
                caption_extra,
                "audio.mp3",
                "audio/mpeg",
            )

        if isinstance(audio, list) and not audio:
            raise ValueError("audio list must not be empty.")
        single_audio = audio[0] if isinstance(audio, list) else audio
        single_audio, item_name, item_extra = self._normalize_single_item(single_audio)
        file_name = file_name or item_name or (file_names[0] if file_names else None)

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "caption": caption,
                    "reply_to_message_id": reply_to_message_id,
                    "parse_mode": parse_mode,
                    "duration": duration,
                    "performer": performer,
                    "title": title,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "caption_entities": _json_param(caption_entities),
                    "show_caption_above_media": show_caption_above_media,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            data.update(_clean(item_extra))
            files: dict[str, Any] = {}
            self._add_upload(data, files, stack, "audio", single_audio, file_name, "audio.mp3", "audio/mpeg")
            if thumbnail is not None:
                self._add_upload(
                    data,
                    files,
                    stack,
                    "thumbnail",
                    thumbnail,
                    thumbnail_file_name,
                    "thumbnail.jpg",
                    "image/jpeg",
                )
            result = self._call("sendAudio", data, files)

        return self._parse_result(result)

    def send_video(
        self,
        chat_id: ChatId,
        video: MediaSource | list[MediaGroupItem],
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        parse_mode: ParseMode | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        has_spoiler: bool = False,
        duration: int | None = None,
        width: int | None = None,
        height: int | None = None,
        thumbnail: MediaSource | None = None,
        supports_streaming: bool = False,
        byte: bool = False,
        file_name: str | None = None,
        thumbnail_file_name: str | None = None,
        file_names: Sequence[str] | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a video or a list of videos to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - video: Path, bytes, file-like object, HTTP URL, file_id, or a list of those.
        - caption: Caption for the video, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this video message will reply to.
        - parse_mode: Mode for parsing entities in the video caption. 'Markdown', 'MarkdownV2', or 'HTML'.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent video message from forwarding and saving.
        - has_spoiler: Indicates whether the video has spoiler content.
        - duration: Duration of the video in seconds.
        - width: Width of the video in pixels.
        - height: Height of the video in pixels.
        - thumbnail: Path, bytes, URL, or file_id of a thumbnail image for the video.
        - supports_streaming: Pass True if the uploaded video is suitable for streaming.
        - byte: Kept for backwards compatibility. Bytes are detected automatically.
        - file_name: Name shown to users when uploading from memory.
        - thumbnail_file_name: Name of the thumbnail when uploading from memory.
        - file_names: Names for list uploads, in the same order as `video`.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - caption_entities: List of special entities that appear in the caption.
        - show_caption_above_media: Pass True to show the caption above the media.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_video(chat_id='@example_channel', video='/path/to/video.mp4', caption='Check out this video!', reply_to_message_id=123456789, has_spoiler=True)
        """
        if isinstance(video, list) and len(video) > 1:
            base_data = _clean(
                {
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            caption_extra = _clean(
                {
                    "parse_mode": parse_mode,
                    "caption_entities": caption_entities,
                    "show_caption_above_media": show_caption_above_media,
                }
            )
            return self._send_media_group(
                "video",
                video,
                file_names,
                base_data,
                caption,
                caption_extra,
                "video.mp4",
                "video/mp4",
            )

        if isinstance(video, list) and not video:
            raise ValueError("video list must not be empty.")
        single_video = video[0] if isinstance(video, list) else video
        single_video, item_name, item_extra = self._normalize_single_item(single_video)
        file_name = file_name or item_name or (file_names[0] if file_names else None)

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "caption": caption,
                    "reply_to_message_id": reply_to_message_id,
                    "parse_mode": parse_mode,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "has_spoiler": has_spoiler,
                    "duration": duration,
                    "width": width,
                    "height": height,
                    "supports_streaming": supports_streaming,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "caption_entities": _json_param(caption_entities),
                    "show_caption_above_media": show_caption_above_media,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            data.update(_clean(item_extra))
            files: dict[str, Any] = {}
            self._add_upload(data, files, stack, "video", single_video, file_name, "video.mp4", "video/mp4")
            if thumbnail is not None:
                self._add_upload(
                    data,
                    files,
                    stack,
                    "thumbnail",
                    thumbnail,
                    thumbnail_file_name,
                    "thumbnail.jpg",
                    "image/jpeg",
                )
            result = self._call("sendVideo", data, files)

        return self._parse_result(result)

    def send_photo(
        self,
        chat_id: ChatId,
        photo: MediaSource | list[MediaGroupItem],
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        parse_mode: ParseMode | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        has_spoiler: bool = False,
        byte: bool = False,
        file_name: str | None = None,
        file_names: Sequence[str] | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a photo or a list of photos to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - photo: Path, bytes, file-like object, HTTP URL, file_id, or a list of those.
        - caption: Photo caption, 0-1024 characters after entities parsing.
        - reply_to_message_id: The message ID to which this photo message will reply to.
        - parse_mode: Mode for parsing entities in the photo caption. 'Markdown', 'MarkdownV2', or 'HTML'.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent photo message from forwarding and saving.
        - has_spoiler: Pass True if the photo needs to be covered with a spoiler animation.
        - byte: Kept for backwards compatibility. Bytes are detected automatically.
        - file_name: Name shown to users when uploading from memory.
        - file_names: Names for list uploads, in the same order as `photo`.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - caption_entities: List of special entities that appear in the caption.
        - show_caption_above_media: Pass True to show the caption above the media.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_photo(chat_id='@example_channel', photo='/path/to/photo.jpg', caption='Check out this photo!', reply_to_message_id=123456789, has_spoiler=True)
        """
        if isinstance(photo, list) and len(photo) > 1:
            base_data = _clean(
                {
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            caption_extra = _clean(
                {
                    "parse_mode": parse_mode,
                    "caption_entities": caption_entities,
                    "show_caption_above_media": show_caption_above_media,
                }
            )
            return self._send_media_group(
                "photo",
                photo,
                file_names,
                base_data,
                caption,
                caption_extra,
                "photo.jpg",
                "image/jpeg",
            )

        if isinstance(photo, list) and not photo:
            raise ValueError("photo list must not be empty.")
        single_photo = photo[0] if isinstance(photo, list) else photo
        single_photo, item_name, item_extra = self._normalize_single_item(single_photo)
        file_name = file_name or item_name or (file_names[0] if file_names else None)

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "caption": caption,
                    "reply_to_message_id": reply_to_message_id,
                    "parse_mode": parse_mode,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "has_spoiler": has_spoiler,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "caption_entities": _json_param(caption_entities),
                    "show_caption_above_media": show_caption_above_media,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            data.update(_clean(item_extra))
            files: dict[str, Any] = {}
            self._add_upload(data, files, stack, "photo", single_photo, file_name, "photo.jpg", "image/jpeg")
            result = self._call("sendPhoto", data, files)

        return self._parse_result(result)

    def send_document(
        self,
        chat_id: ChatId,
        document: MediaSource | list[MediaGroupItem],
        caption: str | None = None,
        thumbnail: MediaSource | None = None,
        parse_mode: ParseMode | None = None,
        byte: bool = False,
        disable_content_type_detection: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int | None = None,
        file_name: str | None = None,
        thumbnail_file_name: str | None = None,
        file_names: Sequence[str] | None = None,
        message_thread_id: int | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a document or a list of documents to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - document: Path, bytes, file-like object, HTTP URL, file_id, or a list of those.
        - caption: Caption for the document, 0-1024 characters after entities parsing.
        - thumbnail: Path, bytes, URL, or file_id of a thumbnail image for the document.
        - parse_mode: Mode for parsing entities in the document caption. 'Markdown', 'MarkdownV2', or 'HTML'.
        - byte: Kept for backwards compatibility. Bytes are detected automatically.
        - disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent document message from forwarding and saving.
        - reply_to_message_id: The message ID to which this document message will reply to.
        - file_name: Name shown to users when uploading from memory.
        - thumbnail_file_name: Name of the thumbnail when uploading from memory.
        - file_names: Names for list uploads, in the same order as `document`.
        - message_thread_id: Identifier of the message thread for forum topics.
        - caption_entities: List of special entities that appear in the caption.
        - show_caption_above_media: Pass True to show the caption above the media.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_document(chat_id='@example_channel', document='/path/to/document.pdf', caption='Check out this document!', thumbnail='/path/to/thumbnail.jpg', disable_content_type_detection=False)
        """
        if isinstance(document, list) and len(document) > 1:
            base_data = _clean(
                {
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            caption_extra = _clean(
                {
                    "parse_mode": parse_mode,
                    "caption_entities": caption_entities,
                    "show_caption_above_media": show_caption_above_media,
                }
            )
            return self._send_media_group(
                "document",
                document,
                file_names,
                base_data,
                caption,
                caption_extra,
                "document.bin",
                "application/octet-stream",
            )

        if isinstance(document, list) and not document:
            raise ValueError("document list must not be empty.")
        single_document = document[0] if isinstance(document, list) else document
        single_document, item_name, item_extra = self._normalize_single_item(single_document)
        file_name = file_name or item_name or (file_names[0] if file_names else None)

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": parse_mode,
                    "disable_content_type_detection": disable_content_type_detection,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "reply_to_message_id": reply_to_message_id,
                    "message_thread_id": message_thread_id,
                    "caption_entities": _json_param(caption_entities),
                    "show_caption_above_media": show_caption_above_media,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            data.update(_clean(item_extra))
            files: dict[str, Any] = {}
            self._add_upload(
                data,
                files,
                stack,
                "document",
                single_document,
                file_name,
                "document.bin",
                "application/octet-stream",
            )
            if thumbnail is not None:
                self._add_upload(
                    data,
                    files,
                    stack,
                    "thumbnail",
                    thumbnail,
                    thumbnail_file_name,
                    "thumbnail.jpg",
                    "image/jpeg",
                )
            result = self._call("sendDocument", data, files)

        return self._parse_result(result)

    def send_sticker(
        self,
        chat_id: ChatId,
        sticker: MediaSource,
        emoji: str | None = None,
        reply_to_message_id: int | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        byte: bool = False,
        file_name: str | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a sticker to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - sticker: Path, bytes, file-like object, HTTP URL, or file_id.
        - emoji: Emoji associated with the sticker; only for just uploaded stickers.
        - reply_to_message_id: The message ID to which this message will reply to.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent message from forwarding and saving.
        - byte: Kept for backwards compatibility. Bytes are detected automatically.
        - file_name: Name shown to users when uploading from memory.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_sticker(chat_id='ID or @channel', sticker='filepath', disable_notification=True)
        """
        if isinstance(sticker, list):
            raise TypeError("send_sticker does not support lists of files.")

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "emoji": emoji,
                    "reply_to_message_id": reply_to_message_id,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            files: dict[str, Any] = {}
            self._add_upload(data, files, stack, "sticker", sticker, file_name, "sticker.webp", "image/webp")
            result = self._call("sendSticker", data, files)

        return self._parse_result(result)

    def send_animation(
        self,
        chat_id: ChatId,
        animation: MediaSource,
        caption: str | None = None,
        parse_mode: ParseMode | None = None,
        duration: int | None = None,
        width: int | None = None,
        height: int | None = None,
        thumbnail: MediaSource | None = None,
        has_spoiler: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int | None = None,
        file_name: str | None = None,
        thumbnail_file_name: str | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends an animation (GIF or muted video) to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - animation: Path, bytes, file-like object, HTTP URL, or file_id.
        - caption: Caption for the animation, 0-1024 characters after entities parsing.
        - parse_mode: Mode for parsing entities in the animation caption. 'Markdown', 'MarkdownV2', or 'HTML'.
        - duration: Duration of the animation in seconds.
        - width: Width of the animation in pixels.
        - height: Height of the animation in pixels.
        - thumbnail: Path, bytes, URL, or file_id of a thumbnail image for the animation.
        - has_spoiler: Indicates whether the animation has spoiler content.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent animation from forwarding and saving.
        - reply_to_message_id: The message ID to which this message will reply to.
        - file_name: Name shown to users when uploading from memory.
        - thumbnail_file_name: Name of the thumbnail when uploading from memory.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - caption_entities: List of special entities that appear in the caption.
        - show_caption_above_media: Pass True to show the caption above the media.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_animation(chat_id='ID or @channel', animation='/path/to/animation.mp4', caption='Look at this!')
        """
        if isinstance(animation, list):
            raise TypeError("send_animation does not support lists of files.")

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": parse_mode,
                    "duration": duration,
                    "width": width,
                    "height": height,
                    "has_spoiler": has_spoiler,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "reply_to_message_id": reply_to_message_id,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "caption_entities": _json_param(caption_entities),
                    "show_caption_above_media": show_caption_above_media,
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            files: dict[str, Any] = {}
            self._add_upload(
                data,
                files,
                stack,
                "animation",
                animation,
                file_name,
                "animation.mp4",
                "video/mp4",
            )
            if thumbnail is not None:
                self._add_upload(
                    data,
                    files,
                    stack,
                    "thumbnail",
                    thumbnail,
                    thumbnail_file_name,
                    "thumbnail.jpg",
                    "image/jpeg",
                )
            result = self._call("sendAnimation", data, files)

        return self._parse_result(result)

    def send_video_note(
        self,
        chat_id: ChatId,
        video_note: MediaSource,
        duration: int | None = None,
        length: int | None = None,
        thumbnail: MediaSource | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int | None = None,
        file_name: str | None = None,
        thumbnail_file_name: str | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        allow_sending_without_reply: bool | None = None,
    ):
        """
        Sends a round video note to the specified chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - video_note: Path, bytes, file-like object, HTTP URL, or file_id.
        - duration: Duration of the video note in seconds.
        - length: Diameter of the video note in pixels.
        - thumbnail: Path, bytes, URL, or file_id of a thumbnail image for the video note.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the sent video note from forwarding and saving.
        - reply_to_message_id: The message ID to which this message will reply to.
        - file_name: Name shown to users when uploading from memory.
        - thumbnail_file_name: Name of the thumbnail when uploading from memory.
        - message_thread_id: Identifier of the message thread for forum topics.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - allow_sending_without_reply: Pass True if the message should be sent even if the replied-to message is not found.

        Example:
        bot.send_video_note(chat_id='ID or @channel', video_note='/path/to/circle.mp4', duration=10, length=240)
        """
        if isinstance(video_note, list):
            raise TypeError("send_video_note does not support lists of files.")

        with ExitStack() as stack:
            data = _clean(
                {
                    "chat_id": chat_id,
                    "duration": duration,
                    "length": length,
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                    "reply_to_message_id": reply_to_message_id,
                    "message_thread_id": message_thread_id,
                    "reply_markup": _json_param(reply_markup),
                    "allow_sending_without_reply": allow_sending_without_reply,
                }
            )
            files: dict[str, Any] = {}
            self._add_upload(
                data,
                files,
                stack,
                "video_note",
                video_note,
                file_name,
                "video_note.mp4",
                "video/mp4",
            )
            if thumbnail is not None:
                self._add_upload(
                    data,
                    files,
                    stack,
                    "thumbnail",
                    thumbnail,
                    thumbnail_file_name,
                    "thumbnail.jpg",
                    "image/jpeg",
                )
            result = self._call("sendVideoNote", data, files)

        return self._parse_result(result)

    def send_chat_action(
        self,
        chat_id: ChatId,
        action: str,
        message_thread_id: int | None = None,
    ):
        """
        Tells the user that something is happening on the bot's side.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - action: Type of action to broadcast, for example 'typing' or 'upload_photo'.
        - message_thread_id: Identifier of the message thread for forum topics.

        Example:
        bot.send_chat_action(chat_id='ID or @channel', action='typing')
        """
        data = _clean({"chat_id": chat_id, "action": action, "message_thread_id": message_thread_id})
        return self._call("sendChatAction", data)

    def forward_message(
        self,
        chat_id: ChatId,
        from_chat_id: ChatId,
        message_id: int,
        message_thread_id: int | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
    ):
        """
        Forwards a message.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel.
        - from_chat_id: Unique identifier for the chat where the original message was sent.
        - message_id: Message identifier in the chat specified in from_chat_id.
        - message_thread_id: Identifier of the message thread for forum topics.
        - disable_notification: Sends the message silently. Users will receive a notification with no sound.
        - protect_content: Protects the contents of the forwarded message from forwarding and saving.

        Example:
        bot.forward_message(chat_id='ID', from_chat_id='ID', message_id=12345)
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
                "message_thread_id": message_thread_id,
                "disable_notification": disable_notification,
                "protect_content": protect_content,
            }
        )
        return self._parse_result(self._call("forwardMessage", data))

    def copy_message(
        self,
        chat_id: ChatId,
        from_chat_id: ChatId,
        message_id: int,
        caption: str | None = None,
        parse_mode: ParseMode | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        allow_sending_without_reply: bool | None = None,
        show_caption_above_media: bool | None = None,
    ) -> dict[str, Any]:
        """
        Copies a message of any type without a link to the original message.

        Returns Telegram's MessageId object ({"message_id": ...}).

        Example:
        bot.copy_message(chat_id='ID', from_chat_id='ID', message_id=12345, caption='Copied!')
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": _json_param(caption_entities),
                "disable_notification": disable_notification,
                "protect_content": protect_content,
                "reply_to_message_id": reply_to_message_id,
                "message_thread_id": message_thread_id,
                "reply_markup": _json_param(reply_markup),
                "allow_sending_without_reply": allow_sending_without_reply,
                "show_caption_above_media": show_caption_above_media,
            }
        )
        return self._call("copyMessage", data)

    def delete_message(self, chat_id: ChatId, message_id: int | str):
        """
        Deletes the given message from the chat.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - message_id: The ID of the message you wish to delete.

        Example:
        bot.delete_message(chat_id = 123456789, message_id = 1235)
        """
        return self._call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def delete_messages(self, chat_id: ChatId, message_ids: Sequence[int | str]):
        """
        Deletes multiple messages at once.

        Example:
        bot.delete_messages(chat_id = 123456789, message_ids = [1235, 1236])
        """
        return self._call(
            "deleteMessages",
            {"chat_id": chat_id, "message_ids": _json_param(list(message_ids))},
        )

    def edit_message(
        self,
        chat_id: ChatId,
        message_id: int | str,
        text: str,
        parse_mode: ParseMode | None = None,
        no_webpage: bool = False,
        entities: list[dict[str, Any]] | str | None = None,
        reply_markup: dict[str, Any] | str | None = None,
        link_preview_options: dict[str, Any] | str | None = None,
    ):
        """
        Updates the given message with the new text.

        Parameters:
        - chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
        - message_id: The ID of the message you wish to edit.
        - text: The new text of the message.
        - parse_mode: Mode for parsing entities in the message text. 'Markdown', 'MarkdownV2', or 'HTML'.
        - no_webpage: Set this flag to disable the generation of the webpage preview.
        - entities: List of special entities that appear in the message text.
        - reply_markup: Inline keyboard, reply keyboard, or keyboard removal markup.
        - link_preview_options: Options for the link preview.

        Example:
        bot.edit_message(chat_id = 123456789, message_id = 1235, text = 'This is an updated text!')
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": parse_mode,
                "entities": _json_param(entities),
                "reply_markup": _json_param(reply_markup),
                "link_preview_options": _json_param(link_preview_options),
            }
        )
        if no_webpage and "link_preview_options" not in data:
            data["disable_web_page_preview"] = True
        return self._parse_result(self._call("editMessageText", data))

    def edit_message_caption(
        self,
        chat_id: ChatId,
        message_id: int | str,
        caption: str | None = None,
        parse_mode: ParseMode | None = None,
        caption_entities: list[dict[str, Any]] | str | None = None,
        show_caption_above_media: bool | None = None,
        reply_markup: dict[str, Any] | str | None = None,
    ):
        """
        Edits the caption of a message.

        Example:
        bot.edit_message_caption(chat_id='ID', message_id=1235, caption='New caption')
        """
        data = _clean(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": _json_param(caption_entities),
                "show_caption_above_media": show_caption_above_media,
                "reply_markup": _json_param(reply_markup),
            }
        )
        return self._parse_result(self._call("editMessageCaption", data))

    def edit_message_reply_markup(
        self,
        chat_id: ChatId,
        message_id: int | str,
        reply_markup: dict[str, Any] | str | None = None,
    ):
        """
        Edits only the reply markup of a message.

        Example:
        bot.edit_message_reply_markup(chat_id='ID', message_id=1235, reply_markup={'inline_keyboard': []})
        """
        return self._parse_result(
            self._call(
                "editMessageReplyMarkup",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reply_markup": _json_param(reply_markup),
                },
            )
        )

    def pin_chat_message(
        self,
        chat_id: ChatId,
        message_id: int | str,
        disable_notification: bool = False,
    ):
        """
        Pins a message in a chat.

        Example:
        bot.pin_chat_message(chat_id='ID', message_id=1235, disable_notification=True)
        """
        return self._call(
            "pinChatMessage",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "disable_notification": disable_notification,
            },
        )

    def unpin_chat_message(self, chat_id: ChatId, message_id: int | str | None = None):
        """
        Unpins a message in a chat. If no message_id is given, the most recent pinned message is unpinned.

        Example:
        bot.unpin_chat_message(chat_id='ID', message_id=1235)
        """
        return self._call(
            "unpinChatMessage",
            _clean({"chat_id": chat_id, "message_id": message_id}),
        )

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
        url: str | None = None,
        cache_time: int | None = None,
    ):
        """
        Answers a callback query sent from an inline keyboard.

        Example:
        bot.answer_callback_query(callback_query_id='12345', text='Done!', show_alert=False)
        """
        data = _clean(
            {
                "callback_query_id": callback_query_id,
                "text": text,
                "show_alert": show_alert,
                "url": url,
                "cache_time": cache_time,
            }
        )
        return self._call("answerCallbackQuery", data)

    def set_webhook(
        self,
        url: str,
        certificate: MediaSource | None = None,
        ip_address: str | None = None,
        max_connections: int | None = None,
        allowed_updates: Sequence[str] | None = None,
        drop_pending_updates: bool | None = None,
        secret_token: str | None = None,
        certificate_file_name: str | None = None,
    ):
        """
        Sets a webhook for the bot.

        Parameters:
        - url: HTTPS URL to send updates to.
        - certificate: Optional public certificate, path, bytes, or file-like object.
        - ip_address: Fixed IP address for the webhook.
        - max_connections: Maximum allowed number of simultaneous HTTPS connections.
        - allowed_updates: List of update types the bot wants to receive.
        - drop_pending_updates: Pass True to drop all pending updates.
        - secret_token: Secret token for the webhook.
        - certificate_file_name: Name of the certificate when uploading from memory.

        Example:
        bot.set_webhook(url='https://example.com/webhook', allowed_updates=['message'])
        """
        with ExitStack() as stack:
            data = _clean(
                {
                    "url": url,
                    "ip_address": ip_address,
                    "max_connections": max_connections,
                    "allowed_updates": _json_param(list(allowed_updates)) if allowed_updates is not None else None,
                    "drop_pending_updates": drop_pending_updates,
                    "secret_token": secret_token,
                }
            )
            files: dict[str, Any] = {}
            if certificate is not None:
                self._add_upload(
                    data,
                    files,
                    stack,
                    "certificate",
                    certificate,
                    certificate_file_name,
                    "certificate.pem",
                    "application/x-pem-file",
                )
            result = self._call("setWebhook", data, files)

        return result

    def delete_webhook(self, drop_pending_updates: bool | None = None):
        """
        Removes the webhook integration for the bot.

        Example:
        bot.delete_webhook(drop_pending_updates=True)
        """
        return self._call(
            "deleteWebhook",
            _clean({"drop_pending_updates": drop_pending_updates}),
        )

    def get_webhook_info(self) -> dict[str, Any]:
        """
        Returns the current webhook status.

        Example:
        print(bot.get_webhook_info())
        """
        return self._call("getWebhookInfo")
