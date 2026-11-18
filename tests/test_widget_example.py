"""Check the example against TelegramWidget's text and event contract."""
import ast
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is needed for the widget runtime check")
class WidgetExampleTests(unittest.TestCase):
    def test_counter_handles_text_state_events_reload_and_errors(self):
        tree = ast.parse((ROOT / "examples/widget_bot.py").read_text(encoding="utf-8"))
        html = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "HTML"
                            for target in node.targets))
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        harness = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const script = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
function boot(text) {
  const events = {}, requests = [];
  const elements = {tap: {}, count: {}, status: {}};
  const widget = {
    chatData: text,
    onEvent: (name, callback) => { events[name] = callback; },
    request: async (data) => { requests.push(data); return {result: '{"count":4,"revision":4}'}; }
  };
  vm.runInNewContext(script, {
    window: {TelegramWidget: widget},
    document: {getElementById: (id) => elements[id]}
  });
  return {events, requests, elements, widget};
}
(async () => {
  const app = boot('{"count":3,"revision":3}');
  assert.equal(app.elements.count.textContent, 'Taps: 3');
  await app.elements.tap.onclick();
  assert.deepEqual(app.requests, ['tap:3']);
  assert.equal(app.elements.count.textContent, 'Taps: 4');
  assert.equal(app.elements.tap.disabled, false);
  app.widget.chatData = '{"count":5,"revision":5}';
  app.events.chatDataChanged();
  assert.equal(app.elements.count.textContent, 'Taps: 5');
  app.widget.chatData = '{"count":2,"revision":2}';
  app.events.chatDataChanged();
  assert.equal(app.elements.count.textContent, 'Taps: 5');
  assert.equal(boot('{"count":5,"revision":5}').elements.count.textContent, 'Taps: 5');
  app.widget.request = async () => { throw {code: 'TIMEOUT'}; };
  await app.elements.tap.onclick();
  assert.equal(app.elements.status.textContent, 'Not sent: TIMEOUT');
  assert.equal(app.elements.tap.disabled, false);
  assert.equal(app.elements.count.textContent, 'Taps: 5');
  assert.equal(boot(null).elements.count.textContent, 'Taps: 0');
  assert.equal(boot('invalid JSON').elements.status.textContent, 'Invalid state from the bot');
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(
            [shutil.which("node"), "-e", harness], input=json.dumps(script),
            capture_output=True, text=True, encoding="utf-8", timeout=15
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
