# UIT 3D

Website khám phá khuôn viên Trường ĐH Công nghệ Thông tin (ĐHQG-HCM) bằng 3D: trang chủ với sa bàn thu nhỏ,
chuyến tham quan qua từng khu vực, rồi tự do đi lại như game thế giới mở.

Bản chạy thật: https://uit-3d-alpha.vercel.app (tự cập nhật khi push lên `main`).

## Chạy trên máy

```
npm install      # lần đầu
npm run dev      # mở http://localhost:5173
npm run build    # kiểm tra bản build
```

Trong VS Code: bấm **F5** là tự chạy dev server và mở Chrome (chọn Edge hoặc "vào thẳng khám phá"
trong khung Run and Debug).

- `?play`: bỏ qua trang chủ, vào thẳng chế độ khám phá.
- `?debug`: hiện khung va chạm, vùng khu vực, điểm vật phẩm.

## Điều khiển

- W A S D / mũi tên: đi · C: chạy · Space: nhảy · E: xem thông tin khu vực · M: bản đồ · Esc: menu
- Shift: khóa chuột (shift lock) · V: đổi góc nhìn · chuột phải kéo: xoay camera · lăn chuột: zoom
- Đổi phím trong Menu → Phím điều khiển
- Điện thoại: joystick ảo + nút nhảy

## Cấu trúc

```
src/
  main.jsx, App.jsx   khởi động, Canvas, chuyển chế độ intro → tour → explore
  world/              mọi thứ trong cảnh 3D
    Campus.jsx          tải mô hình, va chạm (tòa nhà khối đặc), vùng ZONE_/ITEM_, nhãn tên
    Player.jsx          nhân vật, bàn phím/joystick/tay cầm, camera, phát hiện khu vực
    Student.jsx         nhân vật sinh viên dựng bằng khối, animation bằng code
    Waypoint.jsx        cột sáng đánh dấu điểm đến
    IntroScene.jsx      sa bàn trang chủ + camera bay khi tham quan
  ui/                 giao diện HTML phủ lên cảnh
    Hud.jsx, Menu.jsx, MapView.jsx, Tutorial.jsx, Admin.jsx, IntroUi.jsx
  game/               trạng thái và logic không vẽ gì
    store.js (zustand), settings.js (cài đặt, phím), actions.js (phím tắt), sfx.js (âm thanh)
  data/
    zones.js            tên, mô tả, ảnh từng khu vực
  styles/             CSS theo phần (thứ tự nạp trong main.jsx)
public/
  models/uit_campus.glb mô hình xuất từ Blender
  images/               ảnh khu vực (tự chụp; tạo thư mục khi thêm ảnh đầu tiên)
tools/blender/        script dựng mô hình trong Blender, xem README trong đó
```

## Sửa nội dung

- Tên, mô tả, ảnh từng khu vực: `src/data/zones.js` (ảnh đặt trong `public/images/`). Thẻ tham quan dùng chung dữ liệu này.
- Mô hình: sửa trong Blender (`D:\uit3d\blender\uit_blockout.blend`), chạy `uit_export.py` rồi tải lại trang.
