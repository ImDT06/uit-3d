import { zoneInfo } from "../data/zones";

// Thanh chon toa cho che do xem rieng (?toa=...)
const LIST = ["A", "B", "C", "D", "E", "CanTin", "CanTin2", "ChotBaoVe", "X2"];

export default function PreviewUi({ name }) {
  return (
    <div className="preview-bar">
      <b>Xem riêng: {zoneInfo(name).title}</b>
      <span>Kéo chuột để xoay, cuộn để phóng to</span>
      <nav>
        {LIST.map((k) => (
          <a key={k} href={`?toa=${k}`} className={name === "BLD_" + k ? "on" : ""}>
            {zoneInfo("BLD_" + k).title}
          </a>
        ))}
        <a href="/">Về trang chủ</a>
      </nav>
    </div>
  );
}
