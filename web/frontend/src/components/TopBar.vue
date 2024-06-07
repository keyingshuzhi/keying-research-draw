<script setup>
import { useResearchDrawStore } from "../composables/useResearchDrawStore";

const store = useResearchDrawStore();
const {
  TOOL_NAME,
  TOOL_SUBTITLE,
  mainView,
  activeMenu,
  renderMode,
  fmt,
  rendering,
  toggleMenu,
  closeMenu,
  scrollToSection,
  openMainView,
  triggerFilePick,
  renderImage,
  resetResult,
  fetchHealth,
  fetchPlotRegistry,
  fetchPlots,
  dataSourceMode
} = store;

function bindMenuWrap(el) {
  store.menuWrapRef.value = el;
}
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <div class="brand-title">{{ TOOL_NAME }}</div>
      <div class="brand-sub">{{ TOOL_SUBTITLE }}</div>
    </div>

    <nav :ref="bindMenuWrap" class="menu-wrap">
      <div class="menu-item">
        <button class="menu-trigger" :class="{ active: mainView === 'workspace' }" @click.stop="toggleMenu('workspace')">
          工作区
          <span class="caret">▾</span>
        </button>
        <div v-if="activeMenu === 'workspace'" class="dropdown">
          <button @click="scrollToSection('section-data', 'data'); closeMenu()">数据输入</button>
          <button @click="scrollToSection('section-plot', 'plot'); closeMenu()">图型选择</button>
          <button @click="scrollToSection('section-figure', 'figure'); closeMenu()">图形设置</button>
          <button @click="scrollToSection('section-result', 'result'); closeMenu()">渲染结果</button>
        </div>
      </div>

      <div class="menu-item">
        <button class="menu-trigger" @click.stop="toggleMenu('dataset')">
          数据集
          <span class="caret">▾</span>
        </button>
        <div v-if="activeMenu === 'dataset'" class="dropdown">
          <button @click="dataSourceMode = 'upload'; scrollToSection('section-data', 'data'); closeMenu()">文件上传</button>
          <button @click="dataSourceMode = 'table'; scrollToSection('section-data', 'data'); closeMenu()">表格录入</button>
          <button @click="triggerFilePick(); closeMenu()">选择文件</button>
        </div>
      </div>

      <div class="menu-item">
        <button class="menu-trigger" @click.stop="toggleMenu('actions')">
          操作
          <span class="caret">▾</span>
        </button>
        <div v-if="activeMenu === 'actions'" class="dropdown">
          <button @click="renderImage(); closeMenu()">渲染图像</button>
          <button @click="resetResult(); closeMenu()">清空结果</button>
          <button @click="fetchHealth(); fetchPlotRegistry(); fetchPlots(); closeMenu()">刷新连接</button>
        </div>
      </div>

      <button class="menu-link" :class="{ active: mainView === 'about' }" @click="openMainView('about')">关于页面</button>
      <button class="menu-link" :class="{ active: mainView === 'manual' }" @click="openMainView('manual')">用户手册页面</button>
    </nav>

    <div class="top-actions">
      <label class="compact-field">
        <span>模式</span>
        <select v-model="renderMode">
          <option value="file">file</option>
          <option value="demo">demo</option>
        </select>
      </label>
      <label class="compact-field">
        <span>格式</span>
        <select v-model="fmt">
          <option value="png">png</option>
          <option value="svg">svg</option>
          <option value="pdf">pdf</option>
        </select>
      </label>
      <button class="primary top-render-btn" :disabled="rendering" @click="renderImage()">
        {{ rendering ? "渲染中..." : "渲染图像" }}
      </button>
    </div>
  </header>
</template>
