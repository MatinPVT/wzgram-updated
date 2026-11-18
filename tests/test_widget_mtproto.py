"""Native widget methods, media and dispatcher regression checks (no network)."""
import zlib
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from pyrogram import Client, enums, raw, types, utils
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import SharedWidgetQueryHandler, WidgetQueryHandler
from pyrogram.handlers import EditedMessageHandler


def received(value):
    """Use TL-decoded defaults, as a real Telegram response would."""
    return raw.core.TLObject.read(BytesIO(value.write()))


@pytest.fixture
def client():
    app = Client("native_widgets", api_id=1, api_hash="test", in_memory=True,
                 widget_transport="mtproto")
    app.invoke = AsyncMock(return_value=True)
    app.resolve_peer = AsyncMock(return_value=raw.types.InputPeerUser(user_id=5, access_hash=0))
    return app


def media(**kwargs):
    return raw.types.MessageMediaWidget(
        width=300, height=100, payload=zlib.compress(b"<button>Tap</button>", 9),
        chat_data='{"count":1}', public_data="text", public_data_hash=9,
        widget_id=77, can_query=True, **kwargs
    )


async def test_native_send_returns_parsed_widget_message_and_options(client):
    client.invoke.return_value = received(raw.types.Updates(
        updates=[raw.types.UpdateNewMessage(message=raw.types.Message(
            id=7, peer_id=raw.types.PeerUser(user_id=5), date=1, message="Hi", media=media()),
            pts=1, pts_count=1)],
        users=[raw.types.User(id=5, first_name="User", usernames=[])], chats=[], date=1, seq=1
    ))
    sent = await client.send_widget(5, "<button>Tap</button>", {"count": 0}, True,
        public_data="raw text", is_shared=True, caption="Hi", message_thread_id=9,
        disable_notification=True, protect_content=True, allow_paid_broadcast=True,
        show_caption_above_media=True, message_effect_id="123",
        caption_entities=[{"type": "bold", "offset": 0, "length": 2}],
        reply_markup={"inline_keyboard": [[{"text": "Tap", "callback_data": "tap"}]]})
    request = client.invoke.await_args.args[0]
    assert isinstance(request, raw.functions.messages.SendMedia)
    assert isinstance(request.media, raw.types.InputMediaWidget)
    assert request.media.chat_data == '{"count":0}'
    assert request.media.public_data == "raw text"
    assert request.media.allow_queries and request.media.shared_widget
    assert request.media.width == request.media.height == 0
    assert request.reply_to.reply_to_msg_id == 9
    assert request.silent and request.noforwards and request.allow_paid_floodskip
    assert request.invert_media and request.effect == 123
    assert isinstance(request.entities[0], raw.types.MessageEntityBold)
    assert request.reply_markup.rows[0].buttons[0].text == "Tap"
    assert sent.widget.html == "<button>Tap</button>"
    assert sent.widget.chat_data == {"count": 1}
    assert sent.widget.public_data == "text"
    assert sent.widget.id == "77"
    assert sent.media == enums.MessageMediaType.WIDGET
    assert sent.caption == "Hi"


async def test_native_shared_send_uses_widget_id(client):
    client.invoke.return_value = SimpleNamespace(
        updates=[raw.types.UpdateNewMessage(message=received(raw.types.Message(
            id=7, peer_id=raw.types.PeerUser(user_id=5), date=1, message="", media=media())),
            pts=1, pts_count=1)], users=[received(raw.types.User(id=5))], chats=[])
    sent = await client.send_shared_widget(5, "77", "raw text")
    request = client.invoke.await_args.args[0]
    assert isinstance(request.media, raw.types.InputMediaWidgetId)
    assert request.media.widget_id == 77 and request.media.chat_data == "raw text"
    assert sent.widget.id == "77"


async def test_native_answers_support_omitted_empty_and_json(client):
    for value, expected in (({}, "{}"), ("", ""), (None, "null")):
        assert await client.answer_widget_query("123", value)
        request = client.invoke.await_args.args[0]
        assert isinstance(request, raw.functions.messages.SetBotWidgetQueryAnswer)
        assert request.query_id == 123 and request.result == expected
    await client.answer_widget_query("123")
    assert client.invoke.await_args.args[0].result is None


async def test_native_edits_preserve_omitted_fields(client):
    await client.edit_message_widget_data(5, 7, public_data={"v": 1})
    request = client.invoke.await_args.args[0]
    assert isinstance(request, raw.functions.messages.EditMessageWidgetData)
    assert request.id == 7 and request.public_data == '{"v":1}'
    assert request.chat_data is None
    await client.edit_shared_widget_data("77", "", cache_time=60)
    request = client.invoke.await_args.args[0]
    assert isinstance(request, raw.functions.messages.EditWidgetData)
    assert request.widget_id == 77 and request.public_data == "" and request.cache_time == 60


async def test_native_inline_edit_uses_dc_routing(client):
    inline_id = raw.types.InputBotInlineMessageID(dc_id=2, id=5, access_hash=9)
    with patch("pyrogram.methods.bots._widget_mtproto.invoke_inline", AsyncMock(return_value=True)) as invoke:
        assert await client.edit_message_widget_data(
            inline_message_id=utils.pack_inline_message_id(inline_id), chat_data="")
    app, dc_id, request = invoke.await_args.args
    assert app is client and dc_id == 2
    assert isinstance(request, raw.functions.messages.EditInlineBotMessageWidgetData)
    assert request.chat_data == "" and request.public_data is None


