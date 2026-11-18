# Telegram Widgets - Bot API 10.4 compatibility

Checked against Telegram's current official documentation for Bot API 10.4
(November 9, 2026) and the TelegramWidget JavaScript runtime:

- https://core.telegram.org/bots/api#widget
- https://core.telegram.org/bots/widgets
- https://github.com/telegramdesktop/tdesktop/blob/dev/Telegram/SourceFiles/mtproto/scheme/api.tl

## Supported widget surface

- `send_widget`, `send_shared_widget`, `answer_widget_query`,
  `edit_message_widget_data`, `edit_shared_widget_data`.
- `Widget`, `WidgetQuery`, `SharedWidgetQuery`, data/sign-data/transaction
  query variants and `WidgetQueryWallet`.
- `on_widget_query` and `on_shared_widget_query`, with widget-only Bot API
  polling alongside the existing MTProto dispatcher.
- `InputWidgetMessageContent` and `InputSharedWidgetMessageContent` with
  `to_dict()` for Bot API inline results.
- Widget send options for topics, captions, caption entities and placement,
  notification/content protection/broadcast options, message effects,
  replies and reply markup. Caption entities and reply objects use Bot API
  dictionaries.

## Native MTProto support

The repository already pins layer 233, whose raw schema includes widgets.
Set `widget_transport="mtproto"` when constructing `Client` to use native
widget sends, shared sends, answers and chat/inline/shared edits. Native bot
sessions do not need the bot token again after authorization. The default
`widget_transport="botapi"` preserves the previous HTTPS bridge.

Native widget queries from chat messages, inline messages and forwarded shared
widgets reach the existing widget handlers without an extra Bot API poller.
Only the selected transport delivers high-level queries, preventing duplicates.
Widget messages and external replies expose `.widget`; widget media has
`MessageMediaType.WIDGET` and a `filters.widget` filter. Layer 233 widget state
updates refresh cached messages and reach edited-message handlers. Compressed
HTML is decoded with zlib; invalid payloads use unsupported-media fallback.
Both inline content types now implement native `write()` in addition to
Bot API `to_dict()`, and work in `InlineQueryResultArticle`.

## Compatibility fixes

The official data fields are **text strings**, not JSON objects. Strings are
now sent unchanged, including arbitrary text, pre-encoded JSON and empty text.
Python dictionaries, lists and other JSON values remain accepted and are
serialized once to compact JSON strings before sending. Size checks measure
the actual field's UTF-8 bytes, without counting the outer request's JSON
escaping. Each data field allows 0-1,024 bytes. HTML allows 1-32,768 bytes
and at most 4,096 bytes after zlib level 9 compression.

For `edit_message_widget_data`, omitted fields now stay unchanged instead of
resetting chat state to an empty object. Pass `""` to clear data; explicit
`None` serializes to the string `"null"`. To reset to an empty object, pass
`{}` explicitly. Sending without `chat_data` retains the existing default
empty object, now sent as `"{}"`.

`answer_widget_query` and both query-bound `answer()` methods allow omitted
data. An explicit Python `None` sends the string `"null"`. Answers reach only
the requesting widget and do not edit its persistent state; answer within
15 seconds and use the separate edit methods to persist changes.

Bot API widget requests honor the client's `test_mode`: test requests use
`https://api.telegram.org/bot<token>/test/<method>`. The widget poller uses
the same environment. Use a bot token created in the selected environment.

`Widget` response data continues to decode JSON text when possible and keeps
other text unchanged. The legacy `chat_data` and `public_data` query extensions
behave the same way; official queries do not include these state fields.
Keep authoritative state in bot storage.

The tap-counter example parses JavaScript `chatData` and request `result` as
JSON text, handles `chatDataChanged`, ignores stale revisions, shows request
errors and persists successful taps with `edit_message_widget_data`. Its
in-memory bot storage is for demonstration; deployed bots need durable storage.

Widget methods, decorators and types are registered with the docs compiler;
see [the widget guide](docs/source/features/widgets.rst) and
[example](examples/widget_bot.py).

## Telegram restrictions and scope

- In production, widgets currently work only in private chats with the bot
  and automatically have protected content. Groups and inline widgets work
  on Telegram's test server. Widget messages cannot be copied with
  `copyMessage`/`copyMessages`.
- In HTTPS mode, use one Bot API poller and no webhook. Widget handlers poll
  `widget_query` and `shared_widget_query` only.
- Shared public data can be edited at most once per second. `cache_time` is
  an integer from 5 to 3,600 seconds; omitted values keep the current setting
  (30 by default). Shared widgets must call `watchPublicData()` to receive
  live public-data changes while open.
- `wallet_card` is preserved as a Bot API dictionary or native wallet card. Other Bot API 10.4
  features and the repository's separately pinned MTProto/Bot API schema are
  outside this widget compatibility change.

## Validation

`tests/test_widget_mtproto.py` checks native sends, edits, answers, inline
content, compressed media, queries, cache state updates and external replies.
`tests/test_widget.py` checks HTTPS wire payloads, raw text and JSON conversion,
UTF-8 size boundaries, data removal/omission/null, query parsing, test-mode
routing, handlers and polling. `tests/test_widget_example.py` executes the
example's JavaScript against the runtime's text-state and event contract.
These checks use mocked HTTPS and a local JavaScript runtime; they do not
send messages to a live Telegram bot.
