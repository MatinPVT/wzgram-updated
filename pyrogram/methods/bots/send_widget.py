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

from typing import Any, List, Optional, Union

import pyrogram
from pyrogram import types

from ._widget import parse_message, validate_data, validate_html, widget_request


class SendWidget:
    async def send_widget(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        html: str,
        chat_data: Any = None,
        allow_queries: bool = False,
        public_data: Any = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        caption: Optional[str] = None,
        is_shared: bool = False,
        message_thread_id: Optional[int] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[dict]] = None,
        show_caption_above_media: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[dict] = None,
        reply_markup: Optional[dict] = None
    ) -> "types.Message":
        """Send a self-contained HTML widget to a chat.

        .. include:: /_includes/usable-by/bots.rst

        In production, widgets can currently be sent only to private chats
        and automatically have protected content. Group chats work on the
        Telegram test server.

        Set widget_transport="mtproto" on the client for native layer 233
        calls. The default "botapi" transport uses the HTTPS bridge.

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier or username of the target chat.

            html (``str``):
                Self-contained HTML, at most 32,768 UTF-8 bytes and 4,096 bytes
                after zlib level 9 compression. Widgets cannot access the network.

            chat_data (JSON value | ``str``, *optional*):
                Initial state, at most 1,024 UTF-8 bytes. Strings are sent
                unchanged; Python JSON values are serialized. Defaults to "{}".

            allow_queries (``bool``, *optional*):
                Allow the widget to send queries to the bot. Defaults to False.

            public_data (JSON value | ``str``, *optional*):
                Public data, at most 1,024 UTF-8 bytes, available wherever
                the widget is shown. Strings are sent unchanged; Python JSON
                values are serialized. All messages with a shared widget have
                the same public data.

            width (``int``, *optional*):
                Width in logical pixels; omit if the widget must occupy the
                whole width of the message bubble. Clamped by the app to
                200-max bubble width.

            height (``int``, *optional*):
                Height in logical pixels; omit if the height isn't fixed.
                Clamped by the app to 50-600.

            caption (``str``, *optional*):
                Widget caption, 0-1,024 characters.

            is_shared (``bool``, *optional*):
                Pass True to create a shared widget, which can be sent
                again using :meth:`~pyrogram.Client.send_shared_widget`.
                Defaults to False.

            message_thread_id (``int``, *optional*):
                Target forum topic or private bot chat topic.

            parse_mode (``str``, *optional*):
                Bot API mode for parsing caption entities, such as "HTML".

            caption_entities (List of ``dict``, *optional*):
                Bot API MessageEntity dictionaries, instead of parse_mode.

            show_caption_above_media (``bool``, *optional*):
                Show the caption above the widget.

            disable_notification (``bool``, *optional*):
                Send silently.

            protect_content (``bool``, *optional*):
                Protect the message from forwarding and saving.

            allow_paid_broadcast (``bool``, *optional*):
                Allow paid broadcasts up to 1,000 messages per second.

            message_effect_id (``str``, *optional*):
                Message effect identifier, for private chats only.

            reply_parameters (``dict``, *optional*):
                Bot API ReplyParameters dictionary describing the reply.

            reply_markup (``dict``, *optional*):
                Bot API keyboard markup, keyboard removal or force reply.

        Returns:
            :obj:`~pyrogram.types.Message`: On success the sent message is returned.

        Raises:
            ValueError: If HTML or state exceeds its size limit or the bot token is missing.
        """
        payload = {
            "chat_id": chat_id,
            "html": validate_html(html),
            "chat_data": validate_data({} if chat_data is None else chat_data),
            "allow_queries": allow_queries
        }
        if public_data is not None:
            payload["public_data"] = validate_data(public_data, "public_data")
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if caption is not None:
            payload["caption"] = caption
        if is_shared:
            payload["is_shared"] = True
        payload.update({name: value for name, value in {
            "message_thread_id": message_thread_id,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "show_caption_above_media": show_caption_above_media,
            "disable_notification": disable_notification,
            "protect_content": protect_content,
            "allow_paid_broadcast": allow_paid_broadcast,
            "message_effect_id": message_effect_id,
            "reply_parameters": reply_parameters,
            "reply_markup": reply_markup
        }.items() if value is not None})
        return parse_message(self, await widget_request(self, "sendWidget", payload))
