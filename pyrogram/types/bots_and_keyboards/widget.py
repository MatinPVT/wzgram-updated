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

import json
import zlib
from typing import Any, Optional

import pyrogram
from ..object import Object


def _parse_json_value(value, name):
    """Parse a Bot API data field: a JSON string, a JSON value, or None."""
    if value is None:
        return None
    if isinstance(value, str):
        if value == "":
            return None
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


class Widget(Object):
    """An HTML widget (Bot API 10.4).

    Parameters:
        html (``str``):
            HTML code of the widget.

        id (``str``, *optional*):
            Unique identifier of the shared widget, which can be used to
            send the widget again using ``send_shared_widget``; omitted
            if the widget isn't shared.

        width (``int``, *optional*):
            Width of the widget in logical pixels; omitted if the widget
            must occupy the whole width of the message bubble.

        height (``int``, *optional*):
            Height of the widget in logical pixels; omitted if the height
            of the widget isn't fixed.

        public_data (JSON value, *optional*):
            Public data of the widget, available wherever the widget is
            shown. All messages with a shared widget have the same
            public data. The Bot API sends this as a JSON string; it is
            parsed here when possible and left as a string otherwise.

        chat_data (JSON value, *optional*):
            Data of the widget, specific to the message. Parsed the same
            way as ``public_data``.

        is_copy (``bool``, *optional*):
            Whether the MTProto widget is a forwarded copy.

        can_query (``bool``, *optional*):
            Whether the MTProto widget can query its bot.

        background_query (``bool``, *optional*):
            Whether background requests are allowed.

        public_data_hash (``int``, *optional*):
            MTProto hash of the current public data.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        html: str,
        id: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        public_data: Any = None,
        chat_data: Any = None,
        is_copy: Optional[bool] = None,
        can_query: Optional[bool] = None,
        background_query: Optional[bool] = None,
        public_data_hash: Optional[int] = None
    ):
        super().__init__(client)
        self.html = html
        self.id = id
        self.width = width
        self.height = height
        self.public_data = public_data
        self.chat_data = chat_data
        self.is_copy = is_copy
        self.can_query = can_query
        self.background_query = background_query
        self.public_data_hash = public_data_hash

    @staticmethod
    def _parse(client: "pyrogram.Client", data: dict) -> "Widget":
        if not isinstance(data, dict):
            decoder = zlib.decompressobj()
            try:
                html = decoder.decompress(data.payload, 32769)
            except zlib.error as exc:
                raise ValueError("Invalid compressed widget HTML") from exc
            if len(html) > 32768 or not decoder.eof or decoder.unused_data:
                raise ValueError("Invalid compressed widget HTML")
            return Widget(
                client=client, html=html.decode("utf-8"),
                id=str(data.widget_id) if data.widget_id is not None else None,
                width=data.width, height=data.height,
                public_data=_parse_json_value(data.public_data, "public_data"),
                chat_data=_parse_json_value(data.chat_data, "chat_data"),
                is_copy=getattr(data, "is_copy", None), can_query=getattr(data, "can_query", None),
                background_query=getattr(data, "background_query", None),
                public_data_hash=getattr(data, "public_data_hash", None)
            )
        return Widget(
            client=client,
            html=data["html"],
            id=data.get("id"),
            width=data.get("width"),
            height=data.get("height"),
            public_data=_parse_json_value(data.get("public_data"), "public_data"),
            chat_data=_parse_json_value(data.get("chat_data"), "chat_data")
        )
