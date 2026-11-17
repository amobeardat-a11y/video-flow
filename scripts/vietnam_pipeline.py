#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Vietnamese Stickman Video Pipeline with VieNeu-TTS
Tự động hóa quy trình sản xuất video hoạt hình người que tiếng Việt:
1. Tổng hợp giọng đọc tiếng Việt bằng VieNeu-TTS.
2. Căn chỉnh phụ đề theo giọng nói (Whisper vi / Semantic aligner).
3. Cấu hình dự án với font chữ Noto Sans hỗ trợ 100% dấu tiếng Việt.
4. Tự động chia các cảnh (shots), tư thế người que (poses), chữ viết tay.
5. Render bản preview 20s hoặc toàn bộ video.
"""

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT_DIR / "skills" / "directing-stickman-videos"
SCRIPTS_DIR = SKILLS_DIR / "scripts"
FONTS_DIR = SKILLS_DIR / "assets" / "fonts"
NOTO_FONT = FONTS_DIR / "NotoSans.ttf"


def run_command(cmd, cwd=None, check=True):
    """Run shell command safely."""
    print(f"[*] Chạy lệnh: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode != 0:
        print(f"[LỖI] Lệnh thất bại (mã thoát {result.returncode}):\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(result.stderr or "Lệnh thất bại")
    return result.stdout.strip()


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    out = run_command(cmd)
    return float(out)


def align_audio_whisper(audio_path: Path, output_json: Path):
    """Run Whisper to get word timestamps."""
    align_script = SCRIPTS_DIR / "align_captions.py"
    cmd = [
        sys.executable, str(align_script),
        str(audio_path),
        "--output", str(output_json),
        "--language", "vi",
        "--allow-model-download"
    ]
    try:
        run_command(cmd)
        return True
    except Exception as e:
        print(f"[!] Whisper chưa khả dụng ({e}). Sử dụng bộ ước tính thời gian ngữ nghĩa thay thế...")
        return False


def estimate_word_timings(text: str, total_duration: float, output_json: Path):
    """Fallback word aligner based on syllable count and pauses."""
    words = [w.strip() for w in text.split() if w.strip()]
    if not words:
        raise ValueError("Kịch bản rỗng")

    # Vietnamese words are mostly monosyllabic tokens
    weights = [max(1, len(w)) for w in words]
    total_weight = sum(weights)
    lead = 0.2
    effective_duration = max(0.5, total_duration - lead - 0.2)

    word_items = []
    current_time = lead
    for w, weight in zip(words, weights):
        duration = (weight / total_weight) * effective_duration
        word_items.append({
            "word": w,
            "start": round(current_time, 3),
            "end": round(current_time + duration, 3)
        })
        current_time += duration

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"words": word_items, "method": "proportional_fallback"}, f, ensure_ascii=False, indent=2)


def generate_shots_from_captions(captions: list, total_duration: float, style: str = "B1"):
    """Auto-generate dynamic shots, poses, and layers based on captions."""
    shots = []
    if not captions:
        return [
            {
                "start": 0,
                "end": round(total_duration, 2),
                "layers": [
                    {"type": "pose", "pose": 0, "x": 650, "y": 30, "w": 450},
                    {"type": "text", "text": "VIDEO TIẾNG VIỆT", "x": 100, "y": 150, "size": 52, "bold": True}
                ]
            }
        ]

    # Group captions into shot blocks around 2.5 - 4.5 seconds
    shot_cues = []
    current_chunk = []
    chunk_start = 0.0

    for cue in captions:
        if not current_chunk:
            chunk_start = cue["start"]
            current_chunk.append(cue)
        else:
            if cue["end"] - chunk_start > 4.2 or len(current_chunk) >= 2:
                shot_cues.append(current_chunk)
                current_chunk = [cue]
                chunk_start = cue["start"]
            else:
                current_chunk.append(cue)
    if current_chunk:
        shot_cues.append(current_chunk)

    prev_end = 0.0
    pose_cycle = [0, 1, 2, 0, 3, 1]

    for i, chunk in enumerate(shot_cues):
        is_last = (i == len(shot_cues) - 1)
        shot_start = prev_end
        shot_end = round(total_duration, 3) if is_last else round(chunk[-1]["end"] + 0.1, 3)
        if shot_end <= shot_start:
            shot_end = shot_start + 2.0
        prev_end = shot_end

        pose_idx = pose_cycle[i % len(pose_cycle)]
        main_text = chunk[0]["text"].upper()
        shot_dur = round(shot_end - shot_start, 3)

        # Tạo chuỗi keyframe chuyển động phủ kín toàn bộ thời lượng cảnh
        t_points = []
        cur = 0.0
        while cur < shot_dur - 0.4:
            t_points.append(round(cur, 3))
            cur += 1.0
        if not t_points or t_points[-1] < shot_dur:
            t_points.append(shot_dur)

        keys = []
        for idx, t in enumerate(t_points):
            y_val = 35 if idx % 2 == 0 else 25
            angle_val = -0.04 if idx % 2 == 0 else 0.04
            keys.append({
                "t": t,
                "y": y_val,
                "angle": angle_val
            })

        layers = [
            {
                "id": f"actor_shot_{i}",
                "type": "pose",
                "pose": pose_idx,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {
                    "role": "actor",
                    "reason": "Nhân vật chuyển động diễn giải nội dung"
                },
                "keys": keys
            },
            {"type": "text", "text": main_text, "x": 90, "y": 120, "size": 48, "bold": True, "color": "#1A1A1A"}
        ]

        if len(chunk) > 1:
            sub_text = chunk[1]["text"]
            layers.append({
                "type": "text",
                "text": sub_text,
                "x": 90,
                "y": 190,
                "size": 40,
                "color": "#EC4338",
                "bold": True
            })

        shots.append({
            "start": shot_start,
            "end": shot_end,
            "layers": layers
        })

    return shots


def build_vietnamese_project(project_dir: Path, script_text: str, voice: str = "Minh Quân",
                             ref_audio: str = None, api_url: str = None, style: str = "B1",
                             ratio: str = "16:9", preview: bool = False, mock: bool = False):
    """Complete end-to-end pipeline."""
    project_dir = project_dir.resolve()
    print(f"\n=======================================================")
    print(f"🎬 Bắt đầu quy trình tạo video Stickman tiếng Việt với VieNeu-TTS")
    print(f"📁 Thư mục dự án: {project_dir}")
    print(f"🎙 Giọng đọc: {voice} {'(Clone: ' + ref_audio + ')' if ref_audio else ''}")
    print(f"🎨 Phong cách: {style} | Tỷ lệ: {ratio}")
    print(f"=======================================================\n")

    project_dir.mkdir(parents=True, exist_ok=True)
    narration_wav = project_dir / "narration.wav"
    word_timings_json = project_dir / "word-timings.json"
    captions_json = project_dir / "captions.json"
    project_json = project_dir / "project.json"

    # 1. Sinh Voiceover bằng VieNeu-TTS
    print("[1/5] Tạo âm thanh giọng đọc bằng VieNeu-TTS...")
    tts_script = ROOT_DIR / "scripts" / "tts_vieneu.py"
    cmd = [
        sys.executable, str(tts_script),
        "--text", script_text,
        "-o", str(narration_wav),
        "--voice", voice
    ]
    if mock:
        cmd.append("--mock")
    if ref_audio:
        cmd.extend(["--ref-audio", str(ref_audio)])
    if api_url:
        cmd.extend(["--api-url", str(api_url)])

    run_command(cmd)
    duration = get_audio_duration(narration_wav)
    print(f"[✓] Đã tạo file narration.wav thành công! Thời lượng: {duration:.2f} giây.")

    # 2. Căn chỉnh phụ đề
    print("\n[2/5] Căn chỉnh timestamp từ vựng (Word Alignment)...")
    aligned = False
    try:
        import whisper
        aligned = align_audio_whisper(narration_wav, word_timings_json)
    except ImportError:
        aligned = False

    if not aligned or not word_timings_json.exists():
        estimate_word_timings(script_text, duration, word_timings_json)
        print("[✓] Đã tạo word-timings.json.")

    # 3. Gom cụm phụ đề ngữ nghĩa qua autopilot.mjs
    print("\n[3/5] Gom cụm phụ đề ngữ nghĩa (Semantic Captions)...")
    autopilot_mjs = SCRIPTS_DIR / "autopilot.mjs"
    if captions_json.exists():
        captions_json.unlink()
    cmd = ["node", str(autopilot_mjs), "captions", str(word_timings_json), str(captions_json)]
    run_command(cmd)
    with open(captions_json, "r", encoding="utf-8") as f:
        captions_data = json.load(f)
    print(f"[✓] Đã tạo {len(captions_data)} cụm phụ đề tiếng Việt chuẩn.")

    # 4. Tạo project.json hoàn chỉnh với Font tiếng Việt Noto Sans
    print("\n[4/5] Thiết lập cấu hình dự án project.json...")
    width = 720 if ratio == "9:16" else 1280
    height = 1280 if ratio == "9:16" else 720

    shots = generate_shots_from_captions(captions_data, duration, style=style)

    # Sử dụng font NotoSans.ttf để đảm bảo hiển thị 100% tiếng Việt
    rel_noto_font = os.path.relpath(NOTO_FONT, project_dir).replace("\\", "/")

    project_config = {
        "version": 1,
        "style": style,
        "width": width,
        "height": height,
        "fps": 30,
        "font": rel_noto_font,
        "captionFont": rel_noto_font,
        "voice": {
            "path": "narration.wav",
            "lead": 0,
            "tail": 0,
            "contains_sfx": True
        },
        "captions": captions_data,
        "shots": shots,
        "sfx": []
    }

    if style in ["B1", "B2", "B3"]:
        project_config["reference_review"] = {
            "author_id": "vietneu_pipeline",
            "capability": {
                "mode": "sample_target",
                "environment": "local_vietnamese",
                "limitations": []
            }
        }

    with open(project_json, "w", encoding="utf-8") as f:
        json.dump(project_config, f, ensure_ascii=False, indent=2)
    print(f"[✓] Đã lưu project.json sẵn sàng render!")

    # 5. Xem trước hoặc Render
    if preview:
        print("\n[5/5] Đang render bản xem trước (Preview 20s)...")
        cmd = ["node", str(autopilot_mjs), "preview", str(project_json), "--seconds", "20"]
        run_command(cmd)
        print(f"[✓] Hoàn thành xem trước tại: {project_dir / 'output' / 'preview.mp4'}")
    else:
        print(f"\n[5/5] Dự án đã sẵn sàng! Bạn có thể xem trước hoặc render đầy đủ bằng lệnh:")
        print(f"  Xem trước: node {autopilot_mjs} preview {project_json}")
        print(f"  Render full: node {autopilot_mjs} render {project_json}")


def main():
    parser = argparse.ArgumentParser(description="Tạo video Stickman tiếng Việt tự động với VieNeu-TTS")
    parser.add_argument("--project", "-p", type=Path, required=True, help="Thư mục dự án (ví dụ: my-viet-video)")
    parser.add_argument("--script", "-s", type=str, help="Văn bản kịch bản tiếng Việt")
    parser.add_argument("--script-file", "-f", type=Path, help="File text kịch bản tiếng Việt")
    parser.add_argument("--voice", "-v", type=str, default="Minh Quân", help="Tên giọng VieNeu-TTS ('Minh Quân', 'Trúc Ly', 'Hải Đăng', ...)")
    parser.add_argument("--ref-audio", type=str, help="File âm thanh mẫu để clone giọng (3-8 giây)")
    parser.add_argument("--api-url", type=str, help="Endpoint OpenAI-compatible API nếu chạy server VieNeu-TTS")
    parser.add_argument("--style", type=str, default="B1", choices=["B1", "B2", "B3", "B4"], help="Phong cách đồ hoạ (mặc định B1)")
    parser.add_argument("--ratio", type=str, default="16:9", choices=["16:9", "9:16"], help="Tỷ lệ khung hình")
    parser.add_argument("--preview", action="store_true", help="Tự động render bản xem trước 20s ngay sau khi chuẩn bị xong")
    parser.add_argument("--mock", action="store_true", help="Chạy thử nghiệm mock TTS không cần cài đặt VieNeu-TTS")

    args = parser.parse_args()

    script_text = None
    if args.script_file:
        with open(args.script_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
    elif args.script:
        script_text = args.script.strip()
    else:
        parser.error("Cần truyền --script hoặc --script-file.")

    build_vietnamese_project(
        project_dir=args.project,
        script_text=script_text,
        voice=args.voice,
        ref_audio=args.ref_audio,
        api_url=args.api_url,
        style=args.style,
        ratio=args.ratio,
        preview=args.preview,
        mock=args.mock
    )


if __name__ == "__main__":
    main()
