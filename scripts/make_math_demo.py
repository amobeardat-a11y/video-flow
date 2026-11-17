#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Hoạt Hình Toán Học Giàu Animation (High-Dynamic Explainer)
Áp dụng đầy đủ kỹ thuật animation của Stickman Video Director:
1. Nhịp cắt cảnh nhanh (3-5s mỗi cảnh thay vì 11s nhàm chán).
2. Hiệu ứng xuất hiện động: Slide-in, Pop-in, Đổi tư thế người que liên tục.
3. Hoạt ảnh vẽ nét vector: Đường cong Parabol vẽ dần, Tiếp tuyến nghiêng động, Mũi tên vẽ dài ra, Nét gạch chéo đỏ gạch bỏ sai lầm.
4. Công thức toán phong cách Bút sáp màu & Bảng phấn (Phương án 2).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
from scripts.math_latex import render_crayon_formula

SKILLS_DIR = ROOT_DIR / "skills" / "directing-stickman-videos"
NOTO_FONT = SKILLS_DIR / "assets" / "fonts" / "NotoSans.ttf"

PROJECT_DIR = ROOT_DIR / "math_derivative_demo"
PROJECT_DIR.mkdir(parents=True, exist_ok=True)
FORMULAS_DIR = PROJECT_DIR / "formulas"
FORMULAS_DIR.mkdir(parents=True, exist_ok=True)


