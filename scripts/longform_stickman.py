#!/usr/bin/env python3
"""Hybrid 90–210 second stickman film builder for an Antigravity agent.

The agent writes the story and obtains any model-generated clips. This program
validates the timeline, renders code-animated scenes, and assembles the film.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from a7_style import INK as A7_INK, PAPER as A7_PAPER, RED as A7_RED, classroom_background, draw_classroom_motion, draw_stickman_a7
from stickman_rig import StickmanAnimator, draw_stickman_soft


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FONT = ROOT / "skills/directing-stickman-videos/assets/fonts/NotoSans.ttf"
ACTIONS = {"walk", "wave", "point", "think", "explain", "shrug", "recoil", "trace", "present", "celebrate", "crouch", "lean"}
EXPRESSIONS = {"smile", "open", "think", "neutral", "sad", "worried", "angry", "surprised"}
SYMBOLS = {"none", "question", "idea", "clock", "check", "arrow", "heart"}
ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")


def run(args: list[str], *, cwd: Path | None = None, input_bytes: bytes | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, input=input_bytes, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{result.stderr.decode('utf-8', 'replace')[-3000:]}")
    return result.stdout.decode("utf-8", "replace").strip()


def probe(path: Path) -> dict:
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))


def duration_of(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def resolve(base: Path, name: str) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Expected a nonempty media path")
    return (base / name).resolve()


def seconds(x, label: str) -> float:
    try:
        n = float(x)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{label} must be a number") from e
    if not math.isfinite(n):
        raise ValueError(f"{label} must be finite")
    return n


def dimensions(ratio: str) -> tuple[int, int]:
    if ratio == "16:9":
        return 1280, 720
    if ratio == "9:16":
        return 720, 1280
    raise ValueError("ratio must be 16:9 or 9:16")


def init_project(directory: Path, length: int, ratio: str, scene_length: int) -> None:
    if not 90 <= length <= 210:
        raise ValueError("duration must be 90–210 seconds")
    dimensions(ratio)
    if not 5 <= scene_length <= 12:
        raise ValueError("scene-seconds must be 5–12")
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / "production.json"
    if manifest.exists():
        raise FileExistsError(f"Will not overwrite {manifest}")
    count = math.ceil(length / scene_length)
    scenes = []
    for i in range(count):
        remaining = length - i * scene_length
        d = min(scene_length, remaining)
        scenes.append({
            "id": f"scene_{i + 1:02d}", "duration": d, "mode": "code",
            "heading": f"THAY NỘI DUNG CẢNH {i + 1}", "background": "#F8F6F0",
            "actor_side": "left" if i % 2 == 0 else "right",
            "beats": [
                {"at": 0, "action": "think", "expression": "think", "text": "Thay câu hình ảnh", "symbol": "question"},
                {"at": round(d / 2, 2), "action": "explain", "expression": "smile", "text": "Thay điểm nhấn", "symbol": "idea"},
            ],
        })
    data = {
        "version": 1, "ready": False, "title": "THAY TÊN VIDEO", "language": "vi",
        "ratio": ratio, "fps": 30, "narration": "narration.wav",
        "captions": "captions.json",
        "character_anchor": "Người que 2D đầu tròn trắng ngà viền xanh than, thân và tứ chi là nét cong mềm bo tròn, bàn tay và bàn chân nhỏ, mặt có lông mày và miệng biểu cảm, đúng hai tay hai chân, không quần áo.",
        "scenes": scenes,
    }
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / "script.txt").write_text("Viết lời thoại hoàn chỉnh tại đây.\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest), "duration": length, "scene_count": count}, ensure_ascii=False))


def validate(manifest: Path, *, preview: float | None = None, media: bool = True) -> tuple[dict, float, list[tuple[dict, float]]]:
    p = json.loads(manifest.read_text(encoding="utf-8"))
    if p.get("version") != 1:
        raise ValueError("production.json version must be 1")
    if media and p.get("ready") is not True:
        raise ValueError("Set ready=true only after writing the real script, scene beats, and media")
    if media and (not str(p.get("title", "")).strip() or str(p["title"]).upper() == "THAY TÊN VIDEO"):
        raise ValueError("Replace the draft title before rendering")
    width, height = dimensions(p.get("ratio"))
    if p.get("fps") != 30:
        raise ValueError("fps must be 30")
    scenes = p.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("scenes must be a nonempty list")
    total = 0.0
    selected = []
    ids = set()
    for scene in scenes:
        sid = scene.get("id")
        if not isinstance(sid, str) or not ID.fullmatch(sid) or sid in ids:
            raise ValueError(f"Invalid or duplicate scene id: {sid!r}")
        ids.add(sid)
        d = seconds(scene.get("duration"), f"{sid}.duration")
        if not 1 <= d <= 12:
            raise ValueError(f"{sid}: scene duration must be 1–12 seconds")
        mode = scene.get("mode")
        if mode == "code":
            if scene.get("style", "soft") not in {"soft", "a7"}:
                raise ValueError(f"{sid}: code style must be soft or a7")
            visual = scene.get("visual")
            if visual is not None:
                if not isinstance(visual, dict) or visual.get("kind") not in {"formula", "compare", "graph"}:
                    raise ValueError(f"{sid}: visual.kind must be formula, compare, or graph")
                if visual["kind"] == "formula" and not isinstance(visual.get("lines"), list):
                    raise ValueError(f"{sid}: formula visual needs lines")
                if visual["kind"] == "compare" and not all(isinstance(visual.get(k), str) for k in ("wrong", "right")):
                    raise ValueError(f"{sid}: compare visual needs wrong and right")
                if visual["kind"] == "graph" and visual.get("function") not in {"square", "abs"}:
                    raise ValueError(f"{sid}: graph.function must be square or abs")
            beats = scene.get("beats")
            if not isinstance(beats, list) or len(beats) < 2:
                raise ValueError(f"{sid}: code scene needs at least two acting beats")
            last = -1.0
            changes = set()
            for beat in beats:
                at = seconds(beat.get("at"), f"{sid}.beat.at")
                if not last < at < d or (last < 0 and at != 0):
                    raise ValueError(f"{sid}: beats must start at 0 and increase within scene duration")
                last = at
                if beat.get("action") not in ACTIONS or beat.get("expression") not in EXPRESSIONS:
                    raise ValueError(f"{sid}: unsupported action/expression")
                if beat.get("symbol", "none") not in SYMBOLS:
                    raise ValueError(f"{sid}: unsupported symbol")
                if not isinstance(beat.get("text"), str) or not beat["text"].strip():
                    raise ValueError(f"{sid}: each beat needs visual text")
                if media and beat["text"] in {"Thay câu hình ảnh", "Thay điểm nhấn"}:
                    raise ValueError(f"{sid}: replace draft beat text")
                text_width = width - 110 if height > width else int(width * .42)
                measured = wrapped(ImageDraw.Draw(Image.new("RGB", (1, 1))), beat["text"], font(39 if height > width else 42), text_width)
                if len(measured) > 3 or any(font(39 if height > width else 42).getlength(line) > text_width for line in measured):
                    raise ValueError(f"{sid}: beat text is too long for its panel")
                changes.add((beat["action"], beat["expression"], beat["text"], beat.get("symbol")))
            if len(changes) < 2:
                raise ValueError(f"{sid}: acting beats must visibly change")
            if scene.get("actor_side", "left") not in {"left", "right"}:
                raise ValueError(f"{sid}: actor_side must be left or right")
            if not isinstance(scene.get("heading"), str) or not scene["heading"].strip():
                raise ValueError(f"{sid}: heading is required")
            if media and scene["heading"].startswith("THAY NỘI DUNG CẢNH"):
                raise ValueError(f"{sid}: replace draft heading")
            heading_size = 37 if height > width else 43
            if font(heading_size).getlength(scene["heading"]) > width - 110:
                raise ValueError(f"{sid}: heading is too wide for the frame")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", scene.get("background", "")):
                raise ValueError(f"{sid}: background must be #RRGGBB")
        elif mode == "video":
            if any(not scene.get(key) for key in ("video", "prompt", "provider", "model")):
                raise ValueError(f"{sid}: video, prompt, provider and model are required for a model scene")
            anchor = p.get("character_anchor")
            if not isinstance(anchor, str) or not anchor.strip() or anchor not in scene["prompt"]:
                raise ValueError(f"{sid}: repeat character_anchor verbatim in the model prompt")
        else:
            raise ValueError(f"{sid}: mode must be code or video")
        effective = d if preview is None else max(0.0, min(d, preview - total))
        if effective > 0:
            selected.append((scene, effective))
        total += d
    total = round(total, 3)
    if not 90 <= total <= 210:
        raise ValueError(f"Total timeline {total}s must be 90–210s")
    if preview is not None and not 1 <= preview <= min(60, total):
        raise ValueError("preview-seconds must be 1–60 and fit within the film")
    if media:
        voice = resolve(manifest.parent, p.get("narration"))
        captions = resolve(manifest.parent, p.get("captions"))
        if not voice.is_file() or not captions.is_file():
            raise FileNotFoundError("narration and captions files must exist")
        voice_info = probe(voice)
        if not any(s["codec_type"] == "audio" for s in voice_info["streams"]):
            raise ValueError("narration has no audio stream")
        voice_duration = float(voice_info["format"]["duration"])
        if abs(voice_duration - total) > 2.0:
            raise ValueError(f"Narration is {voice_duration:.2f}s but scene timeline is {total:.2f}s; revise scene timing or voice")
        cues = json.loads(captions.read_text(encoding="utf-8"))
        if not isinstance(cues, list) or not cues:
            raise ValueError("captions.json must contain a nonempty cue array")
        last = 0.0
        for cue in cues:
            start, end = seconds(cue.get("start"), "caption.start"), seconds(cue.get("end"), "caption.end")
            if start < last - .001 or end <= start or end > total + .05 or not str(cue.get("text", "")).strip():
                raise ValueError("Caption cues must be sorted, nonoverlapping, nonempty, and inside the film")
            caption_size = 35 if height > width else 38
            caption_width = font(caption_size).getlength(str(cue["text"]).strip())
            if caption_width > width - 70 or "\n" in str(cue["text"]):
                raise ValueError(f"Caption is too wide for one line: {cue['text']!r}; split at a speech boundary")
            last = end
        for scene, effective in selected:
            if scene["mode"] == "video":
                video = resolve(manifest.parent, scene["video"])
                if not video.is_file():
                    raise FileNotFoundError(video)
                info = probe(video)
                if not any(s["codec_type"] == "video" for s in info["streams"]):
                    raise ValueError(f"{video} has no video stream")
                if float(info["format"]["duration"]) < effective - .08:
                    raise ValueError(f"{scene['id']}: model clip is shorter than its timeline slot")
        for item in [p.get("music"), *(s.get("path") for s in p.get("sfx", []))]:
            if item and not resolve(manifest.parent, item).is_file():
                raise FileNotFoundError(resolve(manifest.parent, item))
    return p, total, selected


def color(hex_color: str) -> tuple[int, int, int]:
    return tuple(bytes.fromhex(hex_color[1:]))


def font(size: int) -> ImageFont.FreeTypeFont:
    if not DEFAULT_FONT.is_file():
        raise FileNotFoundError(DEFAULT_FONT)
    return ImageFont.truetype(str(DEFAULT_FONT), size)


def wrapped(draw: ImageDraw.ImageDraw, value: str, f: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    for paragraph in value.split("\n"):
        line = ""
        for word in paragraph.split():
            trial = (line + " " + word).strip()
            if line and draw.textbbox((0, 0), trial, font=f)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
    return lines


def draw_symbol(draw: ImageDraw.ImageDraw, symbol: str, x: int, y: int, radius: int, phase: float, ink=(49, 92, 176)) -> None:
    if symbol == "none":
        return
    bob = int(7 * math.sin(phase * 3))
    y += bob
    if symbol == "question":
        draw.text((x - radius // 2, y - radius), "?", font=font(radius * 2), fill=ink)
    elif symbol == "idea":
        draw.ellipse((x - radius // 2, y - radius, x + radius // 2, y), outline=ink, width=5)
        draw.line((x - radius // 4, y, x + radius // 4, y), fill=ink, width=6)
        draw.line((x - radius // 5, y + 11, x + radius // 5, y + 11), fill=ink, width=5)
    elif symbol == "clock":
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=ink, width=6)
        draw.line((x, y, x, y - radius * .6), fill=ink, width=6)
        draw.line((x, y, x + radius * .45, y + radius * .25), fill=ink, width=6)
    elif symbol == "check":
        draw.line([(x - radius, y), (x - radius // 4, y + radius // 2), (x + radius, y - radius)], fill=ink, width=10, joint="curve")
    elif symbol == "arrow":
        draw.line((x - radius, y, x + radius, y), fill=ink, width=9)
        draw.line([(x + radius // 2, y - radius // 2), (x + radius, y), (x + radius // 2, y + radius // 2)], fill=ink, width=9)
    elif symbol == "heart":
        points = [(x, y + radius), (x - radius, y), (x - radius, y - radius // 2), (x - radius // 2, y - radius), (x, y - radius // 2), (x + radius // 2, y - radius), (x + radius, y - radius // 2), (x + radius, y)]
        draw.polygon(points, fill=A7_RED if ink == A7_RED else (224, 85, 94))


def draw_math_visual(draw: ImageDraw.ImageDraw, visual: dict, box: tuple[int, int, int, int], t: float, style="soft") -> None:
    x0, y0, x1, y1 = box
    a7 = style == "a7"
    draw.rounded_rectangle(box, radius=3 if a7 else 15, fill=A7_PAPER if a7 else (255, 255, 255), outline=A7_INK if a7 else (220, 224, 229), width=2)
    kind = visual["kind"]
    if kind == "formula":
        lines = visual.get("lines", [])[:2]
        for i, line in enumerate(lines):
            if i and t < visual.get("reveal_at", 0):
                continue
            f = font(36 if x1 - x0 > 500 else 30)
            draw.text((x0 + 20, y0 + 22 + i * 58), line, font=f, fill=(51, 70, 61) if a7 else (29, 84, 151))
    elif kind == "compare":
        f = font(34 if x1 - x0 > 500 else 27)
        marker_x, marker_y = x0 + 28, y0 + 36
        wrong = A7_RED if a7 else (192, 61, 59)
        right = (56, 100, 72) if a7 else (29, 126, 77)
        draw.line((marker_x - 8, marker_y - 8, marker_x + 8, marker_y + 8), fill=wrong, width=4)
        draw.line((marker_x + 8, marker_y - 8, marker_x - 8, marker_y + 8), fill=wrong, width=4)
        draw.text((x0 + 54, y0 + 17), visual["wrong"], font=f, fill=wrong)
        if t >= visual.get("reveal_at", 0):
            draw.line((x0 + 17, y0 + (y1-y0)//2, x1 - 17, y0 + (y1-y0)//2), fill=(164, 166, 151) if a7 else (225, 225, 225), width=2)
            check_y = y0 + (y1-y0)//2 + 33
            check_points = [(x0 + 19, check_y), (x0 + 27, check_y + 8), (x0 + 41, check_y - 10)]
            progress = min(1.0, max(0.0, (t - visual.get("reveal_at", 0)) / .35)) if a7 else 1.0
            if progress <= .4:
                a, b = check_points[:2]
                end = (a[0] + (b[0]-a[0]) * progress/.4, a[1] + (b[1]-a[1]) * progress/.4)
                draw.line([a, end], fill=right, width=4, joint="curve")
            else:
                a, b = check_points[1:]
                end = (a[0] + (b[0]-a[0]) * (progress-.4)/.6, a[1] + (b[1]-a[1]) * (progress-.4)/.6)
                draw.line(check_points[:2] + [end], fill=right, width=4, joint="curve")
            draw.text((x0 + 54, y0 + (y1-y0)//2 + 13), visual["right"], font=f, fill=right)
    else:
        left, right = x0 + 42, x1 - 26
        top, bottom = y0 + 17, y1 - 30
        ox, oy = (left + right) / 2, bottom - 20
        draw.line((left, oy, right, oy), fill=(112, 118, 125), width=2)
        draw.line((ox, top, ox, bottom), fill=(112, 118, 125), width=2)
        spread_x = (right - left) / 4
        spread_y = (oy - top) / 4.5
        fn = (lambda x: x*x) if visual["function"] == "square" else abs
        pts = [(ox + x / 2 * spread_x * 2, oy - fn(x) * spread_y) for x in [(-2 + i * .04) for i in range(101)]]
        draw.line(pts, fill=(55, 87, 72) if a7 else (35, 91, 170), width=5, joint="curve")
        if visual["function"] == "square":
            keys = visual.get("tangent_keys", [])
            if keys:
                prev_key = keys[0]
                next_key = keys[-1]
                for key in keys[1:]:
                    if t <= key["at"]:
                        next_key = key
                        break
                    prev_key = key
                span = max(.001, next_key["at"] - prev_key["at"])
                fraction = max(0, min(1, (t - prev_key["at"]) / span))
                tangent_x = prev_key["x"] + (next_key["x"] - prev_key["x"]) * fraction
            else:
                tangent_x = .5 + .5 * math.sin(t * 1.1)
            px, py = ox + tangent_x * spread_x, oy - tangent_x*tangent_x*spread_y
            slope = -2 * tangent_x * spread_y / spread_x
            draw.line((px - 72, py - slope * 72, px + 72, py + slope * 72), fill=A7_RED if a7 else (219, 75, 66), width=4)
            draw.ellipse((px-6, py-6, px+6, py+6), fill=A7_RED if a7 else (219, 75, 66))
        else:
            draw.ellipse((ox-7, oy-7, ox+7, oy+7), fill=A7_RED if a7 else (219, 75, 66))


def interpolate_pose(previous, current, fraction: float):
    if fraction >= 1:
        return current
    out = copy.deepcopy(current)
    def lerp(a, b): return a + (b - a) * fraction
    out.hip = tuple(lerp(a, b) for a, b in zip(previous.hip, current.hip))
    out.torso_angle = lerp(previous.torso_angle, current.torso_angle)
    out.head_tilt = lerp(previous.head_tilt, current.head_tilt)
    for limb in ("left_arm", "right_arm", "left_leg", "right_leg"):
        old, new = getattr(previous, limb), getattr(current, limb)
        if old and new:
            setattr(out, limb, [tuple(lerp(a, b) for a, b in zip(p, q)) for p, q in zip(old, new)])
    shoulder = out.compute_skeleton()[3]
    left_root, right_root = out.shoulder_points()
    for limb, root in (("left_arm", left_root), ("right_arm", right_root)):
        chain = getattr(out, limb)
        if chain:
            chain[0] = shoulder
            if len(chain) >= 4:
                chain[1] = root
    for limb in ("left_leg", "right_leg"):
        chain = getattr(out, limb)
        if chain:
            chain[0] = out.hip
    return out


def code_frame(scene: dict, t: float, size: tuple[int, int]) -> Image.Image:
    width, height = size
    portrait = height > width
    a7 = scene.get("style") == "a7"
    actor_left = scene.get("actor_side", "left") == "left"
    img = classroom_background(size, actor_left).copy() if a7 else Image.new("RGB", size, color(scene["background"]))
    draw = ImageDraw.Draw(img)
    scale = min(width / 1280, height / 720) if not portrait else width / 720
    margin = int(55 * scale)
    title_font = font(int((43 if not portrait else 37) * scale))
    body_font = font(int((42 if not portrait else 39) * scale))
    draw.text((margin, margin), scene["heading"], font=title_font, fill=A7_INK if a7 else (30, 29, 28))
    draw.line((margin, margin + int(72 * scale), width - margin, margin + int(72 * scale)), fill=A7_INK if a7 else (90, 93, 96), width=max(2, int(3 * scale)))
    beats = scene["beats"]
    index = max(i for i, b in enumerate(beats) if b["at"] <= t)
    beat = beats[index]
    beat_age = t - beat["at"]
    if a7:
        draw_classroom_motion(img, size, actor_left, t, beat_age)
    if portrait:
        hip = (width * .5, height * .75)
        actor_scale = width / 720
        text_x, text_y, text_width = margin, int(height * .17), width - margin * 2
    else:
        hip = (width * (.27 if actor_left else .73), height * (.63 if a7 else .62))
        actor_scale = height / 720 * 1.3
        text_x = int(width * (.51 if actor_left else .06))
        text_y = int(height * .28)
        text_width = int(width * .42)
    symbol_x = int(hip[0] + (90 if actor_left else -90) * actor_scale)
    symbol_y = int(hip[1] - 100 * actor_scale)
    target = (symbol_x, symbol_y)
    pose = StickmanAnimator.evaluate_pose(beat["action"], beat_age, base_hip=hip, scale=actor_scale, target=target)
    pose.expression = beat["expression"]
    if index and beat_age < .42:
        prior = beats[index - 1]
        old = StickmanAnimator.evaluate_pose(prior["action"], t - prior["at"], base_hip=hip, scale=actor_scale, target=target)
        old.expression = prior["expression"]
        progress = beat_age / .42
        eased = progress * progress * (3 - 2 * progress)
        pose = interpolate_pose(old, pose, eased)
        pose.expression = prior["expression"] if eased < .5 else beat["expression"]
    symbol_pop = 1 + .15*math.exp(-beat_age*5)*math.sin(beat_age*14) if a7 else 1
    if a7:
        draw_symbol(draw, beat.get("symbol", "none"), symbol_x, symbol_y, int(40 * scale * symbol_pop), beat_age, ink=A7_RED)
        draw_stickman_a7(img, pose, width=max(3, int(4 * scale)), time_seconds=t)
    else:
        draw_stickman_soft(img, pose, ink=(40, 52, 62), width=max(5, int(10 * scale)), time_seconds=t)
        draw_symbol(draw, beat.get("symbol", "none"), symbol_x, symbol_y, int(40 * scale), t)
    lines = wrapped(draw, beat["text"], body_font, text_width)
    line_step = int(60 * scale)
    card_shift = round(18 * scale * max(0, 1 - beat_age/.42)**2) if a7 else 0
    draw.rounded_rectangle((text_x - 16, text_y + card_shift - 16, text_x + text_width + 16, text_y + card_shift + len(lines) * line_step + 16), radius=3 if a7 else 15, fill=A7_PAPER if a7 else (255, 255, 255), outline=A7_INK if a7 else (220, 224, 229), width=2)
    for i, line in enumerate(lines):
        draw.text((text_x, text_y + card_shift + i * line_step), line, font=body_font, fill=(49, 67, 57) if a7 else (35, 57, 91))
    if scene.get("visual"):
        visual_y = int(height * (.36 if portrait else .53))
        visual_height = int(height * (.16 if portrait else .25))
        draw_math_visual(draw, scene["visual"], (text_x - 16, visual_y, text_x + text_width + 16, visual_y + visual_height), t, style="a7" if a7 else "soft")
    ground_y = int(hip[1] + 126 * actor_scale)
    if not a7:
        draw.line((max(margin, int(hip[0] - 180 * actor_scale)), ground_y, min(width - margin, int(hip[0] + 180 * actor_scale)), ground_y), fill=(188, 190, 190), width=max(1, int(2 * scale)))
    return img


def encode_code(scene: dict, path: Path, duration: float, size: tuple[int, int]) -> None:
    width, height = size
    frames = round(duration * 30)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{width}x{height}", "-framerate", "30", "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.stdin
        for i in range(frames):
            process.stdin.write(code_frame(scene, i / 30, size).tobytes())
        process.stdin.close()
        assert process.stderr
        error = process.stderr.read().decode("utf-8", "replace")
        if process.wait() != 0:
            raise RuntimeError(f"Code scene encode failed: {error[-3000:]}")
        process.stderr.close()
    except Exception:
        process.kill()
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
        if process.stderr and not process.stderr.closed:
            process.stderr.close()
        process.wait()
        raise


def encode_video(scene: dict, base: Path, path: Path, duration: float, size: tuple[int, int]) -> None:
    width, height = size
    run(["ffmpeg", "-v", "error", "-y", "-i", str(resolve(base, scene["video"])), "-t", f"{duration:.3f}", "-vf", f"fps=30,scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", str(path)])


def timecode(value: float, *, ass: bool = False) -> str:
    ticks = max(0, round(value * (100 if ass else 1000)))
    scale = 100 if ass else 1000
    whole, fraction = divmod(ticks, scale)
    hours, rem = divmod(whole, 3600)
    minutes, secs = divmod(rem, 60)
    if ass:
        return f"{hours}:{minutes:02}:{secs:02}.{fraction:02}"
    return f"{hours:02}:{minutes:02}:{secs:02},{fraction:03}"


def write_captions(cues: list, build: Path, limit: float, size: tuple[int, int]) -> int:
    width, height = size
    portrait = height > width
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "WrapStyle: 2", "", "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding", f"Style: Default,Noto Sans,{35 if portrait else 38},&H00FFFFFF,&H00FFFFFF,&H00202123,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,35,35,{100 if portrait else 42},1", "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    srt = []
    number = 0
    for cue in cues:
        if cue["start"] >= limit:
            break
        start, end = float(cue["start"]), min(limit, float(cue["end"]))
        if end <= start:
            continue
        number += 1
        content = str(cue["text"]).strip().replace("\n", " ")
        safe = content.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        ass.append(f"Dialogue: 0,{timecode(start, ass=True)},{timecode(end, ass=True)},Default,,0,0,0,,{safe}")
        srt.append(f"{number}\n{timecode(start)} --> {timecode(end)}\n{content}\n")
    (build / "captions.ass").write_text("\n".join(ass) + "\n", encoding="utf-8-sig")
    (build / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    return number


def audio_filter(p: dict, base: Path, limit: float) -> tuple[list[str], str]:
    inputs = ["-i", str(resolve(base, p["narration"]))]
    filters = ["[1:a]volume=1[a0]"]
    labels = ["[a0]"]
    if p.get("music"):
        inputs += ["-stream_loop", "-1", "-i", str(resolve(base, p["music"]))]
        index = 1 + len(labels)
        filters.append(f"[{index}:a]volume=0.12,atrim=duration={limit:.3f}[a{index - 1}]")
        labels.append(f"[a{index - 1}]")
    for item in p.get("sfx", []):
        start = seconds(item.get("at"), "sfx.at")
        if start >= limit:
            continue
        if start < 0 or start > 210:
            raise ValueError("sfx.at outside timeline")
        gain = seconds(item.get("gain", .35), "sfx.gain")
        if not 0 <= gain <= 1:
            raise ValueError("sfx.gain must be 0–1")
        inputs += ["-i", str(resolve(base, item["path"]))]
        index = 1 + len(labels)
        delay = round(start * 1000)
        filters.append(f"[{index}:a]volume={gain},adelay={delay}|{delay}[a{index - 1}]")
        labels.append(f"[a{index - 1}]")
    if len(labels) == 1:
        filters.append("[a0]alimiter=limit=0.95[aout]")
    else:
        filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.95[aout]")
    return inputs, ";".join(filters)


def contact_sheet(output: Path, build: Path, selected: list[tuple[dict, float]], size: tuple[int, int]) -> Path:
    thumb_w, thumb_h = (320, 180) if size[0] > size[1] else (180, 320)
    cell_w, cell_h = thumb_w + 16, thumb_h + 38
    sheet = Image.new("RGB", (3 * cell_w, len(selected) * cell_h), "#f2f2f2")
    draw = ImageDraw.Draw(sheet)
    offset = 0.0
    for row, (scene, length) in enumerate(selected):
        times = [offset + min(.18, length / 4), offset + length / 2, offset + max(length - .18, length * .75)]
        for col, at in enumerate(times):
            frame = build / f"contact_{row:02}_{col}.png"
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(output), "-frames:v", "1", "-vf", f"scale={thumb_w}:{thumb_h}:force_original_aspect_ratio=decrease", str(frame)])
            with Image.open(frame) as still:
                tile = still.convert("RGB")
                sheet.paste(tile, (col * cell_w + (cell_w - tile.width) // 2, row * cell_h + 4))
            draw.text((col * cell_w + 8, row * cell_h + thumb_h + 8), f"{scene['id']} {('start', 'mid', 'end')[col]}", font=font(17), fill=(25, 25, 25))
            frame.unlink()
        offset += length
    path = build / "scene-contact-sheet.jpg"
    sheet.save(path, quality=90)
    return path


def render(manifest: Path, preview: float | None) -> None:
    p, total, selected = validate(manifest, preview=preview)
    limit = preview or total
    size = dimensions(p["ratio"])
    build = manifest.parent / "output" / ("preview_build" if preview else "film_build")
    scene_dir = build / "scenes"
    scene_dir.mkdir(parents=True, exist_ok=True)
    scene_paths = []
    for scene, effective in selected:
        clip = scene_dir / f"{scene['id']}.mp4"
        print(f"Rendering {scene['id']} ({scene['mode']}, {effective:.2f}s)", flush=True)
        if scene["mode"] == "code":
            encode_code(scene, clip, effective, size)
        else:
            encode_video(scene, manifest.parent, clip, effective, size)
        scene_paths.append(clip)
    concat = build / "concat.txt"
    concat.write_text("\n".join(f"file 'scenes/{c.name}'" for c in scene_paths) + "\n", encoding="utf-8")
    visuals = build / "visuals.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(visuals)])
    cues = json.loads(resolve(manifest.parent, p["captions"]).read_text(encoding="utf-8"))
    caption_count = write_captions(cues, build, limit, size)
    extra_inputs, mix = audio_filter(p, manifest.parent, limit)
    output = manifest.parent / "output" / ("preview.mp4" if preview else "film.mp4")
    # Relative subtitle path avoids Windows drive-letter escaping in libass.
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(visuals), *extra_inputs, "-filter_complex", mix, "-map", "0:v", "-map", "[aout]", "-vf", "subtitles=captions.ass:fontsdir=fonts", "-t", f"{limit:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    fonts_dir = build / "fonts"
    fonts_dir.mkdir(exist_ok=True)
    (fonts_dir / DEFAULT_FONT.name).write_bytes(DEFAULT_FONT.read_bytes())
    run(cmd, cwd=build)
    info = probe(output)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
    real_duration = float(info["format"]["duration"])
    if abs(real_duration - limit) > .35 or (video["width"], video["height"]) != size or video.get("r_frame_rate") != "30/1" or not audio:
        raise RuntimeError("Output failed duration, resolution, or audio QA")
    run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"])
    contact = contact_sheet(output, build, selected, size)
    report = {"output": str(output), "duration": real_duration, "target_duration": limit, "size": list(size), "scenes": len(scene_paths), "caption_count": caption_count, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "decode": "pass", "contact_sheet": str(contact), "creative_review": "pending"}
    (build / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Scaffold a 90–210s project")
    init.add_argument("directory", type=Path)
    init.add_argument("--duration", type=int, default=120)
    init.add_argument("--ratio", default="16:9", choices=["16:9", "9:16"])
    init.add_argument("--scene-seconds", type=int, default=8)
    check = sub.add_parser("validate", help="Validate timeline and existing media")
    check.add_argument("manifest", type=Path)
    check.add_argument("--plan-only", action="store_true")
    check.add_argument("--preview-seconds", type=float)
    render_parser = sub.add_parser("render", help="Render preview or complete film")
    render_parser.add_argument("manifest", type=Path)
    render_parser.add_argument("--preview-seconds", type=float)
    args = parser.parse_args()
    if args.command == "init":
        init_project(args.directory, args.duration, args.ratio, args.scene_seconds)
    elif args.command == "validate":
        _, total, selected = validate(args.manifest.resolve(), preview=args.preview_seconds, media=not args.plan_only)
        print(json.dumps({"valid": True, "duration": total, "selected_scenes": len(selected), "media_checked": not args.plan_only}))
    else:
        render(args.manifest.resolve(), args.preview_seconds)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
