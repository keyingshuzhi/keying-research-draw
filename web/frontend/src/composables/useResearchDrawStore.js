import { inject } from "vue";

export const RESEARCH_DRAW_STORE_KEY = Symbol("research-draw-store");

export function useResearchDrawStore() {
  const store = inject(RESEARCH_DRAW_STORE_KEY, null);
  if (!store) {
    throw new Error("ResearchDraw store is not provided.");
  }
  return store;
}
