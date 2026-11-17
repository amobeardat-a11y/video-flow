#!/usr/bin/env python3
"""Build the Vietnamese derivative-mistakes demonstration project.

Use an isolated environment for gTTS (see requirements-derivative-demo.txt).
Caption boundaries come from exact concatenated audio chunks; no proportional
word timing is used. Existing voice clips are reused on repeat runs.
"""

from __future__ import annotations

import json
import hashlib
import math
import re
import struct
import subprocess
import time
import wave
from pathlib import Path

from gtts import gTTS


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "videos" / "dao_ham_loi_sai"
RATE = 24000


def make(title, say, beats, visual):
    return {"title": title, "say": say, "beats": beats, "visual": visual}


SCENES = [
    make("THUỘC MÀ VẪN SAI?", [
        "Thuộc bảng công thức, nhưng bài đạo hàm vẫn sai?",
        "Có thể bạn học thuộc nhiều hơn là hiểu.",
        "Cùng xem sáu lỗi thường gặp và cách sửa.",
    ], [("think", "worried", "Thuộc công thức...", "question"), ("explain", "surprised", "...nhưng vẫn sai?", "question"), ("point", "smile", "Sáu lỗi cần tránh", "check")], {"kind": "compare", "wrong": "Chỉ học thuộc", "right": "Hiểu rồi mới tính"}),
    make("LỖI 1: HỌC VẸT", [
        "Lỗi đầu tiên: xem đạo hàm như trò thay công thức.",
        "Thấy x bình phương, bạn lập tức viết hai x.",
        "Nhưng hai x đang nói gì trên đồ thị?",
    ], [("think", "worried", "Cứ thấy x² là viết 2x", "question"), ("point", "open", "Công thức có ý nghĩa gì?", "question"), ("explain", "think", "Hãy nhìn đồ thị", "arrow")], {"kind": "graph", "function": "square"}),
    make("ĐẠO HÀM LÀ ĐỘ DỐC", [
        "Đạo hàm cho biết độ dốc tại một điểm.",
        "Đường cong càng dốc, độ lớn càng cao.",
        "Ở chỗ phẳng, độ dốc có thể bằng không.",
    ], [("point", "open", "Độ dốc ngay tại điểm", "arrow"), ("explain", "smile", "Độ lớn độ dốc tăng", "arrow"), ("think", "think", "Chỗ phẳng → độ dốc 0", "check")], {"kind": "graph", "function": "square"}),
    make("CÁCH SỬA LỖI 1", [
        "Khi học quy tắc, hãy vẽ một đồ thị đơn giản.",
        "Đoán chiều dốc trước khi tính ra kết quả.",
        "Cách đó giúp bạn nhận ra dấu sai nhanh hơn.",
    ], [("wave", "smile", "Vẽ đồ thị nhỏ", "idea"), ("point", "think", "Đoán chiều dốc", "arrow"), ("explain", "smile", "Rồi kiểm đáp án", "check")], {"kind": "formula", "lines": ["f′(a) = độ dốc tại a", "Dốc lên: dương; dốc xuống: âm"]}),
    make("LỖI 2: NHẦM GIÁ TRỊ", [
        "Lỗi hai: lẫn giá trị hàm với giá trị đạo hàm.",
        "Với hàm x bình phương, thay ba được chín.",
        "Chín là độ cao, chưa phải độ dốc.",
    ], [("think", "worried", "f(3) và f′(3) khác nhau", "question"), ("point", "open", "f(3) = 9", "arrow"), ("explain", "think", "9 là độ cao", "question")], {"kind": "compare", "wrong": "f(3) = f′(3)", "right": "Giá trị khác độ dốc"}),
    make("ĐỘ CAO KHÁC ĐỘ DỐC", [
        "Đạo hàm của x bình phương là hai x.",
        "Tại x bằng ba, độ dốc bằng sáu.",
        "Nhớ nhé: chín là vị trí, sáu là độ nghiêng.",
    ], [("point", "open", "f′(x) = 2x", "arrow"), ("explain", "surprised", "f′(3) = 6", "idea"), ("wave", "smile", "9 là cao; 6 là dốc", "check")], {"kind": "formula", "lines": ["f(3) = 3² = 9", "f′(3) = 2 · 3 = 6"]}),
    make("TÍNH TẠI MỘT ĐIỂM", [
        "Muốn tìm đạo hàm tại điểm, làm hai bước.",
        "Trước tiên, tính đạo hàm tổng quát.",
        "Sau đó mới thay tọa độ điểm vào.",
    ], [("think", "think", "Có hai bước rõ ràng", "clock"), ("point", "open", "Bước 1: tính f′(x)", "arrow"), ("explain", "smile", "Bước 2: thay x = a", "check")], {"kind": "formula", "lines": ["f(x) → f′(x)", "f′(x) → f′(a)"]}),
    make("LỖI 3: SAI SỐ MŨ", [
        "Lỗi ba: giữ nguyên số mũ sau khi đạo hàm.",
        "X mũ ba không thành ba x mũ ba.",
        "Số mũ phải giảm đúng một đơn vị.",
    ], [("think", "worried", "Quên giảm số mũ", "question"), ("point", "angry", "3x³ là sai", "arrow"), ("explain", "smile", "Đúng là 3x²", "check")], {"kind": "compare", "wrong": "(x³)′ = 3x³", "right": "(x³)′ = 3x²"}),
    make("QUY TẮC LŨY THỪA", [
        "Đưa số mũ xuống làm hệ số phía trước.",
        "Rồi giảm số mũ của x đi một.",
        "Vậy x mũ bốn cho ra bốn x mũ ba.",
    ], [("point", "open", "Đưa số mũ xuống", "arrow"), ("explain", "think", "Giảm đi một", "clock"), ("wave", "smile", "x⁴ → 4x³", "check")], {"kind": "formula", "lines": ["(x³)′ = 3x²", "(x⁴)′ = 4x³"]}),
    make("HẰNG SỐ THÌ SAO?", [
        "Còn một trường hợp rất dễ quên.",
        "Đạo hàm của hằng số bảy là không.",
        "Đường thẳng ngang có độ dốc bằng không.",
    ], [("think", "think", "Số 7 có thay đổi không?", "question"), ("point", "surprised", "Không: (7)′ = 0", "idea"), ("explain", "smile", "Đường ngang, dốc 0", "check")], {"kind": "compare", "wrong": "(7)′ = 7", "right": "(7)′ = 0"}),
    make("LỖI 4: QUÊN LỚP TRONG", [
        "Lỗi bốn: quên đạo hàm phần bên trong.",
        "Xét cả ngoặc hai x cộng một, mũ ba.",
        "Dừng ở ba nhân ngoặc bình phương là chưa đủ.",
    ], [("think", "worried", "Có hàm trong hàm", "question"), ("point", "open", "Ngoài: lũy thừa ba", "arrow"), ("explain", "surprised", "Còn phần bên trong!", "idea")], {"kind": "compare", "wrong": "3(2x+1)²", "right": "6(2x+1)²"}),
    make("QUY TẮC DÂY CHUYỀN", [
        "Đặt u bằng hai x cộng một.",
        "Đạo hàm u mũ ba là ba u bình phương.",
        "Nhưng còn phải nhân thêm đạo hàm của u.",
    ], [("think", "think", "Đặt u = 2x + 1", "idea"), ("point", "open", "Lớp ngoài: 3u²", "arrow"), ("explain", "smile", "Nhân thêm u′", "check")], {"kind": "formula", "lines": ["u = 2x + 1", "(u³)′ = 3u² · u′"]}),
    make("ĐỪNG LÀM RƠI SỐ 2", [
        "Đạo hàm của u ở đây là hai.",
        "Vậy đáp án đúng có hệ số sáu.",
        "Đó chính là quy tắc dây chuyền.",
    ], [("point", "open", "u′ = 2", "arrow"), ("explain", "surprised", "3 nhân 2 bằng 6", "idea"), ("wave", "smile", "Đáp án đủ hệ số", "check")], {"kind": "formula", "lines": ["u′ = 2", "f′(x)=6(2x+1)²"]}),
    make("MẸO NHỚ DÂY CHUYỀN", [
        "Mẹo nhớ: lớp ngoài trước, lớp trong sau.",
        "Nếu bên trong chỉ là x, hệ số là một.",
        "Nếu là hai x, đừng làm rơi số hai.",
    ], [("explain", "smile", "Ngoài trước", "arrow"), ("point", "think", "Trong sau", "clock"), ("wave", "smile", "Nhân đủ hệ số", "check")], {"kind": "formula", "lines": ["[g(x)]³ → 3[g(x)]²", "Rồi nhân thêm g′(x)"]}),
    make("LỖI 5: NHẦM QUY TẮC TÍCH", [
        "Lỗi năm: nhân hai đạo hàm với nhau.",
        "Đây là một phép biến đổi sai phổ biến.",
        "Đạo hàm của tích cần hai hạng tử.",
    ], [("think", "worried", "(uv)′ = u′v′?", "question"), ("point", "angry", "Sai quy tắc tích", "arrow"), ("explain", "smile", "Cần hai hạng tử", "check")], {"kind": "compare", "wrong": "(uv)′ = u′v′", "right": "(uv)′ = u′v + uv′"}),
    make("VÍ DỤ QUY TẮC TÍCH", [
        "Đạo hàm x bình phương nhân sin x sẽ là:",
        "Hai x nhân sin x, cộng x bình phương cos x.",
        "Đừng chỉ giữ một trong hai phần ấy.",
    ], [("point", "open", "Đạo hàm từng lượt", "arrow"), ("explain", "think", "Cộng hai hạng tử", "idea"), ("wave", "smile", "Không làm rơi phần nào", "check")], {"kind": "formula", "lines": ["(x² sin x)′", "= 2x sin x + x² cos x"]}),
    make("LỖI 6: QUÊN ĐIỂM GÃY", [
        "Lỗi sáu: tưởng đồ thị nào cũng có đạo hàm.",
        "Giá trị tuyệt đối có một góc nhọn.",
        "Tại x bằng không, hai phía dốc khác nhau.",
    ], [("think", "worried", "Góc nhọn có độ dốc?", "question"), ("point", "surprised", "Nhìn vào x = 0", "arrow"), ("explain", "think", "Hai phía khác nhau", "question")], {"kind": "graph", "function": "abs"}),
    make("KHÔNG CÓ ĐẠO HÀM TẠI 0", [
        "Bên trái dốc âm một, bên phải dốc dương một.",
        "Hai giới hạn không khớp, nên đạo hàm không tồn tại.",
        "Đừng áp dụng công thức tại điểm gãy.",
    ], [("point", "open", "Trái: −1", "arrow"), ("explain", "surprised", "Phải: +1", "arrow"), ("think", "think", "Tại 0: không tồn tại", "question")], {"kind": "compare", "wrong": "|x|: f′(0)=0", "right": "f′(0) không tồn tại"}),
    make("BỐN CÂU HỎI CUỐI", [
        "Trước khi chốt đáp án, tự hỏi bốn điều.",
        "Độ dốc có hợp lý? Quy tắc đã đúng?",
        "Đã thay đúng điểm, và hàm có khả vi?",
    ], [("think", "think", "1. Độ dốc hợp lý?", "question"), ("point", "open", "2. Đúng quy tắc?", "question"), ("explain", "smile", "3. Đúng điểm? 4. Khả vi?", "check")], {"kind": "formula", "lines": ["Hiểu → Chọn quy tắc", "Tính → Kiểm tra"]}),
    make("HỌC ĐẠO HÀM THÔNG MINH", [
        "Chọn một bài cũ bạn từng làm sai.",
        "Soi lại bằng bốn câu hỏi vừa rồi.",
        "Hiểu bản chất giúp nhớ công thức lâu hơn.",
    ], [("think", "think", "Lấy một bài cũ", "idea"), ("point", "open", "Kiểm theo bốn câu hỏi", "arrow"), ("wave", "smile", "Hiểu rồi sẽ nhớ lâu", "heart")], {"kind": "formula", "lines": ["Đừng chỉ thuộc công thức.", "Hãy hiểu độ dốc và quy tắc."]}),
]


