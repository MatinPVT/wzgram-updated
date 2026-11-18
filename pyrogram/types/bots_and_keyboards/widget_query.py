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

from typing import Any, List, Match, Optional, Union

import pyrogram
from pyrogram import types
from ..object import Object
from ..update import Update
from .widget_query_type import WidgetQueryType
from .widget import _parse_json_value


_UNSET = object()


class WidgetQuery(Object, Update):
    """An incoming query from an HTML widget.

    Queries identify either a chat and message_id, or an inline_message_id.
    Tap data is untrusted; keep authoritative state in the bot.

    Parameters:
        id (``str``):
            Unique identifier for this query.

        from_user (:obj:`~pyrogram.types.User`):
            Sender of the query (the Bot API ``from`` field).

        chat (:obj:`~pyrogram.types.Chat`, *optional*):
            Chat containing the widget message.

        message_id (``int``, *optional*):
            Identifier of the widget message in the chat.

        inline_message_id (``str``, *optional*):
            Identifier of an inline widget message.

        data (``str``):
            Tap payload, 1-64 UTF-8 bytes.

        chat_data (JSON value, *optional*):
            Legacy state extension, parsed from JSON when possible. Official
            Bot API queries do not include state; keep it in bot storage.
            Defaults to an empty object.

        public_data (JSON value, *optional*):
            Legacy public state extension, parsed from JSON when possible.
            Official Bot API queries do not include it. Defaults to an empty object.

        chat_instance (``str``, *optional*):
            Global identifier, uniquely corresponding to the chat to which
            the message with the widget was sent (Bot API 10.4).

        chat_type (``str``, *optional*):
            For widgets in inline messages, type of the chat to which the
            message was sent: "sender", "private", "group", "supergroup"
            or "channel".

        type (:obj:`~pyrogram.types.WidgetQueryTypeData` | :obj:`~pyrogram.types.WidgetQueryTypeSignData` | :obj:`~pyrogram.types.WidgetQueryTypeSentTransaction`, *optional*):
            Type of the query (Bot API 10.4).

        widget_id (``str``, *optional*):
            Unique identifier of the shared widget, which sent the query;
            omitted if the widget isn't shared.

        matches (List of regex Matches, *optional*):
            Matches produced by :meth:`~pyrogram.filters.regex` on tap data.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        id: str,
        from_user: "types.User",
        data: str,
        chat_data: Any = _UNSET,
        public_data: Any = _UNSET,
        chat: Optional["types.Chat"] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        chat_instance: Optional[str] = None,
        chat_type: Optional[str] = None,
        type: Union["types.WidgetQueryTypeData", "types.WidgetQueryTypeSignData", "types.WidgetQueryTypeSentTransaction", dict, None] = None,
        widget_id: Optional[str] = None,
        matches: Optional[List[Match]] = None
    ):
        super().__init__(client)
        self.id = id
        self.from_user = from_user
        self.chat = chat
        self.message_id = message_id
        self.inline_message_id = inline_message_id
        self.data = data
        self.chat_data = {} if chat_data is _UNSET else chat_data
        self.public_data = {} if public_data is _UNSET else public_data
        self.chat_instance = chat_instance
        self.chat_type = chat_type
        self.type = type
        self.widget_id = widget_id
        self.matches = matches

    @staticmethod
    async def _parse(client: "pyrogram.Client", widget_query: dict, users=None, chats=None) -> "WidgetQuery":
        if not isinstance(widget_query, dict):
            from pyrogram import raw, utils
            users, chats = users or {}, chats or {}
            chat = None
            inline_id = None
            message_id = None
            if isinstance(widget_query, raw.types.UpdateBotWidgetQuery):
                peer = widget_query.peer
                message_id = widget_query.msg_id
                chat = types.Chat._parse_chat(client,
                    users.get(peer.user_id) if isinstance(peer, raw.types.PeerUser)
                    else chats.get(utils.get_raw_peer_id(peer)))
            else:
                inline_id = utils.pack_inline_message_id(widget_query.inline_message_id)
            query_type = WidgetQueryType._parse(client, widget_query.query_type)
            if hasattr(query_type, "wallet_card"):
                query_type.wallet_card = widget_query.wallet_card
            return WidgetQuery(
                client=client, id=str(widget_query.query_id),
                from_user=types.User._parse(client, users.get(widget_query.user_id)),
                data=widget_query.data.decode("utf-8"), chat=chat, message_id=message_id,
                inline_message_id=inline_id, chat_instance=str(widget_query.chat_instance),
                chat_type=widget_query.chat_type, type=query_type,
                widget_id=str(widget_query.widget_id) if widget_query.widget_id is not None else None
            )
        from ...methods.bots._widget import parse_chat, parse_user

        return WidgetQuery(
            client=client, id=str(widget_query["id"]),
            from_user=parse_user(client, widget_query["from"]),
            chat=parse_chat(client, widget_query.get("chat")),
            message_id=widget_query.get("message_id"),
            inline_message_id=widget_query.get("inline_message_id"),
            data=widget_query["data"],
            chat_data=_parse_json_value(widget_query.get("chat_data", {}), "chat_data"),
            public_data=_parse_json_value(widget_query.get("public_data", {}), "public_data"),
            chat_instance=widget_query.get("chat_instance"),
            chat_type=widget_query.get("chat_type"),
            type=WidgetQueryType._parse(client, widget_query.get("type")),
            widget_id=widget_query.get("widget_id")
        )

    async def answer(self, data: Any = _UNSET) -> bool:
        """Bound method of :meth:`~pyrogram.Client.answer_widget_query`."""
        if data is _UNSET:
            return await self._client.answer_widget_query(self.id)
        return await self._client.answer_widget_query(self.id, data)
