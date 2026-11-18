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

from typing import Any

import pyrogram

from ...types.bots_and_keyboards.widget_query import _UNSET
from ._widget import validate_data, widget_request


class AnswerWidgetQuery:
    async def answer_widget_query(
        self: "pyrogram.Client",
        widget_query_id: str,
        data: Any = _UNSET
    ) -> bool:
        """Answer an incoming widget query.

        .. include:: /_includes/usable-by/bots.rst

        Answer within 15 seconds. Only the requesting widget receives the
        answer; it does not change widget state. Use
        :meth:`~pyrogram.Client.edit_message_widget_data` or
        :meth:`~pyrogram.Client.edit_shared_widget_data` to change state.

        Parameters:
            widget_query_id (``str``):
                Unique identifier for the answered query.

            data (JSON value | ``str``, *optional*):
                Response data, at most 1,024 UTF-8 bytes. Strings are sent
                unchanged; Python JSON values are serialized. Omit to acknowledge
                without data. Explicit None sends the string "null".

        Returns:
            ``bool``: On success, True is returned.

        Raises:
            ValueError: If state is invalid, exceeds its size limit or the bot token is missing.
        """
        payload = {"widget_query_id": widget_query_id}
        if data is not _UNSET:
            payload["data"] = validate_data(data, "data")
        return await widget_request(self, "answerWidgetQuery", payload)
