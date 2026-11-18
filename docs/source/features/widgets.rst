HTML Widgets
============

Telegram Bot API 10.4 (November 9, 2026) adds interactive HTML widgets inside
messages. The HTML is fixed when sent; the bot can change the message's
``chat_data`` and a shared widget's ``public_data`` later.

Send and update
---------------

Use ``widget_transport="mtproto"`` for native layer 233 methods and queries:

.. code-block:: python

    from wzgram import Client

    app = Client("widget_bot", api_id=12345, api_hash="your_api_hash",
                 bot_token="your_bot_token", widget_transport="mtproto")

Native widget handlers use the normal MTProto dispatcher and need no extra
poller. An existing authorized bot session does not need ``bot_token`` again.
The default ``widget_transport="botapi"`` retains the original HTTPS bridge
and requires ``bot_token``. ``test_mode=True`` selects the test environment;
use a bot token created in that environment when testing.

.. code-block:: python

    sent = await app.send_widget(
        chat_id,
        '<button onclick="TelegramWidget.request(\'tap\')">Tap</button>',
        {"count": 0},
        allow_queries=True,
    )
    await app.edit_message_widget_data(sent.chat.id, sent.id, {"count": 1})

Strings are sent unchanged, including plain text, JSON text and ``""``. Python
JSON values such as dictionaries and lists are serialized to compact JSON
strings. Each data field is limited to 1,024 UTF-8 bytes. HTML must be 1–32,768
UTF-8 bytes and no more than 4,096 bytes after zlib level 9 compression.

For edits, omit a data argument to keep its current value, pass ``""`` to clear
it, or pass ``None`` to store the text ``"null"``. For sending, omitted
``chat_data`` retains wzgram's default empty object, serialized as ``"{}"``.

Handle requests
---------------

.. code-block:: python

    @app.on_widget_query()
    async def on_widget(client, query):
        # Read authoritative state from your bot's storage.
        await query.answer({"ok": True})

    @app.on_shared_widget_query()
    async def on_shared_widget(client, query):
        await query.answer()

Queries carry ``data`` (1–64 bytes), sender, query type and message or widget
identifiers. Official queries do not carry the current widget state. The legacy
``chat_data`` and ``public_data`` query attributes remain available for older
payloads, defaulting to empty objects. Wallet query variants retain their wallet
and signed-data or transaction fields; ``wallet_card`` remains a Bot API dictionary.

Answer within 15 seconds. An answer reaches only the widget that requested it;
persist a state change separately with ``edit_message_widget_data`` or
``edit_shared_widget_data``. The JavaScript runtime exposes data as text or
``null``, so use ``JSON.parse(TelegramWidget.chatData)`` and parse the ``result``
of ``TelegramWidget.request()`` when your protocol uses JSON. Register
``chatDataChanged`` and ``publicDataChanged`` with ``TelegramWidget.onEvent``
to redraw when state changes. See ``examples/widget_bot.py`` for a tap counter
that handles requests, edits, stale revisions and errors.

In ``botapi`` mode, registering either widget handler starts widget-only Bot API
polling. Use one Bot API poller for the bot and remove any webhook first. The
``mtproto`` mode receives native chat, inline and forwarded-widget queries and
does not start an HTTPS poller. A single selected transport delivers widget
queries to high-level handlers, avoiding duplicate delivery from both APIs.

Widget messages are parsed as ``message.widget`` with
``message.media == MessageMediaType.WIDGET``. Use ``filters.widget`` to filter
them. Native widget state updates refresh cached messages and reach
``on_edited_message`` handlers. ``ExternalReplyInfo.widget`` is parsed too.

Shared widgets
--------------

.. code-block:: python

    sent = await app.send_widget(chat_id, html, is_shared=True)
    await app.send_shared_widget(chat_id, sent.widget.id, {"count": 0})
    await app.edit_shared_widget_data(sent.widget.id, {"count": 1}, cache_time=30)

Shared public data can be edited at most once per second. ``cache_time`` is an
integer from 5 to 3,600 seconds; omitted values keep the current setting. A
running shared widget calls ``TelegramWidget.watchPublicData()`` to receive
updates to public data. Keep a revision in your state to ignore older responses.

Availability
------------

In production, widgets currently work only in private chats with the bot and
automatically have protected content. Groups and inline results work on the
Telegram test server. ``InputWidgetMessageContent`` and
``InputSharedWidgetMessageContent`` provide ``to_dict()`` for Bot API inline
result payloads. Their native ``write()`` implementations also work with
``InlineQueryResultArticle`` and ``answer_inline_query``. Telegram's production
restriction still applies regardless of transport.

Official references: `Bot API widgets <https://core.telegram.org/bots/api#widget>`_
and `widget JavaScript runtime <https://core.telegram.org/bots/widgets>`_.
