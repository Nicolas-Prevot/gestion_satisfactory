import { create } from "zustand";

import type { ApiErrorPayload } from "../lib/types";

type ErrorState = {
  latestError: ApiErrorPayload | null;
  setError: (error: ApiErrorPayload | null) => void;
  clearError: () => void;
};

export const useErrorStore = create<ErrorState>((set) => ({
  latestError: null,
  setError: (error) => set({ latestError: error }),
  clearError: () => set({ latestError: null }),
}));
