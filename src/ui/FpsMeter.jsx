import { useEffect, useState } from "react";

// Bo dem FPS nho o goc man hinh, bat bang ?fps tren URL (de do tren dien thoai that, khong can ban phim)
export const fpsEnabled = new URLSearchParams(window.location.search).has("fps");

export default function FpsMeter() {
  const [fps, setFps] = useState(0);
  useEffect(() => {
    let frames = 0, raf;
    let last = performance.now();
    const loop = (now) => {
      frames++;
      if (now - last >= 1000) {
        setFps(Math.round((frames * 1000) / (now - last)));
        frames = 0;
        last = now;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);
  const color = fps >= 50 ? "#3ddc84" : fps >= 30 ? "#ffd23f" : "#ff5a5a";
  return (
    <div className="fps-meter" style={{ color }}>
      {fps} FPS
    </div>
  );
}
