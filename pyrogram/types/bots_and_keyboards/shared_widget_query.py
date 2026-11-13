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
from .widget_query import _UNSET


class SharedWidgetQuery(Object, Update):
    """An incoming query from a forwarded message with a shared widget.

    Use :meth:`~pyrogram.Client.answer_widget_query` to answer the query.
    Each user can send at most 5 queries per 5 seconds to the bot from
    all its widgets.

    Parameters:
        id (``str``):
            Unique identifier for this query.

        from_user (:obj:`~pyrogram.types.User`):
            Sender of the query (the Bot API ``from`` field).

        type (:obj:`~pyrogram.types.WidgetQueryTypeData` | :obj:`~pyrogram.types.WidgetQueryTypeSignData` | :obj:`~pyrogram.types.WidgetQueryTypeSentTransaction`, *optional*):
            Type of the query.

        data (``str``):
            Data of the query, 1-64 bytes.

        widget_id (``str``):
            Unique identifier of the shared widget, which sent the query.

        chat_data (JSON value, *optional*):
            Current chat state, when the sending widget included it
            (test-server payloads). Not part of the official Bot API 10.4
            query; defaults to an empty object.

        public_data (JSON value, *optional*):
            Public state, when included; defaults to an empty object.

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
        widget_id: str,
        type: Union["types.WidgetQueryTypeData", "types.WidgetQueryTypeSignData", "types.WidgetQueryTypeSentTransaction", dict, None] = None,
        chat_data: Any = None,
        public_data: Any = None,
        matches: Optional[List[Match]] = None
    ):
        super().__init__(client)
        self.id = id
        self.from_user = from_user
        self.type = type
        self.data = data
        self.widget_id = widget_id
        self.chat_data = {} if chat_data is None else chat_data
        self.public_data = {} if public_data is None else public_data
        self.matches = matches

    @staticmethod
    async def _parse(client: "pyrogram.Client", shared_widget_query: dict, users=None, chats=None) -> "SharedWidgetQuery":
        from ...methods.bots._widget import parse_user, validate_data

        return SharedWidgetQuery(
            client=client, id=str(shared_widget_query["id"]),
            from_user=parse_user(client, shared_widget_query["from"]),
            type=WidgetQueryType._parse(client, shared_widget_query.get("type")),
            data=shared_widget_query["data"],
            widget_id=shared_widget_query["widget_id"],
            chat_data=validate_data(shared_widget_query.get("chat_data", {})),
            public_data=validate_data(shared_widget_query.get("public_data", {}), "public_data")
        )

    async def answer(self, data: Any = _UNSET) -> bool:
        """Bound method of :meth:`~pyrogram.Client.answer_widget_query`."""
        if data is _UNSET:
            return await self._client.answer_widget_query(self.id)
        return await self._client.answer_widget_query(self.id, data)
