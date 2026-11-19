# Script Blender

Các script dựng mô hình `D:\uit3d\blender\uit_blockout.blend` → `public/models/uit_campus.glb`.
Trong file .blend, mỗi script là một Text đã liên kết tới file ở đây: sửa trong Blender xong bấm
**Text → Save** (Alt+S) là lưu vào repo. Sửa file bên ngoài thì trong Blender bấm **Text → Reload**.

Thứ tự chạy khi dựng lại từ đầu (tab Scripting → chọn Text → Run Script):

| Bước | Script | Việc làm | Chạy lại được? |
|---|---|---|---|
| 1 | `uit_import.py` | Tải dữ liệu OpenStreetMap + ảnh vệ tinh, dựng khối tòa nhà, mặt đất, lối đi | Một lần |
| 2 | `uit_cleanup.py` | Bỏ các tòa ngoài khuôn viên UIT | Một lần |
| 3 | `uit_fix.py` | Đặt tên `BLD_*`, chỉnh chiều cao theo số tầng | Một lần |
| 4 | `uit_detail.py` | Cửa sổ, gờ sàn, lan can, kiểu riêng từng tòa (`STYLE`), cổng chính (`GATE`), trồng cây | Có, tự xóa chi tiết cũ |
| 5 | `uit_gameplay.py` | Vùng khu vực `ZONE_*`, điểm vật phẩm `ITEM_*` | Có, tự xóa dữ liệu cũ |
| 6 | `uit_export.py` | Xuất `.glb` nén Draco vào `public/models/` | Có |

Thường ngày chỉ cần bước 4 → 5 → 6 (hoặc chỉ 6 nếu sửa tay trong Blender).
Lưu ý: bước 4 trồng lại cây nên tên `TREE_*` thay đổi.

Bước 1–3 đã chạy xong và có các chỉnh tay sau đó (cắt mặt đất theo khuôn viên 340 × 370 m,
xóa cây ngoài biên). Chạy lại từ bước 1 sẽ mất các chỉnh tay này.
