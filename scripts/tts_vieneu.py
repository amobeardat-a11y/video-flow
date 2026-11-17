#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VieNeu-TTS Adapter for Stickman Video Director
Integrates VieNeu-TTS (Phạm Nguyễn Ngọc Bảo / pnnbao97) into the stickman video pipeline.

Supports:
1. Local execution via the `vieneu` Python package (CPU/ONNX or CUDA/GPU).
2. Remote/Local HTTP API execution via OpenAI-compatible endpoints (/v1/audio/speech).
3. Zero-shot instant voice cloning from reference audio (3-8 seconds).
4. Audio standardization (16-bit WAV, 44.1kHz/48kHz) for FFmpeg and Whisper alignment.
"""

import argparse
import os
import sys
import json
import subprocess
from pathlib import Path

# Popular VieNeu-TTS preset voices
DEFAULT_VOICES = {
    "Minh Quân": "Nam miền Bắc - Tự nhiên, trầm ấm, truyền cảm (Phù hợp phóng sự, giải thích)",
    "Trúc Ly": "Nữ miền Bắc - Trong trẻo, thanh thoát, rõ ràng (Phù hợp kể chuyện, kiến thức)",
    "Hải Đăng": "Nam miền Nam - Hiện đại, năng động, cuốn hút (Phù hợp review, tin tức)",
    "Ngọc Trân": "Nữ miền Nam - Ngọt ngào, nhẹ nhàng, sinh động",
    "Quang Sơn": "Nam miền Trung - Mộc mạc, truyền cảm",
    "Phạm Tuyên": "Nam - Trầm, trang trọng, tự sự"
}


def list_preset_voices():
    """Print preset voice list from local SDK or fallback registry."""
    print("=== Danh sách giọng đọc có sẵn trong VieNeu-TTS ===")
    try:
        from vieneu import Vieneu
        tts = Vieneu()
        if hasattr(tts, "list_preset_voices"):
            voices = tts.list_preset_voices()
            for label, vid in voices:
                print(f" - {label} (ID: {vid})")
            return
    except Exception:
        pass

    for name, desc in DEFAULT_VOICES.items():
        print(f" - '{name}': {desc}")
    print("\n* Bạn cũng có thể dùng cờ --ref-audio để clone bất kỳ giọng nào từ mẫu thu 3-8s.")


def synthesize_mock(text: str, output_path: Path):
    """Generate mock audio for quick testing when VieNeu-TTS is not yet running."""
    print(f"[*] [Chế độ thử nghiệm Mock/Fallback] Tạo file audio giả lập từ Windows Speech Synthesis...")
    # Use PowerShell System.Speech to generate a WAV file
    clean_text = text.replace('"', ' ').replace("'", " ")
    ps_cmd = f"""
    Add-Type -AssemblyName System.Speech;
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
    $synth.SetOutputToWaveFile('{str(output_path.resolve())}');
    $synth.Speak('{clean_text}');
    $synth.Dispose();
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, capture_output=True)
        print(f"[✓] Đã tạo file âm thanh test: {output_path}")
    except Exception as e:
        print(f"[!] Không thể dùng Windows Speech: {e}, tạo file tone mẫu thay thế...", file=sys.stderr)
        # Create silent/tone wav via ffmpeg
        subprocess.run([
            "ffmpeg", "-v", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
            "-ar", "44100", "-ac", "1",
            str(output_path)
        ], check=True)


