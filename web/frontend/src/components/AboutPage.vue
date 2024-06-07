<script setup>
import { useResearchDrawStore } from "../composables/useResearchDrawStore";

const store = useResearchDrawStore();
const {
  TOOL_NAME,
  ABOUT_FEATURES,
  contactLoading,
  fetchContactAssets,
  openMainView,
  aboutOverview,
  aboutPlotCatalog,
  contactError,
  contactAssets,
  apiUrl
} = store;
</script>

<template>
  <section class="panel page-card">
    <div class="section-head">
      <h2>关于页面</h2>
      <div class="btn-row">
        <button class="ghost" :disabled="contactLoading" @click="fetchContactAssets(true)">
          {{ contactLoading ? "刷新中..." : "刷新联系方式" }}
        </button>
        <button class="primary" @click="openMainView('workspace')">返回工作区</button>
      </div>
    </div>

    <div class="about-intro">
      <p><strong>{{ TOOL_NAME }}</strong> 是柯影数智团队面向科研分析场景开发的可视化工具。</p>
      <p class="muted">本工具站聚焦科研数据可视化，提供从数据输入、字段映射、图型渲染到结果管理的完整闭环。</p>
    </div>

    <div class="about-overview-grid">
      <article v-for="item in aboutOverview" :key="item.label" class="overview-item">
        <span class="overview-label">{{ item.label }}</span>
        <strong class="overview-value">{{ item.value }}</strong>
      </article>
    </div>

    <div class="about-feature-block">
      <h3>工具站功能</h3>
      <div class="about-feature-grid">
        <article v-for="item in ABOUT_FEATURES" :key="item.title" class="feature-item">
          <h4>{{ item.title }}</h4>
          <p>{{ item.content }}</p>
        </article>
      </div>
    </div>

    <div class="about-plot-catalog">
      <h3>可绘制图型清单</h3>
      <p class="muted">以下图型按分组展示，便于快速确认工具站支持范围。</p>
      <div class="plot-catalog-grid">
        <article v-for="group in aboutPlotCatalog" :key="group.key" class="plot-group-card">
          <div class="plot-group-head">
            <h4>{{ group.title }}</h4>
            <span class="plot-count">{{ group.plots.length }} 种</span>
          </div>
          <p class="muted">{{ group.description }}</p>
          <p class="muted">适用场景：{{ group.scene }}</p>
          <div class="plot-tag-list">
            <span v-for="plotName in group.plots" :key="`${group.key}-${plotName}`" class="plot-tag">{{ plotName }}</span>
          </div>
        </article>
      </div>
    </div>

    <div class="contact-block">
      <h3>联系方式</h3>
      <p v-if="contactLoading" class="muted">正在加载联系方式资源...</p>
      <p v-else-if="contactError" class="msg error">{{ contactError }}</p>
      <div v-else-if="contactAssets.length" class="contact-grid">
        <article v-for="item in contactAssets" :key="item.url" class="contact-item">
          <img :src="apiUrl(item.url)" :alt="item.displayName || item.name || 'contact'" />
          <span>{{ item.displayName || item.name || "联系方式" }}</span>
        </article>
      </div>
      <p v-else class="muted">未找到联系方式资源，请检查 web/assets 目录。</p>
    </div>
  </section>
</template>
