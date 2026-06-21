import os
import cv2
import numpy as np
import scipy.io as sio
import glob
import random

# Kích thước crop cố định
CROP_SIZE = (400, 400)  # (height, width)


# ─────────────────────────────────────────────────────────────
# 1. Cấu hình thư mục
# ─────────────────────────────────────────────────────────────
def configure_directories():
    base_dir = r"C:\Study\DA_ThiGiacMayTinh\ShanghaiTech\New_folder"
    part_A_dir    = os.path.join(base_dir, "part_A")
    processed_dir = os.path.join(base_dir, "processed")

    dirs_to_create = [
        os.path.join(processed_dir, "train_data", "images"),
        os.path.join(processed_dir, "train_data", "ground-truth"),
        os.path.join(processed_dir, "test_data",  "images"),
        os.path.join(processed_dir, "test_data",  "ground-truth"),
    ]
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)

    return part_A_dir, processed_dir


# ─────────────────────────────────────────────────────────────
# 2. Đọc ảnh và ground truth
# ─────────────────────────────────────────────────────────────
def load_data(img_path, mat_path):
    """
    Trả về:
        img    : np.ndarray (H, W, 3), kênh màu RGB, dtype uint8
        points : np.ndarray (N, 2), [[x1,y1], [x2,y2], ...]
    """
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"  [ERROR] Không đọc được ảnh: {img_path}")
        return None, None

    if img.ndim == 2:
        # Grayscale thực sự → duplicate 3 kênh
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:
        # BGRA → RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    else:
        # BGR bình thường → RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    try:
        mat    = sio.loadmat(mat_path, squeeze_me=False)
        points = mat['image_info'][0, 0][0, 0][0].astype(np.float32)
        if points.ndim == 1:
            points = points.reshape(-1, 2)
    except Exception as e:
        print(f"  [ERROR] Không đọc được GT: {mat_path}: {e}")
        return img, np.zeros((0, 2), dtype=np.float32)

    return img, points

# ─────────────────────────────────────────────────────────────
# 3. Làm sạch điểm GT nằm ngoài biên
# ─────────────────────────────────────────────────────────────
def clean_points(img, points):
    """Lọc bỏ các điểm nằm ngoài kích thước thực tế của ảnh."""
    if len(points) == 0:
        return np.zeros((0, 2), dtype=np.float32)

    h, w = img.shape[:2]
    mask = (
        (points[:, 0] >= 0) & (points[:, 0] < w) &
        (points[:, 1] >= 0) & (points[:, 1] < h)
    )
    cleaned   = points[mask]
    n_removed = len(points) - len(cleaned)
    if n_removed > 0:
        print(f"  [CLEAN] Loại {n_removed} điểm ngoài biên (còn {len(cleaned)})")
    return cleaned if len(cleaned) > 0 else np.zeros((0, 2), dtype=np.float32)


# ─────────────────────────────────────────────────────────────
# 4. Random crop + cập nhật tọa độ GT
# ─────────────────────────────────────────────────────────────
def get_random_crop(img, points, crop_size=CROP_SIZE):
    """
    Crop ngẫu nhiên vùng crop_size từ ảnh.

    Cập nhật tọa độ GT:
        x' = x - start_x
        y' = y - start_y
    Lọc điểm nằm ngoài vùng crop.

    FIX [BUG 5]: nếu ảnh nhỏ hơn crop_size → pad ảnh trước,
    không return sớm mà bỏ qua việc filter points.
    """
    ch, cw = crop_size
    h, w   = img.shape[:2]

    # Pad nếu ảnh nhỏ hơn kích thước crop
    if h < ch or w < cw:
        pad_b = max(0, ch - h)
        pad_r = max(0, cw - w)
        img   = cv2.copyMakeBorder(img, 0, pad_b, 0, pad_r,
                                                cv2.BORDER_CONSTANT, value=0)
        h, w  = img.shape[:2]

    start_y = random.randint(0, h - ch)
    start_x = random.randint(0, w - cw)

    cropped_img = img[start_y:start_y + ch, start_x:start_x + cw]

    if len(points) > 0:
        pts       = points.copy()
        pts[:, 0] -= start_x   # x' = x - start_x
        pts[:, 1] -= start_y   # y' = y - start_y
        inside = (
            (pts[:, 0] >= 0) & (pts[:, 0] < cw) &
            (pts[:, 1] >= 0) & (pts[:, 1] < ch)
        )
        cropped_pts = pts[inside]
    else:
        cropped_pts = np.zeros((0, 2), dtype=np.float32)

    return cropped_img, cropped_pts


# ─────────────────────────────────────────────────────────────
# 5. Horizontal flip + cập nhật tọa độ GT
# ─────────────────────────────────────────────────────────────
def horizontal_flip(img, points):
    """
    Lật ngang ảnh.
    Cập nhật tọa độ GT:
        x' = w - x   ← FIX [BUG 3]: thay vì w-1-x
        y' = y         (không đổi)

    Lý do: (w-1-x) với float gây x' âm khi x ≈ w.
    Ví dụ: w=400, x=399.9 → 399-399.9 = -0.9 (lỗi).
    Dùng w-x: 400-399.9 = 0.1 ∈ [0,400) (đúng).
    """
    flipped_img = cv2.flip(img, 1)
    w = img.shape[1]

    if len(points) > 0:
        pts       = points.copy()
        pts[:, 0] = w - pts[:, 0] 
        return flipped_img, pts

    return flipped_img, np.zeros((0, 2), dtype=np.float32)


