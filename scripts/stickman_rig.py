"""
stickman_rig.py - Skeletal Rigging & Procedural Animation Engine cho Stickman
Lấy cảm hứng từ SweeWarman/Stickman (rig xương 2D) & AutoChar (đồng bộ biểu cảm/hành động).

Tính năng:
- Hệ thống xương khớp (Skeletal Rig): Đầu, cổ, thân, vai, khuỷu tay, bàn tay, hông, đầu gối, bàn chân.
- Nghịch đảo động học (2-Bone Inverse Kinematics - IK): Bàn tay chạm chính xác vào điểm mục tiêu (bảng, công thức, lái xe).
- Thuận động học (Forward Kinematics - FK): Xoay khớp mượt mà theo góc.
- Chu trình hoạt hình mẫu (Animation Presets):
    1. 'walk': Bước đi tự nhiên (chân vung, tay đánh chéo, thân nhấp nhô).
    2. 'wave': Đứng vẫy tay chào vui vẻ.
    3. 'point': Giơ tay chỉ trực tiếp vào công thức toán/bảng phấn.
    4. 'think': Gãi đầu, nghiêng đầu, suy nghĩ băn khoăn.
    5. 'explain': Vung cả 2 tay diễn giải nhịp nhàng như người thuyết trình thực thụ.
    6. 'shrug', 'recoil': Phản ứng băn khoăn và giật mình khi phát hiện lỗi.
    7. 'trace', 'present', 'lean': Dò công thức, trình bày và nghiêng về bảng.
    8. 'celebrate', 'crouch': Chốt đáp án và cúi soi chi tiết.
- Rig bản 3 tham khảo files (1).zip: tay dùng IK, mỗi tay có điểm xoay vai riêng,
  khuỷu gập theo hành động; bàn chân đứng cố định khi thân chuyển trọng tâm,
  pose chuyển bằng easing.
- Xuất video MP4 (30 FPS) nền trong suốt hoặc ghép trực tiếp vào khung cảnh.
"""

import math
import copy
import os
import shutil
import subprocess
from PIL import Image, ImageDraw

def ik_solve(root, target, l1, l2, side=1):
    """2-Bone Inverse Kinematics solver."""
    dx = target[0] - root[0]
    dy = target[1] - root[1]
    d = math.hypot(dx, dy)
    # Giới hạn tầm với để không gãy khớp
    max_reach = l1 + l2 - 1.0
    min_reach = abs(l1 - l2) + 1.0
    d_clamped = max(min_reach, min(max_reach, d))
    
    if d != 0:
        ux, uy = dx / d, dy / d
    else:
        ux, uy = 1.0, 0.0

    q = (l1 * l1 - l2 * l2 + d_clamped * d_clamped) / (2.0 * d_clamped)
    h = math.sqrt(max(0.0, l1 * l1 - q * q))
    
    mid_x = root[0] + q * ux - h * uy * side
    mid_y = root[1] + q * uy + h * ux * side
    
    end_x = root[0] + ux * d_clamped
    end_y = root[1] + uy * d_clamped
    return [root, (mid_x, mid_y), (end_x, end_y)]

def fk_chain(root, angles_deg, lengths):
    """Forward Kinematics chain."""
    points = [root]
    cur_x, cur_y = root
    accum_angle = 0.0
    for ang, length in zip(angles_deg, lengths):
        accum_angle += ang
        rad = math.radians(accum_angle)
        cur_x += length * math.cos(rad)
        cur_y += length * math.sin(rad)
        points.append((cur_x, cur_y))
    return points


def _smooth_points(points, steps=12):
    """Catmull–Rom samples through every joint, retaining exact end points."""
    if len(points) < 3:
        return points
    output = []
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        for j in range(steps):
            t = j / steps
            t2, t3 = t * t, t * t * t
            output.append(tuple(.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2*p0[k] - 5*p1[k] + 4*p2[k] - p3[k]) * t2 + (-p0[k] + 3*p1[k] - 3*p2[k] + p3[k]) * t3) for k in (0, 1)))
    output.append(points[-1])
    return output