def run(command):
    subprocess.run(command, check=True, capture_output=True)


def samples(path: Path) -> bytes:
    with wave.open(str(path), "rb") as source:
        assert source.getframerate() == RATE and source.getnchannels() == 1 and source.getsampwidth() == 2
        return source.readframes(source.getnframes())


def tone(path: Path, hz: float, seconds: float):
    frames = []
    total = int(seconds * RATE)
    for i in range(total):
        x = i / RATE
        envelope = min(1, i / (RATE * .015), (total - i) / (RATE * .06))
        frames.append(struct.pack("<h", int(11000 * envelope * math.sin(2 * math.pi * hz * x))))
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        out.writeframes(b"".join(frames))


def main():
    PROJECT.mkdir(parents=True, exist_ok=True)
    cache = PROJECT / "voice_clips"
    cache.mkdir(exist_ok=True)
    pcm_parts = []
    cues = []
    scenes = []
    clock_samples = 0
    palette = ("#F8F6F0", "#F2F6FB", "#FFF8F1", "#F3F8F4")
    errors = {2, 5, 8, 11, 15, 17}
    sfx = []
    (PROJECT / "sfx").mkdir(exist_ok=True)
    tone(PROJECT / "sfx" / "error.wav", 220, .20)
    tone(PROJECT / "sfx" / "correct.wav", 660, .16)

    for index, item in enumerate(SCENES, 1):
        scene_start = clock_samples
        beats = []
        for part_index, (phrase, acting) in enumerate(zip(item["say"], item["beats"]), 1):
            key = hashlib.sha256(phrase.encode("utf-8")).hexdigest()[:12]
            mp3 = cache / f"{key}.mp3"
            wav = cache / f"{key}.wav"
            if not wav.exists():
                if not mp3.exists():
                    for attempt in range(3):
                        try:
                            gTTS(phrase, lang="vi", slow=False).save(str(mp3))
                            break
                        except Exception:
                            if attempt == 2:
                                raise
                            time.sleep(2 ** attempt)
                run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(wav)])
            data = samples(wav)
            start = clock_samples / RATE
            duration = len(data) // 2 / RATE
            pcm_parts.append(data)
            clock_samples += len(data) // 2
            cues.append({"start": round(start, 3), "end": round(clock_samples / RATE, 3), "text": phrase})
            action, expression, visual_text, symbol = acting
            beats.append({"at": round(start - scene_start / RATE, 3), "action": action, "expression": expression, "text": visual_text, "symbol": symbol})
            # Small breathing pause becomes part of the master WAV and timeline.
            pause = int(RATE * (.07 if part_index < 3 else .12))
            pcm_parts.append(b"\0\0" * pause)
            clock_samples += pause
        scene_duration = (clock_samples - scene_start) / RATE
        visual = dict(item["visual"])
        if visual["kind"] in {"formula", "compare"}:
            visual["reveal_at"] = beats[2]["at"] if item["title"] in {"TÍNH TẠI MỘT ĐIỂM", "LỖI 4: QUÊN LỚP TRONG"} else beats[1]["at"]
        if item["title"] == "ĐẠO HÀM LÀ ĐỘ DỐC":
            visual["tangent_keys"] = [
                {"at": 0, "x": .4},
                {"at": beats[1]["at"], "x": .8},
                {"at": beats[2]["at"] - .6, "x": 1.5},
                {"at": beats[2]["at"], "x": 0},
            ]
        scenes.append({"id": f"scene_{index:02d}", "duration": round(scene_duration, 3), "mode": "code", "heading": item["title"], "background": palette[(index - 1) % len(palette)], "actor_side": "left" if index % 2 else "right", "beats": beats, "visual": visual})
        if index in errors:
            sfx.append({"path": "sfx/error.wav", "at": round(scene_start / RATE, 3), "gain": .09})
        print(f"scene_{index:02d}: {scene_duration:.2f}s", flush=True)

    with wave.open(str(PROJECT / "narration.wav"), "wb") as out:
        out.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        out.writeframes(b"".join(pcm_parts))
    manifest = {
        "version": 1, "ready": True, "title": "Sáu lỗi sai khi học đạo hàm",
        "language": "vi", "ratio": "16:9", "fps": 30,
        "character_anchor": "Người que 2D có đầu tròn trắng viền đen, hai mắt chấm, một miệng đổi biểu cảm, đúng hai tay hai chân nét đen dày, không quần áo.",
        "narration": "narration.wav", "captions": "captions.json", "sfx": sfx, "scenes": scenes,
    }
    (PROJECT / "script.txt").write_text("\n\n".join(" ".join(s["say"]) for s in SCENES) + "\n", encoding="utf-8")
    (PROJECT / "captions.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # The bundled NotoSans subset has no U+2192 glyph; keep all visual text renderable.
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2).replace("→", "=>")
    (PROJECT / "production.json").write_text(manifest_text + "\n", encoding="utf-8")
    (PROJECT / "voice-source.json").write_text(json.dumps({"service": "gTTS", "language": "vi", "chunks": len(cues), "alignment": "caption timing from exact concatenated PCM chunks"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for stale in cache.iterdir():
        if stale.is_file() and re.fullmatch(r"\d{2}_\d\.(?:mp3|wav)", stale.name):
            stale.unlink()
    print(json.dumps({"duration": round(clock_samples / RATE, 3), "scenes": len(scenes), "cues": len(cues), "project": str(PROJECT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
