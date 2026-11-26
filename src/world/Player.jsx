import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { useKeyboardControls, CameraControlsImpl } from "@react-three/drei";
import * as THREE from "three";
import { Ecctrl } from "ecctrl";
import { EcctrlCameraControls } from "ecctrl/camera";
import { useJoystickStore, useButtonStore } from "ecctrl/input";
import { useGame, playerPos } from "../game/store";
import { useSettings } from "../game/settings";
import { doAction } from "../game/actions";
import { sfx } from "../game/sfx";
import Student from "./Student";

const SHOULDER_OFFSET = 1.2;  // m: lech camera sang phai khi shift lock
const MOUSE_SENS = 0.003;     // rad / pixel khi khoa chuot (nhan voi do nhay trong cai dat)
const PAD_SENS = 2.6;         // rad / giay khi gat het cam phai tay cam
const THIRD_MIN_DIST = 3;
const FIRST_DIST = 0.05;
const HEAD_HEIGHT = 0.7;      // m tren tam vien nhong
const COYOTE_TIME = 0.12;     // s: van nhay duoc ngay sau khi buoc khoi mep
const JUMP_BUFFER = 0.15;     // s: bam nhay som truoc khi cham dat van tinh
const DOUBLE_TAP = 0.3;       // s: go dup phim tien de chay
const CAM_FOLLOW_DELAY = 1.2; // s: khong cham camera bao lau thi camera tu ve sau lung
const _zp = new THREE.Vector3();
const ZONE_MARGIN = 8;        // m: dung cach toa nha bao nhieu thi tinh la "o gan"

const wrapAngle = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const dz = (v, d = 0.15) => (Math.abs(v) < d ? 0 : (v - Math.sign(v) * d) / (1 - d));
const fwd = new THREE.Vector3();

