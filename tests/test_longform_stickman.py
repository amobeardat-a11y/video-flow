"""Integration smoke test for the 90–210 second hybrid film contract."""

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import longform_stickman as film  # noqa: E402
from stickman_rig import StickmanAnimator  # noqa: E402


class LongformPipelineTest(unittest.TestCase):
    def test_rig_v2_plants_feet_and_mirrors_reaching_arm(self):
        base = (930, 453)
        target = (813, 323)
        for action in ("shrug", "recoil", "trace", "present", "celebrate", "crouch", "lean"):
            a = StickmanAnimator.evaluate_pose(action, .2, base_hip=base, scale=1.3, target=target)
            b = StickmanAnimator.evaluate_pose(action, 1.4, base_hip=base, scale=1.3, target=target)
            self.assertEqual(a.left_leg[-1], b.left_leg[-1], action)
            self.assertEqual(a.right_leg[-1], b.right_leg[-1], action)
            self.assertTrue(a.left_arm and a.right_arm, action)
        pose = StickmanAnimator.evaluate_pose("trace", 1.0, base_hip=base, scale=1.3, target=target)
        left = math.dist(pose.left_arm[-1], target)
        right = math.dist(pose.right_arm[-1], target)
        self.assertLess(left, right)
        old = StickmanAnimator.evaluate_pose("shrug", 1.2, base_hip=base, scale=1.3, target=target)
        new = StickmanAnimator.evaluate_pose("recoil", .2, base_hip=base, scale=1.3, target=target)
        mixed = film.interpolate_pose(old, new, .5)
        shoulder = mixed.compute_skeleton()[3]
        self.assertEqual(mixed.left_arm[0], shoulder)
        self.assertEqual(mixed.right_arm[0], shoulder)
        self.assertEqual(mixed.left_arm[1], mixed.shoulder_points()[0])
        self.assertEqual(mixed.right_arm[1], mixed.shoulder_points()[1])
        self.assertEqual(mixed.left_leg[0], mixed.hip)
        self.assertEqual(mixed.right_leg[0], mixed.hip)

    def test_scaffold_validation_and_real_preview_encode(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            film.init_project(project, 90, "16:9", 8)
            manifest = project / "production.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(len(data["scenes"]), 12)
            self.assertEqual(film.validate(manifest, media=False)[1], 90)
            data["ready"] = True
            data["title"] = "A complete longform test"
            for index, scene in enumerate(data["scenes"]):
                scene["heading"] = f"CẢNH {index + 1}"
                scene["beats"][0]["text"] = "Một vấn đề xuất hiện"
                scene["beats"][1]["text"] = "Người que tìm ra lời giải"
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "90", str(project / "narration.wav")], check=True)
            (project / "captions.json").write_text(json.dumps([{"start": 0.0, "end": 1.0, "text": "Một vấn đề xuất hiện"}], ensure_ascii=False), encoding="utf-8")
            film.validate(manifest, preview=1.0)
            film.render(manifest, 1.0)
            result = project / "output" / "preview.mp4"
            self.assertTrue(result.is_file())
            info = film.probe(result)
            self.assertEqual(next(s for s in info["streams"] if s["codec_type"] == "video")["width"], 1280)
            self.assertAlmostEqual(float(info["format"]["duration"]), 1.0, delta=.35)
            self.assertTrue((project / "output" / "preview_build" / "captions.srt").is_file())

    def test_missing_model_clip_fails_before_render(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            film.init_project(project, 90, "9:16", 8)
            manifest = project / "production.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["title"] = "A complete longform test"
            data["scenes"][0] = {"id": "scene_01", "duration": 8, "mode": "video", "video": "model_clips/scene_01.mp4", "provider": "Google", "model": "Omni", "prompt": data["character_anchor"] + " consistent expressive character"}
            for scene in data["scenes"][1:]:
                scene["heading"] = "A new scene"
                scene["beats"][0]["text"] = "Problem"
                scene["beats"][1]["text"] = "Solution"
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(film.validate(manifest, media=False)[1], 90)
            data["ready"] = True
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                film.validate(manifest)

    def test_model_clip_and_sound_mix_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            film.init_project(project, 90, "9:16", 8)
            manifest = project / "production.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["ready"] = True
            data["title"] = "A complete longform test"
            data["scenes"][0] = {"id": "scene_01", "duration": 1, "mode": "video", "video": "model_clips/scene_01.mp4", "provider": "test", "model": "test-clip", "prompt": data["character_anchor"] + " actor moves"}
            data["scenes"][-1]["duration"] = 9  # Keep the complete project at 90 seconds.
            for scene in data["scenes"][1:]:
                scene["heading"] = "A new scene"
                scene["beats"][0]["text"] = "Problem"
                scene["beats"][1]["text"] = "Solution"
            data["music"] = "music.wav"
            data["sfx"] = [{"path": "sfx.wav", "at": .3, "gain": .2}]
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            (project / "model_clips").mkdir()
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=24:d=2", "-c:v", "libx264", str(project / "model_clips" / "scene_01.mp4")], check=True)
            for name, source, length in [("narration.wav", "anullsrc=r=24000:cl=mono", "90"), ("music.wav", "sine=frequency=440:duration=2", "2"), ("sfx.wav", "sine=frequency=660:duration=0.3", "0.3")]:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", source, "-t", length, str(project / name)], check=True)
            (project / "captions.json").write_text(json.dumps([{"start": 0, "end": 1, "text": "Cảnh model có âm thanh riêng"}, {"start": 1, "end": 2, "text": "Cảnh code tiếp nối"}], ensure_ascii=False), encoding="utf-8")
            film.render(manifest, 2.0)
            self.assertTrue((project / "output" / "preview.mp4").is_file())
            report = json.loads((project / "output" / "preview_build" / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["scenes"], 2)


if __name__ == "__main__":
    unittest.main()