def _round_stroke(draw, points, fill, width):
    points = _smooth_points(points)
    draw.line(points, fill=fill, width=width, joint="curve")
    radius = width / 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)

class StickmanPose:
    def __init__(self, hip=(200, 350), scale=1.0):
        self.hip = hip
        self.scale = scale
        self.torso_len = 100 * scale
        self.neck_len = 25 * scale
        self.head_radius = 42 * scale
        self.arm_len = (60 * scale, 55 * scale)
        self.leg_len = (65 * scale, 60 * scale)
        
        # State
        self.torso_angle = -90.0  # hướng lên trên
        self.head_tilt = 0.0
        self.expression = "smile"  # 'smile', 'think', 'open', 'neutral'
        
        # Left/Right joints
        self.left_arm = None
        self.right_arm = None
        self.left_leg = None
        self.right_leg = None

    def compute_skeleton(self):
        rad = math.radians(self.torso_angle)
        torso_top = (
            self.hip[0] + self.torso_len * math.cos(rad),
            self.hip[1] + self.torso_len * math.sin(rad)
        )
        neck = (
            torso_top[0] + self.neck_len * math.cos(rad),
            torso_top[1] + self.neck_len * math.sin(rad)
        )
        head_center = (
            neck[0] + self.head_radius * math.cos(rad + math.radians(self.head_tilt)),
            neck[1] + self.head_radius * math.sin(rad + math.radians(self.head_tilt))
        )
        shoulder = torso_top
        return torso_top, neck, head_center, shoulder

    def shoulder_points(self):
        """Two small shoulder pivots follow the torso lean."""
        shoulder = self.compute_skeleton()[3]
        rad = math.radians(self.torso_angle)
        right = (-math.sin(rad), math.cos(rad))
        half_width = 8 * self.scale
        return (
            (shoulder[0] - right[0]*half_width, shoulder[1] - right[1]*half_width),
            (shoulder[0] + right[0]*half_width, shoulder[1] + right[1]*half_width),
        )

