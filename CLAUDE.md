# UIT 3D

Website khám phá khuôn viên trường UIT (ĐH Công nghệ Thông tin, ĐHQG-HCM) bằng 3D, kiểu game thế giới mở:
đi lại trong trường, mỗi khu vực có thông tin, ảnh, nhiệm vụ, minigame và easter egg.

- Deploy: https://uit-3d-alpha.vercel.app (Vercel tự build khi push lên `main`)
- Trả lời và viết comment, nội dung giao diện bằng tiếng Việt.

## Quy tắc commit

- Commit chỉ đứng tên chủ dự án (ImDT06). **Không** thêm `Co-Authored-By`, không ghi tên Claude
  hay link session vào commit message, PR, hay code.
- Commit message ngắn gọn, tiếng Việt không dấu cũng được.

## Stack

- Vite + React 19 + React Three Fiber 9 + drei
- Vật lý: @react-three/rapier
- Nhân vật: `ecctrl` v2. Lưu ý: v2 **không** tự đọc bàn phím. Input được đưa vào bằng
  `ecctrl.current.setMovement({...})` mỗi frame (xem `src/world/Player.jsx`), camera dùng
  `EcctrlCameraControls` và tự `moveTo` theo `currPos`.
- State: zustand (`src/game/store.js`)

## Cấu trúc

Chia theo vai trò; file mới đặt đúng nhóm, import bằng đường dẫn tương đối.

- `src/world/` (trong Canvas 3D):
  - `campusModel.js`: `MODEL_URL`, `splitScene()` (tách cây, đọc `ZONE_*`/`ITEM_*`, dựng khối va chạm, cài bóng đổ).
    Không import Rapier: trang chủ dùng file này mà không phải tải thư viện vật lý.
  - `Explore.jsx`: `<Physics>` + Campus + Player + Waypoint, **tải lười** (`lazy`) cùng `ui/ExploreUi.jsx`;
    `App.jsx` tải ngầm sau 2,5 s ở trang chủ. Đừng import Rapier/ecctrl/Campus/Player từ file thuộc trang chủ.
  - `Campus.jsx`: va chạm (tòa nhà khối đặc, còn lại trimesh), tường biên, nhãn tên tòa, điểm xuất phát.
  - `Sun.jsx`: ánh sáng + bóng. Khám phá: vùng bóng ±60 m đi theo nhân vật; trang chủ/tham quan: phủ cả trường.
    Vật liệu glb đều 2 mặt nên `shadowSide = BackSide`; đất, lối đi, kính không đổ bóng (tránh vệt lấm tấm).
  - `Atmosphere.jsx`: nền trời, sương mù, `Sky`; trang chủ trong suốt, vào tham quan thì hiện dần. Luôn gắn sẵn,
    chỉ đổi thông số (thêm/bớt sương mù bắt biên dịch lại shader mọi vật liệu → đứng hình). Tone mapping: Neutral (`App.jsx`).
  - `Player.jsx`: điều khiển (bàn phím + joystick + tay cầm), camera (không xuyên tường), phát hiện khu vực.
  - `Student.jsx`: nhân vật sinh viên low-poly dựng bằng khối hình học, animation đi/chạy/nhảy
    tính bằng code theo vận tốc của ecctrl (không cần file model).
  - `Waypoint.jsx`: cột sáng đánh dấu điểm đến.
  - `IntroScene.jsx`: sa bàn trang chủ (tự xoay, bấm tòa để xem) + camera bay khi tham quan, danh sách điểm dừng.
- `src/ui/` (HTML phủ lên cảnh): `Hud.jsx` (thẻ khu vực, tiến độ, màn hình tải, joystick mobile), `Menu.jsx`,
  `MapView.jsx` (bản đồ nhỏ + lớn), `Tutorial.jsx`, `Admin.jsx` (phím Backquote, cạnh số 1), `IntroUi.jsx` (trang chủ + thẻ tham quan),
  `Loading.jsx`, `FpsMeter.jsx` (`?fps`), `ExploreUi.jsx`.
- `src/game/`: `store.js` (trạng thái), `settings.js` (cài đặt, phím), `actions.js` (phím tắt, chỉ chạy khi
  `mode === "explore"`), `sfx.js`.
- `src/data/zones.js`: tên, mô tả, ảnh từng khu vực. Key = tên object trong Blender. Thẻ tham quan dùng chung.
- `src/styles/*.css`: CSS theo phần. Thứ tự import trong `main.jsx` có ý nghĩa (`hud.css` sau `map.css`).
- `store.mode`: `intro` → `tour` → `explore`, dùng chung Canvas và mô hình (một object chỉ gắn vào một nơi,
  nên `IntroScene` và `Campus` không bao giờ mount cùng lúc). `?play` vào thẳng khám phá.
- `tools/blender/`: script Blender (xem README trong đó). Trong .blend các Text đã liên kết tới file ở đây.
- `.vscode/`: F5 chạy `npm run dev` rồi mở Chrome.

## Mô hình 3D

