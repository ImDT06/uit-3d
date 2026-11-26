// Giao dien che do kham pha (tai rieng cung Explore)
import Hud from "./Hud";
import Admin from "./Admin";
import CharacterPicker from "./CharacterPicker";

export default function ExploreUi() {
  return (
    <>
      <Hud />
      <Admin />
      <CharacterPicker />
      <div className="fade-in" />
    </>
  );
}