class StickmanAnimator:
    @staticmethod
    def evaluate_pose(action: str, t: float, base_hip=(300, 480), scale=1.2, target=(0, 0)):
        """Return a connected pose with planted feet and purposeful acting."""
        if action not in {"walk", "wave", "point", "think", "explain", "shrug", "recoil", "trace", "present", "celebrate", "crouch", "lean"}:
            raise ValueError(f"Unsupported stickman action: {action}")
        s = scale
        toward = 1 if target[0] >= base_hip[0] else -1
        pose = StickmanPose(hip=base_hip, scale=s)

        if action == "walk":
            phase = t * 1.2 * 2 * math.pi
            pose.hip = (
                base_hip[0] + math.sin(t * .72) * 21*s,
                base_hip[1] - (1 - math.cos(phase * 2)) * 2.2*s,
            )
            pose.torso_angle = -90 + math.sin(phase) * 2.4
            _, _, _, shoulder = pose.compute_skeleton()
            swing = math.sin(phase)
            pose.left_leg = fk_chain(pose.hip, [96 + swing*22, max(0, -swing*21)], pose.leg_len)
            pose.right_leg = fk_chain(pose.hip, [84 - swing*22, max(0, swing*21)], pose.leg_len)
            left_root, right_root = pose.shoulder_points()
            pose.left_arm = [shoulder] + fk_chain(left_root, [125 + swing*25, -30], pose.arm_len)
            pose.right_arm = [shoulder] + fk_chain(right_root, [55 + swing*25, 30], pose.arm_len)
            pose.head_tilt = -math.sin(phase) * 2
            return pose

        # All non-walk actions move the hip over two fixed foot targets. The
        # knees solve against those targets, so breathing and leaning do not
        # drag the feet across the classroom floor.
        side_shift = math.sin(t * 1.4) * 2.3*s
        rise = math.sin(t * 1.45) * 1.3*s
        if action == "celebrate":
            rise -= (1 - math.cos(t * 4.4)) * 1.8*s
        if action == "recoil":
            side_shift -= toward * (4.5 + 1.5*math.sin(t*2.0))*s
        if action == "crouch":
            rise += 28*s
        pose.hip = (base_hip[0] + side_shift, base_hip[1] + rise)
        lean = math.sin(t * 1.15) * 1.4
        if action in {"point", "trace", "present"}:
            lean += toward * 4.0
        elif action == "lean":
            lean += toward * 16.0
        elif action == "crouch":
            lean += toward * 9.0
        elif action == "recoil":
            lean -= toward * 10.0
        elif action == "shrug":
            lean -= toward * 2.0
        pose.torso_angle = -90 + lean
        stance = 30 if action in {"recoil", "celebrate", "crouch"} else 28
        foot_y = base_hip[1] + 118*s
        left_foot = (base_hip[0] - stance*s, foot_y)
        right_foot = (base_hip[0] + stance*s, foot_y)
        # Rubber-hose legs stay nearly straight between the moving hip and
        # fixed feet; a small outward bend reads as a knee without bowing.
        bend = 16*s if action == "crouch" else 3*s
        pose.left_leg = [
            pose.hip,
            ((pose.hip[0] + left_foot[0])*.5 - bend, (pose.hip[1] + left_foot[1])*.5),
            left_foot,
        ]
        pose.right_leg = [
            pose.hip,
            ((pose.hip[0] + right_foot[0])*.5 + bend, (pose.hip[1] + right_foot[1])*.5),
            right_foot,
        ]
        _, _, head, shoulder = pose.compute_skeleton()
        left_root, right_root = pose.shoulder_points()
        left_len, right_len = pose.arm_len
        def arm_fk(side, angles):
            root = left_root if side == "left" else right_root
            return [shoulder] + fk_chain(root, angles, pose.arm_len)
        def arm_ik(side, point, bend):
            root = left_root if side == "left" else right_root
            return [shoulder] + ik_solve(root, point, left_len, right_len, side=bend)
        def arm_support(side):
            sign = -1 if side == "left" else 1
            hand = (pose.hip[0] + sign*16*s, pose.hip[1] - 30*s)
            return arm_ik(side, hand, -sign)
        def aim_at(point):
            """Mirror the reaching arm toward the board-facing side."""
            if toward > 0:
                pose.left_arm = arm_support("left")
                pose.right_arm = arm_ik("right", point, -1)
            else:
                pose.left_arm = arm_ik("left", point, 1)
                pose.right_arm = arm_support("right")

        if action == "wave":
            pose.left_arm = arm_fk("left", [112, -20])
            pose.right_arm = arm_fk("right", [-45, -45 + 18*math.sin(t*3.1)])
            pose.head_tilt = math.sin(t*1.5) * 3
        elif action == "point":
            aim = (target[0] + math.sin(t*1.5)*2*s, target[1] + math.cos(t*1.5)*2*s)
            aim_at(aim)
            pose.head_tilt = toward * 4 + math.sin(t*1.2)*1.5
        elif action == "think":
            pose.left_arm = arm_support("left")
            touch = (head[0] + pose.head_radius + 7*s, head[1] - 8*s + math.sin(t*2.4)*2.5*s)
            pose.right_arm = arm_ik("right", touch, 1)
            pose.head_tilt = 8 + math.sin(t*1.2)*2
        elif action == "explain":
            # Two offset gestures read as conversation rather than a mirrored T pose.
            pose.left_arm = arm_fk("left", [135 + 10*math.sin(t*1.5), 70 + 8*math.sin(t*1.1)])
            pose.right_arm = arm_fk("right", [28 - 12*math.sin(t*1.4 + 1.0), -65 + 10*math.sin(t*1.2 + .5)])
            pose.head_tilt = math.sin(t*1.5)*2.5
        elif action == "shrug":
            lift = math.sin(t*1.7)*5
            pose.left_arm = arm_fk("left", [145 + lift, 95])
            pose.right_arm = arm_fk("right", [35 - lift, -95])
            pose.head_tilt = -toward * (6 + math.sin(t*1.2)*2)
        elif action == "recoil":
            pose.left_arm = arm_ik("left", (head[0] - pose.head_radius*1.35, head[1] + 28*s), -1)
            pose.right_arm = arm_ik("right", (head[0] + pose.head_radius*1.35, head[1] + 28*s), 1)
            pose.head_tilt = -toward * (9 + math.sin(t*2.0)*2)
        elif action == "trace":
            follow = (target[0] - toward*18*s + math.sin(t*1.35)*17*s,
                      target[1] - 10*s + math.cos(t*1.35)*12*s)
            aim_at(follow)
            pose.head_tilt = toward*(3 + math.sin(t*1.35)*2)
        elif action == "present":
            sweep = .5 - .5*math.cos(t*1.55)
            follow = (shoulder[0] + (target[0]-shoulder[0])*(.65+.35*sweep),
                      target[1] - (24-18*sweep)*s)
            aim_at(follow)
            pose.head_tilt = toward * (3 + 2*math.sin(t*1.55))
        elif action == "celebrate":
            pump = math.sin(t*3.2)*10
            pose.left_arm = arm_support("left")
            pose.right_arm = arm_fk("right", [-40, -50 - pump])
            pose.head_tilt = math.sin(t*2.4)*4
        elif action == "crouch":
            # A crouched question: one hand supports the waist, the other opens toward the graph.
            if toward > 0:
                pose.left_arm = arm_support("left")
                pose.right_arm = arm_ik("right", (shoulder[0]+70*s, shoulder[1]+27*s), 1)
            else:
                pose.left_arm = arm_ik("left", (shoulder[0]-70*s, shoulder[1]+27*s), -1)
                pose.right_arm = arm_support("right")
            pose.head_tilt = toward * (5 + math.sin(t*1.4)*2)
        elif action == "lean":
            aim_at(target)
            pose.head_tilt = -toward * (6 + math.sin(t*1.3)*2)
        return pose

    @staticmethod
    def draw_stickman(draw: ImageDraw.ImageDraw, pose: StickmanPose, color=(30, 28, 26), width=10):
        """Vẽ khung xương người que lên canvas với độ nét cao."""
        torso_top, neck, head_center, shoulder = pose.compute_skeleton()
        
        # 1. Vẽ chân (Legs)
        if pose.left_leg:
            draw.line(pose.left_leg, fill=color, width=width, joint="curve")
        if pose.right_leg:
            draw.line(pose.right_leg, fill=color, width=width, joint="curve")
            
        # 2. Vẽ thân (Torso)
        draw.line([pose.hip, torso_top], fill=color, width=int(width * 1.3), joint="curve")
        draw.line([torso_top, neck], fill=color, width=width, joint="curve")
        
        # 3. Vẽ tay (Arms)
        if pose.left_arm:
            draw.line(pose.left_arm, fill=color, width=width, joint="curve")
        if pose.right_arm:
            draw.line(pose.right_arm, fill=color, width=width, joint="curve")
            
        # 4. Vẽ đầu & mặt (Head & Facial Expression)
        r = pose.head_radius
        hx, hy = head_center
        # Vòng tròn đầu trắng viền đậm
        draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(251, 250, 248), outline=color, width=int(width * 0.9))
        
        # Mắt (Eyes)
        eye_r = max(3, int(6 * pose.scale))
        eye_dist = 18 * pose.scale
        eye_y = hy - 6 * pose.scale
        draw.ellipse([hx - eye_dist - eye_r, eye_y - eye_r, hx - eye_dist + eye_r, eye_y + eye_r], fill=color)
        draw.ellipse([hx + eye_dist - eye_r, eye_y - eye_r, hx + eye_dist + eye_r, eye_y + eye_r], fill=color)
        
        # Miệng biểu cảm (Mouth)
        mouth_y = hy + 14 * pose.scale
        mouth_w = 16 * pose.scale
        if pose.expression == "smile":
            draw.arc([hx - mouth_w, mouth_y - 8, hx + mouth_w, mouth_y + 12], start=10, end=170, fill=color, width=int(width * 0.6))
        elif pose.expression == "open":
            draw.ellipse([hx - 8, mouth_y - 4, hx + 8, mouth_y + 12], fill=color)
        elif pose.expression == "think":
            draw.line([(hx - 10, mouth_y + 4), (hx + 10, mouth_y)], fill=color, width=int(width * 0.6))
        elif pose.expression == "sad":
            draw.arc([hx - mouth_w, mouth_y - 1, hx + mouth_w, mouth_y + 17], start=190, end=350, fill=color, width=int(width * 0.6))
            draw.line([(hx - eye_dist - 8, eye_y - 14), (hx - eye_dist + 8, eye_y - 8)], fill=color, width=max(2, int(width * 0.45)))
            draw.line([(hx + eye_dist - 8, eye_y - 8), (hx + eye_dist + 8, eye_y - 14)], fill=color, width=max(2, int(width * 0.45)))
        elif pose.expression == "worried":
            draw.ellipse([hx - 6, mouth_y - 2, hx + 6, mouth_y + 9], outline=color, width=max(2, int(width * 0.5)))
            draw.line([(hx - eye_dist - 8, eye_y - 16), (hx - eye_dist + 8, eye_y - 9)], fill=color, width=max(2, int(width * 0.45)))
            draw.line([(hx + eye_dist - 8, eye_y - 9), (hx + eye_dist + 8, eye_y - 16)], fill=color, width=max(2, int(width * 0.45)))
        elif pose.expression == "angry":
            draw.line([(hx - mouth_w, mouth_y + 5), (hx + mouth_w, mouth_y + 1)], fill=color, width=max(2, int(width * 0.65)))
            draw.line([(hx - eye_dist - 9, eye_y - 15), (hx - eye_dist + 8, eye_y - 7)], fill=color, width=max(2, int(width * 0.55)))
            draw.line([(hx + eye_dist - 8, eye_y - 7), (hx + eye_dist + 9, eye_y - 15)], fill=color, width=max(2, int(width * 0.55)))
        elif pose.expression == "surprised":
            draw.ellipse([hx - 9, mouth_y - 6, hx + 9, mouth_y + 14], outline=color, width=max(2, int(width * 0.65)))
            draw.arc([hx - eye_dist - 11, eye_y - 20, hx - eye_dist + 11, eye_y - 6], start=180, end=360, fill=color, width=max(2, int(width * 0.45)))
            draw.arc([hx + eye_dist - 11, eye_y - 20, hx + eye_dist + 11, eye_y - 6], start=180, end=360, fill=color, width=max(2, int(width * 0.45)))
        else:
            draw.line([(hx - 10, mouth_y + 2), (hx + 10, mouth_y + 2)], fill=color, width=int(width * 0.6))


