# UIT 3D

Website đi dạo khuôn viên UIT bằng 3D.

## Chạy lần đầu

1. Giải nén thư mục `web` vào `D:\uit3d\` (để có `D:\uit3d\web\package.json`).
2. Trong Blender, mở `uit_blockout.blend`, chạy script `uit_export.py`. File sẽ được xuất vào `D:\uit3d\web\public\models\uit_campus.glb`.
3. Mở Terminal tại `D:\uit3d\web` và chạy:

```
npm install
npm run dev
```

4. Mở link `http://localhost:5173` hiện trong Terminal.

## Điều khiển

- W A S D / mũi tên: đi · Shift: chạy · Space: nhảy
- Kéo chuột: xoay camera · Lăn chuột: zoom
- Điện thoại: joystick ảo + nút Nhảy

## Sửa nội dung

- Tên, mô tả, ảnh từng tòa: `src/zones.js` (ảnh đặt trong `public/images/`).
- Xem khung va chạm: thêm `?debug` vào cuối link.
- Mỗi lần sửa mô hình trong Blender: chạy lại `uit_export.py` rồi tải lại trang.

## Cấu trúc

- `src/Campus.jsx`: tải mô hình, va chạm, nhãn tên tòa nhà
- `src/Player.jsx`: nhân vật, bàn phím/joystick, camera, phát hiện khu vực
- `src/Hud.jsx`: giao diện (thẻ khu vực, tiến độ khám phá, màn hình tải)
- `src/store.js`: trạng thái game (zustand)
