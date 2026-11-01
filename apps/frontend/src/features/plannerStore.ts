import { create } from "zustand";

type PlannerState = {
  scenarioId: number | null;
  areaId: number | null;
  factoryId: number | null;
  setScenario: (id: number | null) => void;
  setArea: (id: number | null) => void;
  setFactory: (id: number | null) => void;
};

export const usePlannerStore = create<PlannerState>((set) => ({
  scenarioId: null,
  areaId: null,
  factoryId: null,
  setScenario: (id) => set({ scenarioId: id, areaId: null, factoryId: null }),
  setArea: (id) => set({ areaId: id, factoryId: null }),
  setFactory: (id) => set({ factoryId: id }),
}));
