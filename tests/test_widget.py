"""Offline widget tests: python3 -B tests/test_widget.py.

Source-only checkouts without generated TL files use dependency stubs below;
all widget implementations and their method registrations are loaded unchanged.
"""
import ast
import asyncio
import importlib.util
import io
import json
import random
import sys
import types as module_types
import unittest
import zlib
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]


def _source_only_imports():
    """Mock unrelated MTProto dependencies, never generate schema or use network."""
    def package(name, path):
        module = module_types.ModuleType(name)
        module.__path__ = [str(ROOT / path)]
        sys.modules[name] = module
        return module

    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, ROOT / path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    pg = package('pyrogram', 'pyrogram')
    pg.types = package('pyrogram.types', 'pyrogram/types')
    pg.enums = package('pyrogram.enums', 'pyrogram/enums')
    load('pyrogram.enums.auto_name', 'pyrogram/enums/auto_name.py')
    pg.enums.ChatType = load('pyrogram.enums.chat_type', 'pyrogram/enums/chat_type.py').ChatType
    pg.enums.ListenerTypes = load('pyrogram.enums.listener_types', 'pyrogram/enums/listener_types.py').ListenerTypes
    for name in ('User', 'Chat', 'Message'):
        def init(self, client=None, **values):
            self._client = client
            self.__dict__.update(values)
        setattr(pg.types, name, type(name, (), {'__init__': init}))
    load('pyrogram.types.object', 'pyrogram/types/object.py')
    pg.types.Update = load('pyrogram.types.update', 'pyrogram/types/update.py').Update
    package('pyrogram.types.bots_and_keyboards', 'pyrogram/types/bots_and_keyboards')
    package('pyrogram.types.input_content', 'pyrogram/types/input_content')
    load('pyrogram.types.input_content.input_message_content', 'pyrogram/types/input_content/input_message_content.py')
    package('pyrogram.methods', 'pyrogram/methods')
    package('pyrogram.methods.bots', 'pyrogram/methods/bots')
    package('pyrogram.methods.decorators', 'pyrogram/methods/decorators')
    pg.filters = module_types.ModuleType('pyrogram.filters')
    pg.filters.Filter = type('Filter', (), {})
    async def check_filter(flt, client, update):
        return True if flt is None else await flt(client, update)
    pg.filters.check_filter = check_filter
    sys.modules['pyrogram.filters'] = pg.filters
    pg.utils = module_types.SimpleNamespace(
        unbound_handler_args=lambda self, filters, group: (filters, group)
    )
    package('pyrogram.handlers', 'pyrogram/handlers')
    load('pyrogram.handlers.handler', 'pyrogram/handlers/handler.py')
    load('pyrogram.handlers.widget_query_handler', 'pyrogram/handlers/widget_query_handler.py')
    load('pyrogram.handlers.shared_widget_query_handler', 'pyrogram/handlers/shared_widget_query_handler.py')
    # Load widget_query_type first: widget_query imports it, and loading it
    # twice would create two distinct class objects.
    load('pyrogram.types.bots_and_keyboards.widget_query_type', 'pyrogram/types/bots_and_keyboards/widget_query_type.py')
    load('pyrogram.types.bots_and_keyboards.widget', 'pyrogram/types/bots_and_keyboards/widget.py')
    load('pyrogram.types.bots_and_keyboards.widget_query', 'pyrogram/types/bots_and_keyboards/widget_query.py')
    load('pyrogram.types.bots_and_keyboards.shared_widget_query', 'pyrogram/types/bots_and_keyboards/shared_widget_query.py')
    load('pyrogram.types.bots_and_keyboards.input_widget_message_content', 'pyrogram/types/bots_and_keyboards/input_widget_message_content.py')
    for name in ('_widget', 'send_widget', 'send_shared_widget', 'answer_widget_query', 'edit_message_widget_data', 'edit_shared_widget_data'):
        load('pyrogram.methods.bots.' + name, 'pyrogram/methods/bots/' + name + '.py')
    load('pyrogram.methods.decorators.on_widget_query', 'pyrogram/methods/decorators/on_widget_query.py')
    load('pyrogram.methods.decorators.on_shared_widget_query', 'pyrogram/methods/decorators/on_shared_widget_query.py')

    def exports(name, path):
        for node in ast.parse((ROOT / path).read_text()).body:
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                target = name + '.' + node.module
                if target not in sys.modules:
                    stub = module_types.ModuleType(target)
                    for alias in node.names:
                        setattr(stub, alias.name, type(alias.name, (), {}))
                    sys.modules[target] = stub
        return load(name, path)

    pg.handlers = exports('pyrogram.handlers', 'pyrogram/handlers/__init__.py')
    exports_types = exports('pyrogram.types.bots_and_keyboards', 'pyrogram/types/bots_and_keyboards/__init__.py')
    pg.types.WidgetQuery = exports_types.WidgetQuery
    for _name in ('SharedWidgetQuery', 'Widget', 'WidgetQueryType', 'WidgetQueryTypeData',
                  'WidgetQueryTypeSignData', 'WidgetQueryTypeSentTransaction', 'WidgetQueryWallet',
                  'InputWidgetMessageContent', 'InputSharedWidgetMessageContent'):
        setattr(pg.types, _name, getattr(exports_types, _name))
    bots = exports('pyrogram.methods.bots', 'pyrogram/methods/bots/__init__.py')
    decorators = exports('pyrogram.methods.decorators', 'pyrogram/methods/decorators/__init__.py')
    def client_init(self, name, **kwargs):
        self.bot_token = kwargs.get('bot_token')
    pg.Client = type('Client', (bots.Bots, decorators.Decorators), {
        '__init__': client_init, 'add_handler': lambda *args: None
    })
    pg.raw = package('pyrogram.raw', 'pyrogram/raw')
    pg.raw.types = package('pyrogram.raw.types', 'pyrogram/raw/types')
    for node in ast.walk(ast.parse((ROOT / 'pyrogram/dispatcher.py').read_text())):
        if isinstance(node, ast.ImportFrom) and node.module == 'pyrogram.raw.types':
            for alias in node.names:
                setattr(pg.raw.types, alias.name, type(alias.name, (), {}))
    load('pyrogram.dispatcher', 'pyrogram/dispatcher.py')


