import asyncio

from wzgram import Client, filters

app = Client(
    "widget_bot",
    api_id=12345,
    api_hash="0123456789abcdef0123456789abcdef",
    bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    widget_transport="mtproto"
)

HTML = """<!doctype html><meta charset="utf-8"><button id="tap">Tap</button>
<p id="count"></p><p id="status"></p><script>
const widget = window.TelegramWidget;
let state = {count: 0, revision: 0};
const tap = document.getElementById('tap');
const count = document.getElementById('count');
const status = document.getElementById('status');
function apply(text) {
  try {
    const next = JSON.parse(text);
    if (next && next.revision >= state.revision) { state = next; draw(); }
  } catch (error) { status.textContent = 'Invalid state from the bot'; }
}
function draw() { count.textContent = 'Taps: ' + state.count; }
tap.onclick = async () => {
  tap.disabled = true;
  status.textContent = 'Sending...';
  try {
    const {result} = await widget.request('tap:' + state.revision);
    status.textContent = '';
    apply(result);
  } catch (error) {
    status.textContent = 'Not sent: ' + (error.code || 'UNKNOWN');
  } finally { tap.disabled = false; }
};
if (widget) {
  widget.onEvent('chatDataChanged', () => apply(widget.chatData));
  apply(widget.chatData);
} else { tap.disabled = true; }
draw();
</script>"""

# Demo state is bot-owned; use durable storage in a deployed bot.
states = {}
lock = asyncio.Lock()


@app.on_message(filters.command("widget"))
async def widget(client, message):
    state = {"count": 0, "revision": 0}
    sent = await client.send_widget(message.chat.id, HTML, state, allow_queries=True)
    states[(sent.chat.id, sent.id)] = state


@app.on_widget_query()
async def tap(client, query):
    key = (query.chat.id, query.message_id) if query.chat else query.inline_message_id
    async with lock:
        state = states.get(key, {"count": 0, "revision": 0})
        if key in states and query.data == "tap:" + str(state["revision"]):
            state = {"count": state["count"] + 1, "revision": state["revision"] + 1}
            # Answers reach only this widget. Persist state for reloads and
            # other open copies using the separate Bot API edit method.
            await client.edit_message_widget_data(
                query.chat.id, query.message_id, state
            )
            states[key] = state
        # Answer every query, including stale revisions and invalid tap payloads.
        await client.answer_widget_query(query.id, state)


app.run()
