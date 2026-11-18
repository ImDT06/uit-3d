import { useEffect } from "react";
import { useGame } from "./store";
import { bindLabel, useSettings } from "./settings";

// Huong dan lan dau: tung buoc, tu qua buoc khi nguoi choi lam dung
function steps() {
  const mv = ["forward", "leftward", "backward", "rightward"].map(bindLabel).map((s) => s.split(" / ")[0]).join(" ");
  return [
    { id: "move", text: <>Dùng <kbd>{mv}</kbd> để đi lại</> },
    { id: "jump", text: <>Nhấn <kbd>{bindLabel("jump")}</kbd> để nhảy</> },
    { id: "camera", text: <>Giữ <kbd>chuột phải</kbd> và kéo để xoay camera</> },
    { id: "shiftLock", text: <>Nhấn <kbd>{bindLabel("shiftLock")}</kbd> để bật shift lock (ghim chuột giữa màn hình), nhấn lại để tắt</> },
    { id: "interact", text: <>Lại gần một tòa nhà và nhấn <kbd>{bindLabel("interact")}</kbd> để xem thông tin</> },
  ];
}

export default function Tutorial() {
  const done = useGame((s) => s.tutorialDone);
  const seen = useGame((s) => s.tutorialSeen);
  const finish = useGame((s) => s.finishTutorial);
  const spawn = useGame((s) => s.spawn);
  useSettings((s) => s.binds); // cap nhat khi doi phim
  const list = steps();
  const idx = list.findIndex((s) => !seen[s.id]);

  useEffect(() => {
    if (!done && spawn && idx === -1) {
      const t = setTimeout(finish, 2500);
      return () => clearTimeout(t);
    }
  }, [done, spawn, idx, finish]);

  if (done || !spawn) return null;
  return (
    <div className="tutorial">
      <div className="tutorial-step">
        {idx === -1 ? (
          <b>Xong rồi! Chúc bạn khám phá vui vẻ 🎉</b>
        ) : (
          <>
            <span className="tutorial-n">{idx + 1}/{list.length}</span>
            {list[idx].text}
          </>
        )}
      </div>
      <div className="tutorial-dots">
        {list.map((s, i) => (
          <i key={s.id} className={seen[s.id] ? "on" : i === idx ? "cur" : ""} />
        ))}
      </div>
      <button className="tutorial-skip" onClick={finish}>Bỏ qua</button>
    </div>
  );
}