def build_dynamic_shots(total_duration: float):
    """
    Xây dựng 12 phân cảnh nhịp độ nhanh (2.5s - 5s mỗi cảnh)
    với animation liên tục, nét vẽ động và chuyển đổi tư thế.
    """
    shots = []
    
    # 12 mốc thời gian phân cảnh tương ứng với dòng kịch bản
    # Tổng thời lượng ~ 53.9s
    cuts = [
        0.0,    # Shot 1
        4.0,    # Shot 2
        8.2,    # Shot 3
        12.5,   # Shot 4
        16.8,   # Shot 5
        21.2,   # Shot 6
        25.8,   # Shot 7
        30.2,   # Shot 8
        35.0,   # Shot 9
        40.5,   # Shot 10
        46.0,   # Shot 11
        total_duration  # Shot 12
    ]

    # --- SHOT 1 (0.0 -> 4.0s): Hook - Bạn có đang học đạo hàm như cái máy? ---
    s1_dur = cuts[1] - cuts[0]
    shots.append({
        "start": cuts[0],
        "end": cuts[1],
        "layers": [
            # Người que pose 0 suy nghĩ, trượt từ phải vào
            {
                "id": "s1_actor",
                "type": "pose",
                "pose": 0,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que bước vào và suy nghĩ"},
                "keys": [
                    {"t": 0.0, "x": 800, "y": 45, "angle": 0.06},
                    {"t": 1.2, "x": 680, "y": 35, "angle": -0.04},
                    {"t": 2.5, "x": 670, "y": 30, "angle": 0.03},
                    {"t": s1_dur, "x": 680, "y": 35, "angle": 0.0}
                ]
            },
            # Tiêu đề rơi xuống
            {
                "type": "text",
                "text": "BẠN CÓ ĐANG HỌC ĐẠO HÀM...",
                "x": 90, "y": 110, "size": 46, "bold": True, "color": "#1A1A1A"
            },
            # Dòng nhấn mạnh màu đỏ trượt lên
            {
                "type": "text",
                "text": "...NHƯ MỘT CÁI MÁY?",
                "x": 90, "y": 180, "size": 52, "bold": True, "color": "#EC4338",
                "from": 1.0
            },
            # Dấu chấm hỏi to lắc lư
            {
                "id": "s1_question",
                "type": "text",
                "text": "???",
                "x": 450, "y": 280, "size": 90, "bold": True, "color": "#EC4338",
                "from": 1.2
            },
            # Gạch chân vẽ dần dưới chữ
            {
                "id": "s1_line",
                "type": "line",
                "points": [[90, 250], [580, 250]],
                "color": "#EC4338",
                "lineWidth": 5,
                "from": 1.5,
                "motion": {"role": "information", "reason": "Nét gạch chân cảnh báo vẽ dần"},
                "keys": [
                    {"t": 0.0, "progress": 0.0},
                    {"t": 1.2, "progress": 1.0},
                    {"t": s1_dur - 1.5, "progress": 1.0}
                ]
            }
        ]
    })

    # --- SHOT 2 (4.0 -> 8.2s): Sai lầm học vẹt bảng công thức ---
    s2_dur = cuts[2] - cuts[1]
    shots.append({
        "start": cuts[1],
        "end": cuts[2],
        "layers": [
            # Người que pose 2 ôm đầu bối rối!
            {
                "id": "s2_actor",
                "type": "pose",
                "pose": 2,
                "x": 700,
                "y": 30,
                "w": 450,
                "motion": {"role": "actor", "reason": "Người que ôm đầu bối rối trước đống công thức"},
                "keys": [
                    {"t": 0.0, "y": 45, "angle": -0.05},
                    {"t": 1.2, "y": 25, "angle": 0.05},
                    {"t": 2.4, "y": 40, "angle": -0.03},
                    {"t": s2_dur, "y": 30, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "SAI LẦM PHỔ BIẾN:", "x": 90, "y": 90, "size": 42, "bold": True, "color": "#1A1A1A"},
            {"type": "text", "text": "HỌC VẸT BẢNG CÔNG THỨC!", "x": 90, "y": 150, "size": 46, "bold": True, "color": "#EC4338"},
            # Tờ giấy công thức chao đảo
            {
                "id": "s2_paper",
                "type": "image",
                "path": "@b1/script-page-crayon.png",
                "x": 90,
                "y": 240,
                "w": 180,
                "motion": {"role": "prop", "reason": "Tờ giấy công thức rơi xuống"},
                "keys": [
                    {"t": 0.0, "y": 180, "angle": -0.1},
                    {"t": 0.8, "y": 240, "angle": 0.05},
                    {"t": 2.0, "y": 235, "angle": -0.03},
                    {"t": s2_dur, "y": 240, "angle": 0.0}
                ]
            },
            # Bảng phấn đen mini chứa công thức
            {
                "id": "s2_formula",
                "type": "image",
                "path": "formulas/shot1.png",
                "x": 280,
                "y": 260,
                "w": 380,
                "from": 0.6,
                "motion": {"role": "information", "reason": "Bảng phấn công thức bay vào"},
                "keys": [
                    {"t": 0.0, "x": 350, "w": 320},
                    {"t": 1.0, "x": 280, "w": 380},
                    {"t": s2_dur - 0.6, "x": 280, "w": 380}
                ]
            },
            # Dấu gạch chéo ĐỎ đè lên công thức thể hiện sự sai lầm!
            {
                "id": "s2_cross1",
                "type": "line",
                "points": [[280, 270], [640, 420]],
                "color": "#D93025",
                "lineWidth": 6,
                "from": 2.0,
                "motion": {"role": "information", "reason": "Nét gạch chéo đỏ thứ nhất"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.5, "progress": 1.0}, {"t": s2_dur - 2.0, "progress": 1.0}]
            },
            {
                "id": "s2_cross2",
                "type": "line",
                "points": [[640, 270], [280, 420]],
                "color": "#D93025",
                "lineWidth": 6,
                "from": 2.4,
                "motion": {"role": "information", "reason": "Nét gạch chéo đỏ thứ hai"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.5, "progress": 1.0}, {"t": s2_dur - 2.4, "progress": 1.0}]
            }
        ]
    })

    # --- SHOT 3 (8.2 -> 12.5s): Câu hỏi lật ngược - Đạo hàm là gì? ---
    s3_dur = cuts[3] - cuts[2]
    shots.append({
        "start": cuts[2],
        "end": cuts[3],
        "layers": [
            # Người que pose 0 gãi đầu thắc mắc
            {
                "id": "s3_actor",
                "type": "pose",
                "pose": 0,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que thắc mắc bản chất"},
                "keys": [
                    {"t": 0.0, "x": 680, "angle": 0.04},
                    {"t": 1.5, "x": 660, "angle": -0.04},
                    {"t": 2.8, "x": 680, "angle": 0.03},
                    {"t": s3_dur, "x": 680, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "HÃY TỰ HỎI BẢN THÂN:", "x": 90, "y": 100, "size": 42, "color": "#555555"},
            {"type": "text", "text": "ĐẠO HÀM THỰC SỰ LÀ GÌ?", "x": 90, "y": 160, "size": 52, "bold": True, "color": "#1A73E8"},
            # Mũi tên uốn lượn hướng về tương lai
            {
                "id": "s3_arrow",
                "type": "arrow",
                "x": 100, "y": 350, "w": 380,
                "color": "#1A73E8",
                "motion": {"role": "information", "reason": "Mũi tên dẫn hướng suy nghĩ"},
                "keys": [
                    {"t": 0.0, "progress": 0.0},
                    {"t": 1.2, "progress": 1.0},
                    {"t": s3_dur, "progress": 1.0}
                ]
            },
            {"type": "text", "text": "KHÔNG PHẢI PHÉP THUẬT!", "x": 100, "y": 270, "size": 40, "bold": True, "color": "#188038", "from": 1.2}
        ]
    })

    # --- SHOT 4 (12.5 -> 16.8s): Khai sáng - Bóng đèn ý tưởng bùng sáng! ---
    s4_dur = cuts[4] - cuts[3]
    shots.append({
        "start": cuts[3],
        "end": cuts[4],
        "layers": [
            # Người que pose 1 chỉ tay đắc ý
            {
                "id": "s4_actor",
                "type": "pose",
                "pose": 1,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que phát hiện ra chân lý"},
                "keys": [
                    {"t": 0.0, "y": 50, "angle": -0.05},
                    {"t": 1.0, "y": 25, "angle": 0.05},
                    {"t": 2.2, "y": 40, "angle": -0.03},
                    {"t": s4_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "BẢN CHẤT CỰC KỲ ĐƠN GIẢN:", "x": 90, "y": 90, "size": 40, "color": "#555555"},
            {"type": "text", "text": "TỐC ĐỘ BIẾN ĐỔI TỨC THỜI!", "x": 90, "y": 150, "size": 48, "bold": True, "color": "#188038"},
            # Bóng đèn nảy to lên
            {
                "id": "s4_bulb",
                "type": "image",
                "path": "@b1/idea-bulb-crayon.png",
                "x": 100,
                "y": 240,
                "w": 180,
                "motion": {"role": "prop", "reason": "Bóng đèn ý tưởng bừng sáng nở rộng"},
                "keys": [
                    {"t": 0.0, "w": 100, "angle": -0.1},
                    {"t": 0.8, "w": 200, "angle": 0.06},
                    {"t": 1.6, "w": 180, "angle": -0.02},
                    {"t": s4_dur, "w": 180, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "MỌI THỨ ĐANG ĐỔI NHANH CỠ NÀO?", "x": 100, "y": 450, "size": 36, "bold": True, "color": "#1A1A1A", "from": 1.0}
        ]
    })

    # --- SHOT 5 (16.8 -> 21.2s): Công thức định nghĩa phân số vi phân ---
    s5_dur = cuts[5] - cuts[4]
    shots.append({
        "start": cuts[4],
        "end": cuts[5],
        "layers": [
            {
                "id": "s5_actor",
                "type": "pose",
                "pose": 0,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que tập trung vào công thức phân số"},
                "keys": [
                    {"t": 0.0, "x": 700, "angle": 0.04},
                    {"t": 1.5, "x": 670, "angle": -0.04},
                    {"t": s5_dur, "x": 680, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "KHOẢNH KHẮC VÔ CÙNG NHỎ:", "x": 90, "y": 90, "size": 40, "color": "#555555"},
            {"type": "text", "text": "KHI Δx TIẾN TỚI 0", "x": 90, "y": 150, "size": 48, "bold": True, "color": "#1A73E8"},
            # Công thức phân số xanh sáp bay lên
            {
                "id": "s5_formula",
                "type": "image",
                "path": "formulas/shot2.png",
                "x": 90,
                "y": 240,
                "w": 420,
                "motion": {"role": "information", "reason": "Công thức giới hạn trượt lên"},
                "keys": [
                    {"t": 0.0, "y": 300, "w": 360},
                    {"t": 1.0, "y": 240, "w": 420},
                    {"t": s5_dur, "y": 240, "w": 420}
                ]
            },
            # Mũi tên chỉ vào delta x
            {
                "id": "s5_arrow",
                "type": "arrow",
                "x": 120, "y": 420, "w": 280,
                "color": "#188038",
                "from": 1.2,
                "motion": {"role": "information", "reason": "Mũi tên chỉ vào mẫu số tiến tới 0"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.8, "progress": 1.0}, {"t": s5_dur - 1.2, "progress": 1.0}]
            }
        ]
    })

    # --- SHOT 6 (21.2 -> 25.8s): Ví dụ thực tế - Chiếc xe đang chuyển động ---
    s6_dur = cuts[6] - cuts[5]
    shots.append({
        "start": cuts[5],
        "end": cuts[6],
        "layers": [
            {
                "id": "s6_actor",
                "type": "pose",
                "pose": 1,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que liên tưởng tới lái xe"},
                "keys": [
                    {"t": 0.0, "y": 40, "angle": -0.04},
                    {"t": 1.5, "y": 25, "angle": 0.04},
                    {"t": s6_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "HÃY TƯỞNG TƯỢNG:", "x": 90, "y": 90, "size": 42, "color": "#555555"},
            {"type": "text", "text": "BẠN ĐANG LÁI XE TRÊN ĐƯỜNG", "x": 90, "y": 140, "size": 46, "bold": True, "color": "#1A1A1A"},
            # Phân cảnh minh họa xe chạy do Gemini AI tạo ra (bo góc viền đen)
            {
                "id": "s6_gemini_car",
                "type": "image",
                "path": "gemini_car_card.png",
                "x": 80,
                "y": 205,
                "w": 530,
                "motion": {"role": "prop", "reason": "Phân cảnh xe chạy tạo bởi Gemini AI phóng to"},
                "keys": [
                    {"t": 0.0, "x": 60, "w": 480, "angle": -0.03},
                    {"t": 1.5, "x": 90, "w": 540, "angle": 0.02},
                    {"t": round(s6_dur - 0.05, 2), "x": 80, "w": 530, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "[AI] XE CHAY TRÊN DUONG (GEMINI)", "x": 90, "y": 510, "size": 32, "bold": True, "color": "#1A73E8", "from": 0.6}
        ]
    })

    # --- SHOT 7 (25.8 -> 30.2s): Đồng hồ công-tơ-mét chỉ đúng 60 km/h ---
    s7_dur = cuts[7] - cuts[6]
    shots.append({
        "start": cuts[6],
        "end": cuts[7],
        "layers": [
            {
                "id": "s7_actor",
                "type": "pose",
                "pose": 1,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que chỉ vào đồng hồ xe"},
                "keys": [
                    {"t": 0.0, "y": 45, "angle": -0.05},
                    {"t": 1.2, "y": 25, "angle": 0.05},
                    {"t": s7_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "TẠI GIÂY THỨ 5:", "x": 90, "y": 90, "size": 40, "color": "#555555"},
            {"type": "text", "text": "KIM ĐỒNG HỒ CHỈ ĐÚNG 60 KM/H", "x": 90, "y": 140, "size": 44, "bold": True, "color": "#1A1A1A"},
            # Giấy note công thức vận tốc tức thời
            {
                "id": "s7_formula",
                "type": "image",
                "path": "formulas/shot3.png",
                "x": 90,
                "y": 220,
                "w": 480,
                "motion": {"role": "information", "reason": "Giấy note công thức dán vào màn hình"},
                "keys": [
                    {"t": 0.0, "x": 50, "angle": -0.06},
                    {"t": 0.8, "x": 90, "angle": 0.03},
                    {"t": s7_dur, "x": 90, "angle": 0.0}
                ]
            },
            # Nét gạch chân đỏ quét qua
            {
                "id": "s7_underline",
                "type": "line",
                "points": [[90, 360], [540, 360]],
                "color": "#D93025",
                "lineWidth": 6,
                "from": 1.0,
                "motion": {"role": "information", "reason": "Nét gạch chân quét qua"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.8, "progress": 1.0}, {"t": s7_dur - 1.0, "progress": 1.0}]
            },
            {"type": "text", "text": "=> VẬN TỐC TỨC THỜI LÀ ĐẠO HÀM!", "x": 90, "y": 390, "size": 38, "bold": True, "color": "#188038", "from": 1.4}
        ]
    })

    # --- SHOT 8 (30.2 -> 35.0s): Góc nhìn hình học - Bắt đầu vẽ đồ thị ---
    s8_dur = cuts[8] - cuts[7]
    shots.append({
        "start": cuts[7],
        "end": cuts[8],
        "layers": [
            {
                "id": "s8_actor",
                "type": "pose",
                "pose": 0,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que chuẩn bị vẽ đồ thị"},
                "keys": [
                    {"t": 0.0, "y": 35, "angle": 0.04},
                    {"t": 1.5, "y": 25, "angle": -0.04},
                    {"t": s8_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "GÓC NHÌN HÌNH HỌC:", "x": 90, "y": 90, "size": 44, "bold": True, "color": "#1A1A1A"},
            {"type": "text", "text": "PHÓNG TO MỘT ĐƯỜNG CONG...", "x": 90, "y": 150, "size": 40, "color": "#1A73E8"},
            # Trục tọa độ vẽ từ gốc ra
            {
                "id": "s8_axis_x",
                "type": "line",
                "points": [[100, 480], [500, 480]],
                "color": "#888888",
                "lineWidth": 3,
                "motion": {"role": "information", "reason": "Trục hoành Ox vẽ ra"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.8, "progress": 1.0}, {"t": s8_dur, "progress": 1.0}]
            },
            {
                "id": "s8_axis_y",
                "type": "line",
                "points": [[100, 480], [100, 240]],
                "color": "#888888",
                "lineWidth": 3,
                "motion": {"role": "information", "reason": "Trục tung Oy vẽ lên"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.8, "progress": 1.0}, {"t": s8_dur, "progress": 1.0}]
            },
            {"type": "text", "text": "x", "x": 510, "y": 465, "size": 32, "bold": True, "color": "#888888", "from": 0.8},
            {"type": "text", "text": "y", "x": 90, "y": 200, "size": 32, "bold": True, "color": "#888888", "from": 0.8}
        ]
    })

    # --- SHOT 9 (35.0 -> 40.5s): Đồ thị Parabol & Đường tiếp tuyến vẽ động ---
    s9_dur = cuts[9] - cuts[8]
    shots.append({
        "start": cuts[8],
        "end": cuts[9],
        "layers": [
            {
                "id": "s9_actor",
                "type": "pose",
                "pose": 1,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que quan sát đường cong biến thành tiếp tuyến"},
                "keys": [
                    {"t": 0.0, "y": 40, "angle": -0.04},
                    {"t": 1.5, "y": 25, "angle": 0.04},
                    {"t": s9_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "PHÓNG TO VÔ HẠN LẦN:", "x": 90, "y": 80, "size": 40, "color": "#555555"},
            {"type": "text", "text": "ĐƯỜNG CONG BIẾN THÀNH ĐƯỜNG THẲNG!", "x": 90, "y": 130, "size": 38, "bold": True, "color": "#1A73E8"},
            # Trục tọa độ cố định
            {"type": "line", "points": [[100, 480], [500, 480]], "color": "#888888", "lineWidth": 3},
            {"type": "line", "points": [[100, 480], [100, 230]], "color": "#888888", "lineWidth": 3},
            # Đường cong Parabol vẽ uốn lượn
            {
                "id": "s9_parabol",
                "type": "line",
                "points": [[100, 470], [180, 440], [260, 380], [340, 300], [420, 200]],
                "color": "#1A73E8",
                "lineWidth": 5,
                "motion": {"role": "information", "reason": "Đường cong Parabol vẽ dần"},
                "keys": [
                    {"t": 0.0, "progress": 0.0},
                    {"t": 1.5, "progress": 1.0},
                    {"t": s9_dur, "progress": 1.0}
                ]
            },
            # Đường tiếp tuyến màu đỏ vẽ cắt qua và rung nhẹ góc nghiêng
            {
                "id": "s9_tangent",
                "type": "line",
                "points": [[140, 490], [390, 220]],
                "color": "#EC4338",
                "lineWidth": 5,
                "from": 1.8,
                "motion": {"role": "information", "reason": "Đường tiếp tuyến xuất hiện và lắc nhẹ góc nghiêng"},
                "keys": [
                    {"t": 0.0, "progress": 0.0, "angle": -0.06},
                    {"t": 1.0, "progress": 1.0, "angle": 0.04},
                    {"t": s9_dur - 1.8, "progress": 1.0, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "TIẾP TUYẾN ĐỎ", "x": 400, "y": 210, "size": 32, "bold": True, "color": "#EC4338", "from": 2.2}
        ]
    })

    # --- SHOT 10 (40.5 -> 46.0s): Bảng phấn hệ số góc tiếp tuyến = Đạo hàm ---
    s10_dur = cuts[10] - cuts[9]
    shots.append({
        "start": cuts[9],
        "end": cuts[10],
        "layers": [
            {
                "id": "s10_actor",
                "type": "pose",
                "pose": 1,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que tự tin khẳng định độ dốc"},
                "keys": [
                    {"t": 0.0, "y": 35, "angle": 0.05},
                    {"t": 1.5, "y": 20, "angle": -0.05},
                    {"t": s10_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "ĐỘ DỐC TIẾP TUYẾN CHÍNH LÀ ĐẠO HÀM!", "x": 90, "y": 90, "size": 42, "bold": True, "color": "#188038"},
            # Bảng phấn xanh dương hệ số góc k = tan(alpha)
            {
                "id": "s10_board",
                "type": "image",
                "path": "formulas/shot4.png",
                "x": 90,
                "y": 180,
                "w": 460,
                "motion": {"role": "information", "reason": "Bảng phấn hệ số góc phóng to vào giữa"},
                "keys": [
                    {"t": 0.0, "w": 380, "angle": -0.05},
                    {"t": 1.0, "w": 460, "angle": 0.02},
                    {"t": s10_dur, "w": 460, "angle": 0.0}
                ]
            },
            # Mũi tên chỉ vào ý nghĩa độ dốc
            {
                "id": "s10_arrow",
                "type": "arrow",
                "x": 100, "y": 370, "w": 380,
                "color": "#1A73E8",
                "from": 1.0,
                "motion": {"role": "information", "reason": "Mũi tên xác nhận định lý"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.8, "progress": 1.0}, {"t": s10_dur - 1.0, "progress": 1.0}]
            },
            {"type": "text", "text": "DỐC CÀNG NHIỀU -> ĐẠO HÀM CÀNG LỚN!", "x": 90, "y": 420, "size": 36, "bold": True, "color": "#EC4338", "from": 1.4}
        ]
    })

    # --- SHOT 11 (46.0 -> 50.0s): Phương pháp học chuẩn - 3 bước vàng ---
    s11_dur = 4.0
    shots.append({
        "start": cuts[10],
        "end": cuts[10] + s11_dur,
        "layers": [
            {
                "id": "s11_actor",
                "type": "pose",
                "pose": 0,
                "x": 680,
                "y": 35,
                "w": 440,
                "motion": {"role": "actor", "reason": "Người que hướng dẫn 3 bước học chuẩn"},
                "keys": [
                    {"t": 0.0, "y": 40, "angle": -0.04},
                    {"t": 1.5, "y": 25, "angle": 0.04},
                    {"t": s11_dur, "y": 35, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "CÁCH HỌC CHUẨN: 3 BƯỚC VÀNG", "x": 90, "y": 90, "size": 44, "bold": True, "color": "#1A1A1A"},
            {"type": "text", "text": "1. Hiểu tốc độ biến đổi tức thời", "x": 100, "y": 180, "size": 38, "color": "#1A1A1A"},
            {"type": "text", "text": "2. Nhìn qua độ dốc tiếp tuyến", "x": 100, "y": 250, "size": 38, "color": "#1A73E8", "from": 1.0},
            {"type": "text", "text": "3. Sau cùng mới áp dụng công thức!", "x": 100, "y": 320, "size": 38, "bold": True, "color": "#188038", "from": 2.0},
            # Nét gạch chân xanh lá chạy qua bước 3
            {
                "id": "s11_underline",
                "type": "line",
                "points": [[100, 375], [580, 375]],
                "color": "#188038",
                "lineWidth": 5,
                "from": 2.2,
                "motion": {"role": "information", "reason": "Gạch chân bước quan trọng nhất"},
                "keys": [{"t": 0.0, "progress": 0.0}, {"t": 0.8, "progress": 1.0}, {"t": s11_dur - 2.2, "progress": 1.0}]
            }
        ]
    })

    # --- SHOT 12 (50.0 -> total_duration): Đúc kết & Thành công ăn mừng ---
    s12_start = cuts[10] + s11_dur
    s12_dur = round(total_duration - s12_start, 2)
    shots.append({
        "start": s12_start,
        "end": round(total_duration, 2),
        "layers": [
            # Người que pose 1 giơ tay ăn mừng
            {
                "id": "s12_actor",
                "type": "pose",
                "pose": 1,
                "x": 680,
                "y": 30,
                "w": 450,
                "motion": {"role": "actor", "reason": "Người que ăn mừng thành quả học tập"},
                "keys": [
                    {"t": 0.0, "y": 45, "angle": -0.06},
                    {"t": 1.2, "y": 20, "angle": 0.06},
                    {"t": s12_dur, "y": 30, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "HIỂU BẢN CHẤT TRƯỚC,", "x": 90, "y": 100, "size": 48, "bold": True, "color": "#1A1A1A"},
            {"type": "text", "text": "CÔNG THỨC TỰ KHẮC DỄ NHỚ!", "x": 90, "y": 170, "size": 52, "bold": True, "color": "#188038"},
            # Biểu tượng open source xoay nhẹ
            {
                "id": "s12_icon",
                "type": "image",
                "path": "@b1/open-source-crayon.png",
                "x": 100,
                "y": 260,
                "w": 180,
                "motion": {"role": "prop", "reason": "Biểu tượng thành công nảy nở"},
                "keys": [
                    {"t": 0.0, "w": 130, "angle": -0.1},
                    {"t": 1.0, "w": 190, "angle": 0.08},
                    {"t": s12_dur, "w": 180, "angle": 0.0}
                ]
            },
            {"type": "text", "text": "CHÚC BẠN HỌC TỐT!", "x": 310, "y": 300, "size": 44, "bold": True, "color": "#EC4338"}
        ]
    })

    # Đảm bảo tuyệt đối mọi key.t đều hợp lệ và strictly increasing
    for s in shots:
        span = s["end"] - s["start"]
        max_t = span - 0.002
        for l in s["layers"]:
            if "keys" in l:
                prev_t = -1.0
                for k in l["keys"]:
                    if k["t"] > max_t:
                        k["t"] = round(max_t, 3)
                    if k["t"] <= prev_t:
                        k["t"] = round(min(max_t, prev_t + 0.05), 3)
                    prev_t = k["t"]

    return shots


def main():
    print("=== DỰNG VIDEO TOÁN HỌC SIÊU ĐỘNG (HIGH-ANIMATION EXPLAINER) ===")
    
    # 1. Tạo audio nếu chưa có
    wav_path = PROJECT_DIR / "narration.wav"
    cmd_probe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)]
    res = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
    duration = float(res.stdout.strip())
    print(f"[✓] File audio: {wav_path} (Thời lượng: {duration:.2f}s)")

    # 2. Sinh các công thức phong cách Bảng phấn & Bút sáp màu (Phương án 2)
    print("\n[*] Render công thức toán phong cách Bảng phấn & Bút sáp...")
    render_crayon_formula(r'y = x^n \ \ \Rightarrow \ \ y^\prime = n \cdot x^{n-1}', FORMULAS_DIR / 'shot1.png', fontsize=34, color='#FF8787', style='chalkboard')
    render_crayon_formula(r'\frac{dy}{dx} = \lim_{\Delta x \to 0} \frac{\Delta y}{\Delta x}', FORMULAS_DIR / 'shot2.png', fontsize=38, color='#2B8A3E', style='crayon')
    render_crayon_formula(r'v(t) = s^\prime(t) = \frac{ds}{dt} = 60\ \mathrm{km/h}', FORMULAS_DIR / 'shot3.png', fontsize=34, color='#C92A2A', style='note')
    render_crayon_formula(r'k = \tan(\alpha) = f^\prime(x_0) = \frac{dy}{dx}', FORMULAS_DIR / 'shot4.png', fontsize=34, color='#4DABF7', style='chalkboard')

    # 3. Phụ đề ngữ nghĩa
    captions = [
        {"start": 0.3, "end": 4.0, "text": "Bạn có đang học đạo hàm như một cái máy?"},
        {"start": 4.1, "end": 8.2, "text": "Sai lầm lớn nhất là cắm đầu học vẹt công thức."},
        {"start": 8.3, "end": 12.5, "text": "Thực chất đạo hàm không hề phức tạp như bạn nghĩ."},
        {"start": 12.6, "end": 16.8, "text": "Nó đo lường tốc độ biến đổi tức thời tại một thời điểm."},
        {"start": 16.9, "end": 21.2, "text": "Khi khoảng thời gian xét tiến dần về không."},
        {"start": 21.3, "end": 25.8, "text": "Ví dụ khi lái xe, quãng đường chia thời gian là vận tốc."},
        {"start": 25.9, "end": 30.2, "text": "Kim đồng hồ chỉ đúng 60 km/h tại giây thứ năm."},
        {"start": 30.3, "end": 35.0, "text": "Đó chính là đạo hàm của chuyển động theo thời gian."},
        {"start": 35.1, "end": 40.5, "text": "Về mặt hình học, phóng to đường cong vô hạn lần,"},
        {"start": 40.6, "end": 46.0, "text": "Độ dốc của đường tiếp tuyến đó chính là đạo hàm!"},
        {"start": 46.1, "end": 50.0, "text": "Muốn học chuẩn, hãy bắt đầu từ sự trực quan."},
        {"start": 50.1, "end": round(duration - 0.2, 2), "text": "Hiểu bản chất trước, công thức tự khắc dễ nhớ!"}
    ]

    # 4. Tạo 12 shots giàu animation
    shots = build_dynamic_shots(duration)
    print(f"[✓] Đã tạo {len(shots)} phân cảnh chuyển động nhanh (2.5s - 5s/cảnh).")

    rel_noto_font = os.path.relpath(NOTO_FONT, PROJECT_DIR).replace("\\", "/")

    project_config = {
        "version": 1,
        "style": "B1",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "font": rel_noto_font,
        "captionFont": rel_noto_font,
        "voice": {
            "path": "narration.wav",
            "lead": 0,
            "tail": 0,
            "contains_sfx": True
        },
        "captions": captions,
        "shots": shots,
        "sfx": [],
        "reference_review": {
            "author_id": "math_director",
            "capability": {
                "mode": "sample_target",
                "environment": "math_explainer",
                "limitations": []
            }
        }
    }

    project_json = PROJECT_DIR / "project.json"
    with open(project_json, "w", encoding="utf-8") as f:
        json.dump(project_config, f, ensure_ascii=False, indent=2)
    print(f"[✓] Đã lưu {project_json}")

    # 5. Render Video
    print("\n[*] Tiến hành Render Video Preview...")
    autopilot_mjs = SKILLS_DIR / "scripts" / "autopilot.mjs"
    cmd = ["node", str(autopilot_mjs), "preview", str(project_json), "--seconds", str(min(60, int(duration) + 1)), "--replace"]
    subprocess.run(cmd, check=True)

    print("\n🎉 HOÀN THÀNH VIDEO DEMO TOÁN HỌC SIÊU ĐỘNG!")
    print(f"👉 File video: {PROJECT_DIR / 'output' / 'preview.mp4'}")


if __name__ == "__main__":
    main()