def synthesize_local(text: str, output_path: Path, voice: str = "Minh Quân", ref_audio: str = None, device: str = "cpu", allow_fallback: bool = False):
    """Synthesize speech using locally installed `vieneu` library."""
    try:
        from vieneu import Vieneu
    except ImportError:
        if allow_fallback:
            print("[!] Chưa cài đặt 'vieneu'. Tự động chuyển sang chế độ test...", file=sys.stderr)
            synthesize_mock(text, output_path)
            return

        print("\n[LỖI] Chưa tìm thấy thư viện 'vieneu'.", file=sys.stderr)
        print("Hãy cài đặt VieNeu-TTS bằng lệnh sau:\n", file=sys.stderr)
        print("  Windows (CPU):", file=sys.stderr)
        print("    pip install vieneu --extra-index-url https://pnnbao97.github.io/llama-cpp-python-v0.3.16/cpu/", file=sys.stderr)
        print("  Linux/GPU:", file=sys.stderr)
        print("    pip install vieneu", file=sys.stderr)
        print("\nLưu ý: Bạn cũng cần cài đặt eSpeak NG (https://github.com/espeak-ng/espeak-ng/releases) nếu dùng chế độ local.", file=sys.stderr)
        print("Hoặc bạn có thể chạy VieNeu-TTS server và dùng cờ: --api-url http://localhost:8000/v1/audio/speech", file=sys.stderr)
        print("Để chạy thử nghiệm mà không cần VieNeu-TTS, hãy thêm cờ: --mock\n", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Khởi tạo VieNeu-TTS trên thiết bị: {device}...")
    tts = Vieneu()

    print(f"[*] Đang tổng hợp giọng nói cho văn bản ({len(text)} ký tự)...")
    if ref_audio:
        print(f"[*] Kích hoạt chế độ Voice Cloning từ file mẫu: {ref_audio}")
        audio = tts.infer(text=text, ref_audio=ref_audio)
    else:
        print(f"[*] Sử dụng giọng đọc mẫu: {voice}")
        audio = tts.infer(text=text, voice=voice)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tts.save(audio, str(output_path))
    print(f"[✓] Đã tạo file âm thanh: {output_path}")


def synthesize_api(text: str, output_path: Path, api_url: str, voice: str = "Minh Quân", api_key: str = None):
    """Synthesize speech via OpenAI-compatible REST API endpoint."""
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        pass

    print(f"[*] Gửi yêu cầu tổng hợp TTS tới API: {api_url}")
    payload = {
        "model": "vieneu-v3-turbo",
        "input": text,
        "voice": voice,
        "response_format": "wav"
    }

    req_data = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(api_url, data=req_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            audio_bytes = resp.read()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            print(f"[✓] Đã lưu file âm thanh từ API: {output_path}")
    except urllib.error.URLError as e:
        print(f"\n[LỖI] Không thể kết nối tới VieNeu-TTS API ({api_url}): {e}", file=sys.stderr)
        print("Hãy đảm bảo server VieNeu-TTS đang chạy hoặc chuyển sang chạy local không truyền --api-url.", file=sys.stderr)
        sys.exit(1)


def normalize_audio(audio_path: Path):
    """Ensure audio is 16-bit PCM WAV (44.1kHz or 48kHz) for FFmpeg and Whisper."""
    temp_wav = audio_path.with_suffix('.norm.wav')
    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-i", str(audio_path),
        "-ar", "44100",
        "-ac", "1",
        "-sample_fmt", "s16",
        str(temp_wav)
    ]
    try:
        subprocess.run(cmd, check=True)
        temp_wav.replace(audio_path)
    except Exception:
        # If ffmpeg fails or isn't needed, keep original file
        if temp_wav.exists():
            temp_wav.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="VieNeu-TTS Adapter for Stickman Video Director",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # 1. Tạo audio từ văn bản trực tiếp (local):
  python scripts/tts_vieneu.py --text "Chào mừng bạn đến với kênh của tôi!" -o narration.wav --voice "Minh Quân"

  # 2. Tạo audio từ file kịch bản tiếng Việt:
  python scripts/tts_vieneu.py --file script.txt -o my-video/narration.wav

  # 3. Clone giọng từ 1 đoạn ghi âm mẫu 5s:
  python scripts/tts_vieneu.py --file script.txt -o narration.wav --ref-audio sample_voice.wav

  # 4. Sử dụng server API:
  python scripts/tts_vieneu.py --text "Xin chào" -o narration.wav --api-url http://localhost:8000/v1/audio/speech

  # 5. Xem danh sách giọng có sẵn:
  python scripts/tts_vieneu.py --list-voices
        """
    )
    parser.add_argument("--text", type=str, help="Văn bản tiếng Việt cần đọc")
    parser.add_argument("--file", type=Path, help="Đường dẫn file text chứa kịch bản")
    parser.add_argument("-o", "--output", type=Path, default=Path("narration.wav"), help="File âm thanh xuất ra (.wav)")
    parser.add_argument("--voice", type=str, default="Minh Quân", help="Tên giọng đọc VieNeu-TTS (mặc định: 'Minh Quân')")
    parser.add_argument("--ref-audio", type=str, help="File âm thanh mẫu (3-8s) để clone giọng (Zero-shot cloning)")
    parser.add_argument("--api-url", type=str, help="Endpoint OpenAI-compatible API (nếu chạy server VieNeu-TTS)")
    parser.add_argument("--api-key", type=str, default=os.environ.get("VIENEU_API_KEY"), help="API Key nếu dùng dịch vụ cloud")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"], help="Thiết bị chạy local (cpu hoặc cuda)")
    parser.add_argument("--list-voices", action="store_true", help="Hiển thị danh sách giọng đọc có sẵn")
    parser.add_argument("--test", action="store_true", help="Chạy thử nghiệm câu chào mẫu")
    parser.add_argument("--mock", action="store_true", help="Tạo audio test giả lập (không cần cài VieNeu-TTS)")

    args = parser.parse_args()

    if args.list_voices:
        list_preset_voices()
        return

    text = None
    if args.test:
        text = "Xin chào! Đây là video hoạt hình người que tiếng Việt, được tạo hoàn toàn tự động bằng VieNeu-TTS và Stickman Video Director."
    elif args.file:
        if not args.file.exists():
            parser.error(f"File không tồn tại: {args.file}")
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read().strip()
    elif args.text:
        text = args.text.strip()
    else:
        parser.error("Cần truyền --text hoặc --file (hoặc --test / --list-voices).")

    if not text:
        parser.error("Nội dung văn bản không được để trống.")

    output_path = args.output.resolve()

    if args.mock:
        synthesize_mock(text, output_path)
    elif args.api_url:
        synthesize_api(text, output_path, args.api_url, voice=args.voice, api_key=args.api_key)
    else:
        synthesize_local(text, output_path, voice=args.voice, ref_audio=args.ref_audio, device=args.device)

    # Chuẩn hoá file wav để tương thích tốt nhất với Whisper và FFmpeg
    normalize_audio(output_path)
    print(f"[✓] Đã hoàn tất và chuẩn hóa: {output_path}")


if __name__ == "__main__":
    main()
