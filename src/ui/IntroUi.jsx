import { useEffect } from "react";
import { useGame } from "../game/store";
import { ZONES } from "../data/zones";

// Giao dien trang chu + the tham quan
export default function IntroUi() {
  const mode = useGame((s) => s.mode);
  const step = useGame((s) => s.tourStep);
  const stops = useGame((s) => s.tourStops);
  const setMode = useGame((s) => s.setMode);
  const setStep = useGame((s) => s.setTourStep);
  // chi dem cac toa co trong mo hinh (moi toa la mot diem tham quan); mo hinh chua tai xong thi de trong
  const zoneCount = stops.filter((s) => ZONES[s.key]).length || "…";

  // phim tat: Enter bat dau / tiep, mui ten chuyen diem, Esc quay lai
  useEffect(() => {
    if (mode === "explore") return;
    const onKey = (e) => {
      const g = useGame.getState();
      if (g.mode === "intro") {
        if (e.code === "Enter" || e.code === "Space") g.setMode("tour", 0);
        return;
      }
      const last = g.tourStops.length - 1;
      if (e.code === "ArrowRight" || e.code === "KeyD" || e.code === "Space") {
        e.preventDefault();
        if (g.tourStep < last) g.setTourStep(g.tourStep + 1);
      } else if (e.code === "ArrowLeft" || e.code === "KeyA") {
        if (g.tourStep > 0) g.setTourStep(g.tourStep - 1);
      } else if (e.code === "Enter" && g.tourStep === last) g.setMode("explore");
      else if (e.code === "Escape") g.setMode("intro");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode]);

  if (mode === "intro") {
    return (
      <div className="intro">
        <div className="intro-hero">
          <div className="intro-eyebrow">Trường ĐH Công nghệ Thông tin · ĐHQG-HCM</div>
          <h1>
            Khám phá <span>UIT</span>
            <br />
            trong thế giới 3D
          </h1>
          <p>
            Dạo quanh khuôn viên như một game thế giới mở: đi giữa các tòa nhà, xem thông tin từng khu vực, làm nhiệm
            vụ và tìm những điều bất ngờ.
          </p>
          <div className="intro-actions">
            <button className="btn-primary" onClick={() => setMode("tour", 0)}>
              Bắt đầu tham quan <span aria-hidden>→</span>
            </button>
            <button className="btn-ghost" onClick={() => setMode("explore")}>
              Vào khám phá ngay
            </button>
          </div>
          <div className="intro-hint">hoặc bấm vào một tòa nhà trên mô hình</div>
          <ul className="intro-stats">
            <li>
              <b>{zoneCount}</b> khu vực
            </li>
            <li>
              <b>3D</b> đi · chạy · nhảy
            </li>
            <li>
              <b>PC</b> & điện thoại
            </li>
          </ul>
        </div>
        <div className="intro-foot">Dự án sinh viên · không phải trang chính thức của trường</div>
      </div>
    );
  }

  if (mode === "tour" && stops.length) {
    const s = stops[Math.min(step, stops.length - 1)];
    const last = stops.length - 1;
    return (
      <div className="tour">
        <div className="tour-top">
          <button className="tour-back" onClick={() => setMode("intro")}>
            ← Trang chủ
          </button>
          <button className="tour-skip" onClick={() => setMode("explore")}>
            Bỏ qua, vào khám phá
          </button>
        </div>
        <div className="tour-card" key={s.key}>
          <div className="tour-count">
            {String(step + 1).padStart(2, "0")} <span>/ {String(stops.length).padStart(2, "0")}</span>
          </div>
          {s.image && <img src={s.image} alt="" />}
          <div className="zone-sub">{s.subtitle || "Khu vực"}</div>
          <h2>{s.title}</h2>
          <p>{s.description || "Thông tin về khu vực này đang được cập nhật."}</p>
          <div className="tour-dots">
            {stops.map((x, i) => (
              <button
                key={x.key}
                className={i === step ? "on" : i < step ? "done" : ""}
                onClick={() => setStep(i)}
                title={x.title}
              />
            ))}
          </div>
          <div className="tour-nav">
            <button className="btn-ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>
              ←
            </button>
            {step < last ? (
              <button className="btn-primary" onClick={() => setStep(step + 1)}>
                Tiếp theo →
              </button>
            ) : (
              <button className="btn-primary" onClick={() => setMode("explore")}>
                Vào khám phá 3D →
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }
  return null;
}
