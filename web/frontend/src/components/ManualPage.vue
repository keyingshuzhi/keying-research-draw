<script setup>
import { useResearchDrawStore } from "../composables/useResearchDrawStore";

const store = useResearchDrawStore();
const {
  manualTitle,
  manualLoading,
  fetchUserManual,
  openMainView,
  manualError,
  manualHtml
} = store;
</script>

<template>
  <section class="panel page-card manual-page">
    <div class="section-head">
      <h2>{{ manualTitle }}</h2>
      <div class="btn-row">
        <button class="ghost" :disabled="manualLoading" @click="fetchUserManual(true)">
          {{ manualLoading ? "刷新中..." : "刷新手册" }}
        </button>
        <button class="primary" @click="openMainView('workspace')">返回工作区</button>
      </div>
    </div>
    <p class="muted">本页面展示项目用户手册，便于直接查阅操作流程与参数说明。</p>
    <div class="manual-card">
      <p v-if="manualLoading" class="muted">正在读取用户手册...</p>
      <p v-else-if="manualError" class="msg error">{{ manualError }}</p>
      <div v-else class="manual-markdown" v-html="manualHtml || '<p>暂无手册内容</p>'"></div>
    </div>
  </section>
</template>
