import { EffectComposer, N8AO, Bloom, ToneMapping } from "@react-three/postprocessing";
import { ToneMappingMode } from "postprocessing";

// Hieu ung hinh anh (chi chat luong Cao, khong chay tren man hinh cam ung; xem App.jsx):
// N8AO = bong nhe o goc tuong, gam mai, chan bac; Bloom = choi nhe cho cho rat sang;
// multisampling = khu rang cua. Composer tat tone mapping cua renderer nen phai them ToneMapping o cuoi.
export default function Effects() {
  return (
    <EffectComposer multisampling={4}>
      <N8AO halfRes aoRadius={2.2} distanceFalloff={1} intensity={2.6} color="#0b1430" />
      <Bloom mipmapBlur intensity={0.25} luminanceThreshold={1.15} luminanceSmoothing={0.2} />
      <ToneMapping mode={ToneMappingMode.NEUTRAL} />
    </EffectComposer>
  );
}
