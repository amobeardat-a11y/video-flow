# Quy trình sản xuất video người que dài 1:30–3:30

Đây là hướng dẫn vận hành cho agent chạy trong Antigravity. Mục tiêu của mỗi lần chạy là **một MP4 hoàn chỉnh dài 90–210 giây**, có người que chuyển động và thay đổi biểu cảm theo nội dung, lời đọc liên tục, phụ đề tiếng Việt đúng nhịp, âm thanh phù hợp và báo cáo kiểm tra. Khi người dùng chỉ đưa chủ đề, hãy tự viết kịch bản và triển khai; chỉ hỏi thêm nếu thiếu một quyết định thật sự không thể suy ra.

## Phân biệt model và chọn đường tạo cảnh

Gemini 3.8 Flash trong Antigravity làm đạo diễn, viết kịch bản, tạo code, gọi công cụ và kiểm tra đầu ra. **Đừng gửi prompt tạo clip vào `gemini-3.8-flash` như thể đó là model video.** Theo [tài liệu Google về Antigravity](https://ai.google.dev/gemini-api/docs/antigravity-agent) và [tài liệu Gemini API về video](https://ai.google.dev/gemini-api/docs/video), video được tạo bằng Gemini Omni Flash hoặc Veo nếu tài khoản/công cụ hiện tại hỗ trợ. Kiểm tra model, giới hạn clip, tỉ lệ, giá/quota và quyền truy cập thật trong phiên đang dùng trước khi gọi. Nếu không có đường tạo video, hoàn thành phim bằng cảnh code; không để lỗ hổng trên timeline.

Mỗi cảnh có một trong hai `mode`:

- `code`: rig người que vẽ và animate bằng Python/Pillow, với hành động `walk`, `wave`, `point`, `think`, `explain`, `shrug`, `recoil`, `trace`, `present`, `celebrate`, `crouch`, `lean`; biểu cảm `smile`, `open`, `think`, `neutral`, `sad`, `worried`, `angry`, `surprised`. Phải có ít nhất hai beat khác nhau trong cảnh.
- `video`: clip thật đã tạo bằng công cụ video, lưu tại đường dẫn trong project. Ghi `provider`, `model` và prompt thực tế trong manifest. Pipeline cắt clip theo thời lượng cảnh, chuẩn hóa 30 fps và bỏ âm thanh của clip để giữ một lời đọc xuyên suốt.

Thiết kế nhân vật mặc định cho cảnh `code`: đầu tròn màu trắng ngà, viền và thân xanh than đậm; tay/chân là nét cong mềm, đầu nét bo tròn, bàn tay/bàn chân nhỏ. Mặt có lông mày, mắt, miệng đổi theo biểu cảm và chớp mắt nhẹ; cơ thể có nhịp thở/chuyển trọng tâm rất nhỏ. `draw_stickman_soft` trong `scripts/stickman_rig.py` vẽ ở độ phân giải 2× rồi thu nhỏ để khử răng cưa. Chuyển giữa các beat bằng easing, không đổi tư thế đột ngột. Giữ cùng tỉ lệ đầu, màu mực và kiểu mặt ở mọi cảnh; dùng `videos/dao_ham_loi_sai/output/character_v2_sheet.png` làm tham chiếu khi tạo clip bằng model.

Nếu người dùng chọn phong cách `asset/a7`, dùng `"style": "a7"` cho từng cảnh `code`. `scripts/a7_style.py` vẽ người que nét mực mảnh, mặt trắng, hai lọn tóc cong, găng tay trắng, bàn chân ngắn và lớp học màu trầm; đây là **bản dựng bằng code lấy cảm hứng từ A7**, không phải clip được tạo bằng workflow model A7 đã kiểm chứng. Ví dụ chạy được ở `videos/dao_ham_loi_sai_a7/production.json`. Nếu dùng cảnh `video` theo A7, đọc `skills/directing-stickman-videos/references/a7-prompt-contract.md` và `a7-acceptance.md`, dùng đúng hai block prompt cố định và gắn ảnh tham chiếu vào đầu vào model thực tế. Không gọi cảnh code là clip A7 do model tạo.

Rig A7 bản 3 tham khảo `files (1).zip`: lấy ý tưởng chuỗi khớp, IK cho tay, chân bám sàn, dáng gập/nghiêng, hướng vươn theo vị trí bảng và nội suy tư thế. Mỗi tay có điểm xoay vai riêng theo thân, khuỷu và bàn tay; tay nghỉ gập ở eo trên, khuỷu hướng ra ngoài. Giữ hai gốc tay nối đúng vai khi chuyển beat; tránh tay thẳng ngang, hai tay đối xứng máy móc hoặc bàn tay xuyên thân. Trong cảnh, dùng `trace` khi dò đồ thị, `crouch` khi soi điểm gãy, `recoil` khi phát hiện lời giải sai, `present` khi trình bày, `celebrate` ở kết quả đúng. `scripts/a7_style.py` còn animate kim đồng hồ, quả lắc và viên phấn; thẻ nội dung trượt vào nhẹ theo beat. Đồ vật chuyển động phải hỗ trợ ý thoại và tránh che công thức, mặt người que hoặc phụ đề.

Ưu tiên `code` cho nhân vật lặp lại, biểu đồ, nội dung cần chính xác và cảnh cần sửa nhanh. Dùng `video` cho cảnh hành động giàu chuyển động khi có reference nhân vật và công cụ tạo video. Không kéo giãn clip quá ngắn, lặp một động tác để lấp thời gian, hoặc cho một cảnh tĩnh kéo dài quá 12 giây.

Cảnh `code` có thể thêm `visual`: `{"kind":"formula","lines":["...","..."]}`, `{"kind":"compare","wrong":"...","right":"..."}` hoặc `{"kind":"graph","function":"square"}` / `"abs"`. `reveal_at` (giây trong cảnh) cho công thức hoặc đáp án xuất hiện đúng lúc lời đọc. Đồ thị `square` còn nhận `tangent_keys` gồm các cặp `at`, `x` để chuyển độ dốc theo lời. Ví dụ hoàn chỉnh nằm trong `videos/dao_ham_loi_sai/production.json`.

## Trình tự bắt buộc

1. **Khảo sát:** đọc `README.md`, file này, `scripts/longform_stickman.py` và `scripts/stickman_rig.py`. Xác định chủ đề, đối tượng xem, tỉ lệ `16:9` hay `9:16`, mục tiêu thời lượng 90–210 giây, phong cách/màu và giọng đọc. Nếu không được chỉ định, chọn `16:9`, 120 giây, tiếng Việt và một nhân vật xuyên suốt. Không tự nhận các ví dụ 8–54 giây là video dài đã hoàn thành.
2. **Lập kịch bản:** viết `script.txt` theo mở đầu có hành động/hình ảnh trong 3 giây, nêu vấn đề, 2–4 phần triển khai, kết có payoff rõ. Chia thành 12–26 cảnh, thường 5–10 giây/cảnh. Mỗi cảnh có mục đích, hành động người que, biểu cảm, vật thể/chữ minh họa và liên hệ với câu thoại. Thay đổi diễn xuất hoặc trạng thái hình ảnh mỗi 2–4 giây. Dùng cùng một mô tả nhân vật, màu, độ dày nét và cách vẽ mặt cho mọi clip model.
3. **Tạo manifest:** chạy `init` bên dưới, sau đó sửa toàn bộ `production.json`: thay mọi placeholder, đặt đúng scene duration và beat theo kịch bản. Với cảnh model thêm `mode`, `video`, `prompt`, `provider`, `model`. Kiểm tra tổng thời lượng bằng `validate --plan-only`. `ready` chỉ đổi sang `true` sau khi đã thay hết placeholder và có file cần thiết; đây là cờ kỹ thuật, không thay thế đánh giá hình ảnh.
4. **Lời đọc:** tạo một `narration.wav` cho cả phim. Có thể dùng `scripts/tts_vieneu.py` nếu VieNeu-TTS đã cài, hoặc nguồn TTS/giọng thu hợp lệ khác. Không dùng `--mock` cho bản giao. Nghe thử câu đầu, giữa và cuối; sửa phát âm, tiếng ồn, âm lượng. Dùng `ffprobe` lấy thời lượng thật và chỉnh scene durations để tổng timeline lệch lời đọc không quá 2 giây. Không tăng tốc giọng để ép khớp.
5. **Phụ đề:** tạo word timing từ chính audio, rồi nhóm thành `captions.json` có `start`, `end`, `text`. Có thể dùng Whisper ở lệnh bên dưới; nếu không có Whisper, agent phải tự căn bằng nghe và xem waveform. Không dùng timing tỉ lệ theo số chữ làm bản cuối. Mỗi cue một dòng, không tràn chiều ngang, không chồng cue, đúng dấu tiếng Việt. Pipeline sẽ xuất phụ đề cháy vào MP4 và SRT riêng.
6. **Tạo clip model:** chỉ cho các cảnh `video`, tạo bằng model video thật qua công cụ Antigravity/API đang truy cập được; lưu clip vào thư mục project và ghi nguồn trong manifest. Dùng reference nhân vật/khung hình đầu khi công cụ hỗ trợ. Xem clip trước khi nhận: đúng danh tính, hai tay/hai chân, mặt rõ, chuyển động có nguyên nhân, không đổi phục trang bất ngờ, không có chữ AI sai, không có lỗi hình thể. Clip phải dài ít nhất bằng slot timeline. Nếu lỗi, sửa prompt/reference và tạo lại cảnh đó; giữ các cảnh đã đạt.
7. **Xem trước:** render 15–30 giây đầu, xem ở tốc độ bình thường với âm thanh. Sửa nhịp mở đầu, chuyển cảnh, khẩu hình/biểu cảm, vị trí phụ đề, âm lượng. Rồi render toàn phim.
8. **Kiểm tra toàn phim:** đọc `report.json` và `scene-contact-sheet.jpg`, mở MP4 thật và nghe/xem ít nhất đầu, các đoạn giữa, cuối và mọi scene chuyển từ `code` sang `video`. Contact sheet lấy frame đầu/giữa/cuối của từng cảnh từ MP4 đã mã hóa. Đối chiếu script, cue, thời lượng, tỉ lệ, chuyển động, nét nhân vật và nhạc/SFX. Nếu hỏng, sửa scene/âm thanh và render lại. Báo `creative_review: pending` trong report chỉ là kiểm tra máy; agent không được gọi nó là đã được xem xét về thẩm mỹ.
9. **Giao:** đưa đường dẫn MP4, SRT, manifest, report và mô tả ngắn những gì đã kiểm tra cùng giới hạn còn lại. Chỉ nói đã xem/nghe phần nào nếu thực sự đã làm. Không xuất bản hoặc tải lên dịch vụ ngoài nếu người dùng chưa yêu cầu.

## Lệnh chạy trên PowerShell tại root repo

Yêu cầu: Python 3.10+, Pillow, FFmpeg/FFprobe trên `PATH`. Node 20+ dùng cho bước nhóm phụ đề có sẵn. Cài dependency local khi thiếu: `python -m pip install pillow` và `npm ci --prefix skills/directing-stickman-videos`.

```powershell
python scripts/longform_stickman.py init videos/my_topic --duration 120 --ratio 16:9 --scene-seconds 8
# Sửa videos/my_topic/script.txt và videos/my_topic/production.json
python scripts/longform_stickman.py validate videos/my_topic/production.json --plan-only

# Ví dụ TTS local; có thể thay bằng narration.wav từ nguồn khác
python scripts/tts_vieneu.py --file videos/my_topic/script.txt -o videos/my_topic/narration.wav --voice "Minh Quân"

# Nếu Whisper đã có hoặc cho phép tải model; kiểm tra lại chữ và mốc thời gian sau khi chạy
python skills/directing-stickman-videos/scripts/align_captions.py videos/my_topic/narration.wav --output videos/my_topic/word-timings.json --language vi --allow-model-download
node skills/directing-stickman-videos/scripts/autopilot.mjs captions videos/my_topic/word-timings.json videos/my_topic/captions.json

# Sau khi đã tạo đủ clip video, đặt ready=true trong production.json
python scripts/longform_stickman.py validate videos/my_topic/production.json
python scripts/longform_stickman.py render videos/my_topic/production.json --preview-seconds 20
python scripts/longform_stickman.py render videos/my_topic/production.json
```

File đầu ra ở `videos/my_topic/output/`: `preview.mp4`, `film.mp4`, `preview_build/captions.srt`, `film_build/captions.srt`, `film_build/report.json`, `film_build/scene-contact-sheet.jpg`. Media cho mỗi scene được lưu trong `film_build/scenes/` để sửa từng cảnh và kiểm tra. Render lại sẽ thay file trong `output/` của chính project đó.

## Hợp đồng `production.json`

`init` tạo manifest mẫu. Agent phải sửa nội dung và timeline theo audio thật. Ví dụ hai kiểu scene:

```json
{
  "version": 1,
  "ready": true,
  "title": "Một ý tưởng giải thích bằng người que",
  "language": "vi",
  "ratio": "16:9",
  "fps": 30,
  "character_anchor": "Người que 2D đầu tròn trắng ngà viền xanh than, thân và tứ chi là nét cong mềm bo tròn, bàn tay và bàn chân nhỏ, mặt có lông mày và miệng biểu cảm, đúng hai tay hai chân, không quần áo.",
  "narration": "narration.wav",
  "captions": "captions.json",
  "music": "music/bed.wav",
  "sfx": [{"path": "sfx/pop.wav", "at": 3.2, "gain": 0.25}],
  "scenes": [
    {
      "id": "scene_01", "duration": 8, "mode": "code",
      "heading": "MỞ ĐẦU", "background": "#F8F6F0", "actor_side": "left",
      "beats": [
        {"at": 0, "action": "think", "expression": "worried", "text": "Vấn đề đang xảy ra", "symbol": "question"},
        {"at": 3, "action": "point", "expression": "surprised", "text": "Chi tiết bất ngờ", "symbol": "idea"}
      ]
    },
    {
      "id": "scene_02", "duration": 8, "mode": "video",
      "video": "model_clips/scene_02.mp4", "provider": "Google", "model": "tên model thực tế",
      "prompt": "Người que 2D đầu tròn trắng ngà viền xanh than, thân và tứ chi là nét cong mềm bo tròn, bàn tay và bàn chân nhỏ, mặt có lông mày và miệng biểu cảm, đúng hai tay hai chân, không quần áo. Nhân vật chỉ tay vào vật thể rồi chuyển từ ngạc nhiên sang vui mừng. Camera cố định; 8 giây; không chữ."
    }
  ]
}
```

Ví dụ trên chỉ minh họa schema; phim thật phải có tổng `duration` 90–210 giây. `music` và `sfx` là tùy chọn. Nếu dùng, chỉ đưa file có quyền sử dụng và nguồn rõ ràng; lời đọc phải nghe rõ hơn nhạc. Không đặt lời đọc trong clip model vì pipeline tắt âm thanh gốc của clip.

`captions.json` là một mảng:

```json
[
  {"start": 0.2, "end": 1.8, "text": "Một câu ngắn đúng nhịp đọc."},
  {"start": 1.8, "end": 3.4, "text": "Ý tiếp theo hiện một dòng."}
]
```

## Prompt cho mỗi scene model

Giữ `character_anchor` trong manifest nguyên văn ở đầu **mọi** `prompt` model: tỉ lệ đầu/thân, màu nét, mặt, tóc/phụ kiện, trang phục, số tay/chân, bảng màu. Bộ kiểm tra sẽ từ chối prompt thiếu chuỗi này. Thêm đúng **một mục tiêu hành động** và 2–3 beat có thời điểm, ví dụ “0–2s thấy vấn đề, 2–5s chỉ tay và chuyển từ lo lắng sang ngạc nhiên, 5–8s giải pháp hiện trong hành động”. Nêu camera, tỉ lệ và frame reference nếu dùng. Yêu cầu không chèn phụ đề/chữ; phụ đề được dựng sau. Xuất clip không có lời thoại riêng. Không dùng câu “same character” nếu không có reference hoặc mô tả cố định đầy đủ.

## Điều kiện hoàn thành

- `validate` thành công; report có `decode: pass`, video đúng tỉ lệ/âm thanh và tổng thời lượng 90–210 giây.
- Người que thực sự đổi hành động và biểu cảm theo lời, không chỉ lắc toàn hình hoặc thay subtitle. Cảnh model phải được xem để phát hiện drift và lỗi cơ thể.
- Lời đọc không bị cắt, phụ đề không tràn, không sai mốc lớn, không trùng âm thanh của clip model.
- Mở đầu, ít nhất ba đoạn rải trong thân phim và kết được xem/nghe ở tốc độ gốc; các lỗi được sửa và kiểm lại.

Nếu model video không dùng được, tiếp tục với `code` cho mọi cảnh và giao phim hoàn chỉnh sau khi kiểm tra. Nếu không thể tạo giọng đọc thật, dừng trước khi gọi bản giao là hoàn thành và nêu đúng phụ thuộc còn thiếu.
