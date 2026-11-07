"""Unit tests: narration/markers, subtitles, secrets, voice cache keys, retries, budget.

    .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automatio import ROOT
from automatio import narration as N
from automatio import subtitles as S
from automatio.config import SubtitleSettings, load_voices
from automatio.errors import BudgetExceeded, ProviderError, QuotaExceeded


class TestMarkers(unittest.TestCase):
    def test_compose_positions_survive_respelling(self):
        text = "आपने एक AI से {ask}पूछा, इस {err}Error का मतलब?"
        spoken, pos = N.compose(text, {"AI": "एआई"})
        self.assertEqual(spoken, "आपने एक एआई से पूछा, इस Error का मतलब?")
        self.assertTrue(spoken[pos["ask"]:].startswith("पूछा"))
        self.assertTrue(spoken[pos["err"]:].startswith("Error"))

    def test_display_strips_markers_and_tags(self):
        self.assertEqual(N.display("[warmly] Hello {x}there."), "Hello there.")
        self.assertEqual(N.markers_in("a {x}b {y_2}c"), ["x", "y_2"])

    def test_marker_times(self):
        spoken, pos = N.compose("one two {m}three four")
        words = [[0.0, 0.2, "one"], [0.3, 0.2, "two"], [0.6, 0.3, "three"], [1.0, 0.2, "four"]]
        self.assertAlmostEqual(N.marker_times(spoken, words, pos)["m"], 0.6)

    def test_sentences(self):
        self.assertEqual(N.sentences("एक। दो? Three. four!"), ["एक।", "दो?", "Three.", "four!"])

    def test_validate_catches_parity_markers_and_untranslated(self):
        data = {"schema": N.SCHEMA, "sections": [{"key": "s01", "chapter": {"number": "01", "title": "T"}, "lines": [
            {"key": "s01_01", "en": "One. Two {a}words.", "hi": "एक।"},
            {"key": "s01_02", "en": "Same text.", "hi": "Same text."},
            {"key": "s01_03", "en": "Fine {b}here.", "hi": "यहाँ {c}ठीक।"}]}]}
        rep = N.validate(N.Narration(Path("x.json"), data), langs=["hi", "en"], subtitle_lang="en", source_lang="en")
        errs = " | ".join(rep["errors"])
        self.assertIn("1 sentence(s) but the en subtitle text has 2", errs)
        self.assertIn("markers differ", errs)
        self.assertIn("untranslated", errs)

    def test_ingest_and_completeness(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "script.md"
            p.write_text("# Title\n\n## 01. Intro: why\n\nFirst sentence here. Second one follows.\n\n"
                         "[VISUAL: a robot waves]\n\n## 02. Next\n\nAnother part. And more text here!\n",
                         encoding="utf-8")
            prod = mock.Mock(script=p, source_language="en", title="Title")
            data = N.ingest(prod, [])
            self.assertEqual([s["chapter"] for s in data["sections"]],
                             [{"number": "01", "title": "Intro"}, {"number": "02", "title": "Next"}])
            self.assertEqual(data["excluded"][0]["text"], "[VISUAL: a robot waves]")
            narr = N.Narration(Path(d) / "n.json", data)
            self.assertEqual(N.completeness(prod, narr)["coverage"], 1.0)
            data["sections"][1]["lines"][0]["en"] = "Another part."           # the agent dropped a sentence
            comp = N.completeness(prod, narr)
            self.assertLess(comp["coverage"], 0.985)
            self.assertIn("and more text here", comp["missing"][0])


class TestSubtitles(unittest.TestCase):
    def test_reproduces_previous_hindi_srt(self):
        """The ported aligner must give byte-identical cues for the released video."""
        man_p, srt_p = ROOT / "assets/voice/manifest.json", ROOT / "output/agentic_ai_intro_hi_1080p.srt"
        cues_d, scenes_d = ROOT / "build/cues", ROOT / "build/scenes"
        if not (man_p.exists() and srt_p.exists() and cues_d.exists() and scenes_d.exists()):
            self.skipTest("legacy artefacts of the first production are not present")
        from automatio.util import probe_duration
        man = json.loads(man_p.read_text())
        off, placed = 0.0, []
        for sec in [f"s0{i}" for i in range(1, 10)]:
            cues = json.loads((cues_d / f"{sec}.json").read_text())
            for c in cues["cues"]:
                e = man[c["key"]]
                placed.append((off + c["start"], {"subtitle": e["text"], "spoken": e["tts"], "words": e["words"]}))
            off += probe_duration(scenes_d / f"{sec}.mp4")
        cues = S.build(placed, same_language=False, settings=SubtitleSettings())
        self.assertEqual(S.srt_text(cues), srt_p.read_text(encoding="utf-8"))

    def test_same_language_word_timing(self):
        words = [[0.0, 0.3, "Imagine"], [0.35, 0.3, "you're"], [0.7, 0.4, "running"], [1.15, 0.2, "a"],
                 [1.4, 0.5, "program,"], [2.5, 0.2, "and"], [2.75, 0.5, "suddenly"], [3.3, 0.2, "an"],
                 [3.55, 0.4, "error"], [4.0, 0.5, "appears."]]
        text = "Imagine you're running a program, and suddenly an error appears."
        cues = S.line_cues(10.0, text, text, words, same_language=True)
        self.assertEqual([c[2] for c in cues], ["Imagine you're running a program,", "and suddenly an error appears."])
        self.assertAlmostEqual(cues[1][0], 12.5)          # starts exactly when "and" is spoken
        self.assertAlmostEqual(cues[1][1], 14.5)

    def test_srt_vtt_roundtrip_and_checks(self):
        cues = [(0.0, 1.5, "Hello & <you>"), (1.6, 3.0, "Second cue")]
        with tempfile.TemporaryDirectory() as d:
            for name, txt in (("a.srt", S.srt_text(cues)), ("a.vtt", S.vtt_text(cues))):
                p = Path(d) / name
                p.write_text(txt, encoding="utf-8")
                back = S.parse(p)
                self.assertEqual([c[2] for c in back], [c[2] for c in cues])
        self.assertTrue(S.vtt_text(cues).startswith("WEBVTT\n"))
        bad = S.check([(0, 2, "a"), (1, 3, "b")], 10, SubtitleSettings())
        self.assertTrue(any("overlaps" in i["issue"] for i in bad))


class TestSecrets(unittest.TestCase):
    def test_redaction_and_scrubbed_env(self):
        from automatio import secrets
        fake = "sk_" + "a1b2c3d4" * 6
        with tempfile.TemporaryDirectory() as d:
            env = Path(d) / ".env"
            env.write_text(f"ELEVENLABS_API_KEY={fake}\n# comment\nOTHER='x y'\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"AA_ENV_FILE": str(env)}):
                secrets.CREDS.reload()
                self.assertEqual(secrets.CREDS.get("ELEVENLABS_API_KEY"), fake)
                self.assertNotIn(fake, secrets.redact(f"error for key {fake} in url ?k={fake}"))
                self.assertNotIn(fake, secrets.redact("token sk_" + "Z" * 30))
            with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": fake, "SOME_TOKEN": "abc123456789"}):
                e = secrets.scrubbed_env()
                self.assertNotIn("ELEVENLABS_API_KEY", e)
                self.assertNotIn("SOME_TOKEN", e)
        secrets.CREDS.reload()


class TestInterrupt(unittest.TestCase):
    def test_terminate_children_and_no_new_work(self):
        import threading
        import time
        from automatio import util
        from automatio.errors import StageFailed
        errs = []

        def slow():
            try:
                util.run(["sleep", "30"], what="sleep")
            except StageFailed as e:
                errs.append(e)
        t = threading.Thread(target=slow)
        t.start()
        time.sleep(0.5)
        t0 = time.time()
        try:
            self.assertEqual(util.terminate_children(), 1)
            t.join(10)
            self.assertFalse(t.is_alive())
            self.assertLess(time.time() - t0, 6)              # terminated, not waited out
            self.assertEqual(len(errs), 1)
            with self.assertRaises(StageFailed):              # nothing new starts after an interrupt...
                util.run(["true"], what="true")
            util.run(["true"], what="probe", essential=True)  # ...except quick essential probes
        finally:
            util.STOPPING.clear()


class TestVoice(unittest.TestCase):
    def test_cache_key_matches_previous_production(self):
        """Clips of the released video are reused: same (settings | spoken text) hash."""
        from automatio.providers.elevenlabs import ElevenLabsProvider
        prof = load_voices()["hindi-adam"]
        fp = ElevenLabsProvider().fingerprint(prof)
        self.assertEqual(fp, "eleven-1|eleven_v4|pNInz6obpgDQGcFmaJgB|hi|0.5|0.75")
        spoken = "मान लीजिए, कोई प्रोग्राम चलाते समय अचानक एक Error आ गया।"
        self.assertEqual(hashlib.sha1(f"{fp}|{spoken}".encode()).hexdigest()[:16], "f34c2a3aa9185da2")

    def test_elevenlabs_error_classification(self):
        from automatio.errors import InvalidCredential, ProviderBlocked
        from automatio.providers.elevenlabs import ElevenLabsProvider
        c = ElevenLabsProvider()._classify
        e = c(400, '{"detail":{"status":"invalid_api_key","message":"API key is invalid."}}', {})
        self.assertIsInstance(e, InvalidCredential)            # ElevenLabs answers an invalid key with HTTP 400
        self.assertEqual(e.outcome, "blocked")
        self.assertIsInstance(c(401, '{"detail":{"status":"quota_exceeded","message":"You have 5 credits"}}', {}),
                              QuotaExceeded)
        self.assertIsInstance(c(401, '{"detail":{"status":"missing_permissions","message":"no user_read"}}', {}),
                              ProviderBlocked)
        self.assertIsInstance(c(402, '{"detail":{"code":"paid_plan_required","message":"library voice"}}', {}),
                              ProviderBlocked)
        r = c(429, '{"detail":{"status":"too_many_concurrent_requests"}}', {"Retry-After": "3"})
        self.assertTrue(r.retryable)
        self.assertEqual(r.retry_after, 3.0)
        self.assertTrue(c(503, "upstream", {}).retryable)
        self.assertFalse(c(422, '{"detail":{"status":"invalid_voice_settings"}}', {}).retryable)

    def test_retries_then_succeeds(self):
        from automatio.providers.base import with_retries
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ProviderError("HTTP 429 rate limited", status=429, retryable=True, retry_after=0.01)
            return "ok"
        self.assertEqual(with_retries(flaky, what="t"), "ok")
        self.assertEqual(calls["n"], 3)

    def test_fatal_error_not_retried(self):
        from automatio.providers.base import with_retries
        calls = {"n": 0}

        def quota():
            calls["n"] += 1
            raise QuotaExceeded("no credits", status=401)
        with self.assertRaises(QuotaExceeded):
            with_retries(quota, what="t")
        self.assertEqual(calls["n"], 1)

    def test_budget_and_canary(self):
        from automatio import voice as V
        from automatio.providers.base import Provider, Synthesis

        class Paid(Provider):
            name, paid, ext = "fakepaid", True, "wav"
            calls = 0

            def fingerprint(self, profile):
                return "fake"

            def estimate_credits(self, profile, text):
                return float(len(text))

            def synthesize(self, text, out, profile, **kw):
                Paid.calls += 1
                raise QuotaExceeded("credits exhausted", status=401)

        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"AA_CACHE_DIR": d}), \
                mock.patch("automatio.providers.get", return_value=Paid()):
            prof = mock.Mock(provider="fakepaid", get=lambda k, default=None: default)
            jobs = [V.LineJob("s01", f"s01_0{i}", f"text {i}", f"text {i}", {}, "", "", f"h{i}",
                              Path(d) / f"h{i}.wav", Path(d) / f"h{i}.json") for i in range(5)]
            state = mock.Mock(spent=lambda p: 0.0)
            with self.assertRaises(BudgetExceeded):
                V.generate(mock.Mock(slug="x"), "hi", prof, jobs, state, approval={"budget": {"fakepaid": 10}})
            self.assertEqual(Paid.calls, 0)                 # nothing spent beyond the budget
            with self.assertRaises(QuotaExceeded):
                V.generate(mock.Mock(slug="x"), "hi", prof, jobs, state, approval={"budget": {"fakepaid": 1000}})
            self.assertEqual(Paid.calls, 1)                 # the canary failed; no batch was started



class TestDubFit(unittest.TestCase):
    """Dub lines are fitted onto the master timeline (automatio/dub.py)."""

    def master(self):
        def ln(key, sec, ss, se):
            return {"key": key, "section": sec, "start": ss - 0.1, "speech_start": ss, "speech_end": se}
        return {"total": 16.0, "scenes": [{"section": "s01", "offset": 0.0, "duration": 10.0},
                                          {"section": "s02", "offset": 10.0, "duration": 6.0}],
                "lines": [ln("s01_01", "s01", 0.5, 3.0), ln("s01_02", "s01", 3.5, 6.0), ln("s01_03", "s01", 6.5, 9.0),
                          ln("s02_01", "s02", 10.5, 13.0)]}

    def dub(self, d1, d2, d3, d4):
        return {k: {"speech_start": 0.05, "speech_end": 0.05 + d} for k, d in
                (("s01_01", d1), ("s01_02", d2), ("s01_03", d3), ("s02_01", d4))}

    def settings(self, **kw):
        from automatio.config import DubSettings
        kw.setdefault("min_gap", 0.12)
        return DubSettings(**kw)

    def test_lag_alone_never_speeds_up(self):
        from automatio.dub import fit
        # long first line: the next lines lag, but the section still fits -> no time-stretch at all
        r = fit(self.master(), self.dub(4.0, 2.0, 2.0, 2.0), self.settings(max_lag=0.2))
        self.assertEqual(r["summary"]["sped_up"], 0)
        self.assertTrue(r["summary"]["lag_over"])

    def test_clip_issues_finds_cut_off_endings(self):
        import numpy as np
        import soundfile as sf
        from automatio.dub import audio_extent, clip_issues
        sr = 48000
        t = np.arange(int(1.0 * sr)) / sr
        tone = (0.4 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            cut = Path(d) / "cut.wav"
            sf.write(cut, np.concatenate([np.zeros(int(0.2 * sr), np.float32), tone]), sr)   # stops mid-sound
            ok = Path(d) / "ok.wav"
            env = np.concatenate([np.ones(len(tone) - int(0.15 * sr)), np.linspace(1, 0, int(0.15 * sr))])
            sf.write(ok, np.concatenate([np.zeros(int(0.2 * sr), np.float32), (tone * env).astype(np.float32),
                                         np.zeros(int(0.3 * sr), np.float32)]), sr)
            self.assertTrue(any("cut off" in i for i in clip_issues(cut)))
            self.assertEqual(clip_issues(ok), [])
            from automatio.audio import decode
            a0, a1 = audio_extent(decode(ok))
            self.assertAlmostEqual(a0, 0.2, delta=0.02)
            self.assertAlmostEqual(a1, 1.2, delta=0.06)

    def test_fits_without_speedup_and_starts_on_time(self):
        from automatio.dub import fit
        r = fit(self.master(), self.dub(3.2, 2.5, 2.4, 3.0), self.settings())
        p = {x["key"]: x for x in r["placements"]}
        self.assertEqual(r["summary"]["overflow"], [])
        self.assertEqual(r["summary"]["sped_up"], 0)
        self.assertAlmostEqual(p["s01_01"]["onset"], 0.5)          # speech onset on the master onset
        self.assertAlmostEqual(p["s02_01"]["onset"], 10.5)         # the next section starts on time
        self.assertAlmostEqual(p["s01_02"]["onset"], 3.82)         # previous line + min_gap: a small lag
        self.assertAlmostEqual(p["s01_02"]["lag"], 0.32)
        self.assertAlmostEqual(p["s01_03"]["onset"], 6.5)          # caught up: back on the master onset
        self.assertAlmostEqual(p["s01_01"]["t"], 0.45)             # the clip starts its lead earlier

    def test_speeds_up_only_what_overflows(self):
        from automatio.dub import fit
        # section s01 holds 8.38 s of speech in a 9.2 s window ending at 9.7; at 1x it would end at ~9.86
        r = fit(self.master(), self.dub(3.0, 2.9, 3.1, 2.0), self.settings())
        sm = r["summary"]
        self.assertEqual(sm["overflow"], [])
        self.assertGreater(sm["max_speed"], 1.0)
        self.assertLessEqual(sm["max_speed"], 1.05)
        speeds = {x["key"]: x["speed"] for x in r["placements"]}
        self.assertEqual(speeds["s02_01"], 1.0)                    # the other section is untouched
        self.assertLessEqual(r["placements"][2]["end"], 9.7 + 1e-6)

    def test_reports_what_cannot_fit(self):
        from automatio.dub import fit
        r = fit(self.master(), self.dub(3.5, 3.5, 3.5, 2.0), self.settings())
        self.assertEqual(len(r["summary"]["overflow"]), 1)
        self.assertEqual(r["summary"]["overflow"][0]["lines"], ["s01_01", "s01_02", "s01_03"])
        self.assertAlmostEqual({x["key"]: x for x in r["placements"]}["s02_01"]["onset"], 10.5)  # not pushed on

    def test_anchor_splits_segments(self):
        from automatio.dub import fit, segments
        st = self.settings(anchors=["s01_03"])
        segs = segments(self.master(), st)
        self.assertEqual([[ln["key"] for ln in s["lines"]] for s in segs], [["s01_01", "s01_02"], ["s01_03"], ["s02_01"]])
        self.assertAlmostEqual(segs[0]["end"], 6.5 - st.min_gap)
        r = fit(self.master(), self.dub(2.6, 2.5, 2.4, 2.0), st)
        self.assertAlmostEqual({x["key"]: x for x in r["placements"]}["s01_03"]["onset"], 6.5)  # anchored line on time


if __name__ == "__main__":
    unittest.main()
