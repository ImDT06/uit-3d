import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    // File chinh (three.js + React Three Fiber + drei, ~1,3 MB, nen ~360 KB) va file kham pha
    // (Rapier co WebAssembly nhung san, ~2,3 MB, tai ngam sau) khong chia nho hon duoc nua.
    chunkSizeWarningLimit: 2500,
  },
});
