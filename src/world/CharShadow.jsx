import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useGame, playerPos } from "../game/store";
import { LIGHT } from "./lighting";
import { charShadow, CHAR_LAYER, CHAR_BOX, CHAR_NEAR, CHAR_FAR, CHAR_DIST } from "./charShadowMaterial";

const SIZE = 256;
const dir = new THREE.Vector3(...LIGHT.sun).normalize();
const white = new THREE.Color(1, 1, 1);
const oldColor = new THREE.Color();
const HEIGHTS = [-0.5, 0.1, 0.65]; // m so voi tam than: chan, nguc, dau
const ray = new THREE.Raycaster();
ray.far = 200;

// phan co the dang duoc nang chieu (0..1): ban tia ve phia mat troi, vuong tuong / mai thi la dang trong ram
function sunlit(meshes) {
  let n = 0;
  for (const h of HEIGHTS) {
    ray.ray.origin.set(playerPos.x, playerPos.y + h, playerPos.z);
    ray.ray.direction.copy(dir);
    if (!ray.intersectObjects(meshes, false).length) n++;
  }
  return n / HEIGHTS.length;
}

// Moi khung hinh chup do sau cua rieng nhan vat theo huong nang (xem charShadowMaterial.js). Chi gan khi mo hinh co
// phan da nuong anh sang.
export default function CharShadow() {
  const { target, camera, depth } = useMemo(() => {
    const target = new THREE.WebGLRenderTarget(SIZE, SIZE, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
    const camera = new THREE.OrthographicCamera(-CHAR_BOX, CHAR_BOX, CHAR_BOX, -CHAR_BOX, CHAR_NEAR, CHAR_FAR);
    camera.layers.set(CHAR_LAYER);
    const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide });
    return { target, camera, depth };
  }, []);

  useEffect(() => {
    charShadow.uCharMap.value = target.texture;
    if (import.meta.env.DEV) window.__charShadow = charShadow; // cho script kiem thu
    return () => {
      charShadow.uCharOn.value = 0;
      charShadow.uCharMap.value = null;
      target.dispose();
      depth.dispose();
    };
  }, [target, depth]);

  useFrame(({ gl, scene }, dt) => {
    const { camBlockers, camGround } = useGame.getState();
    charShadow.uCharOn.value = THREE.MathUtils.damp(charShadow.uCharOn.value, sunlit([...camBlockers, ...camGround]), 10, Math.min(dt, 0.05));
    if (charShadow.uCharOn.value < 0.02) return; // trong ram: khoi chup
    camera.position.set(playerPos.x, playerPos.y, playerPos.z).addScaledVector(dir, CHAR_DIST);
    camera.lookAt(playerPos.x, playerPos.y, playerPos.z);
    camera.updateMatrixWorld();
    charShadow.uCharMatrix.value.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);

    // lan ve phu nay khong duoc dung toi anh bong cua mat troi (ve lai se chi con moi nhan vat)
    const old = {
      target: gl.getRenderTarget(),
      alpha: gl.getClearAlpha(),
      auto: gl.shadowMap.autoUpdate,
      needs: gl.shadowMap.needsUpdate,
      background: scene.background,
      override: scene.overrideMaterial,
    };
    gl.getClearColor(oldColor);
    gl.shadowMap.autoUpdate = false;
    gl.shadowMap.needsUpdate = false;
    scene.background = null;
    scene.overrideMaterial = depth;
    gl.setRenderTarget(target);
    gl.setClearColor(white, 1); // trang = do sau xa nhat (khong co gi)
    gl.clear();
    gl.render(scene, camera);
    gl.setRenderTarget(old.target);
    gl.setClearColor(oldColor, old.alpha);
    gl.shadowMap.autoUpdate = old.auto;
    gl.shadowMap.needsUpdate = old.needs;
    scene.background = old.background;
    scene.overrideMaterial = old.override;
  });

  return null;
}