export default function Player() {
  const spawn = useGame((s) => s.spawn);
  const buildings = useGame((s) => s.buildings);
  const camBlockers = useGame((s) => s.camBlockers);
  const tuning = useGame((s) => s.tuning);
  const teleport = useGame((s) => s.teleport);
  const shiftLock = useGame((s) => s.shiftLock);
  const viewMode = useGame((s) => s.viewMode);
  const menuOpen = useGame((s) => s.menuOpen);
  const mapOpen = useGame((s) => s.mapOpen);
  const adminOpen = useGame((s) => s.adminOpen);
  const sens = useSettings((s) => s.mouseSens);
  const invertY = useSettings((s) => s.invertY);

  const ecctrl = useRef(null);
  // chi khi chay dev: cho script kiem thu dieu khien nhan vat (khong co trong ban build)
  useEffect(() => {
    if (import.meta.env.DEV) window.__uitPlayer = ecctrl;
  }, []);
  const cam = useRef(null);
  const [, getKeys] = useKeyboardControls();
  const gl = useThree((s) => s.gl);
  const t = useRef({
    lastZoneCheck: 0,
    lastManualCam: -10,
    lastGround: 0,
    jumpPressedAt: -10,
    prevJumpKey: false,
    jumpedAt: -10,
    prevFwd: false,
    lastFwdTap: -10,
    tapSprint: false,
    idleSince: 0,
    wasOnGround: true,
    airStart: 0,
    stepDist: 0,
    lastPos: null,
    pad: [],
  });

  const first = viewMode === "first";
  const overlay = menuOpen || mapOpen || adminOpen;
  const wantLock = (shiftLock || first) && !overlay;

  // ---- Dich chuyen (admin) ----
  useEffect(() => {
    const c = ecctrl.current;
    if (!teleport || !c?.body) return;
    const [x, y, z] = teleport.pos;
    c.body.setTranslation({ x, y, z }, true);
    c.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    cam.current?.moveTo(x, y + 0.8, z, false);
  }, [teleport]);

  // ---- Camera ban dau: sau lung nhan vat, quay lung ve toa nha gan nhat ----
  useEffect(() => {
    if (!spawn || !cam.current) return;
    let dx = 0;
    let dzz = 1;
    let best = Infinity;
    for (const b of buildings) {
      const cx = (b.box.min.x + b.box.max.x) / 2;
      const cz = (b.box.min.z + b.box.max.z) / 2;
      const d = Math.hypot(cx - spawn[0], cz - spawn[2]);
      if (d < best && d > 0.01) {
        best = d;
        dx = (spawn[0] - cx) / d;
        dzz = (spawn[2] - cz) / d;
      }
    }
    cam.current.setLookAt(spawn[0] - dx * 10, spawn[1] + 5, spawn[2] - dzz * 10, spawn[0], spawn[1], spawn[2], false);
  }, [spawn, buildings]);

  // ---- Camera khong xuyen tuong ----
  useEffect(() => {
    if (cam.current) cam.current.colliderMeshes = first ? [] : camBlockers;
  }, [camBlockers, spawn, first]);

  // ---- Do nhay / dao truc Y khi keo chuot phai, cam ung ----
  useEffect(() => {
    const c = cam.current;
    if (!c) return;
    c.azimuthRotateSpeed = sens;
    c.polarRotateSpeed = invertY ? -sens : sens;
  }, [sens, invertY, spawn]);

  // ---- Nut chuot, focal offset, khoa huong nhan vat theo che do camera ----
  useEffect(() => {
    const c = cam.current;
    if (!c) return;
    const A = CameraControlsImpl.ACTION;
    c.mouseButtons.left = A.NONE;
    c.mouseButtons.middle = A.NONE;
    c.mouseButtons.right = wantLock ? A.NONE : A.ROTATE;
    c.mouseButtons.wheel = A.DOLLY;
    c.touches.one = A.TOUCH_ROTATE;
    c.touches.two = A.TOUCH_DOLLY;
    c.touches.three = A.NONE;
    c.setFocalOffset(shiftLock && !first ? SHOULDER_OFFSET : 0, 0, 0, true);
    ecctrl.current?.setLockForward?.(shiftLock || first);
    if (first) {
      c.minDistance = 0.01;
      c.dollyTo(FIRST_DIST, true);
    } else {
      c.minDistance = THIRD_MIN_DIST;
      if (c.distance < THIRD_MIN_DIST + 0.5) c.dollyTo(6, true);
    }
  }, [spawn, wantLock, shiftLock, first]);

  // ---- Khoa chuot (pointer lock) ----
  useEffect(() => {
    if (!spawn) return;
    const canvas = gl.domElement;
    if (!wantLock) {
      if (document.pointerLockElement) document.exitPointerLock();
      return;
    }
    // trinh duyet chi cho khoa chuot sau thao tac cua nguoi dung; that bai thi bo qua
    const lock = () => {
      // man hinh cam ung (body.touch, xem ui/TouchControls.jsx): khong khoa chuot, shift lock chi xoay nhan vat theo camera
      if (document.body.classList.contains("touch")) return;
      try {
        const r = canvas.requestPointerLock?.();
        if (r && r.catch) r.catch(() => {});
      } catch {}
    };
    lock();
    const onMove = (e) => {
      if (document.pointerLockElement !== canvas) return;
      const s = useSettings.getState();
      const k = MOUSE_SENS * s.mouseSens;
      cam.current?.rotate(-e.movementX * k, -e.movementY * k * (s.invertY ? -1 : 1), false);
      t.current.lastManualCam = performance.now() / 1000;
      useGame.getState().tutorialEvent("camera");
    };
    // bam Esc khi dang khoa chuot: trinh duyet nha chuot -> mo menu (giong Roblox)
    let wasLocked = document.pointerLockElement === canvas;
    const onLockChange = () => {
      if (document.pointerLockElement === canvas) wasLocked = true;
      else if (wasLocked) {
        wasLocked = false;
        if (!useGame.getState().anyOverlay()) useGame.getState().setUi({ menuOpen: true });
      }
    };
    // bam vao canvas khi chua khoa (vd lan khoa truoc bi tu choi) -> thu lai
    const onDown = () => {
      if (document.pointerLockElement !== canvas) lock();
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("pointerlockchange", onLockChange);
    canvas.addEventListener("mousedown", onDown);
    return () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("pointerlockchange", onLockChange);
      canvas.removeEventListener("mousedown", onDown);
    };
  }, [spawn, wantLock, gl]);

  // ---- Lan chuot sat vao -> goc nhin thu nhat, lan ra -> thu ba (giong Roblox) ----
  // ---- Keo chuot / vuot man hinh -> ghi nhan da xoay camera tay ----
  useEffect(() => {
    const c = cam.current;
    if (!c) return;
    const canvas = gl.domElement;
    const onWheel = (e) => {
      const g = useGame.getState();
      if (g.anyOverlay()) return;
      if (g.viewMode === "first" && e.deltaY > 0) g.setViewMode("third");
      else if (g.viewMode === "third" && e.deltaY < 0 && c.distance <= THIRD_MIN_DIST + 0.05) g.setViewMode("first");
    };
    const onControl = () => {
      t.current.lastManualCam = performance.now() / 1000;
      useGame.getState().tutorialEvent("camera");
    };
    canvas.addEventListener("wheel", onWheel, { passive: true });
    c.addEventListener("controlstart", onControl);
    c.addEventListener("control", onControl);
    return () => {
      canvas.removeEventListener("wheel", onWheel);
      c.removeEventListener("controlstart", onControl);
      c.removeEventListener("control", onControl);
    };
  }, [spawn, gl]);

  useFrame((state, delta) => {
    const c = ecctrl.current;
    const cc = cam.current;
    if (!c || !cc) return;
    const dt = Math.min(delta, 0.05);
    const now = state.clock.elapsedTime;
    const T = t.current;
    const g = useGame.getState();
    const settings = useSettings.getState();
    const paused = g.menuOpen || g.mapOpen;

    // ---------- 1. Tay cam (Gamepad API chuan cua trinh duyet) ----------
    let padMove = { x: 0, y: 0 };
    let padJump = false;
    const pads = navigator.getGamepads ? [...navigator.getGamepads()] : [];
    const pad = pads.find((x) => x && x.connected);
    if (pad) {
      const b = pad.buttons.map((x) => x.pressed);
      const edge = (i) => b[i] && !T.pad[i];
      // A=0 nhay, B=1 / L3=10 chay, X=2 tuong tac, Y=3 doi goc nhin, RB=5 shift lock, Back=8 ban do, Start=9 menu
      if (edge(9)) doAction("menu");
      if (edge(8)) doAction("map");
      if (!paused) {
        if (edge(2)) doAction("interact");
        if (edge(3)) doAction("view");
        if (edge(5)) doAction("shiftLock");
        if (edge(1) || edge(10)) doAction("runToggle");
        padJump = !!b[0];
        padMove = { x: dz(pad.axes[0] || 0), y: -dz(pad.axes[1] || 0) };
        const rx = dz(pad.axes[2] || 0);
        const ry = dz(pad.axes[3] || 0);
        if (rx || ry) {
          const s = PAD_SENS * settings.mouseSens * dt;
          cc.rotate(-rx * s, -ry * s * 0.7 * (settings.invertY ? -1 : 1), false);
          T.lastManualCam = performance.now() / 1000;
          g.tutorialEvent("camera");
        }
      }
      T.pad = b;
    }

    // ---------- 2. Ban phim + joystick cam ung ----------
    const k = paused ? {} : getKeys();
    const joy = useJoystickStore.getState().joysticks.move;
    const btn = useButtonStore.getState().buttons;
    const joystick = !paused && joy && (joy.x || joy.y) ? { x: joy.x, y: joy.y } : padMove;
    const hasMove = k.forward || k.backward || k.leftward || k.rightward || joystick.x || joystick.y;

    // go dup W de chay (giong Minecraft)
    if (k.forward && !T.prevFwd) {
      if (now - T.lastFwdTap < DOUBLE_TAP) T.tapSprint = true;
      T.lastFwdTap = now;
    }
    if (!k.forward) T.tapSprint = false;
    T.prevFwd = !!k.forward;

    // dung yen 1 giay thi tu tat che do chay
    if (hasMove) T.idleSince = now;
    else if (g.runToggled && now - T.idleSince > 1) g.setRunToggled(false);

    const run = (settings.holdToRun ? !!k.run : g.runToggled) || T.tapSprint || !!btn.run;

    // nhay: luu dem (bam som van tinh) + coyote time (vua roi khoi mep van nhay duoc)
    const jumpKey = !paused && !!(k.jump || btn.jump || padJump);
    if (jumpKey && !T.prevJumpKey) T.jumpPressedAt = now;
    T.prevJumpKey = jumpKey;
    const onGround = !!c.isOnGround;
    if (onGround) T.lastGround = now;
    const buffered = now - T.jumpPressedAt < JUMP_BUFFER;
    if (buffered && !onGround && now - T.lastGround < COYOTE_TIME && now - T.jumpedAt > 0.3) {
      const v = c.body.linvel();
      c.body.setLinvel({ x: v.x, y: tuning.jump, z: v.z }, true);
      T.jumpedAt = now;
      T.jumpPressedAt = -10;
      sfx.jump();
      g.tutorialEvent("jump");
    } else if (buffered && onGround && now - T.jumpedAt > 0.3) {
      T.jumpedAt = now;
      sfx.jump();
      g.tutorialEvent("jump");
    }

    c.setMovement({
      forward: !!k.forward,
      backward: !!k.backward,
      leftward: !!k.leftward,
      rightward: !!k.rightward,
      run,
      jump: jumpKey || buffered,
      joystick,
    });

    // ---------- 3. Camera bam theo nhan vat ----------
    const p = c.currPos;
    cc.moveTo(p.x, p.y + (g.viewMode === "first" ? HEAD_HEIGHT : 0.8), p.z, true);

    fwd.set(0, 0, 1).applyQuaternion(c.currQuat);
    const speed = c.relativeVelOnPlane ? c.relativeVelOnPlane.length() : 0;
    playerPos.x = p.x;
    playerPos.y = p.y;
    playerPos.z = p.z;
    playerPos.yaw = Math.atan2(fwd.x, fwd.z);
    playerPos.camYaw = cc.azimuthAngle + Math.PI;
    playerPos.running = run && speed > tuning.walk + 0.5;

    // camera tu xoay ve sau lung khi dang di toi va khong cham chuot (giong GTA / Zelda)
    const goingForward = (k.forward && !k.backward) || joystick.y > 0.3;
    if (
      settings.camFollow && !paused && g.viewMode === "third" && !g.shiftLock &&
      goingForward && speed > 1 && performance.now() / 1000 - T.lastManualCam > CAM_FOLLOW_DELAY
    ) {
      const target = Math.atan2(-fwd.x, -fwd.z);
      const diff = wrapAngle(target - cc.azimuthAngle);
      cc.rotate(diff * Math.min(1, dt * 1.2), 0, false);
    }

    // FOV rong ra mot chut khi chay
    const camera = state.camera;
    const targetFov = settings.fov + (playerPos.running ? 7 : 0);
    if (Math.abs(camera.fov - targetFov) > 0.05) {
      camera.fov = THREE.MathUtils.damp(camera.fov, targetFov, 5, dt);
      camera.updateProjectionMatrix();
    }

    // ---------- 4. Am thanh buoc chan / tiep dat ----------
    if (T.lastPos) {
      const moved = Math.hypot(p.x - T.lastPos.x, p.z - T.lastPos.z);
      if (onGround && speed > 0.5) {
        T.stepDist += moved;
        if (T.stepDist > 0.55 + speed * 0.09) {
          T.stepDist = 0;
          sfx.step(playerPos.running);
        }
      }
      if (moved > 0.02 && hasMove) g.tutorialEvent("move");
    }
    T.lastPos = { x: p.x, z: p.z };
    if (!onGround && T.wasOnGround) T.airStart = now;
    if (onGround && !T.wasOnGround && now - T.airStart > 0.25) sfx.land(Math.min((now - T.airStart) / 1.2, 1));
    T.wasOnGround = onGround;

    // ---------- 5. Roi khoi ban do -> ve diem xuat phat ----------
    if (p.y < -20 && spawn) {
      c.body.setTranslation({ x: spawn[0], y: spawn[1], z: spawn[2] }, true);
      c.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    }

    // ---------- 6. Dang o gan toa nao (5 lan/giay) + da toi diem danh dau chua ----------
    if (now - T.lastZoneCheck > 0.2) {
      T.lastZoneCheck = now;
      let best = null;
      let bestD = ZONE_MARGIN;
      if (g.zones.length) {
        // co vung ZONE_ tu Blender: dung trong hop nao (chong lan thi lay hop nho nhat)
        let bestV = Infinity;
        for (const z of g.zones) {
          _zp.set(p.x, p.y, p.z).applyMatrix4(z.inv);
          if (Math.abs(_zp.x) <= 1 && Math.abs(_zp.y) <= 1 && Math.abs(_zp.z) <= 1 && z.volume < bestV) {
            bestV = z.volume;
            best = z.name;
          }
        }
      } else for (const b of buildings) {
        const dx = Math.max(b.box.min.x - p.x, 0, p.x - b.box.max.x);
        const dzz = Math.max(b.box.min.z - p.z, 0, p.z - b.box.max.z);
        const d = Math.hypot(dx, dzz);
        if (d < bestD) {
          bestD = d;
          best = b.name;
        }
      }
      g.setZone(best);
      if (g.waypoint && Math.hypot(g.waypoint.x - p.x, g.waypoint.z - p.z) < 4) g.setWaypoint(null);
    }
  });

  if (!spawn) return null;

  return (
    <>
      <Ecctrl
        ref={ecctrl}
        position={spawn}
        capsuleHalfHeight={0.5}
        capsuleRadius={0.3}
        maxWalkVel={tuning.walk}
        maxRunVel={tuning.run}
        jumpVel={tuning.jump}
        enableToggleRun={false}
        rayHitForgiveness={0.35}
        ccd
        accDeltaTime={0.15}
        decDeltaTime={0.12}
      >
        <Student controller={ecctrl} hidden={first} />
      </Ecctrl>
      <EcctrlCameraControls
        ref={cam}
        makeDefault
        smoothTime={0.15}
        draggingSmoothTime={0.08}
        dollySpeed={0.6}
        minDistance={THIRD_MIN_DIST}
        maxDistance={40}
        maxPolarAngle={Math.PI * 0.48}
      />
    </>
  );
}
