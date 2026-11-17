# Bản thử A7 cho video đạo hàm

Project này dùng lại kịch bản, lời đọc, phụ đề và hiệu ứng âm thanh của `videos/dao_ham_loi_sai`, rồi dựng lại 20 cảnh bằng `style: a7` trong pipeline code. Nhân vật và lớp học được vẽ bằng `scripts/a7_style.py`.

Rig bản 3 tham khảo `files (1).zip` ở root repo: chân đứng bám điểm sàn khi hông/thân chuyển động, tay dùng IK chạm mục tiêu, tay vươn về bên trái/phải tương ứng vị trí bảng. Mỗi tay đi qua điểm xoay riêng ở vai, rồi tới khuỷu và bàn tay; vai xoay theo độ nghiêng thân. Các dáng `shrug`, `explain`, `wave` gập khuỷu rõ hơn; hai tay `explain` chuyển lệch nhịp, `recoil` đưa tay gần mặt, `celebrate` dùng một tay chống hông và một tay giơ lên, `crouch` chống eo và mở tay về phía đồ thị. Tay không vươn dùng IK đặt bàn tay ở eo trên, khuỷu hướng ra ngoài. Nội suy giữa các beat giữ gốc tay bám vào vai để không hở khớp. Các hành động thêm gồm `shrug`, `recoil`, `trace`, `present`, `celebrate`, `crouch`, `lean`. Đồng hồ treo tường và quả lắc chuyển động, viên phấn rung nhẹ khi đổi beat; thẻ nội dung trượt vào và dấu kiểm được vẽ dần. Những chuyển động này được vẽ bằng code, không phát sinh clip model.

Bộ tham chiếu trực quan là `skills/directing-stickman-videos/assets/a7/`. Nhân vật giữ các dấu hiệu chính: mặt trắng tròn, hai lọn tóc cong, mắt oval, thân và tứ chi là nét mực mảnh, găng tay trắng, bàn chân ngắn. Không lấy nguyên khung bếp/sân/áp mái làm nền video đạo hàm.

Đây là phép thử phong cách A7 bằng code. Nó **không** dùng Flow/Veo/Gemini tạo clip và không được ghi là đã qua quy trình chấp nhận A7 cho video do model sinh. Khi cần clip model đúng A7, dùng hai block cố định trong `skills/directing-stickman-videos/assets/a7/approved-prompt-lock.json`, xem hợp đồng prompt và điều kiện nghiệm thu trong `skills/directing-stickman-videos/references/`, đồng thời lưu đầu vào ảnh tham chiếu và job ID thực tế.

Chạy:

```powershell
python scripts/longform_stickman.py validate videos/dao_ham_loi_sai_a7/production.json
python scripts/longform_stickman.py render videos/dao_ham_loi_sai_a7/production.json --preview-seconds 20
python scripts/longform_stickman.py render videos/dao_ham_loi_sai_a7/production.json
```
