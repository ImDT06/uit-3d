// Che do kham pha (tai rieng khi can): vat ly Rapier + khuon vien + nhan vat.
import { Suspense, lazy } from "react";
import { Physics } from "@react-three/rapier";
import Campus from "./Campus";
import Player from "./Player";
import Waypoint from "./Waypoint";
// chi tai thu vien hieu ung khi can (dien thoai khong dung toi)
const Effects = lazy(() => import("./Effects"));
import { useGame } from "../game/store";

export default function Explore({ effects }) {
  const debug = useGame((s) => s.physicsDebug);
  const paused = useGame((s) => s.menuOpen || s.mapOpen);
  return (
    <>
      <Physics debug={debug} paused={paused}>
        <Campus />
        <Player />
      </Physics>
      <Waypoint />
      {effects && (
        <Suspense fallback={null}>
          <Effects />
        </Suspense>
      )}
    </>
  );
}
