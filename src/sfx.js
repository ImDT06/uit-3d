// Am thanh tong hop bang Web Audio (khong can file am thanh)
import { useSettings } from "./settings";

let ctx = null;
let noise = null;

export function unlockAudio() {
  if (ctx) {
    if (ctx.state === "suspended") ctx.resume();
    return;
  }
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  ctx = new AC();
  // 1 giay nhieu trang dung lai cho moi tieng
  noise = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
  const d = noise.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
}

function burst({ freq, q = 1, dur, gain, type = "lowpass", pitchJitter = 0.15 }) {
  const vol = useSettings.getState().volume;
  if (!ctx || ctx.state !== "running" || vol <= 0) return;
  const t = ctx.currentTime;
  const src = ctx.createBufferSource();
  src.buffer = noise;
  src.playbackRate.value = 1 + (Math.random() - 0.5) * pitchJitter;
  const f = ctx.createBiquadFilter();
  f.type = type;
  f.frequency.value = freq * (1 + (Math.random() - 0.5) * pitchJitter);
  f.Q.value = q;
  const g = ctx.createGain();
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(gain * vol, t + 0.008);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  src.connect(f).connect(g).connect(ctx.destination);
  src.start(t, Math.random() * 0.5);
  src.stop(t + dur + 0.02);
}

export const sfx = {
  step: (run) => burst({ freq: run ? 900 : 700, q: 0.8, dur: run ? 0.09 : 0.11, gain: run ? 0.35 : 0.25 }),
  jump: () => burst({ freq: 1400, q: 0.7, dur: 0.18, gain: 0.18, type: "bandpass" }),
  land: (strength = 1) => burst({ freq: 320, q: 0.9, dur: 0.16, gain: Math.min(0.3 + strength * 0.25, 0.7) }),
  click: () => burst({ freq: 2500, q: 2, dur: 0.04, gain: 0.15, type: "bandpass", pitchJitter: 0 }),
};