async def test_widget_inline_content_can_be_sent_through_article(client):
    content = types.InputWidgetMessageContent(html="html", chat_data={"v": 1},
        public_data="raw", allow_queries=True, is_shared=True, caption="Hi", parse_mode="HTML")
    result = await types.InlineQueryResultArticle(title="Widget", input_message_content=content).write(client)
    assert isinstance(result.send_message, raw.types.InputBotInlineMessageWidget)
    assert result.send_message.chat_data == '{"v":1}'
    assert result.send_message.public_data == "raw"
    assert result.send_message.allow_queries and result.send_message.shared_widget
    shared = await types.InputSharedWidgetMessageContent(widget_id="77", chat_data="").write(client)
    assert isinstance(shared, raw.types.InputBotInlineMessageWidgetId)
    assert shared.widget_id == 77 and shared.chat_data == ""


async def test_native_dispatcher_parses_chat_inline_and_forward_queries(client):
    user = received(raw.types.User(id=5, first_name="User"))
    query_type = raw.types.WidgetQueryTypeData()
    common = dict(query_id=123, user_id=5, query_type=query_type, data=b"tap", widget_id=77)
    updates = [
        raw.types.UpdateBotWidgetQuery(peer=raw.types.PeerUser(user_id=5), msg_id=7,
            chat_instance=9, chat_type="private", **common),
        raw.types.UpdateInlineBotWidgetQuery(inline_message_id=raw.types.InputBotInlineMessageID(
            dc_id=2, id=7, access_hash=9), chat_instance=9, chat_type="private", **common),
        raw.types.UpdateBotWidgetCopyQuery(**common)
    ]
    dispatcher = Dispatcher(client)
    for update in updates:
        query, handler = await dispatcher.update_parsers[type(update)](update, {5: user}, {})
        assert query.id == "123" and query.data == "tap" and query.widget_id == "77"
        assert query.from_user.id == 5
        assert isinstance(query.type, types.WidgetQueryTypeData)
        assert handler is (SharedWidgetQueryHandler if isinstance(update, raw.types.UpdateBotWidgetCopyQuery)
                           else WidgetQueryHandler)
        assert await query.answer({"ok": True})
    chat_query = await types.WidgetQuery._parse(client, updates[0], {5: user}, {})
    assert chat_query.chat.id == 5 and chat_query.message_id == 7
    inline_query = await types.WidgetQuery._parse(client, updates[1], {5: user}, {})
    assert inline_query.chat is None and inline_query.inline_message_id is not None
    client.widget_transport = "botapi"
    assert await dispatcher.update_parsers[type(updates[0])](updates[0], {5: user}, {}) == (None, type(None))


def test_native_handlers_do_not_start_a_botapi_poller(client):
    dispatcher = Dispatcher(client)
    dispatcher.handler_worker_tasks = [object()]
    dispatcher.groups[0] = [WidgetQueryHandler(AsyncMock())]
    dispatcher._start_widget_updates()
    assert dispatcher.widget_updates_task is None


def test_native_signed_wallet_fields_use_botapi_encodings(client):
    wallet = raw.types.UserWallet(address="EQabc", balance=1000, public_key=b"\xab\xcd", state_init=b"state")
    query_type = types.WidgetQueryType._parse(client, raw.types.WidgetQueryTypeSignData(
        wallet=wallet, sign_data=raw.types.DataJSON(data='{"a":1}')))
    assert query_type.wallet.amount == "1000"
    assert query_type.wallet.public_key == "abcd"
    assert query_type.wallet.state_init == "c3RhdGU="
    assert query_type.sign_data == '{"a":1}'


async def test_widget_data_update_refreshes_cached_message_without_resetting_public_data(client):
    cached = types.Message(id=7, chat=types.Chat(id=5), widget=types.Widget._parse(client, media()))
    client.message_cache[(5, 7)] = cached
    update = raw.types.UpdateMessageWidgetData(peer=raw.types.PeerUser(user_id=5),
        msg_id=7, chat_data='{"count":2}', pts=1, pts_count=1)
    dispatcher = Dispatcher(client)
    message, handler = await dispatcher.update_parsers[type(update)](update, {}, {})
    assert handler is EditedMessageHandler
    assert message.widget.chat_data == {"count": 2}
    assert message.widget.public_data == "text"
    assert client.message_cache[(5, 7)] is message
    assert cached.widget.chat_data == {"count": 1}
    update = raw.types.UpdateMessageWidgetData(peer=raw.types.PeerUser(user_id=5),
        msg_id=7, public_data="", public_data_hash=10, pts=2, pts_count=1)
    message, _ = await dispatcher.update_parsers[type(update)](update, {}, {})
    assert message.widget.public_data is None and message.widget.public_data_hash == 10
    assert message.widget.chat_data == {"count": 2}


async def test_widgets_in_external_replies_and_filters(client):
    from pyrogram import filters
    reply = raw.types.MessageReplyHeader(reply_to_msg_id=7,
        reply_from=raw.types.MessageFwdHeader(date=1, from_id=raw.types.PeerUser(user_id=5)),
        reply_media=media())
    parsed = await types.ExternalReplyInfo._parse(client, reply, {}, {})
    assert parsed.widget.id == "77" and parsed.media == enums.MessageMediaType.WIDGET
    assert await filters.widget(client, types.Message(id=1, widget=parsed.widget))
    assert not await filters.widget(client, types.Message(id=2))


@pytest.mark.parametrize("payload", [b"broken", zlib.compress(b"x" * 32769), zlib.compress(b"\xff")])
async def test_bad_widget_payload_falls_back_to_unsupported_media(client, payload):
    message = raw.types.Message(id=7, peer_id=raw.types.PeerUser(user_id=5), date=1, message="",
        media=raw.types.MessageMediaWidget(width=0, height=0, payload=payload))
    _, kind, _, fields = await types.Message._parse_media(client, message, {}, {})
    assert kind == enums.MessageMediaType.UNSUPPORTED and fields["widget"] is None
