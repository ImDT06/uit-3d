// Che do kham pha (tai rieng khi can): vat ly Rapier + khuon vien + nhan vat.
import { Physics } from "@react-three/rapier";
import Campus from "./Campus";
import Player from "./Player";
import Waypoint from "./Waypoint";
import { useGame } from "../game/store";

export default function Explore() {
  const debug = useGame((s) => s.physicsDebug);
  const paused = useGame((s) => s.menuOpen || s.mapOpen);
  return (
    <>
      <Physics debug={debug} paused={paused}>
        <Campus />
        <Player />
      </Physics>
      <Waypoint />
    </>
  );
}