# ─────────────────────────────────────────────────────────────
# 6. Lưu / đọc ground truth
# ─────────────────────────────────────────────────────────────
def save_ground_truth(mat_path_out, points):
    """
    Lưu GT points ra file .mat.

    FIX [BUG 1]: chỉ nhận 2 tham số — bỏ mat_path thừa.
    Dùng key 'annPoints' đơn giản, load_ground_truth() hỗ trợ
    cả format này lẫn ShanghaiTech gốc.
    """
    pts = np.array(points, dtype=np.float64) if len(points) > 0 \
          else np.zeros((0, 2), dtype=np.float64)
    sio.savemat(mat_path_out, {
        'annPoints': pts,
        'number':    np.array([[len(pts)]])
    })


def load_ground_truth(mat_path):
    """
    Đọc GT từ .mat, hỗ trợ 2 format:
    - ShanghaiTech gốc : image_info[0,0][0,0][0]
    - Processed (file này): annPoints
    """
    mat = sio.loadmat(mat_path, squeeze_me=False)
    if 'image_info' in mat:
        try:
            pts = mat['image_info'][0, 0][0, 0][0].astype(np.float32)
            if pts.ndim == 1:
                pts = pts.reshape(-1, 2)
            return pts
        except Exception:
            pass
    if 'annPoints' in mat:
        pts = mat['annPoints'].astype(np.float32)
        if pts.ndim == 1:
            pts = pts.reshape(-1, 2)
        return pts
    return np.zeros((0, 2), dtype=np.float32)


# ─────────────────────────────────────────────────────────────
# 7. Pipeline xử lý toàn bộ dataset
# ─────────────────────────────────────────────────────────────
def process_dataset(part_A_dir, processed_dir,
                    mode="train_data", num_crops=4, do_flip=True,
                    crop_size=CROP_SIZE):
    """
    Train : random crop (num_crops lần/ảnh) + horizontal flip 50%
    Test  : chỉ clean + lưu lại, không augment

    FIX [BUG 6]: crop_size cố định qua tham số, không tính
                 (h//2, w//2) theo từng ảnh.
    """
    img_dir   = os.path.join(part_A_dir, mode, "images")
    img_paths = sorted(glob.glob(os.path.join(img_dir, "*.jpg")))
    if not img_paths:
        img_paths = sorted(glob.glob(os.path.join(img_dir, "*.png")))

    out_img_dir = os.path.join(processed_dir, mode, "images")
    out_gt_dir  = os.path.join(processed_dir, mode, "ground-truth")

    print(f"\n{'='*55}")
    print(f"  Bắt đầu xử lý : {mode}  ({len(img_paths)} ảnh)")
    print(f"  Crop size cố định : {crop_size}")
    print(f"{'='*55}")

    success_count = 0
    skip_count    = 0

    for img_path in img_paths:
        filename  = os.path.basename(img_path)
        name, ext = os.path.splitext(filename)
        mat_path  = os.path.join(part_A_dir, mode, "ground-truth",
                                  f"GT_{name}.mat")

        if not os.path.exists(mat_path):
            print(f"  [SKIP] Không tìm thấy GT: {filename}")
            skip_count += 1
            continue

        img, points = load_data(img_path, mat_path)
        if img is None:
            skip_count += 1
            continue

        points = clean_points(img, points)

        if mode == "train_data":
            for i in range(num_crops):
                c_img, c_pts = get_random_crop(img, points, crop_size)

                if do_flip and random.random() > 0.5:
                    c_img, c_pts = horizontal_flip(c_img, c_pts)

                out_name = f"{name}_crop{i}"
                cv2.imwrite(
                    os.path.join(out_img_dir, out_name + ext),
                    cv2.cvtColor(c_img, cv2.COLOR_RGB2BGR)
                )
                save_ground_truth(
                    os.path.join(out_gt_dir, f"GT_{out_name}.mat"),
                    c_pts
                )
                success_count += 1
        else:
            cv2.imwrite(
                os.path.join(out_img_dir, filename),
                cv2.cvtColor(img, cv2.COLOR_RGB2BGR) 
            )
            save_ground_truth(                    
                os.path.join(out_gt_dir, f"GT_{name}.mat"),
                points
            )
            success_count += 1

    print(f"\n  ✓ [{mode.upper()}] Hoàn thành!")
    print(f"    Đã lưu : {success_count} file")
    print(f"    Bỏ qua : {skip_count} file")

# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    part_A_dir, processed_dir = configure_directories()

    if not os.path.exists(part_A_dir):
        print(f"[ERROR] Không tìm thấy: {part_A_dir}")
    else:
        process_dataset(part_A_dir, processed_dir,
                        mode="train_data", num_crops=4, do_flip=True,
                        crop_size=CROP_SIZE)
        process_dataset(part_A_dir, processed_dir,
                        mode="test_data",  num_crops=1, do_flip=False,
                        crop_size=CROP_SIZE)