def _draw_soft_character(draw: ImageDraw.ImageDraw, pose: StickmanPose, ink, width: int, blink: bool):
    """Draw rounded ink contours and a readable face at the supplied scale."""
    torso_top, neck, head, shoulder = pose.compute_skeleton()
    hx, hy = head
    s = pose.scale
    limb_width = max(3, round(width * .92))
    torso_width = max(4, round(width * 1.14))

    for leg in (pose.left_leg, pose.right_leg):
        if leg:
            _round_stroke(draw, leg, ink, limb_width)
            fx, fy = leg[-1]
            draw.ellipse((fx - 9*s, fy - 2*s, fx + 9*s, fy + 4*s), fill=ink)
    _round_stroke(draw, [pose.hip, torso_top, neck], ink, torso_width)
    for arm in (pose.left_arm, pose.right_arm):
        if arm:
            _round_stroke(draw, arm, ink, limb_width)
            px, py = arm[-1]
            hand_r = 4.5 * s
            draw.ellipse((px-hand_r, py-hand_r, px+hand_r, py+hand_r), fill=ink)

    r = pose.head_radius
    draw.ellipse((hx-r, hy-r*.94, hx+r, hy+r*.98), fill=(255, 253, 249), outline=ink, width=max(4, round(width * .78)))
    # Small warm cheeks give the character a stable identity without clothing.
    cheek_y = hy + 10*s
    for sign in (-1, 1):
        cx = hx + sign * 27*s
        draw.ellipse((cx-6*s, cheek_y-3*s, cx+6*s, cheek_y+3*s), fill=(244, 220, 216))

    eye_y = hy - 5*s
    eye_x = 16*s
    eye_r = 3.9*s
    face_width = max(2, round(width * .33))
    for sign in (-1, 1):
        cx = hx + sign * eye_x
        if blink:
            _round_stroke(draw, [(cx-5*s, eye_y), (cx, eye_y+1*s), (cx+5*s, eye_y)], ink, face_width)
        else:
            draw.ellipse((cx-eye_r, eye_y-eye_r, cx+eye_r, eye_y+eye_r), fill=ink)
            draw.ellipse((cx-1.2*s, eye_y-2.1*s, cx+1.2*s, eye_y+.2*s), fill=(255, 253, 249))

    brow_y = eye_y - 14*s
    brow_w = max(2, round(width * .27))
    if pose.expression == "angry":
        _round_stroke(draw, [(hx-25*s, brow_y-5*s), (hx-17*s, brow_y-2*s), (hx-9*s, brow_y+3*s)], ink, brow_w)
        _round_stroke(draw, [(hx+9*s, brow_y+3*s), (hx+17*s, brow_y-2*s), (hx+25*s, brow_y-5*s)], ink, brow_w)
    elif pose.expression in {"worried", "sad"}:
        _round_stroke(draw, [(hx-25*s, brow_y+2*s), (hx-17*s, brow_y-4*s), (hx-9*s, brow_y-2*s)], ink, brow_w)
        _round_stroke(draw, [(hx+9*s, brow_y-2*s), (hx+17*s, brow_y-4*s), (hx+25*s, brow_y+2*s)], ink, brow_w)
    elif pose.expression == "surprised":
        _round_stroke(draw, [(hx-25*s, brow_y-5*s), (hx-17*s, brow_y-8*s), (hx-9*s, brow_y-5*s)], ink, brow_w)
        _round_stroke(draw, [(hx+9*s, brow_y-5*s), (hx+17*s, brow_y-8*s), (hx+25*s, brow_y-5*s)], ink, brow_w)
    elif pose.expression == "think":
        _round_stroke(draw, [(hx-25*s, brow_y-4*s), (hx-17*s, brow_y-7*s), (hx-9*s, brow_y-3*s)], ink, brow_w)
        _round_stroke(draw, [(hx+10*s, brow_y), (hx+18*s, brow_y+1*s), (hx+24*s, brow_y-1*s)], ink, brow_w)
    else:
        for sign in (-1, 1):
            cx = hx + sign * eye_x
            _round_stroke(draw, [(cx-8*s, brow_y), (cx, brow_y-3*s), (cx+8*s, brow_y)], ink, brow_w)

    my = hy + 17*s
    mouth_w = max(2, round(width * .36))
    if pose.expression == "smile":
        _round_stroke(draw, [(hx-13*s, my-3*s), (hx, my+5*s), (hx+13*s, my-3*s)], ink, mouth_w)
    elif pose.expression in {"open", "surprised"}:
        mw = 6*s if pose.expression == "open" else 8*s
        mh = 8*s if pose.expression == "open" else 10*s
        draw.ellipse((hx-mw, my-mh/2, hx+mw, my+mh), fill=ink)
        draw.arc((hx-mw+2*s, my+2*s, hx+mw-2*s, my+mh+1*s), 0, 180, fill=(235, 169, 165), width=max(2, round(2*s)))
    elif pose.expression in {"sad", "worried"}:
        _round_stroke(draw, [(hx-12*s, my+5*s), (hx, my-3*s), (hx+12*s, my+5*s)], ink, mouth_w)
    elif pose.expression == "angry":
        _round_stroke(draw, [(hx-11*s, my+3*s), (hx+11*s, my)], ink, mouth_w)
    elif pose.expression == "think":
        _round_stroke(draw, [(hx-8*s, my+2*s), (hx+8*s, my-1*s)], ink, mouth_w)
    else:
        _round_stroke(draw, [(hx-8*s, my), (hx+8*s, my)], ink, mouth_w)