- Dựng trong Blender 5.3, file gốc `D:\uit3d\blender\uit_blockout.blend` (không nằm trong repo).
- Dữ liệu từ OpenStreetMap. Quy ước tên object:
  - `BLD_*` tòa nhà: `BLD_A`, `BLD_B`, `BLD_C`, `BLD_D`, `BLD_E`, `BLD_CanTin` (= "Nhà ăn", tour 360 gọi
    "Nhà dịch vụ", tòa tròn viền xanh phía đông B, bán cơm), `BLD_CanTin2` (= "Căn tin", mái tôn xanh dương,
    bán bánh/nước; lối đi qua đây ra cổng sau), `BLD_ChotBaoVe` (gần cổng sau?), `BLD_X2` (chưa rõ)
  - `DET_<tòa>_trim` / `DET_<tòa>_glass`: gờ sàn, lan can, cửa sổ (con của `BLD_*`, tạo bởi `uit_detail.py`).
    Tên kết thúc `_glass` hoặc `_decal` (mảng phẳng dán lên tường) thì web không cho đổ bóng.
  - `TREE_*` cây (collection Deco). Trên web cây không dùng va chạm trimesh, mỗi cây một CylinderCollider.
  - `GND_*` mặt đất, sân, cỏ; `PATH_*` lối đi; `REF_*` ảnh tham chiếu (không xuất ra web)
  - `ZONE_<tòa>` (empty hình hộp, collection Gameplay): vùng khu vực, đứng trong hộp = đang ở `BLD_<tòa>`
    (hoặc custom prop `zone`). `ITEM_###` (empty): điểm đặt vật phẩm, custom prop `quest`.
    Tạo bằng script `uit_gameplay.py` (chạy lại được), có thể kéo/sửa tay. Web đọc trong `Campus.jsx` → `store.zones/items`.
  - Mép `GND_Base` = biên khuôn viên (Blender x −200..250, y −230..200), web dựng tường vô hình theo đó.
    Mặt đất/đường gốc chưa cắt nằm trong `D:\uit3d\blender\uit_blockout_backup_truoc_cat.blend` (cần khi nới biên).
    `CAMPUS_CENTER` trong `src/world/Sun.jsx` là tâm khung này.
  - Dự kiến: `COL_*` collider riêng
- Chiều cao: số tầng x 3.5 m + 1 m. A, C: 3 tầng; D: 1; E: 12 (theo OSM, chưa xác nhận);
  B: vòng cung sạch (bảng `ARC` trong `uit_detail.py`: tâm, bán kính, góc, `segments`). Theo ảnh Google Maps
  (chủ dự án xác nhận 6 mái cao 4-5-6-7-8-9 tầng từ đầu đông sang đầu tây). Tường xanh da trời nhạt.
  Từ tây sang đông: khối 9 nhô | lõm 8 | trụ 8 nhô | khối 7 nhô | lõm 6 (cột chữ "B") | trụ 6 nhô (dải kính) |
  khối 5 nhô | lõm nửa 5 + nửa 4 (chung 1 cột) | khối 4 nhô. Mặt nhô: chân xanh lá, dải kính xanh viền xanh dương, vài cột cặp ô vuông nhỏ,
  khối 7 có cột cửa sổ mái che lá sách, còn lại tường trơn (vị trí theo tỉ lệ trong `segments`).
  Phần lõm sâu `recess`: ban công hành lang chồng tầng, cột giữa, cầu thang tối ở chân.
  Giàn lam xanh dương + bồn nước inox trên mái theo từng đoạn.
  Tường hồi hai đầu (đầu tây hướng về C): cột cửa sổ có mái che, lỗ thông gió, rãnh dọc.
  Sân giữa: bậc ngồi vòng cung thấp dần về vòng tròn ở tâm = object `PLAZA_B` (collection Props, va chạm
  trimesh nên đi lên bậc được). Khối tháp nằm trong mesh `BLD_B` (có va chạm). Mặt bằng OSM gốc giữ ở
  `BLD_B_goc`. `TIERS` (cắt tầng theo trục X) dùng được cho tòa khác;
  căn tin, chốt bảo vệ, X2: 1.
- C (theo ảnh "Sân bóng"): 3 tầng, tường xanh nhạt, khung lam trắng chia ô (`STYLE["BLD_C"]["fins"]` = bề ngang ô).
  Khối sảnh mặt nam hướng sân bóng (`porch`, không va chạm, đi vào dưới được): cột tầng trệt, hàng tam giác
  lỗ tròn trên nền gạch đỏ, ban công, lam dọc tầng 3, chữ đỏ tên trường, cột cờ. Mái thật (ảnh Google Maps):
  2 dãy mái tôn xanh nhạt, sân trong hẹp, khối giữa mái ngói cam; chưa dựng.
