<script setup>
import { useResearchDrawStore } from "../composables/useResearchDrawStore";

const store = useResearchDrawStore();
const {
  orderedGroups,
  selectedGroup,
  selectedPlot,
  groupMeta,
  GROUP_META_FALLBACK,
  plotsInSelectedGroup,
  chooseGroup
} = store;
</script>

<template>
  <section id="section-plot" class="panel section-card">
    <div class="section-head">
      <h2>图型选择</h2>
    </div>
    <div class="plot-groups">
      <button
        v-for="group in orderedGroups"
        :key="group"
        :class="['group-chip', { active: selectedGroup === group }]"
        @click="chooseGroup(group)"
      >
        {{ groupMeta[group]?.label || GROUP_META_FALLBACK[group]?.label || group }}
      </button>
    </div>
    <label>
      当前图型
      <select v-model="selectedPlot">
        <option v-for="p in plotsInSelectedGroup" :key="p" :value="p">
          {{ p }}
        </option>
      </select>
    </label>
    <p class="muted">系统会自动识别字段并匹配当前图型，不再显示技术参数面板。</p>
  </section>
</template>