def draw_stickman_soft(image: Image.Image, pose: StickmanPose, ink=(40, 52, 62), width=10, time_seconds=0.0):
    """Render only the character at 2×, then downsample for clean soft edges."""
    torso_top, neck, head, _ = pose.compute_skeleton()
    points = [pose.hip, torso_top, neck, head]
    for limb in (pose.left_arm, pose.right_arm, pose.left_leg, pose.right_leg):
        if limb:
            points.extend(limb)
    margin = pose.head_radius + 24 * pose.scale
    left = max(0, math.floor(min(x for x, _ in points) - margin))
    top = max(0, math.floor(min(y for _, y in points) - margin))
    right = min(image.width, math.ceil(max(x for x, _ in points) + margin))
    bottom = min(image.height, math.ceil(max(y for _, y in points) + margin))
    if right <= left or bottom <= top:
        return
    factor = 2
    detail = copy.deepcopy(pose)
    detail.hip = ((pose.hip[0] - left) * factor, (pose.hip[1] - top) * factor)
    detail.scale *= factor
    detail.torso_len *= factor
    detail.neck_len *= factor
    detail.head_radius *= factor
    detail.arm_len = tuple(x * factor for x in detail.arm_len)
    detail.leg_len = tuple(x * factor for x in detail.leg_len)
    for limb in ("left_arm", "right_arm", "left_leg", "right_leg"):
        chain = getattr(pose, limb)
        if chain:
            setattr(detail, limb, [((x-left)*factor, (y-top)*factor) for x, y in chain])
    layer = Image.new("RGBA", ((right-left)*factor, (bottom-top)*factor), (0, 0, 0, 0))
    phase = time_seconds % 4.8
    blink = 4.08 <= phase <= 4.22
    _draw_soft_character(ImageDraw.Draw(layer), detail, ink, round(width*factor), blink)
    small = layer.resize((right-left, bottom-top), Image.Resampling.LANCZOS)
    image.paste(small, (left, top), small)

