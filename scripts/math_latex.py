#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Render Công Thức Toán Học Phong Cách Bút Sáp Màu & Bảng Phấn (Crayon / Chalkboard Math)
Dành cho Stickman Video Director (Phương án 2)
Tạo công thức có chất cảm vẽ tay, hòa hợp 100% với phong cách hoạt hình người que B1.
"""

import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import matplotlib.pyplot as plt


def apply_crayon_texture(img: Image.Image, roughness: float = 0.15) -> Image.Image:
    """Tạo chất cảm sáp màu/phấn (crayon texture) nhám nhẹ trên viền nét vẽ."""
    arr = np.array(img).copy()
    if arr.shape[2] != 4:
        return img
    
    alpha = arr[:, :, 3]
    mask = alpha > 15
    if not np.any(mask):
        return img

    # Tạo lớp nhiễu hạt sáp phấn
    h, w = alpha.shape
    noise = np.random.normal(1.0 - roughness * 0.5, roughness, (h, w))
    noise = np.clip(noise, 0.45, 1.05)

    # Điều biến kênh Alpha để tạo viền sáp thô tự nhiên
    new_alpha = (alpha.astype(float) * noise).astype(np.uint8)
    arr[:, :, 3] = np.where(mask, new_alpha, alpha)

    # Thêm độ rung nhẹ cho các hạt màu (grain pigment)
    for c in range(3):
        color_channel = arr[:, :, c].astype(float)
        color_noise = np.random.normal(1.0, 0.04, (h, w))
        arr[:, :, c] = np.clip(color_channel * color_noise, 0, 255).astype(np.uint8)

    return Image.fromarray(arr)


def render_crayon_formula(
    formula: str,
    output_path: Path,
    fontsize: int = 34,
    color: str = "#C92A2A",  # Đỏ sáp
    style: str = "crayon",    # "crayon" hoặc "chalkboard" hoặc "note"
    dpi: int = 300
) -> Path:
    """Render công thức LaTeX theo phong cách Bút sáp màu (Crayon) hoặc Bảng phấn (Chalkboard)."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sử dụng bộ font stixsans tạo cảm giác nét vẽ tay, tự nhiên hơn font in sách giáo khoa
    plt.rcParams["mathtext.fontset"] = "stixsans"
    plt.rcParams["text.usetex"] = False

    math_text = formula.strip()
    if not math_text.startswith("$"):
        math_text = f"${math_text}$"

    if style == "chalkboard":
        # === PHONG CÁCH BẢNG PHẤN (CHALKBOARD) ===
        fig = plt.figure(figsize=(7.5, 2.2), dpi=dpi)
        fig.patch.set_facecolor("#1D2521")  # Màu xanh đen bảng lớp
        ax = fig.add_axes([0.06, 0.06, 0.88, 0.88])
        ax.axis("off")
        
        # Chữ phấn trắng ngà hoặc vàng phấn
        chalk_color = "#FFF4E6" if color == "#C92A2A" else color
        ax.text(0.5, 0.5, math_text, fontsize=fontsize, ha="center", va="center", color=chalk_color, weight="bold")
        
        tmp_path = output_path.with_suffix(".tmp.png")
        plt.savefig(str(tmp_path), facecolor="#1D2521", bbox_inches="tight", pad_inches=0.18, dpi=dpi)
        plt.close(fig)

        # Bo góc và tạo viền gỗ vẽ tay
        img = Image.open(tmp_path).convert("RGBA")
        w, h = img.size
        mask = Image.new("L", (w, h), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([0, 0, w, h], radius=int(min(w, h) * 0.12), fill=255)
        img.putalpha(mask)

        # Viền bảng gỗ
        draw = ImageDraw.Draw(img)
        border_w = max(6, int(min(w, h) * 0.035))
        draw.rounded_rectangle(
            [border_w // 2, border_w // 2, w - border_w // 2 - 1, h - border_w // 2 - 1],
            radius=int(min(w, h) * 0.1),
            outline="#8D6E63",
            width=border_w
        )
        
        # Thêm chất cảm phấn mờ trên bảng
        img = apply_crayon_texture(img, roughness=0.08)
        img.save(str(output_path))
        if tmp_path.exists():
            tmp_path.unlink()

    elif style == "note":
        # === PHONG CÁCH TỜ GIẤY NOTE CRAYON (STICKY NOTE) ===
        fig = plt.figure(figsize=(7, 2.0), dpi=dpi)
        fig.patch.set_facecolor("#FFF9DB")  # Vàng nhạt giấy note
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
        ax.axis("off")

        ax.text(0.5, 0.5, math_text, fontsize=fontsize, ha="center", va="center", color=color, weight="bold")
        
        tmp_path = output_path.with_suffix(".tmp.png")
        plt.savefig(str(tmp_path), facecolor="#FFF9DB", bbox_inches="tight", pad_inches=0.15, dpi=dpi)
        plt.close(fig)

        img = Image.open(tmp_path).convert("RGBA")
        w, h = img.size
        draw = ImageDraw.Draw(img)
        # Viền vẽ tay nguệch ngoạc màu bút chì
        draw.rectangle([2, 2, w - 3, h - 3], outline="#D8D2B4", width=3)
        img = apply_crayon_texture(img, roughness=0.12)
        img.save(str(output_path))
        if tmp_path.exists():
            tmp_path.unlink()

    else:
        # === PHONG CÁCH BÚT SÁP MÀU VẼ TAY TRONG SUỐT (CRAYON TRANSPARENT) ===
        fig = plt.figure(figsize=(7, 2), dpi=dpi)
        fig.patch.set_alpha(0.0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.patch.set_alpha(0.0)

        ax.text(0.5, 0.5, math_text, fontsize=fontsize, ha="center", va="center", color=color, weight="bold")

        tmp_path = output_path.with_suffix(".tmp.png")
        plt.savefig(str(tmp_path), transparent=True, bbox_inches="tight", pad_inches=0.08, dpi=dpi)
        plt.close(fig)

        img = Image.open(tmp_path).convert("RGBA")
        img = apply_crayon_texture(img, roughness=0.18)
        img.save(str(output_path))
        if tmp_path.exists():
            tmp_path.unlink()

    print(f"[✓] Đã tạo công thức [{style}]: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Render công thức phong cách Bút sáp màu & Bảng phấn")
    parser.add_argument("formula", type=str, help="Chuỗi LaTeX toán học")
    parser.add_argument("-o", "--output", type=Path, default=Path("crayon_formula.png"), help="File PNG xuất ra")
    parser.add_argument("--style", type=str, default="crayon", choices=["crayon", "chalkboard", "note"], help="Kiểu hiển thị (crayon, chalkboard, note)")
    parser.add_argument("--size", type=int, default=34, help="Kích thước font")
    parser.add_argument("--color", type=str, default="#C92A2A", help="Mã màu HEX")

    args = parser.parse_args()
    render_crayon_formula(args.formula, args.output, fontsize=args.size, color=args.color, style=args.style)


if __name__ == "__main__":
    main()
