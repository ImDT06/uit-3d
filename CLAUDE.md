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
- `src/ui/` (HTML phủ lên cảnh): `Hud.jsx` (thẻ khu vực, tiến độ, màn hình tải), `TouchControls.jsx` (điều khiển
  cảm ứng kiểu Roblox: joystick động nửa trái, nút nhảy/chạy/shift lock; ghi vào store của `ecctrl/input`,
  không dùng `Joystick` có sẵn vì nó không tự định vị; `body.touch` khi đang dùng cảm ứng), `Menu.jsx`,
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
  - `VIS_<tòa>` (con của `BLD_<tòa>`): mô hình hiển thị lấy từ nơi khác (đang thử: A, B, C, E, CanTin, CanTin2 cắt từ `map.glb`
    của MyUIT, chủ dự án đã được phép dùng; mỗi tòa co giãn cho khớp mặt bằng OSM, giữ chiều cao của họ; A tách khối chính +
    Thư viện; MyUIT không có D, chốt bảo vệ, X2). Chi tiết cũ `DET_*` của các tòa này nằm ở collection `VIS_BACKUP` (không xuất).
    Ngoài tòa còn lấy từ MyUIT: `PODIUM_B` (bậc vòng cung + bục tròn sân B, Props, va chạm trimesh nên đi lên được;
    thay `PLAZA_B` cũ, đã cất vào `VIS_BACKUP`), `GND_myuit` (mặt đất/lối đi/sân, ép phẳng dày vài cm, nằm trên mặt đất cũ),
    `PROP_myuit` (giàn hoa, ghế, đèn, mái che, lưới sân; đã bỏ cây). Hai object này được "uốn" (thin-plate spline) theo
    điểm neo = góc các tòa (vị trí MyUIT → mặt bằng OSM), nên lối đi bám theo tòa; đường chính OSM `PATH_Road` vẫn giữ
    (bên trong khuôn viên bị `GND_myuit` phủ; đường nam C đã kéo thêm bằng phép uốn thứ hai về tâm y ≈ −79,5, khớp ảnh vệ tinh).
    Mặt đất MyUIT gốc cao 0,57 m → đã hạ; các tấm đất nâng/sườn dốc của họ cũng ép phẳng; cắt theo khung `GND_Base`.
    Cây: `CAY_myuit` (mesh gộp mọi cây MyUIT, chỉ hiển thị) + `CAY_###` (empty ở gốc, web dựng trụ va chạm như `TREE_*`).
    Có `CAY_*` thì `uit_detail.py` không trồng cây tự động; `TREE_*` cũ trong khuôn viên đã cất vào `VIS_BACKUP`.
    Lớp đất cũ (`GND_Green/Pitch`, `PATH_Footway/Road`) đã cắt phần nằm dưới `GND_myuit` (bản gốc: `*_goc` trong `VIS_BACKUP`).
    Lõi đặc `VIS_<tòa>_core` (script `uit_vis_core.py`): khối lùi sau mặt tường VIS_ ~1 m, theo từng mức mái; web dùng lõi
    làm khối va chạm + chắn camera (thay thân `BLD_`). Sửa/thay `VIS_` thì chạy lại script này.
    Cổng A: chủ dự án xác nhận cổng cũ (`GATE_*`, biến `GATE`) sai → dùng cụm cổng MyUIT (`GND_congA`, `PROP_congA`,
    `CAY_congA`: sân hoa văn mạch điện, hàng cờ, chữ UIT), chỉ dời + xoay (−14°) chứ không uốn để khỏi méo;
    `uit_detail.py` bỏ qua cổng cũ khi có `PROP_congA`. Tour: `GATE_POS` trong `IntroScene.jsx`.
    Web: có `VIS_` thì thân `BLD_` ẩn đi, chỉ làm khối va chạm + chắn camera; `VIS_` không dùng để va chạm.
    `uit_detail.py` bỏ qua tòa có `VIS_` (không dựng chi tiết đè lên) và không xóa `VIS_`.
    So sánh với ảnh vệ tinh: mặt bằng MyUIT lệch/to hơn thực tế (A, nhà ăn), nên chỉ lấy hình tòa, không lấy mặt bằng.
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
  Kiểu riêng từng tòa trong bảng `STYLE` (A: tường trắng, mái cam, 2 vòm xanh ngọc = kiểu cũ, ảnh vệ tinh Esri đã cũ;
  chủ dự án xác nhận mái A nay sơn lại xanh lá có logo UIT như `VIS_A`, vài tòa khác cũng mới sơn lại; E: kính xanh liền,
  bảng tên trên mái; căn tin: mái tôn xanh dương qua `roofs` kiểu `fit`). Cổng chính (`GATE_*`, collection
  Props) chỉnh vị trí qua biến `GATE` (chủ dự án xác nhận vị trí hiện tại là đúng; ô đỏ "cổng hiện tại (sai)"
  trên `ban-do-luoi.png` thực ra đúng).
  Cổng chính = "Cổng A" (đường Hàn Thuyên), cổng sau = "Cổng B" (tên theo Google Maps, nhãn trong `LANDMARKS` ở `zones.js`).
  Cổng sau `GATE_back` (biến `BACK_GATE`): trên nhánh đường từ ngã ba nam bốt bảo vệ ra đường ven xa lộ,
  có trụ, hàng rào, cánh cổng trượt, bốt bảo vệ nhỏ.
  Ảnh flycam (Kỷ yếu Sài Gòn) chỉ dùng làm mẫu dựng, không đưa lên web.
- Va chạm trên web: tòa nhà là khối đặc (mỗi tam giác mặt đáy dựng thành lăng trụ, `ConvexHullCollider`),
  không dùng trimesh vì tường mỏng làm nhân vật lọt vào trong. Mặt đất, lối đi, `GATE_*` vẫn dùng trimesh.
- Nướng ánh sáng (đang thử, mới có B + mặt đất/lối đi/sân bậc): `uit_lightbake.py` nướng nắng, bóng mềm, ánh sáng dội,
  bo cạnh (node Bevel) vào texture; kiểu ánh sáng `LIGHT` = `sang` / `trua` / `chieu` (bảng `PRESETS`, phải khớp
  `src/world/lighting.js`). Object đã nướng có custom prop `baked` → web dùng `MeshBasicMaterial` (không tính đèn,
  không nhận bóng thời gian thực; nhân vật có vệt bóng tròn dưới chân). Bản thử xuất ra `public/models/uit_campus_bakeB*.glb`,
  xem bằng `?model=uit_campus_bakeB_sang&nang=sang` (chưa commit glb thử). Chủ dự án chọn kiểu `sang` (19/11),
  đã đưa vào mô hình chính (B, sân bậc, mặt đất, lối đi; web mặc định nắng sáng). Tòa khác chưa nướng
  (chỉ nướng thêm khi chủ dự án bảo rõ tòa nào). Bản .blend trước khi nướng: `uit_blockout_truoc_nuong.blend`.
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