def render_action_clip(action: str, duration: float, output_path: str, fps=30, size=(1280, 720), target=(600, 300)):
    """Render một đoạn video ngắn về hành động của người que (MP4)."""
    temp_dir = os.path.join(os.path.dirname(output_path), f"temp_{action}_frames")
    os.makedirs(temp_dir, exist_ok=True)
    
    total_frames = int(duration * fps)
    print(f"[*] Rendering {total_frames} frames for action '{action}'...")
    
    for i in range(total_frames):
        t = i / fps
        img = Image.new("RGBA", size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Đặt tọa độ người que
        if action == "walk":
            base_hip = (300, 520)
        elif action == "point":
            base_hip = (320, 520)
        else:
            base_hip = (400, 520)
            
        pose = StickmanAnimator.evaluate_pose(action, t, base_hip=base_hip, scale=1.3, target=target)
        StickmanAnimator.draw_stickman(draw, pose, color=(30, 28, 26), width=12)
        
        frame_file = os.path.join(temp_dir, f"frame_{i:04d}.png")
        img.save(frame_file)
        
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    shutil.rmtree(temp_dir)
    print(f"[✓] Đã tạo video chuyển động: {output_path}")

if __name__ == "__main__":
    os.makedirs("math_derivative_demo/animated_stickman", exist_ok=True)
    render_action_clip("walk", duration=3.0, output_path="math_derivative_demo/animated_stickman/walk.mp4")
    render_action_clip("wave", duration=3.0, output_path="math_derivative_demo/animated_stickman/wave.mp4")
    render_action_clip("point", duration=3.0, output_path="math_derivative_demo/animated_stickman/point.mp4", target=(700, 260))
    render_action_clip("think", duration=3.0, output_path="math_derivative_demo/animated_stickman/think.mp4")
    render_action_clip("explain", duration=3.0, output_path="math_derivative_demo/animated_stickman/explain.mp4")
    print("HOÀN TẤT BỘ ANIMATION MẪU CHO NGƯỜI QUE!")

