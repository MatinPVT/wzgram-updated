#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import json
import zlib
from datetime import datetime, timezone
from urllib import error, request

import pyrogram
from pyrogram import enums, types


def validate_html(html: str) -> str:
    if not isinstance(html, str):
        raise ValueError("html must be a self-contained HTML string")
    encoded = html.encode("utf-8")
    if not encoded:
        raise ValueError("html must contain at least 1 UTF-8 byte")
    if len(encoded) > 32768:
        raise ValueError("html exceeds 32,768 UTF-8 bytes")
    if len(zlib.compress(encoded, 9)) > 4096:
        raise ValueError("html exceeds 4,096 bytes after zlib level 9 compression")
    return html


def validate_data(data, name="chat_data") -> str:
    """Return Bot API text unchanged, or serialize a Python JSON value once."""
    try:
        text = data if isinstance(data, str) else json.dumps(
            data, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        encoded = text.encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError(f"{name} must be UTF-8 text or a valid JSON value") from exc
    if len(encoded) > 1024:
        raise ValueError(f"{name} exceeds 1,024 UTF-8 bytes")
    return text


def _request(token, method, payload, test_mode=False):
    # Optional Bot API bridge; native layer 233 calls use _widget_mtproto.
    req = request.Request(
        f"https://api.telegram.org/bot{token}/{'test/' if test_mode else ''}{method}",
        data=json.dumps(payload, ensure_ascii=False, allow_nan=False,
                        separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            result = json.load(response)
    except error.HTTPError as exc:
        try:
            result = json.loads(exc.read())
        except (ValueError, UnicodeError):
            raise RuntimeError(f"Widget Bot API HTTP error {exc.code}") from None
    except error.URLError as exc:
        raise RuntimeError(f"Widget Bot API connection failed: {exc.reason}") from None
    if not result.get("ok"):
        raise RuntimeError(f"Widget Bot API error {result.get('error_code', '')}: "
                           f"{result.get('description', 'request failed')}")
    return result["result"]


async def widget_request(client: "pyrogram.Client", method: str, payload: dict):
    if getattr(client, "widget_transport", "botapi") == "mtproto":
        from ._widget_mtproto import widget_request as native_request
        return await native_request(client, method, payload)
    token = client.bot_token
    if not token:
        raise ValueError("Widget methods require the client's bot_token")
    # Run blocking standard-library HTTPS outside the asyncio event loop.
    return await asyncio.to_thread(
        _request, token, method, payload, getattr(client, "test_mode", False)
    )


def parse_user(client, data):
    if data is None:
        return None
    return types.User(
        client=client, id=data["id"], is_bot=data.get("is_bot"),
        first_name=data.get("first_name"), last_name=data.get("last_name"),
        username=data.get("username"), language_code=data.get("language_code"),
        is_premium=data.get("is_premium")
    )


def parse_chat(client, data):
    if data is None:
        return None
    return types.Chat(
        client=client, id=data["id"], type=enums.ChatType(data["type"]),
        title=data.get("title"), username=data.get("username"),
        first_name=data.get("first_name"), last_name=data.get("last_name"),
        is_forum=data.get("is_forum")
    )


def parse_message(client, data):
    if isinstance(data, (bool, types.Message)):
        return data
    message = types.Message(
        client=client, id=data["message_id"], chat=parse_chat(client, data["chat"]),
        from_user=parse_user(client, data.get("from")),
        date=datetime.fromtimestamp(data["date"], timezone.utc).replace(tzinfo=None)
        if data.get("date") is not None else None
    )
    # Parse the bridge's Bot API representation of widget media.
    if data.get("widget") is not None:
        from pyrogram.types.bots_and_keyboards.widget import Widget
        message.widget = Widget._parse(client, data["widget"])
    return message
