import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame, useThree } from "@react-three/fiber";
import { Sky } from "@react-three/drei";
import { LIGHT } from "./lighting";

const SKY_COLOR = "#bfe3ff";
const lerp = THREE.MathUtils.lerp;

// Bau troi + nen + suong mu.
// Trang chu: nen trong suot (thay nen CSS), khong suong mu, khong bau troi -> mo hinh nhu sa ban.
// Tham quan/kham pha: troi xanh + suong mu. Chuyen DAN cung luc camera bay vao (~1,5 s): bat dot ngot thi
// luc camera con o xa, ca mo hinh bi suong mu phu trang, nhin nhu tai canh moi chu khong phai bay vao.
// Suong mu va bau troi luon gan san, chi doi thong so: them/bot suong mu bat three bien dich lai shader
// moi vat lieu (dung hinh ~0,7 s).
export default function Atmosphere({ on, fog = true }) {
  const gl = useThree((s) => s.gl);
  const k = useRef(on ? 1 : 0);
  const fogRef = useRef();
  const sky = useRef();
  const color = useMemo(() => new THREE.Color(SKY_COLOR), []);
  const fade = useMemo(() => ({ value: 1 }), []);

  // shader bau troi goc luon xuat alpha = 1: them uniform uFade de lam mo dan
  useLayoutEffect(() => {
    const m = sky.current?.material;
    if (!m) return;
    m.transparent = true;
    m.onBeforeCompile = (sh) => {
      sh.uniforms.uFade = fade;
      sh.fragmentShader = sh.fragmentShader
        .replace("void main()", "uniform float uFade;\nvoid main()")
        .replace("gl_FragColor = vec4( retColor, 1.0 );", "gl_FragColor = vec4( retColor, uFade );");
    };
    m.needsUpdate = true;
    // ve truoc moi vat trong suot khac (kinh...), neu khong troi se ve de len kinh
    sky.current.renderOrder = -1;
  }, [fade]);

  useFrame((_, dt) => {
    const target = on ? 1 : 0;
    k.current = THREE.MathUtils.damp(k.current, target, 2.2, dt);
    if (Math.abs(k.current - target) < 0.002) k.current = target;
    const t = k.current;
    gl.setClearColor(color, t);
    // suong mu day len cham hon (t^2): luc camera con xa thi chua phu mo hinh
    if (fogRef.current) {
      fogRef.current.near = lerp(3000, 150, t * t);
      fogRef.current.far = lerp(6000, 650, t * t);
    }
    if (sky.current) {
      fade.value = t * t;
      sky.current.visible = t > 0.001;
    }
  });

  return (
    <>
      {fog && <fog ref={fogRef} attach="fog" args={[SKY_COLOR, 3000, 6000]} />}
      <Sky ref={sky} sunPosition={LIGHT.skySun} />
    </>
  );
}
