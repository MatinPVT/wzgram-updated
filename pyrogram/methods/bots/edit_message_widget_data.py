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

from typing import Any, Optional, Union

import pyrogram
from pyrogram import types

from ...types.bots_and_keyboards.widget_query import _UNSET
from ._widget import parse_message, validate_data, widget_request


class EditMessageWidgetData:
    async def edit_message_widget_data(
        self: "pyrogram.Client",
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        chat_data: Any = _UNSET,
        inline_message_id: Optional[str] = None,
        public_data: Any = _UNSET
    ) -> Union["types.Message", bool]:
        """Edit the JSON state of a widget message.

        .. include:: /_includes/usable-by/bots.rst

        Public data of a shared widget can be changed at most once per
        second.

        Parameters:
            chat_id (``int`` | ``str``, *optional*):
                Target chat. Required together with message_id for a chat message.

            message_id (``int``, *optional*):
                Identifier of the widget message in the target chat.

            chat_data (JSON value | ``str``, *optional*):
                New state, at most 1,024 UTF-8 bytes. Strings are sent unchanged;
                Python JSON values are serialized. Pass an empty string to remove
                the data; omit to leave it unchanged. Explicit None sends "null".

            inline_message_id (``str``, *optional*):
                Inline message identifier, used instead of chat_id and message_id.

            public_data (JSON value | ``str``, *optional*):
                New public data, at most 1,024 UTF-8 bytes. Strings are sent
                unchanged; Python JSON values are serialized. Pass an empty
                string to remove it; omit to leave it unchanged.

        Returns:
            :obj:`~pyrogram.types.Message` | ``bool``: The Bot API returns True.
                A message response is also parsed for compatibility.

        Raises:
            ValueError: If the target or state is invalid or the bot token is missing.
        """
        payload = {}
        if chat_data is not _UNSET:
            payload["chat_data"] = validate_data(chat_data)
        if public_data is not _UNSET:
            payload["public_data"] = validate_data(public_data, "public_data")
        if inline_message_id is not None:
            if not inline_message_id or chat_id is not None or message_id is not None:
                raise ValueError("Use inline_message_id OR chat_id and message_id")
            payload["inline_message_id"] = inline_message_id
        else:
            if chat_id is None or message_id is None:
                raise ValueError("Both chat_id and message_id are required")
            payload.update(chat_id=chat_id, message_id=message_id)
        return parse_message(self, await widget_request(self, "editMessageWidgetData", payload))
