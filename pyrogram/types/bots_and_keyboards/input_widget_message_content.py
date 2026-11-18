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

from typing import Any, List, Optional

import pyrogram
from ..input_content.input_message_content import InputMessageContent


class InputWidgetMessageContent(InputMessageContent):
    """Content of a message with an HTML widget, to be sent as the result
    of an inline query (Bot API 10.4).

    Currently, widgets can't be sent in response to inline queries in
    the production environment. Use :meth:`to_dict` for Bot API payloads
    or ``write()`` through wzgram's native inline result methods.

    Parameters:
        html (``str``):
            HTML code of the widget, 1-32,768 bytes, at most 4,096 bytes
            after zlib level 9 compression.

        width (``int``, *optional*):
            Width in logical pixels, clamped by the app to 200-max bubble.

        height (``int``, *optional*):
            Height in logical pixels, clamped by the app to 50-600.

        public_data (JSON value | ``str``, *optional*):
            Public data, 0-1,024 UTF-8 bytes. Strings are sent unchanged;
            Python JSON values are serialized.

        chat_data (JSON value | ``str``, *optional*):
            Data specific to the message, 0-1,024 UTF-8 bytes. Strings are
            sent unchanged; Python JSON values are serialized.

        caption (``str``, *optional*):
            Widget caption, 0-1,024 characters.

        allow_queries (``bool``, *optional*):
            Pass True to allow the widget to send queries to the bot.

        is_shared (``bool``, *optional*):
            Pass True to create a shared widget. Each message sent from
            the result creates a separate shared widget.

        parse_mode (``str``, *optional*):
            Bot API mode for parsing caption entities, such as "HTML".

        caption_entities (List of ``dict``, *optional*):
            Bot API MessageEntity dictionaries, instead of parse_mode.

        show_caption_above_media (``bool``, *optional*):
            Show the caption above the widget.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        html: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        public_data: Any = None,
        chat_data: Any = None,
        caption: Optional[str] = None,
        allow_queries: Optional[bool] = None,
        is_shared: Optional[bool] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[dict]] = None,
        show_caption_above_media: Optional[bool] = None
    ):
        super().__init__()
        self._client = client
        self.html = html
        self.width = width
        self.height = height
        self.public_data = public_data
        self.chat_data = chat_data
        self.caption = caption
        self.allow_queries = allow_queries
        self.is_shared = is_shared
        self.parse_mode = parse_mode
        self.caption_entities = caption_entities
        self.show_caption_above_media = show_caption_above_media

    async def write(self, client: "pyrogram.Client", reply_markup=None):
        from pyrogram import raw
        from ...methods.bots._widget_mtproto import caption, markup
        payload = self.to_dict()
        return raw.types.InputBotInlineMessageWidget(
            html=payload["html"], width=payload.get("width") or 0, height=payload.get("height") or 0,
            public_data=payload.get("public_data"), chat_data=payload.get("chat_data"),
            allow_queries=payload.get("allow_queries"), shared_widget=payload.get("is_shared"),
            invert_media=payload.get("show_caption_above_media"),
            reply_markup=await markup(client, reply_markup), **await caption(client, payload)
        )

    def to_dict(self) -> dict:
        from ...methods.bots._widget import validate_data, validate_html

        result = {"html": validate_html(self.html)}
        if self.width is not None:
            result["width"] = self.width
        if self.height is not None:
            result["height"] = self.height
        if self.public_data is not None:
            result["public_data"] = validate_data(self.public_data, "public_data")
        if self.chat_data is not None:
            result["chat_data"] = validate_data(self.chat_data)
        if self.caption is not None:
            result["caption"] = self.caption
        if self.allow_queries is not None:
            result["allow_queries"] = self.allow_queries
        if self.is_shared is not None:
            result["is_shared"] = self.is_shared
        if self.parse_mode is not None:
            result["parse_mode"] = self.parse_mode
        if self.caption_entities is not None:
            result["caption_entities"] = self.caption_entities
        if self.show_caption_above_media is not None:
            result["show_caption_above_media"] = self.show_caption_above_media
        return result


class InputSharedWidgetMessageContent(InputMessageContent):
    """Content of a message with a shared widget, to be sent as the result
    of an inline query (Bot API 10.4).

    Currently, widgets can't be sent in response to inline queries in
    the production environment. See :obj:`InputWidgetMessageContent`
    for the same limitation.

    Parameters:
        widget_id (``str``):
            Unique identifier of the shared widget created by the bot.

        chat_data (JSON value | ``str``, *optional*):
            Data specific to the message, 0-1,024 UTF-8 bytes. Strings are
            sent unchanged; Python JSON values are serialized.

        caption (``str``, *optional*):
            Widget caption, 0-1,024 characters.

        parse_mode (``str``, *optional*):
            Bot API mode for parsing caption entities, such as "HTML".

        caption_entities (List of ``dict``, *optional*):
            Bot API MessageEntity dictionaries, instead of parse_mode.

        show_caption_above_media (``bool``, *optional*):
            Show the caption above the widget.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        widget_id: str,
        chat_data: Any = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[dict]] = None,
        show_caption_above_media: Optional[bool] = None
    ):
        super().__init__()
        self._client = client
        self.widget_id = widget_id
        self.chat_data = chat_data
        self.caption = caption
        self.parse_mode = parse_mode
        self.caption_entities = caption_entities
        self.show_caption_above_media = show_caption_above_media

    async def write(self, client: "pyrogram.Client", reply_markup=None):
        from pyrogram import raw
        from ...methods.bots._widget_mtproto import caption, markup
        payload = self.to_dict()
        return raw.types.InputBotInlineMessageWidgetId(
            widget_id=int(self.widget_id), chat_data=payload.get("chat_data"),
            invert_media=payload.get("show_caption_above_media"),
            reply_markup=await markup(client, reply_markup), **await caption(client, payload)
        )

    def to_dict(self) -> dict:
        from ...methods.bots._widget import validate_data

        result = {"widget_id": self.widget_id}
        if self.chat_data is not None:
            result["chat_data"] = validate_data(self.chat_data)
        if self.caption is not None:
            result["caption"] = self.caption
        if self.parse_mode is not None:
            result["parse_mode"] = self.parse_mode
        if self.caption_entities is not None:
            result["caption_entities"] = self.caption_entities
        if self.show_caption_above_media is not None:
            result["show_caption_above_media"] = self.show_caption_above_media
        return result
