import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
// thu tu nap co y nghia: hud.css ghi de .minimap cua map.css tren man hinh cam ung
import "./styles/base.css";
import "./styles/map.css";
import "./styles/menu.css";
import "./styles/admin.css";
import "./styles/hud.css";
import "./styles/intro.css";
import "./styles/picker.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
