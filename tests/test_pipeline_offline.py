"""End-to-end pipeline test through the harness protocol, fully offline (~1 minute).

The test plays the harness: it creates a production from a script and a plan, approves
it, performs the agent tasks the pipeline hands out (translation, scene authoring) and
runs until delivery. Voices are the `tone` test profiles (no network, no credentials);
rendering, mixing, encoding, subtitles, verification and packaging are real.

    .venv/bin/python -m unittest tests.test_pipeline_offline -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automatio import ROOT

SCRIPT = """# Offline Test

## 01. Hello

This is a tiny test. It checks the whole pipeline.

Now the agent waves goodbye.
"""
PLAN = """# Plan

## 01. Hello
TIME: 0:00–0:10

A title fades in, then turns teal when the agent waves.
"""
SCENE = '''from agentic_video.prelude import *


class S01Hello(VoiceScene):
    SECTION = "s01"

    def construct(self):
        self.show_chapter()
        t = en("Offline test", 60, FG)
        self.narrate("s01_01", FadeIn(t, shift=UP * 0.1), run_time=0.6)
        with self.say("s01_02") as v:
            self.wait_until(v.cue("wave") - 0.2)
            self.play(t.animate.set_color(TEAL), run_time=0.4)
        self.clear_all(0.4)
'''
TOML_EXTRA = """
[video]
width = 854
height = 480
fps = 15
quality = "l"
crf = 30
preset = "ultrafast"

[review]
draft = false

[render]
jobs = 2
"""


class OfflinePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="aa-test-"))
        cls.env = dict(os.environ, AA_PRODUCTIONS_DIR=str(cls.tmp / "productions"), AA_BUILD_DIR=str(cls.tmp / "build"),
                       AA_CACHE_DIR=str(cls.tmp / "cache"), AA_OUTPUT_DIR=str(cls.tmp / "output"),
                       AA_ENV_FILE=str(cls.tmp / "no.env"))
        cls.env.pop("ELEVENLABS_API_KEY", None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def aa(self, *args, expect=None):
        cp = subprocess.run([sys.executable, "-m", "automatio", *args, "--json"], cwd=ROOT, env=self.env,
                            capture_output=True, text=True, timeout=900)
        try:
            out = json.loads(cp.stdout)
        except json.JSONDecodeError:
            self.fail(f"non-JSON output from {args}: {cp.stdout[-2000:]}\n{cp.stderr[-3000:]}")
        if expect is not None:
            self.assertEqual(cp.returncode, expect, f"{args} -> {json.dumps(out, indent=1)[:3000]}\n{cp.stderr[-3000:]}")
        return out

    def test_full_run(self):
        (self.tmp / "in").mkdir()
        (self.tmp / "in/script.md").write_text(SCRIPT, encoding="utf-8")
        (self.tmp / "in/plan.md").write_text(PLAN, encoding="utf-8")
        self.aa("new", "offline-test", "--script", str(self.tmp / "in/script.md"), "--plan",
                str(self.tmp / "in/plan.md"), "--voice", "hi=test-tone-hi", "--voice", "en=test-tone-en", expect=0)
        prod = self.tmp / "productions/offline-test"
        with open(prod / "production.toml", "a", encoding="utf-8") as fh:
            fh.write(TOML_EXTRA)

        # 1. the approval gate comes first
        o = self.aa("run", "offline-test", expect=11)
        self.assertEqual(o["state"], "needs_approval")
        self.assertEqual(o["approval"]["estimate"], {})          # only free voices
        self.aa("approve", "offline-test", "--by", "unit test", expect=0)

        # 2. translation is an agent task
        o = self.aa("run", "offline-test", expect=10)
        self.assertEqual(o["task"]["id"], "translate")
        self.assertTrue((ROOT / o["task"]["file"]).exists() or Path(o["task"]["file"]).exists())
        narr = json.loads((prod / "narration.json").read_text(encoding="utf-8"))
        lines = narr["sections"][0]["lines"]
        self.assertEqual([ln["en"] for ln in lines], ["This is a tiny test. It checks the whole pipeline.",
                                                     "Now the agent waves goodbye."])
        lines[0]["hi"] = "यह एक छोटा परीक्षण है। यह पूरी पाइपलाइन की जाँच करता है।"
        lines[1]["en"] = "Now the agent {wave}waves goodbye."
        lines[1]["hi"] = "अब Agent {wave}अलविदा कहता है।"
        (prod / "narration.json").write_text(json.dumps(narr, ensure_ascii=False, indent=2), encoding="utf-8")
        self.aa("check", "translate", "offline-test", expect=0)

        # 3. scene authoring is an agent task
        o = self.aa("run", "offline-test", expect=10)
        self.assertEqual(o["task"]["id"], "scenes")
        (prod / "scenes/s01_hello.py").write_text(SCENE, encoding="utf-8")
        self.aa("check", "scenes", "offline-test", expect=0)

        # 4. everything else is automatic
        o = self.aa("run", "offline-test", expect=0)
        self.assertEqual(o["state"], "done")
        out = self.tmp / "output/offline-test"
        man = json.loads((out / "manifest.json").read_text())
        for lang, label in (("hi", "hindi"), ("en", "english")):
            d = out / label
            for f in ("final-video.mp4", "subtitles-en.srt", "subtitles-en.vtt", "narration/narration.json",
                      "narration/voice-track.flac", "assets/timeline.json"):
                self.assertTrue((d / f).exists(), f"{label}/{f} missing")
            probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
                                               str(d / "final-video.mp4")], capture_output=True, text=True).stdout)
            kinds = sorted(s["codec_type"] for s in probe["streams"])
            self.assertEqual(kinds, ["audio", "video"])               # no subtitle stream
            ver = man["versions"][lang]["verification"]
            self.assertNotEqual(ver["status"], "fail", json.dumps(ver, indent=1))
            self.assertTrue((d / "narration/lines/s01_02.wav").exists())
        self.assertFalse(man["subtitles"]["burned_in"])
        self.assertTrue((out / "report.md").exists())

        # 5. a second run is a no-op (everything fresh), and the protocol says done
        o = self.aa("run", "offline-test", expect=0)
        st = self.aa("status", "offline-test", expect=0)
        self.assertEqual(st["next"]["action"], "done")


if __name__ == "__main__":
    unittest.main()