if __name__ == '__main__' and not (ROOT / 'pyrogram/raw/all.py').exists():
    _source_only_imports()

from pyrogram import Client, enums, types
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import SharedWidgetQueryHandler, WidgetQueryHandler
from pyrogram.methods.bots import _widget


class WidgetTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = Client('widget_tests', api_id=123, api_hash='test', bot_token='123:TEST')
        async def run_sync(func, *args):
            return func(*args)
        thread_patch = patch.object(_widget.asyncio, 'to_thread', side_effect=run_sync)
        thread_patch.start()
        self.addCleanup(thread_patch.stop)
        self.http_patch = patch.object(_widget.request, 'urlopen')
        self.http = self.http_patch.start()
        self.addCleanup(self.http_patch.stop)
        self.message = {'message_id': 7, 'date': 0, 'chat': {'id': 42, 'type': 'private'},
                        'from': {'id': 123, 'is_bot': True, 'first_name': 'Bot'}}
        self.respond(self.message)

    def respond(self, result, ok=True):
        self.http.return_value = io.BytesIO(json.dumps({'ok': ok, 'result': result}).encode())

    def payload(self, method):
        req = self.http.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.telegram.org/bot123:TEST/' + method)
        self.assertEqual(req.get_method(), 'POST')
        self.assertEqual(req.get_header('Content-type'), 'application/json')
        return json.loads(req.data)

    async def test_send_payload_and_message(self):
        message = await self.client.send_widget(42, '<html>tap</html>', {'count': 0}, True)
        self.assertEqual(self.payload('sendWidget'), {
            'chat_id': 42, 'html': '<html>tap</html>', 'chat_data': '{"count":0}', 'allow_queries': True})
        self.assertIsInstance(message, types.Message)
        self.assertEqual((message.id, message.chat.id, message.from_user.id), (7, 42, 123))
        self.assertIs(message._client, self.client)

    async def test_answer_payload(self):
        self.respond(True)
        self.assertTrue(await self.client.answer_widget_query('query-1', {'count': 1, 'revision': 1}))
        self.assertEqual(self.payload('answerWidgetQuery'), {
            'widget_query_id': 'query-1', 'data': '{"count":1,"revision":1}'})

    async def test_default_send_state_and_omitted_edit_state(self):
        await self.client.send_widget(42, 'html')
        self.assertEqual(self.payload('sendWidget'), {
            'chat_id': 42, 'html': 'html', 'chat_data': '{}', 'allow_queries': False})
        self.respond(True)
        self.assertTrue(await self.client.edit_message_widget_data(42, 7))
        self.assertEqual(self.payload('editMessageWidgetData'), {
            'chat_id': 42, 'message_id': 7})

    async def test_send_message_options(self):
        options = {
            'message_thread_id': 9, 'parse_mode': 'HTML', 'caption_entities': [],
            'show_caption_above_media': False, 'disable_notification': True,
            'protect_content': False, 'allow_paid_broadcast': False,
            'message_effect_id': '123', 'reply_parameters': {'message_id': 3},
            'reply_markup': {'inline_keyboard': [[{'text': 'Tap', 'callback_data': 'tap'}]]}}
        for method, args, required in (
            ('sendWidget', (42, 'html'), {'html': 'html', 'allow_queries': False}),
            ('sendSharedWidget', (42, 'widget-9'), {'widget_id': 'widget-9'})):
            with self.subTest(method=method):
                self.respond(self.message)
                call = self.client.send_widget if method == 'sendWidget' else self.client.send_shared_widget
                await call(*args, **options)
                self.assertEqual(self.payload(method), {
                    'chat_id': 42, 'chat_data': '{}', **required, **options})

    async def test_answer_optional_empty_and_null_data(self):
        self.respond(True)
        self.assertTrue(await self.client.answer_widget_query('q'))
        self.assertEqual(self.payload('answerWidgetQuery'), {'widget_query_id': 'q'})
        for data, expected in (('', ''), (None, 'null'), (False, 'false'),
                               (0, '0'), ([], '[]'), ({'ok': True}, '{"ok":true}')):
            with self.subTest(data=data):
                self.respond(True)
                self.assertTrue(await self.client.answer_widget_query('q', data))
                self.assertEqual(self.payload('answerWidgetQuery'), {
                    'widget_query_id': 'q', 'data': expected})

    async def test_bound_answers_without_data(self):
        for query_type, extra in ((types.WidgetQuery, {}),
                                  (types.SharedWidgetQuery, {'widget_id': 'widget-9'})):
            with self.subTest(query_type=query_type):
                query = await query_type._parse(self.client, {
                    'id': 'q', 'from': {'id': 5, 'first_name': 'User'},
                    'type': {'type': 'data'}, 'data': 'tap', **extra})
                self.respond(True)
                self.assertTrue(await query.answer())
                self.assertEqual(self.payload('answerWidgetQuery'), {'widget_query_id': 'q'})

    def test_construct_official_query_without_local_state(self):
        query = types.WidgetQuery(id='q', from_user=None, data='tap',
            chat_instance='inst-1', type=types.WidgetQueryTypeData())
        self.assertEqual((query.chat_data, query.public_data), ({}, {}))
        query = types.WidgetQuery(id='q', from_user=None, data='tap',
            chat_data=None, public_data=False)
        self.assertIsNone(query.chat_data)
        self.assertIs(query.public_data, False)

    async def test_empty_widget_data(self):
        await self.client.send_widget(42, 'html', '', public_data='')
        self.assertEqual(self.payload('sendWidget'), {
            'chat_id': 42, 'html': 'html', 'chat_data': '', 'public_data': '', 'allow_queries': False})
        self.respond(self.message)
        await self.client.send_shared_widget(42, 'widget-9', '')
        self.assertEqual(self.payload('sendSharedWidget')['chat_data'], '')
        self.assertEqual(types.InputWidgetMessageContent(
            html='html', chat_data='', public_data='').to_dict(), {
                'html': 'html', 'chat_data': '', 'public_data': ''})
        self.assertEqual(types.InputSharedWidgetMessageContent(
            widget_id='widget-9', chat_data='').to_dict(), {'widget_id': 'widget-9', 'chat_data': ''})

    async def test_empty_html_rejected(self):
        with self.assertRaises(ValueError):
            await self.client.send_widget(42, '')
        with self.assertRaises(ValueError):
            types.InputWidgetMessageContent(html='').to_dict()
        self.http.assert_not_called()

    async def test_data_removal_and_boolean_edit_result(self):
        self.respond(True)
        self.assertTrue(await self.client.edit_message_widget_data(42, 7, '', public_data=''))
        self.assertEqual(self.payload('editMessageWidgetData'), {
            'chat_id': 42, 'message_id': 7, 'chat_data': '', 'public_data': ''})
        self.respond(True)
        self.assertTrue(await self.client.edit_shared_widget_data('widget-9', ''))
        self.assertEqual(self.payload('editSharedWidgetData'), {
            'widget_id': 'widget-9', 'public_data': ''})

    def test_inline_caption_formatting_and_defaults(self):
        for content_type, required in (
            (types.InputWidgetMessageContent, {'html': 'html'}),
            (types.InputSharedWidgetMessageContent, {'widget_id': 'widget-9'})):
            with self.subTest(content_type=content_type):
                self.assertEqual(content_type(**required).to_dict(), required)
                self.assertEqual(content_type(**required, caption='<b>Hi</b>', parse_mode='HTML',
                    show_caption_above_media=False).to_dict(), {
                        **required, 'caption': '<b>Hi</b>', 'parse_mode': 'HTML',
                        'show_caption_above_media': False})
                entities = [{'type': 'bold', 'offset': 0, 'length': 2}]
                self.assertEqual(content_type(**required, caption='Hi',
                    caption_entities=entities).to_dict(), {
                        **required, 'caption': 'Hi', 'caption_entities': entities})

    async def test_widget_on_send_results(self):
        widget = {'id': 'widget-9', 'html': 'html', 'width': 300, 'height': 100,
                  'chat_data': {'count': 0}, 'public_data': '{"theme":"blue"}'}
        for call in (lambda: self.client.send_widget(42, 'html', is_shared=True),
                     lambda: self.client.send_shared_widget(42, 'widget-9')):
            with self.subTest(call=call):
                self.respond({**self.message, 'widget': widget})
                message = await call()
                self.assertIsInstance(message.widget, types.Widget)
                self.assertIs(message.widget._client, self.client)
                self.assertEqual(message.widget.id, 'widget-9')
                self.assertEqual(message.widget.chat_data, {'count': 0})
                self.assertEqual(message.widget.public_data, {'theme': 'blue'})

    async def test_shared_query_wallet_types(self):
        for kind, extra, parsed_type in (
            ('sign_data', {'sign_data': '{"a":1}'}, types.WidgetQueryTypeSignData),
            ('sent_transaction', {'msg_hash': 'hash1'}, types.WidgetQueryTypeSentTransaction)):
            with self.subTest(kind=kind):
                query = await types.SharedWidgetQuery._parse(self.client, {
                    'id': 'sq', 'from': {'id': 5, 'first_name': 'User'}, 'data': 'tap',
                    'widget_id': 'widget-9', 'chat_data': {'count': 1}, 'public_data': '{}',
                    'type': {'type': kind, 'wallet': {'address': 'EQabc', 'amount': '1000'}, **extra}})
                self.assertIsInstance(query.type, parsed_type)
                self.assertIsInstance(query.type.wallet, types.WidgetQueryWallet)
                self.assertEqual(query.type.wallet.amount, '1000')
                self.assertIsNone(query.type.wallet.public_key)
                self.assertIsNone(query.type.wallet.state_init)
                self.assertEqual((query.chat_data, query.public_data), ({'count': 1}, {}))

    def test_query_wallet_card_and_unknown_type(self):
        card = {'id': 'card-1'}
        query_type = types.WidgetQueryType._parse(self.client, {'type': 'data', 'wallet_card': card})
        self.assertIsInstance(query_type, types.WidgetQueryTypeData)
        self.assertIs(query_type.wallet_card, card)
        unknown = {'type': 'future_type'}
        self.assertIs(types.WidgetQueryType._parse(self.client, unknown), unknown)

    def test_shared_unbound_decorator(self):
        async def callback(client, query):
            pass
        self.assertIs(Client.on_shared_widget_query(group=2)(callback), callback)
        handler, group = callback.handlers[0]
        self.assertIsInstance(handler, SharedWidgetQueryHandler)
        self.assertEqual(group, 2)

    async def test_dispatcher_query_routes(self):
        dispatcher = Dispatcher(self.client)
        query = {'id': 'q', 'from': {'id': 5, 'first_name': 'User'}, 'data': 'tap',
                 'type': {'type': 'data'}, 'widget_id': 'widget-9'}
        for name, query_type, handler_type in (
            ('widget_query', types.WidgetQuery, WidgetQueryHandler),
            ('shared_widget_query', types.SharedWidgetQuery, SharedWidgetQueryHandler)):
            with self.subTest(name=name):
                parsed, handler = await dispatcher.update_parsers[dict]({name: query}, {}, {})
                self.assertIsInstance(parsed, query_type)
                self.assertIs(handler, handler_type)
        self.assertEqual(await dispatcher.update_parsers[dict]({'update_id': 1}, {}, {}),
                         (None, type(None)))

    async def test_polling_both_query_types_and_offset(self):
        dispatcher = Dispatcher(self.client)
        updates = [{'update_id': 3, 'message': {}}, {'update_id': 4, 'widget_query': {}},
                   {'update_id': 5, 'shared_widget_query': {}}]
        with patch.object(_widget, 'widget_request', AsyncMock(
                side_effect=[updates, asyncio.CancelledError()])) as request:
            with self.assertRaises(asyncio.CancelledError):
                await dispatcher._poll_widget_updates()
        self.assertEqual(dispatcher.widget_update_offset, 6)
        self.assertEqual(dispatcher.updates_queue.get_nowait(), (updates[1], {}, {}))
        self.assertEqual(dispatcher.updates_queue.get_nowait(), (updates[2], {}, {}))
        self.assertTrue(dispatcher.updates_queue.empty())
        self.assertEqual(request.await_args_list[0].args, (self.client, 'getUpdates', {
            'offset': 0, 'timeout': 10, 'allowed_updates': ['widget_query', 'shared_widget_query']}))
        self.assertEqual(request.await_args_list[1].args[2]['offset'], 6)

    async def test_polling_retries_unqueued_update(self):
        dispatcher = Dispatcher(self.client)
        dispatcher.widget_update_offset = 4
        update = {'update_id': 4, 'shared_widget_query': {}}
        with patch.object(_widget, 'widget_request', AsyncMock(
                side_effect=[[update], [update], asyncio.CancelledError()])) as request, \
                patch.object(dispatcher, 'enqueue_update', AsyncMock(side_effect=[False, True])) as enqueue:
            with self.assertRaises(asyncio.CancelledError):
                await dispatcher._poll_widget_updates()
        self.assertEqual([call.args[2]['offset'] for call in request.await_args_list], [4, 4, 5])
        self.assertEqual(enqueue.await_count, 2)

    async def test_polling_starts_for_either_handler_once(self):
        self.client.loop = asyncio.get_running_loop()
        for handler_type in (WidgetQueryHandler, SharedWidgetQueryHandler):
            with self.subTest(handler_type=handler_type):
                dispatcher = Dispatcher(self.client)
                dispatcher.groups[0] = [handler_type(AsyncMock())]
                dispatcher._start_widget_updates()
                self.assertIsNone(dispatcher.widget_updates_task)
                dispatcher.handler_worker_tasks = [object()]
                with patch.object(dispatcher, '_poll_widget_updates', AsyncMock()) as poll:
                    dispatcher._start_widget_updates()
                    task = dispatcher.widget_updates_task
                    dispatcher._start_widget_updates()
                    self.assertIs(dispatcher.widget_updates_task, task)
                    await task
                    poll.assert_awaited_once()
        dispatcher = Dispatcher(self.client)
        dispatcher.handler_worker_tasks = [object()]
        dispatcher.groups[0] = [SharedWidgetQueryHandler(AsyncMock())]
        self.client.bot_token = None
        with self.assertRaises(ValueError):
            dispatcher._start_widget_updates()

    async def test_edit_chat_payload(self):
        result = await self.client.edit_message_widget_data(42, 7, {'count': 2})
        self.assertIsInstance(result, types.Message)
        self.assertEqual(self.payload('editMessageWidgetData'), {
            'chat_id': 42, 'message_id': 7, 'chat_data': '{"count":2}'})

    async def test_edit_inline_payload(self):
        self.respond(True)
        self.assertTrue(await self.client.edit_message_widget_data(
            inline_message_id='inline-1', chat_data={'count': 2}))
        self.assertEqual(self.payload('editMessageWidgetData'), {
            'inline_message_id': 'inline-1', 'chat_data': '{"count":2}'})

    async def test_html_raw_overflow(self):
        with self.assertRaises(ValueError):
            await self.client.send_widget(42, 'x' * 32769)
        self.http.assert_not_called()

    async def test_html_utf8_overflow(self):
        with self.assertRaises(ValueError):
            await self.client.send_widget(42, 'é' * 16385)
        self.http.assert_not_called()

    async def test_html_compressed_overflow(self):
        html = ''.join(random.Random(17).choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10000))
        self.assertLess(len(html.encode()), 32768)
        self.assertGreater(len(zlib.compress(html.encode(), 9)), 4096)
        with self.assertRaises(ValueError):
            await self.client.send_widget(42, html)
        self.http.assert_not_called()

    async def test_size_boundaries_accepted(self):
        await self.client.send_widget(42, 'x' * 32768, {'v': 'x' * 1016})
        payload = self.payload('sendWidget')
        self.assertEqual(len(payload['chat_data'].encode()), 1024)

    async def test_state_overflow_all_methods(self):
        state = {'v': 'x' * 1017}
        for call in (lambda: self.client.send_widget(42, 'html', state),
                     lambda: self.client.answer_widget_query('q', state),
                     lambda: self.client.edit_message_widget_data(42, 7, state)):
            with self.subTest(method=call):
                with self.assertRaises(ValueError):
                    await call()
        self.http.assert_not_called()

    async def test_unicode_state_overflow(self):
        with self.assertRaises(ValueError):
            await self.client.answer_widget_query('q', {'v': 'é' * 509})
        self.http.assert_not_called()

    async def test_invalid_json(self):
        for data in ({'v': float('nan')}, {'v': {1, 2}}, '\ud800'):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    await self.client.answer_widget_query('q', data)
        self.http.assert_not_called()

    async def test_encoded_json(self):
        self.respond(True)
        await self.client.answer_widget_query('q', '{"count":1}')
        self.assertEqual(self.payload('answerWidgetQuery')['data'], '{"count":1}')

    async def test_invalid_edit_target(self):
        for target in ({}, {'chat_id': 42}, {'message_id': 7}, {'inline_message_id': ''},
                       {'chat_id': 42, 'message_id': 7, 'inline_message_id': 'inline'}):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    await self.client.edit_message_widget_data(chat_data={}, **target)
        self.http.assert_not_called()

    async def test_missing_token(self):
        self.client.bot_token = None
        with self.assertRaises(ValueError):
            await self.client.send_widget(42, 'html')
        self.http.assert_not_called()

    async def test_widget_requests_honor_client_test_mode(self):
        self.client.test_mode = True
        await self.client.send_widget(42, 'html', {'count': 0})
        req = self.http.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.telegram.org/bot123:TEST/test/sendWidget')
        self.assertEqual(json.loads(req.data)['chat_data'], '{"count":0}')

    async def test_bot_api_error(self):
        self.http.return_value = io.BytesIO(b'{"ok":false,"error_code":400,"description":"Bad widget"}')
        with self.assertRaisesRegex(RuntimeError, '400: Bad widget'):
            await self.client.answer_widget_query('q', {})

    async def test_parse_chat_query_and_answer(self):
        query = await types.WidgetQuery._parse(self.client, {
            'id': 'q', 'from': {'id': 5, 'is_bot': False, 'first_name': 'User'},
            'chat': {'id': -10042, 'type': 'supergroup', 'title': 'Widgets'},
            'message_id': 7, 'data': 'tap:0', 'chat_data': {'count': 0}, 'public_data': {'theme': 'blue'}})
        self.assertEqual((query.id, query.from_user.id, query.chat.id, query.message_id), ('q', 5, -10042, 7))
        self.assertEqual(query.chat.type, enums.ChatType.SUPERGROUP)
        self.assertEqual((query.data, query.chat_data, query.public_data), ('tap:0', {'count': 0}, {'theme': 'blue'}))
        self.assertIsNone(query.inline_message_id)
        self.client.answer_widget_query = AsyncMock(return_value=True)
        self.assertTrue(await query.answer({'count': 1}))
        self.client.answer_widget_query.assert_awaited_once_with('q', {'count': 1})

    async def test_parse_inline_query(self):
        query = await types.WidgetQuery._parse(self.client, {
            'id': 'inline-q', 'from': {'id': 5, 'first_name': 'User'},
            'inline_message_id': 'inline', 'data': 'tap:0', 'chat_data': '{"revision":0}', 'public_data': '{}'})
        self.assertEqual(query.inline_message_id, 'inline')
        self.assertIsNone(query.chat)
        self.assertIsNone(query.message_id)
        self.assertEqual(query.chat_data, {'revision': 0})

    async def test_bound_decorator(self):
        callback = AsyncMock()
        with patch.object(self.client, 'add_handler') as add:
            self.assertIs(self.client.on_widget_query(group=3)(callback), callback)
        handler, group = add.call_args.args
        self.assertIsInstance(handler, WidgetQueryHandler)
        self.assertIs(handler.callback, callback)
        self.assertEqual(group, 3)
        self.assertTrue(await handler.check(self.client, None))

    def test_unbound_decorator(self):
        async def callback(client, query):
            pass
        self.assertIs(Client.on_widget_query(group=2)(callback), callback)
        handler, group = callback.handlers[0]
        self.assertIsInstance(handler, WidgetQueryHandler)
        self.assertEqual(group, 2)

    async def test_send_shared_widget_payload(self):
        message = await self.client.send_shared_widget(42, 'widget-9', {'count': 0}, 'Shared!')
        self.assertEqual(self.payload('sendSharedWidget'), {
            'chat_id': 42, 'widget_id': 'widget-9', 'chat_data': '{"count":0}', 'caption': 'Shared!'})
        self.assertIsInstance(message, types.Message)

    async def test_edit_shared_widget_data_payload(self):
        self.respond(True)
        self.assertTrue(await self.client.edit_shared_widget_data('widget-9', {'theme': 'blue'}, 60))
        self.assertEqual(self.payload('editSharedWidgetData'), {
            'widget_id': 'widget-9', 'public_data': '{"theme":"blue"}', 'cache_time': 60})

    async def test_edit_shared_widget_data_validation(self):
        with self.assertRaises(ValueError):
            await self.client.edit_shared_widget_data('widget-9', {'v': 'x' * 1017})
        for cache_time in (4, 3601, True, 5.5, '30'):
            with self.assertRaises(ValueError):
                await self.client.edit_shared_widget_data('widget-9', {}, cache_time)
        self.http.assert_not_called()

    async def test_send_widget_shared_extras(self):
        await self.client.send_widget(42, '<html>x</html>', {'count': 0}, True,
                                      public_data={'theme': 'blue'}, width=300, height=200,
                                      caption='Hi', is_shared=True)
        self.assertEqual(self.payload('sendWidget'), {
            'chat_id': 42, 'html': '<html>x</html>', 'chat_data': '{"count":0}',
            'allow_queries': True, 'public_data': '{"theme":"blue"}',
            'width': 300, 'height': 200, 'caption': 'Hi', 'is_shared': True})

    async def test_edit_message_widget_public_data(self):
        self.respond(True)
        self.assertTrue(await self.client.edit_message_widget_data(
            42, 7, public_data={'theme': 'blue'}))
        self.assertEqual(self.payload('editMessageWidgetData'), {
            'chat_id': 42, 'message_id': 7, 'public_data': '{"theme":"blue"}'})

    async def test_parse_official_widget_query(self):
        query = await types.WidgetQuery._parse(self.client, {
            'id': 'q2', 'from': {'id': 5, 'is_bot': False, 'first_name': 'User'},
            'chat': {'id': 42, 'type': 'private'},
            'message_id': 7, 'chat_instance': 'inst-1', 'chat_type': 'private',
            'type': {'type': 'data'}, 'data': 'tap:1', 'widget_id': 'widget-9'})
        self.assertEqual(query.chat_instance, 'inst-1')
        self.assertEqual(query.chat_type, 'private')
        self.assertEqual(query.widget_id, 'widget-9')
        self.assertIsInstance(query.type, types.WidgetQueryTypeData)

    async def test_parse_widget_query_types(self):
        wallet = {'address': 'EQabc', 'amount': '1000', 'public_key': 'abcd', 'state_init': 'eQ=='}
        signed = await types.WidgetQuery._parse(self.client, {
            'id': 'q3', 'from': {'id': 5, 'first_name': 'User'},
            'chat_instance': 'inst-1',
            'type': {'type': 'sign_data', 'wallet': wallet, 'sign_data': '{"a":1}'},
            'data': 'sign:1'})
        self.assertIsInstance(signed.type, types.WidgetQueryTypeSignData)
        self.assertEqual(signed.type.wallet.address, 'EQabc')
        self.assertEqual(signed.type.sign_data, '{"a":1}')
        sent = await types.WidgetQuery._parse(self.client, {
            'id': 'q4', 'from': {'id': 5, 'first_name': 'User'},
            'chat_instance': 'inst-1',
            'type': {'type': 'sent_transaction', 'wallet': wallet, 'msg_hash': 'hash1'},
            'data': 'tx:1'})
        self.assertIsInstance(sent.type, types.WidgetQueryTypeSentTransaction)
        self.assertEqual(sent.type.msg_hash, 'hash1')

    async def test_parse_shared_widget_query(self):
        query = await types.SharedWidgetQuery._parse(self.client, {
            'id': 'sq', 'from': {'id': 5, 'is_bot': False, 'first_name': 'User'},
            'type': {'type': 'data'}, 'data': 'tap:0', 'widget_id': 'widget-9'})
        self.assertEqual((query.id, query.widget_id, query.data), ('sq', 'widget-9', 'tap:0'))
        self.assertIsInstance(query.type, types.WidgetQueryTypeData)
        self.client.answer_widget_query = AsyncMock(return_value=True)
        self.assertTrue(await query.answer({'ok': True}))
        self.client.answer_widget_query.assert_awaited_once_with('sq', {'ok': True})

    def test_widget_type_parse(self):
        widget = types.Widget._parse(self.client, {
            'id': 'widget-9', 'width': 300, 'height': 200, 'html': '<html>x</html>',
            'public_data': '{"theme":"blue"}', 'chat_data': '{"count":0}'})
        self.assertEqual((widget.id, widget.width, widget.height), ('widget-9', 300, 200))
        self.assertEqual((widget.public_data, widget.chat_data), ({'theme': 'blue'}, {'count': 0}))

    def test_input_widget_message_content(self):
        content = types.InputWidgetMessageContent(html='<html>x</html>', is_shared=True)
        self.assertEqual(content.to_dict(), {'html': '<html>x</html>', 'is_shared': True})
        shared = types.InputSharedWidgetMessageContent(widget_id='widget-9', chat_data={'count': 1})
        self.assertEqual(shared.to_dict(), {'widget_id': 'widget-9', 'chat_data': '{"count":1}'})

    async def test_raw_text_is_preserved_across_widget_methods(self):
        for text in ('plain text', ' { "count": 1 } ', '"quoted"', 'null', '0', '\u00e9' * 512):
            with self.subTest(text=text[:32]):
                self.respond(self.message)
                await self.client.send_widget(42, 'html', text, public_data=text)
                payload = self.payload('sendWidget')
                self.assertEqual((payload['chat_data'], payload['public_data']), (text, text))
                self.respond(self.message)
                await self.client.send_shared_widget(42, 'w', text)
                self.assertEqual(self.payload('sendSharedWidget')['chat_data'], text)
                self.respond(True)
                await self.client.answer_widget_query('q', text)
                self.assertEqual(self.payload('answerWidgetQuery')['data'], text)
                self.respond(True)
                await self.client.edit_message_widget_data(42, 7, text, public_data=text)
                payload = self.payload('editMessageWidgetData')
                self.assertEqual((payload['chat_data'], payload['public_data']), (text, text))
                self.respond(True)
                await self.client.edit_shared_widget_data('w', text)
                self.assertEqual(self.payload('editSharedWidgetData')['public_data'], text)
                content = types.InputWidgetMessageContent(html='html', chat_data=text, public_data=text)
                self.assertEqual(content.to_dict()['chat_data'], text)
                self.assertEqual(content.to_dict()['public_data'], text)
                shared = types.InputSharedWidgetMessageContent(widget_id='w', chat_data=text)
                self.assertEqual(shared.to_dict()['chat_data'], text)

    async def test_raw_text_utf8_limit_all_methods(self):
        text = '\u00e9' * 512 + 'x'
        for call in (lambda: self.client.send_widget(42, 'html', text),
                     lambda: self.client.send_widget(42, 'html', public_data=text),
                     lambda: self.client.send_shared_widget(42, 'w', text),
                     lambda: self.client.answer_widget_query('q', text),
                     lambda: self.client.edit_message_widget_data(42, 7, text),
                     lambda: self.client.edit_shared_widget_data('w', text),
                     lambda: types.InputWidgetMessageContent(html='html', chat_data=text).to_dict(),
                     lambda: types.InputSharedWidgetMessageContent(widget_id='w', chat_data=text).to_dict()):
            with self.subTest(call=call), self.assertRaises(ValueError):
                result = call()
                if asyncio.iscoroutine(result):
                    await result
        self.http.assert_not_called()

    async def test_edit_null_differs_from_omission_and_removal(self):
        self.respond(True)
        await self.client.edit_message_widget_data(42, 7, None, public_data=None)
        self.assertEqual(self.payload('editMessageWidgetData'), {
            'chat_id': 42, 'message_id': 7, 'chat_data': 'null', 'public_data': 'null'})

    def test_inline_python_values_are_serialized(self):
        content = types.InputWidgetMessageContent(html='html', chat_data={'v': 1}, public_data=[False, 0])
        self.assertEqual(content.to_dict(), {
            'html': 'html', 'chat_data': '{"v":1}', 'public_data': '[false,0]'})

    async def test_query_legacy_raw_state_does_not_break_parsing(self):
        for query_type, extra in ((types.WidgetQuery, {}),
                                  (types.SharedWidgetQuery, {'widget_id': 'w'})):
            query = await query_type._parse(self.client, {
                'id': 'q', 'from': {'id': 5}, 'data': 'tap', 'type': {'type': 'data'},
                'chat_data': 'plain text', 'public_data': '{"v":1}', **extra})
            self.assertEqual((query.chat_data, query.public_data), ('plain text', {'v': 1}))

    async def test_shared_bound_decorator(self):
        callback = AsyncMock()
        with patch.object(self.client, 'add_handler') as add:
            self.assertIs(self.client.on_shared_widget_query(group=3)(callback), callback)
        handler, group = add.call_args.args
        self.assertIsInstance(handler, SharedWidgetQueryHandler)
        self.assertIs(handler.callback, callback)
        self.assertEqual(group, 3)


if __name__ == '__main__':
    unittest.main()
