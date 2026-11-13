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

from ._widget import parse_message, validate_data, widget_request


class SendSharedWidget:
    async def send_shared_widget(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        widget_id: str,
        chat_data: Any = None,
        caption: Optional[str] = None,
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
        """Send again a shared widget created by the bot.

        .. include:: /_includes/usable-by/bots.rst

        Currently, in the production environment, widgets can be sent
        only to private chats, and sent widgets automatically have
        protected content and therefore can't be forwarded.

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier or username of the target chat.

            widget_id (``str``):
                Unique identifier of the shared widget, from the ``id``
                field of a :obj:`~pyrogram.types.Widget`.

            chat_data (JSON value | ``str``, *optional*):
                Data specific to this message, at most 1,024 bytes of
                JSON. A JSON-encoded string is also accepted. Defaults
                to an empty object.

            caption (``str``, *optional*):
                Widget caption, 0-1,024 characters.

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
            ValueError: If state is invalid or the bot token is missing.
        """
        payload = {
            "chat_id": chat_id,
            "widget_id": widget_id,
            "chat_data": validate_data({} if chat_data is None else chat_data)
        }
        if caption is not None:
            payload["caption"] = caption
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
        return parse_message(self, await widget_request(self, "sendSharedWidget", payload))
