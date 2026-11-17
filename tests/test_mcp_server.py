"""The MCP server: tool mapping, file sandbox, the approval gate and the loop through MCP.

Plays an MCP client in memory (no network, tone voices): creates a production from text,
goes through approval (with and without the client asking the user), the translate and
scenes agent tasks with the server's own file tools, and a preview whose contact sheet
comes back as an image. Skipped when the `mcp` package is not installed.

    .venv/bin/python -m unittest tests.test_mcp_server -v
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from mcp import Client
    from mcp.types import ElicitResult
    from automatio import mcp_server as M
except ImportError:                                          # pragma: no cover
    M = None

from automatio import ROOT

try:
    from tests.test_pipeline_offline import PLAN, SCENE, SCRIPT, TOML_EXTRA
except ImportError:                                          # unittest discover -s tests
    from test_pipeline_offline import PLAN, SCENE, SCRIPT, TOML_EXTRA


def _text(res) -> str:
    return "\n".join(c.text for c in res.content if getattr(c, "type", "") == "text")


def _json(res) -> dict:
    return json.loads(res.content[0].text)


@unittest.skipIf(M is None, "the mcp package is not installed")
class ToolMapping(unittest.TestCase):
    def test_cli_commands_map_to_tools(self):
        self.assertEqual(M.tool_for("python -m automatio check scenes ep05"),
                         {"tool": "check", "arguments": {"slug": "ep05", "what": "scenes"}})
        self.assertEqual(M.tool_for("python -m automatio run ep05 --lang en")["arguments"],
                         {"slug": "ep05", "langs": "en"})
        ap = M.tool_for("python -m automatio approve ep05 --budget elevenlabs=9000")
        self.assertEqual((ap["tool"], ap["arguments"]["budget"]), ("approve", {"elevenlabs": 9000.0}))
        self.assertEqual(M.tool_for('python -m automatio complete review ep05 --notes "x"')["tool"], "complete_review")
        self.assertEqual(M.tool_for("python -m automatio preview ep05 s01,s02 --lang hi")["arguments"],
                         {"slug": "ep05", "sections": "s01,s02", "lang": "hi"})
        self.assertEqual(M.tool_for("python -m automatio next ep05")["tool"], "next_step")
        self.assertIsNone(M.tool_for("python -m automatio report"))
        self.assertIsNone(M.tool_for("ls -la"))

    def test_annotate_adds_tool_calls(self):
        d = M.annotate({"task": {"check": "python -m automatio check translate ep05",
                                 "then": "python -m automatio run ep05"},
                        "command": "python -m automatio run ep05  # re-checks; skips everything fresh"})
        self.assertEqual(d["task"]["check_mcp"]["tool"], "check")
        self.assertEqual(d["task"]["then_mcp"], {"tool": "run", "arguments": {"slug": "ep05"}})
        self.assertEqual(d["command_mcp"]["arguments"], {"slug": "ep05"})


@unittest.skipIf(M is None, "the mcp package is not installed")
class Sandbox(unittest.TestCase):
    def test_reads(self):
        for bad in (".env", ".env.local", ".git/config", "/etc/passwd", "../outside.txt", ".venv/pyvenv.cfg"):
            with self.assertRaises(M.ToolError, msg=bad):
                M.readable(bad)
        for ok in ("AGENTS.md", ".env.example", "agentic_video/style.py", "docs/SCENE_AUTHORING.md"):
            self.assertTrue(M.readable(ok).exists(), ok)

    def test_writes(self):
        for ok in ("productions/x-1/narration.json", "productions/x-1/production.toml",
                   "productions/x-1/scenes/s01_intro.py", "productions/x-1/scenes/kit/helpers.py"):
            M.writable(ok)
        for bad in ("productions/x-1/inputs/script.md", "agentic_video/style.py", "AGENTS.md", "voices.toml",
                    "productions/x-1/scenes/../../../AGENTS.md", "productions/x-1/narration.json.bak",
                    "output/x-1/report.md", "productions/X_bad/narration.json"):
            with self.assertRaises(M.ToolError, msg=bad):
                M.writable(bad)


@unittest.skipIf(M is None, "the mcp package is not installed")
class LoopOverMCP(unittest.TestCase):
    """The harness loop through MCP tools, offline."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="aa-mcp-test-"))
        cls.saved = dict(os.environ)
        os.environ.update(AA_PRODUCTIONS_DIR=str(cls.tmp / "productions"), AA_BUILD_DIR=str(cls.tmp / "build"),
                          AA_CACHE_DIR=str(cls.tmp / "cache"), AA_OUTPUT_DIR=str(cls.tmp / "output"),
                          AA_ENV_FILE=str(cls.tmp / "no.env"), AA_LOCAL_DIR=str(cls.tmp / "local"))
        os.environ.pop("ELEVENLABS_API_KEY", None)

    @classmethod
    def tearDownClass(cls):
        os.environ.clear()
        os.environ.update(cls.saved)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_loop(self):
        asyncio.run(self._loop())

    async def _loop(self):
        answers = []

        async def elicit(context, params):
            return answers.pop(0)

        async with Client(M.server, elicitation_callback=elicit) as c:
            async def call(name, **args):
                res = await c.call_tool(name, args)
                self.assertFalse(res.is_error, f"{name} {args}: {_text(res)[:2000]}")
                return res

            # a production from text, with the test voices (written into production.toml like the CLI test)
            out = _json(await call("new_production", slug="mcp-test", title="MCP test", script_text=SCRIPT,
                                   plan_text=PLAN))
            self.assertTrue(out["ok"], out)
            prod = self.tmp / "productions/mcp-test"
            toml = (prod / "production.toml").read_text(encoding="utf-8")
            toml = toml.replace('voice = "hindi-adam"', 'voice = "test-tone-hi"').replace(
                'voice = "english-andrew"', 'voice = "test-tone-en"') + TOML_EXTRA
            await call("write_file", path=str(prod / "production.toml"), content=toml)
            listed = _json(await call("list_productions"))["productions"]
            self.assertEqual([p["slug"] for p in listed], ["mcp-test"])

            # 1. approval: never without the user's yes; the client is asked when it can be
            o = _json(await call("run", slug="mcp-test", wait_seconds=120))
            self.assertEqual(o["state"], "needs_approval", o)
            self.assertEqual(o["approval"]["command_mcp"]["tool"], "approve")
            r = _json(await call("approve", slug="mcp-test", by="test", confirmed_by_user=False))
            self.assertEqual(r["state"], "not_approved")
            answers.append(ElicitResult(action="decline"))
            r = _json(await call("approve", slug="mcp-test", by="test", confirmed_by_user=True))
            self.assertEqual(r["state"], "not_approved")
            answers.append(ElicitResult(action="accept", content={"approve": True, "name": "Test User"}))
            r = _json(await call("approve", slug="mcp-test", by="test", confirmed_by_user=True))
            self.assertTrue(r["ok"], r)
            self.assertTrue(r["asked_user_directly"])
            self.assertEqual(r["approval"]["by"], "Test User")

            # 2. translation through the server's file tools
            o = _json(await call("run", slug="mcp-test", wait_seconds=120))
            self.assertEqual((o["state"], o["task"]["id"]), ("needs_agent", "translate"), o)
            self.assertEqual(o["task"]["check_mcp"], {"tool": "check", "arguments": {"slug": "mcp-test",
                                                                                      "what": "translate"}})
            task = _json(await call("get_task", slug="mcp-test"))
            self.assertIn("translate", task["content"].lower())
            bad = await c.call_tool("write_file", {"path": str(prod / "narration.json"), "content": "{oops"})
            self.assertTrue(bad.is_error)
            narr = json.loads(await_text(await call("read_file", path=str(prod / "narration.json"))))
            lines = narr["sections"][0]["lines"]
            lines[0]["hi"] = "यह एक छोटा परीक्षण है। यह पूरी पाइपलाइन की जाँच करता है।"
            lines[1]["en"] = "Now the agent {wave}waves goodbye."
            lines[1]["hi"] = "अब Agent {wave}अलविदा कहता है।"
            await call("write_file", path=str(prod / "narration.json"),
                       content=json.dumps(narr, ensure_ascii=False, indent=2))
            self.assertTrue(_json(await call("check", slug="mcp-test", what="translate"))["ok"])

            # 3. scenes, then a preview whose contact sheet comes back as an image
            o = _json(await call("run", slug="mcp-test", wait_seconds=120))
            self.assertEqual(o["task"]["id"], "scenes", o)
            await call("write_file", path=str(prod / "scenes/s01_hello.py"), content=SCENE)
            self.assertTrue(_json(await call("check", slug="mcp-test", what="scenes"))["ok"])
            res = await call("preview", slug="mcp-test", sections="s01", lang="en", wait_seconds=0)
            pv = json.loads(res.content[0].text)
            if pv.get("state") == "running":                       # slow machine: keep waiting
                res = await call("wait", job_id=pv["job_id"], wait_seconds=300)
                pv = json.loads(res.content[0].text)
            self.assertTrue(pv["ok"], pv)
            kinds = [getattr(x, "type", "") for x in res.content]
            self.assertIn("image", kinds)
            sheet = pv["previews"][0]["sheet"]
            self.assertEqual([getattr(x, "type", "") for x in (await call("view_image", path=sheet)).content],
                             ["text", "image"])

            # the docs are resources, and the prompt names the loop
            docs = [str(r.uri) for r in (await c.list_resources()).resources]
            self.assertIn("automatio://docs/AGENTS.md", docs)
            pr = await c.get_prompt("produce_video", {"slug": "mcp-test"})
            self.assertIn("mcp-test", pr.messages[0].content.text)


