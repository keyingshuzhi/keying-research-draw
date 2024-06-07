import { describe, expect, it } from "vitest";

import { useResearchDrawState } from "../src/composables/useResearchDrawState";

describe("useResearchDrawState", () => {
  it("uses expected default state", () => {
    const state = useResearchDrawState();
    expect(state.selectedGroup.value).toBe("stats_2d");
    expect(state.selectedPlot.value).toBe("box");
    expect(state.renderMode.value).toBe("file");
    expect(state.fmt.value).toBe("png");
    expect(state.sectionDefs).toHaveLength(4);
  });

  it("derives required fields from registry metadata", () => {
    const state = useResearchDrawState();
    state.selectedPlot.value = "scatter";
    state.plotRegistry.value = {
      scatter: {
        required_fields: ["x_col", "y_col"]
      }
    };
    expect(state.requiredFields.value).toEqual(["x_col", "y_col"]);
    expect(state.missingRequiredFields.value).toEqual(["x_col", "y_col"]);

    state.mappings.x_col = "x";
    expect(state.missingRequiredFields.value).toEqual(["y_col"]);
  });
});
