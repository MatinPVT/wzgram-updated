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

import base64
from typing import Any, Optional

import pyrogram
from ..object import Object


class WidgetQueryWallet(Object):
    """A TON wallet of the user, used in a query from a widget.

    Parameters:
        address (``str``):
            Address of the wallet.

        amount (``str``):
            Balance of the wallet, in the smallest units of the
            cryptocurrency, as a decimal number.

        public_key (``str``, *optional*):
            Hex-encoded public key of the wallet; omitted if unknown.

        state_init (``str``, *optional*):
            Base64-encoded serialized StateInit of the wallet contract;
            omitted if and only if ``public_key`` is omitted.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        address: str,
        amount: str,
        public_key: Optional[str] = None,
        state_init: Optional[str] = None
    ):
        super().__init__(client)
        self.address = address
        self.amount = amount
        self.public_key = public_key
        self.state_init = state_init

    @staticmethod
    def _parse(client: "pyrogram.Client", data: dict) -> "WidgetQueryWallet":
        if not isinstance(data, dict):
            return WidgetQueryWallet(
                client=client, address=data.address, amount=str(data.balance),
                public_key=data.public_key.hex() if data.public_key is not None else None,
                state_init=base64.b64encode(data.state_init).decode("ascii")
                if data.state_init is not None else None
            )
        return WidgetQueryWallet(
            client=client,
            address=data["address"],
            amount=str(data["amount"]),
            public_key=data.get("public_key"),
            state_init=data.get("state_init")
        )


class WidgetQueryTypeData(Object):
    """The query contains data for the bot.

    The ``type`` attribute is always "data".

    Parameters:
        wallet_card (JSON value, *optional*):
            TON wallet card of the user who sent the query, if it was sent
            to the bot along with the query. Kept as the raw Bot API value:
            this library has no TonWalletCard type yet.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        wallet_card: Any = None
    ):
        super().__init__(client)
        self.type = "data"
        self.wallet_card = wallet_card

    @staticmethod
    def _parse(client: "pyrogram.Client", data: dict) -> "WidgetQueryTypeData":
        return WidgetQueryTypeData(client=client, wallet_card=data.get("wallet_card"))


class WidgetQueryTypeSignData(Object):
    """The query contains data signed by a TON wallet of the user.

    The data is signed for the domain ``bot<bot_id>``.

    The ``type`` attribute is always "sign_data".

    Parameters:
        wallet (:obj:`~pyrogram.types.WidgetQueryWallet`):
            The wallet that signed the data.

        sign_data (``str``):
            JSON-serialized signed data.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        wallet: "WidgetQueryWallet",
        sign_data: str
    ):
        super().__init__(client)
        self.type = "sign_data"
        self.wallet = wallet
        self.sign_data = sign_data

    @staticmethod
    def _parse(client: "pyrogram.Client", data: dict) -> "WidgetQueryTypeSignData":
        return WidgetQueryTypeSignData(
            client=client,
            wallet=WidgetQueryWallet._parse(client, data["wallet"]),
            sign_data=data["sign_data"]
        )


class WidgetQueryTypeSentTransaction(Object):
    """The query notifies the bot about a transaction sent from a TON wallet.

    The ``type`` attribute is always "sent_transaction".

    Parameters:
        wallet (:obj:`~pyrogram.types.WidgetQueryWallet`):
            The wallet from which the transaction was sent.

        msg_hash (``str``):
            Value of ``msg_hash`` of the transaction.
    """

    def __init__(
        self,
        *,
        client: Optional["pyrogram.Client"] = None,
        wallet: "WidgetQueryWallet",
        msg_hash: str
    ):
        super().__init__(client)
        self.type = "sent_transaction"
        self.wallet = wallet
        self.msg_hash = msg_hash

    @staticmethod
    def _parse(client: "pyrogram.Client", data: dict) -> "WidgetQueryTypeSentTransaction":
        return WidgetQueryTypeSentTransaction(
            client=client,
            wallet=WidgetQueryWallet._parse(client, data["wallet"]),
            msg_hash=data["msg_hash"]
        )


class WidgetQueryType:
    """Type of a query from a widget (Bot API 10.4).

    One of :obj:`~pyrogram.types.WidgetQueryTypeData`,
    :obj:`~pyrogram.types.WidgetQueryTypeSignData` or
    :obj:`~pyrogram.types.WidgetQueryTypeSentTransaction`.
    Use :meth:`WidgetQueryType._parse` to build the right one from a
    Bot API ``type`` dictionary. Unknown ``type`` values are returned
    unchanged as a raw ``dict`` so a future type does not break parsing.
    """

    @staticmethod
    def _parse(client: "pyrogram.Client", data: Optional[dict]):
        if data is None:
            return None
        if not isinstance(data, dict):
            from pyrogram import raw
            if isinstance(data, raw.types.WidgetQueryTypeData):
                return WidgetQueryTypeData(client=client)
            if isinstance(data, raw.types.WidgetQueryTypeSignData):
                return WidgetQueryTypeSignData(
                    client=client, wallet=WidgetQueryWallet._parse(client, data.wallet),
                    sign_data=data.sign_data.data
                )
            if isinstance(data, raw.types.WidgetQueryTypeSentTransaction):
                return WidgetQueryTypeSentTransaction(
                    client=client, wallet=WidgetQueryWallet._parse(client, data.wallet),
                    msg_hash=data.msg_hash
                )
            return data
        kind = data.get("type")
        if kind == "data":
            return WidgetQueryTypeData._parse(client, data)
        if kind == "sign_data":
            return WidgetQueryTypeSignData._parse(client, data)
        if kind == "sent_transaction":
            return WidgetQueryTypeSentTransaction._parse(client, data)
        return data
