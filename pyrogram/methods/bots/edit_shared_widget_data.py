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

from typing import Any, Optional

import pyrogram

from ._widget import validate_data, widget_request


class EditSharedWidgetData:
    async def edit_shared_widget_data(
        self: "pyrogram.Client",
        widget_id: str,
        public_data: Any,
        cache_time: Optional[int] = None
    ) -> bool:
        """Edit public data of a shared widget created by the bot.

        .. include:: /_includes/usable-by/bots.rst

        A shared widget can be edited at most once per second.

        Parameters:
            widget_id (``str``):
                Unique identifier of the shared widget.

            public_data (JSON value | ``str``):
                New public data, 0-1,024 bytes of JSON; pass an empty
                string to remove the public data. A JSON-encoded string
                is also accepted.

            cache_time (``int``, *optional*):
                Maximum time in seconds that the public data may be
                cached client-side, 5-3600. If omitted, the current
                value is kept (30 by default).

        Returns:
            ``bool``: On success, True is returned.

        Raises:
            ValueError: If public data is invalid, cache_time is out of
                range, or the bot token is missing.
        """
        if cache_time is not None and not 5 <= cache_time <= 3600:
            raise ValueError("cache_time must be between 5 and 3600 seconds")
        payload = {
            "widget_id": widget_id,
            "public_data": "" if public_data == "" else validate_data(public_data, "public_data")
        }
        if cache_time is not None:
            payload["cache_time"] = cache_time
        return await widget_request(self, "editSharedWidgetData", payload)
