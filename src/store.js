import { create } from "zustand";

// Trang thai chung cua game
export const useGame = create((set) => ({
  spawn: null,            // [x, y, z] diem xuat phat
  buildings: [],          // [{ name, box: THREE.Box3, center: [x,y,z] }]
  currentZone: null,      // ten BLD_ dang dung gan
  visited: {},            // { BLD_A: true, ... }
  setWorld: (spawn, buildings) => set({ spawn, buildings }),
  setZone: (name) =>
    set((s) =>
      s.currentZone === name
        ? s
        : { currentZone: name, visited: name ? { ...s.visited, [name]: true } : s.visited }
    ),
}));
