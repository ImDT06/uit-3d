// Bong rieng cua nhan vat tren be mat DA NUONG anh sang (vat lieu khong nhan bong thoi gian thuc).
// CharShadow.jsx chup do sau cua nhan vat nhin tu huong mat troi vao mot anh nho; vat lieu da nuong tra anh do
// de lam toi diem nam "sau lung" nhan vat. Nhan vat dung trong ram (tia ve mat troi bi che) thi khong ve bong.
// Khong import Rapier: campusModel.js (trang chu cung dung) goi receiveCharShadow.
import * as THREE from "three";

export const CHAR_LAYER = 2;      // luoi nhan vat bat them lop nay de chup rieng
export const CHAR_BOX = 1.6;      // m: nua canh khung chup (du bao ca nguoi)
export const CHAR_NEAR = 0.1;
export const CHAR_FAR = 20;
export const CHAR_DIST = 5;       // m: may chup cach tam nhan vat ve phia mat troi
const REACH = 7;                  // m: bong keo xa toi da (khong xuyen xuong tang duoi)

export const charShadow = {
  uCharMap: { value: null },
  uCharMatrix: { value: new THREE.Matrix4() },
  uCharOn: { value: 0 },
};

const f = (x) => x.toFixed(6);

export function receiveCharShadow(material) {
  material.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, charShadow);
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vCharPos;")
      .replace("#include <project_vertex>", "#include <project_vertex>\nvCharPos = (modelMatrix * vec4(transformed, 1.0)).xyz;");
    sh.fragmentShader = sh.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
#include <packing>
uniform sampler2D uCharMap;
uniform mat4 uCharMatrix;
uniform float uCharOn;
varying vec3 vCharPos;
float charShade() {
  vec3 p = (uCharMatrix * vec4(vCharPos, 1.0)).xyz * 0.5 + 0.5;
  if (uCharOn < 0.02 || p.x <= 0.0 || p.x >= 1.0 || p.y <= 0.0 || p.y >= 1.0 || p.z >= 1.0) return 0.0;
  float s = 0.0;
  // 9 mau lay quanh: mep bong mem
  for (int i = -1; i <= 1; i++) for (int j = -1; j <= 1; j++) {
    float d = unpackRGBAToDepth(texture2D(uCharMap, p.xy + vec2(float(i), float(j)) / 220.0));
    float behind = (p.z - d) * ${f(CHAR_FAR - CHAR_NEAR)};
    if (d < 0.999 && behind > 0.06) s += 1.0 - smoothstep(${f(REACH * 0.6)}, ${f(REACH)}, behind);
  }
  return s / 9.0 * uCharOn;
}`,
      )
      .replace(
        "#include <opaque_fragment>",
        `float lit = smoothstep(0.12, 0.5, dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722)));
outgoingLight *= 1.0 - charShade() * lit * 0.4 * vec3(1.0, 0.92, 0.75);
#include <opaque_fragment>`,
      );
  };
  material.customProgramCacheKey = () => "charShadow";
}
