# Widgets update — Bot API 10.4 (9 Nov 2026)

Base: wzgram 3.1.7 (Pyrogram fork). Widget support was added locally on top
of it; this update completes the official Bot API 10.4 widget surface.
Tests: `python3 -B tests/test_widget.py` — 47/47 pass (original 30 retained).

## Follow-up audit fixes
- Added the missing Bot API send options to both widget send methods:
  topic targeting, caption formatting and placement, notification/content
  protection/broadcast options, message effects, replies and reply markup.
  Caption entities and reply objects use Bot API dictionaries.
- Added caption formatting and placement to both inline widget content types.
- `answer_widget_query` and both bound `answer()` methods now allow omitted
  data; explicit `None` still sends JSON null. Empty data is accepted across
  widget methods. Answers reach only the requesting widget and do not edit
  state; the answer must be sent within 15 seconds.
- Enforced the official minimum of one byte of HTML. `WidgetQuery` can also
  be constructed without the local-only state fields.
- Confirmed all widget/query/wallet fields, handlers and exports. Added
  dispatcher tests for both query routes, polling offsets, queue retries
  and startup. No dispatcher changes were needed. Existing default payloads
  of `send_widget` and `edit_message_widget_data` are unchanged.

## Added in this update
- `send_shared_widget(chat_id, widget_id, chat_data=None, caption=None)` —
  send again a shared widget created by the bot (`sendSharedWidget`).
- `edit_shared_widget_data(widget_id, public_data, cache_time=None)` —
  change public data of a shared widget, at most once per second
  (`editSharedWidgetData`). `cache_time` is 5–3600, default 30.
- `SharedWidgetQuery` type + `shared_widget_query` update polling +
  `SharedWidgetQueryHandler` + `@client.on_shared_widget_query()`.
- `Widget` type (`id`, `width`, `height`, `html`, `public_data`,
  `chat_data`); Bot API widget messages returned by `send_widget` /
  `send_shared_widget` now carry a `.widget` attribute.
- `WidgetQueryType` family: `WidgetQueryTypeData` (with optional
  `wallet_card`, kept raw — this library has no `TonWalletCard` type yet),
  `WidgetQueryTypeSignData`, `WidgetQueryTypeSentTransaction`, and
  `WidgetQueryWallet`. `WidgetQuery` now also parses the official fields
  `chat_instance`, `chat_type`, `type` and `widget_id`.
- `InputWidgetMessageContent` / `InputSharedWidgetMessageContent` with
  `to_dict()` for Bot API inline-query results. Note: widgets can't be
  sent in response to inline queries in the production environment.
- `send_widget` extras (all optional, old calls unchanged): `public_data`,
  `width`, `height`, `caption`, `is_shared=True` to create a shared widget.
- `edit_message_widget_data` now also accepts `public_data` (and `""` to
  remove data, per the official API).

## Already present before this update
`send_widget`, `answer_widget_query`, `edit_message_widget_data`,
`WidgetQuery` + `on_widget_query`, dispatcher widget polling, size
validation (HTML 32,768 raw / 4,096 zlib-9, state 1,024 bytes JSON).

## Example — shared widget
```python
sent = await app.send_widget(chat.id, html, {"count": 0},
                             allow_queries=True, is_shared=True)
widget_id = sent.widget.id  # from the Widget on the returned Message

await app.send_shared_widget(chat.id, widget_id, {"count": 0})
await app.edit_shared_widget_data(widget_id, {"theme": "blue"}, cache_time=60)

@app.on_shared_widget_query()
async def on_shared(client, query):
    await query.answer({"ok": True})
```

## Deliberately left out / known deviations
- `Widget` on `Message` / `ExternalReplyInfo` for MTProto messages: widgets
  are Bot API only, so the `widget` field is attached only to messages
  returned by the widget methods in `pyrogram/methods/bots/_widget.py`.
  It is not added to the 10,000-line MTProto `Message._parse`.
- `copyMessage` / `copyMessages` cannot copy widget messages (official
  rule). No guard was added in the library; the Bot API returns the error.
- Other Bot API 10.4 sections (Ephemeral messages, TON wallet cards,
  Chat share themes, Gifts `getUniqueGift` / `deleteBusinessAccountGift`)
  are not part of this widget update. Some of those types already exist
  in this codebase (for example ephemeral-message support in `Message`);
  the rest would need a layer/schema upgrade and are out of scope here.
- Local convention, kept for backward compatibility: `chat_data` /
  `public_data` / `data` are passed as JSON values and validated to
  1,024 bytes. The official Bot API documents them as JSON *strings*.
  The existing widget bots in `../widget-bot` rely on the JSON-value
  convention (and on `chat_data` / `public_data` arriving on the query),
  so it was not changed. Verify the new shared-widget methods against
  the live Bot API before relying on them in production.
- Codex was asked to do this update first and crashed twice (exit 101,
  Rust panic "failed printing to stderr: Resource temporarily
  unavailable") with no files changed. This update was implemented
  directly instead, following the existing widget code patterns.
