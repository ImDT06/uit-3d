import { Suspense, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useSettings } from "../game/settings";
import { useGame } from "../game/store";
import Avatar from "./Avatar";

// Nhan vat dieu khien: mo hinh sinh vien (Avatar) + dong tac theo van toc cua ecctrl.
// Goc toa do = tam vien nhong va cham; ban chan o y = -1.0. Mat nhin ve +Z.
// m/s ma ban chan quet tren dat khi dong tac chay o toc do 1x (do trong Blender): phat nhanh theo ti le nay
const STRIDE = { nam: { walk: 1.3, run: 3 }, nu: { walk: 1.05, run: 2.5 } };
const MAX_RATE = 2.8;   // phat nhanh hon nua thi chan quay tit, nhin gia

const local = new THREE.Vector3();
const quat = new THREE.Quaternion();

export default function Student({ controller, hidden = false }) {
  const avatar = useSettings((s) => s.avatar);
  const root = useRef();
  const pose = useRef();
  const st = useRef({ air: 0, speed: 0, off: 0, fly: 0, glide: 0, dive: 0, angle: 0 });

  const drive = (actions, dt) => {
    const c = controller.current;
    if (!c) return;
    const s = st.current;
    const { flying } = useGame.getState();
    const speed = flying ? 0 : c.relativeVelOnPlane ? c.relativeVelOnPlane.length() : 0;
    s.speed = THREE.MathUtils.damp(s.speed, speed, 12, dt);
    // hut dat thoang qua (xuong bac, go go) thi chua tinh la dang bay; nhay len thi tinh ngay
    s.off = flying || c.isOnGround ? 0 : s.off + dt; // dang bay: giu dang dung (nhu Roblox)
    const inAir = s.off > 0.15 || (s.off > 0 && (c.body?.linvel().y ?? 0) > 1.5);
    s.air = THREE.MathUtils.damp(s.air, inAir ? 1 : 0, 14, dt);
    const move = THREE.MathUtils.smoothstep(s.speed, 0.1, 1.2);
    const run = THREE.MathUtils.smoothstep(s.speed, 1.6, 3);
    // bay: lo lung <-> bay toi theo toc do, hoa dan vao / ra khoi che do bay
    const v = c.body?.linvel();
    s.fly = THREE.MathUtils.damp(s.fly, flying ? 1 : 0, 8, dt);
    s.glide = THREE.MathUtils.damp(s.glide, flying && v ? THREE.MathUtils.smoothstep(Math.hypot(v.x, v.y, v.z), 0.5, 7) : 0, 6, dt);
    actions.Hover.setEffectiveWeight(s.fly * (1 - s.glide));
    // lao xuong: dang bay toi ma huong bay chuc xuong (ha thang dung bang Q thi van dung)
    const flat = v ? Math.hypot(v.x, v.z) : 0;
    const angle = v ? Math.atan2(-v.y, flat) : 0; // goc chuc xuong
    // van toc toi truoc theo huong mat (lui khi shift lock thi khong tinh la lao)
    const q = c.body?.rotation();
    const ahead = v && q ? local.set(v.x, 0, v.z).applyQuaternion(quat.set(q.x, q.y, q.z, q.w).invert()).z : 0;
    const dive = flying ? THREE.MathUtils.smoothstep(angle, 0.12, 0.5) * THREE.MathUtils.smoothstep(ahead, 1, 6) : 0;
    s.dive = THREE.MathUtils.damp(s.dive, dive, 6, dt);
    s.angle = THREE.MathUtils.damp(s.angle, Math.max(0, angle), 8, dt);
    actions.Fly.setEffectiveWeight(s.fly * s.glide * (1 - s.dive));
    actions.Dive.setEffectiveWeight(s.fly * s.glide * s.dive);
    s.air *= 1 - s.fly;
    const ground = (1 - s.air) * (1 - s.fly);
    actions.Idle.setEffectiveWeight((1 - move) * ground);
    actions.Walk.setEffectiveWeight(move * (1 - run) * ground);
    actions.Run.setEffectiveWeight(move * run * ground);
    // tren khong: dang di len thi co chan (Jump), roi xuong thi duoi chan (Fall)
    const up = THREE.MathUtils.smoothstep(c.body?.linvel().y ?? 0, -2, 2);
    actions.Jump.setEffectiveWeight(s.air * up * (1 - s.fly));
    actions.Fall.setEffectiveWeight(s.air * (1 - up) * (1 - s.fly));
    const stride = STRIDE[avatar?.gender || "nam"];
    actions.Walk.timeScale = THREE.MathUtils.clamp(s.speed / stride.walk, 0.7, MAX_RATE);
    actions.Run.timeScale = THREE.MathUtils.clamp(s.speed / stride.run, 0.9, MAX_RATE);
  };

  useFrame((_, dt) => {
    const c = controller.current;
    if (!c || !root.current) return;
    const d = Math.min(dt, 0.05);
    // nghieng nguoi vao trong khi re (theo toc do quay quanh truc dung)
    const speed = st.current.speed;
    const turn = c.currAngVel ? c.currAngVel.y : 0;
    const lean = THREE.MathUtils.clamp(-turn * speed * 0.025, -0.3, 0.3);
    root.current.rotation.z = THREE.MathUtils.damp(root.current.rotation.z, speed > 0.3 && c.isOnGround ? lean : 0, 6, d);
  });

  // bay: nghieng theo duong bay, do them ve phia dang bay, nghieng sang ben khi bay ngang, nhap nho nhe
  useFrame(({ clock }, delta) => {
    const g = pose.current;
    const body = controller.current?.body;
    if (!g || !body) return;
    const dt = Math.min(delta, 0.05);
    let tilt = 0, roll = 0, bob = 0;
    if (useGame.getState().flying) {
      const v = body.linvel();
      const q = body.rotation();
      // van toc theo huong nguoi: z = toi, x = sang trai
      local.set(v.x, 0, v.z).applyQuaternion(quat.set(q.x, q.y, q.z, q.w).invert());
      // nghieng theo duong bay (chuc xuong / ngoc len) + do them ve phia truoc
      tilt = Math.atan2(-v.y, Math.abs(local.z) + 0.001) * Math.sign(local.z)
        * THREE.MathUtils.smoothstep(Math.abs(local.z), 1, 6)
        + THREE.MathUtils.clamp(local.z / 8, -0.5, 1) * 0.55;
      roll = THREE.MathUtils.clamp(-local.x / 8, -1, 1) * 0.45;
      // lao xuong: nam han theo duong bay, dau di truoc
      tilt = THREE.MathUtils.lerp(tilt, Math.PI / 2 + st.current.angle, st.current.dive);
      bob = Math.sin(clock.elapsedTime * 2.4) * 0.07 * (1 - st.current.glide);
    }
    g.rotation.x = THREE.MathUtils.damp(g.rotation.x, tilt, 7, dt);
    g.rotation.z = THREE.MathUtils.damp(g.rotation.z, roll, 7, dt);
    g.position.y = THREE.MathUtils.damp(g.position.y, bob, 10, dt);
  });

  return (
    <group ref={root} visible={!hidden}>
      <group ref={pose}>
      {/* tai mo hinh rieng, khong lam treo ca canh vat ly */}
      <Suspense fallback={null}>
        <group position={[0, -0.98, 0]} scale={0.97}>
          <Avatar key={avatar?.gender} gender={avatar?.gender} hair={avatar?.hair} drive={drive} />
        </group>
      </Suspense>
      </group>
    </group>
  );
}