- Script dựng mô hình ở `tools/blender/` (import → cleanup → fix → detail → gameplay → export).
- Chi tiết tòa nhà + trồng cây + cổng chính: script `uit_detail.py` (chạy lại được, tự xóa chi tiết cũ).
  Kiểu riêng từng tòa trong bảng `STYLE` (A: tường trắng, mái cam, 2 vòm xanh ngọc; E: kính xanh liền,
  bảng tên trên mái; căn tin: mái tôn xanh dương qua `roofs` kiểu `fit`). Cổng chính (`GATE_*`, collection
  Props) chỉnh vị trí qua biến `GATE` (chủ dự án xác nhận vị trí hiện tại là đúng; ô đỏ "cổng hiện tại (sai)"
  trên `ban-do-luoi.png` thực ra đúng).
  Cổng sau `GATE_back` (biến `BACK_GATE`): trên nhánh đường từ ngã ba nam bốt bảo vệ ra đường ven xa lộ,
  có trụ, hàng rào, cánh cổng trượt, bốt bảo vệ nhỏ.
  Ảnh flycam (Kỷ yếu Sài Gòn) chỉ dùng làm mẫu dựng, không đưa lên web.
- Va chạm trên web: tòa nhà là khối đặc (mỗi tam giác mặt đáy dựng thành lăng trụ, `ConvexHullCollider`),
  không dùng trimesh vì tường mỏng làm nhân vật lọt vào trong. Mặt đất, lối đi, `GATE_*` vẫn dùng trimesh.
- Nướng ánh sáng (đang thử, mới có B + mặt đất/lối đi/sân bậc): `uit_lightbake.py` nướng nắng, bóng mềm, ánh sáng dội,
  bo cạnh (node Bevel) vào texture; kiểu ánh sáng `LIGHT` = `sang` / `trua` / `chieu` (bảng `PRESETS`, phải khớp
  `src/world/lighting.js`). Object đã nướng có custom prop `baked` → web dùng `MeshBasicMaterial` (không tính đèn,
  không nhận bóng thời gian thực; nhân vật có vệt bóng tròn dưới chân). Bản thử xuất ra `public/models/uit_campus_bakeB*.glb`,
  xem bằng `?model=uit_campus_bakeB_sang&nang=sang` (chưa commit glb thử). Chưa chọn kiểu ánh sáng cuối cùng.
- Xuất ra web bằng script `uit_export.py` trong Blender → `public/models/uit_campus.glb` (nén Draco).
  Trục: Blender Z-up → glTF Y-up; 1 đơn vị = 1 m; gốc tọa độ = tâm khuôn viên.

## Lệnh

- `npm install` (lần đầu), `npm run dev` (chạy thử tại http://localhost:5173), `npm run build`
- `?model=<tên>`: dùng `public/models/<tên>.glb` thay bản chính; `?nang=sang|chieu`: kiểu mặt trời trên web.
- Thêm `?debug` vào URL để xem khung va chạm, `?fps` để hiện bộ đếm FPS (đo trên điện thoại thật).
- `?toa=C` (hoặc `?toa=CanTin`...): xem riêng một tòa, xoay/zoom tự do (`world/BuildingPreview.jsx`, `ui/PreviewUi.jsx`).
  Quy trình dựng chi tiết: sửa script → dựng lại → gửi ảnh + link `?toa=` cho chủ dự án duyệt → mới commit.
- Khi chạy dev có `window.__uitPlayer` (ref ecctrl) và `window.__uitR3f` (state R3F) cho script kiểm thử
  (teleport, đẩy vận tốc, đọc `gl.info`); bản build không có.
- `public/og.jpg`: ảnh xem trước khi gửi link (chụp từ trang chủ, 1200×630). Đổi giao diện trang chủ nhiều thì chụp lại.

## Việc tiếp theo (theo thứ tự)

0. Kiểm tra trang chủ + tham quan trên máy và điện thoại thật, commit, push để Vercel deploy.
1. Hệ thống nhiệm vụ: hiện vật phẩm tại các `ITEM_*` (đã có vị trí trong `store.items`), chạm là nhặt,
   danh sách nhiệm vụ trên HUD, lưu tiến độ localStorage. Nhiệm vụ mẫu: nhặt 12 vật phẩm; "khám phá đủ khu vực"
   chuyển từ bộ đếm `visited` thành nhiệm vụ.
2. ~~Sửa lỗi + tối ưu~~ (xong 19/11: va chạm 304 lần thử không lọt, hết vệt bóng, JS lúc mở trang 3,6 → 1,3 MB,
   og:image). Còn: đo FPS trên điện thoại thật bằng `?fps`.
3. Nội dung `src/data/zones.js`: mô tả cho E, D, chốt bảo vệ, X2 (X2 chưa rõ là gì), ảnh ở `public/images/`.
   Thẻ tham quan lấy nội dung từ đây.
4. Minigame theo khu vực (quiz thư viện, căn tin...), easter egg.
5. Ảnh tham khảo đã có ở `D:/uit3d/reference/` (chụp màn hình tour 360, có bản quyền, chỉ làm mẫu; ghi chú
   trong `NGUON.md`). Đã dựng theo ảnh: C, B, căn tin (mái), cổng sau. Còn: nhà ăn (tòa tròn viền xanh),
   chi tiết cổng chính, A, E (ảnh `E/nha-gui-xe-E-cau-thang-xoan.png`: khối bên phải là cầu thang bộ xoắn
   ốc ngoài trời), mặt ngoài phía bắc B (chưa có ảnh).
