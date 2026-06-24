
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import matplotlib.pyplot as plt

# ==========================
# THÔNG SỐ
# ==========================

IN_X, IN_Y = 768, 1024
OUT_X, OUT_Y = 96, 128

# ==========================
# NHẬN ĐƯỜNG DẪN ẢNH TỪ JAVA
# ==========================

image_path = sys.argv[1]

# ==========================
# LOAD MODEL
# ==========================

#model = load_model("/Users/nguyenviethuynh/Downloads/processed/best_model206.keras")
model = load_model("best_model206.keras")
# ==========================
# ĐỌC ẢNH
# ==========================

im_array = img_to_array(
    load_img(
        image_path,
        target_size=(IN_X, IN_Y)
    )
)

# ==========================
# TIỀN XỬ LÝ
# ==========================

im_array = im_array.astype(np.float32)

im_array /= 255

for i in range(3):
    im_array[:,:,i] = (
        im_array[:,:,i]
        - np.mean(im_array[:,:,i])
    ) / (np.std(im_array[:,:,i]) + 1e-8)

# ==========================
# DỰ ĐOÁN
# ==========================

output = model.predict(
    tf.expand_dims(im_array, axis=0),
    verbose=0
)

output = np.reshape(output,(OUT_X,OUT_Y))

# ==========================
# ĐẾM NGƯỜI
# ==========================

n_people = float(np.sum(output))

# ==========================
# LƯU DENSITY MAP
# ==========================

output_path = "output.jpg"

plt.imsave(
    output_path,
    output,
    cmap='jet'
)

# ==========================
# TRẢ KẾT QUẢ CHO JAVA
# ==========================

print(f"{int(n_people)}|{output_path}")