def await_text(res) -> str:
    return res.content[0].text


class LocalOverrides(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aa-local-"))
        self.saved = os.environ.get("AA_LOCAL_DIR")
        os.environ["AA_LOCAL_DIR"] = str(self.tmp)

    def tearDown(self):
        if self.saved is None:
            os.environ.pop("AA_LOCAL_DIR", None)
        else:
            os.environ["AA_LOCAL_DIR"] = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_no_overrides_is_the_house_setup(self):
        from automatio.config import HOUSE_DEFAULTS, default_voices, load_voices
        self.assertEqual(default_voices(), HOUSE_DEFAULTS)
        self.assertIn("hindi-adam", load_voices())

    def test_local_profiles_and_defaults(self):
        from automatio.config import default_voices, load_voices
        (self.tmp / "voices.toml").write_text(
            '[defaults]\nen = "my-english"\n\n[my-english]\nlanguage = "en"\nprovider = "edge"\n'
            'voice = "en-US-GuyNeural"\n', encoding="utf-8")
        v = load_voices()
        self.assertIn("my-english", v)
        self.assertIn("hindi-adam", v)                                  # house profiles stay
        self.assertEqual(default_voices(), {"hi": "hindi-adam", "en": "my-english"})

    def test_house_profiles_are_never_redefined(self):
        from automatio.config import load_voices
        from automatio.errors import ConfigError
        (self.tmp / "voices.toml").write_text('[hindi-adam]\nlanguage = "hi"\nprovider = "edge"\nvoice = "x"\n',
                                              encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_voices()

    def test_example_file_parses(self):
        from automatio.config import load_voices
        shutil.copy(ROOT / "local" / "voices.example.toml", self.tmp / "voices.toml")
        v = load_voices()
        self.assertEqual(v["my-hindi"].draft, "hindi-madhur-draft")


if __name__ == "__main__":
    unittest.main()
