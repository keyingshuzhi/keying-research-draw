<script setup>
import { useResearchDrawStore } from "../composables/useResearchDrawStore";

const store = useResearchDrawStore();
const {
  rendering,
  renderProgress,
  renderStatusText,
  currentTaskId,
  messageErr,
  messageOk,
  lastFailedPayload,
  retryLastRender,
  cancelCurrentRenderTask,
  lastSaveName,
  currentResultFmt,
  fmt,
  imageUrl,
  resultPreviewType,
  resultFileName,
  resetResult,
  clearRenderHistory,
  clearRenderHistoryAndLocalFiles,
  renderHistory,
  historyScrollRef,
  visibleRenderHistory,
  hasMoreHistory,
  onHistoryScroll,
  historyHasImagePreview,
  historyImageUrl,
  historyPreviewLabel,
  formatHistoryTime,
  applyHistoryItem,
  openHistoryResult,
  deleteHistoryItem,
  loadMoreHistory,
  renderFilesLoading,
  renderFiles,
  renderFilesScrollRef,
  visibleRenderFiles,
  hasMoreRenderFiles,
  fetchRenderFiles,
  renderFileTypeBadge,
  renderFileTypeLabel,
  formatFileSize,
  openRenderFileItem,
  renderFilePreviewType,
  openRenderFileInNewWindow,
  deleteRenderFileItem,
  loadMoreRenderFiles,
  onRenderFilesScroll
} = store;
</script>

<template>
  <section id="section-result" class="panel section-card">
    <div class="section-head">
      <h2>渲染结果</h2>
      <div class="btn-row">
        <button class="ghost" @click="resetResult">清空结果</button>
      </div>
    </div>

    <div v-if="rendering || renderProgress > 0" class="progress-card">
      <div class="progress-head">
        <span>{{ renderStatusText || (rendering ? "渲染中..." : "任务完成") }}</span>
        <span>{{ Math.round(renderProgress) }}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-bar" :style="{ width: `${renderProgress}%` }"></div>
      </div>
      <div class="btn-row" v-if="rendering && currentTaskId">
        <button class="ghost" @click="cancelCurrentRenderTask">取消任务</button>
      </div>
    </div>

    <div v-if="messageErr" class="error-row">
      <p class="msg error">{{ messageErr }}</p>
      <button class="ghost" :disabled="rendering || !lastFailedPayload" @click="retryLastRender">失败重试</button>
    </div>
    <p v-if="messageOk" class="msg ok">{{ messageOk }}</p>
    <p v-if="lastSaveName" class="muted">输出文件名：{{ lastSaveName }}.{{ (currentResultFmt || fmt).toUpperCase() }}</p>

    <div class="image-wrap" :class="`preview-${resultPreviewType}`">
      <img v-if="imageUrl && resultPreviewType === 'image'" :key="imageUrl" :src="imageUrl" alt="render result" />
      <div v-else-if="imageUrl && resultPreviewType === 'pdf'" class="pdf-preview-wrap">
        <iframe class="result-pdf-frame" :src="imageUrl" title="pdf result"></iframe>
        <a class="open-link pdf-open-link" :href="imageUrl" target="_blank" rel="noopener noreferrer">若页面未显示 PDF，请在新窗口打开</a>
      </div>
      <div v-else-if="imageUrl && resultPreviewType === 'unsupported'" class="empty">
        <p>当前文件类型暂不支持内嵌预览</p>
        <p class="muted">文件：{{ resultFileName || "unknown" }}</p>
        <a class="open-link" :href="imageUrl" target="_blank" rel="noopener noreferrer">在新窗口打开文件</a>
      </div>
      <div v-else class="empty">
        <p>尚未渲染图像</p>
        <p class="muted">请在顶部菜单栏点击“渲染图像”。</p>
      </div>
    </div>

    <div class="history-card">
      <div class="history-head">
        <h3>渲染历史</h3>
        <div class="btn-row">
          <button class="ghost" :disabled="!renderHistory.length" @click="clearRenderHistory">仅清空历史记录</button>
          <button class="ghost" :disabled="!renderHistory.length" @click="clearRenderHistoryAndLocalFiles">清空历史并删除本地图像</button>
        </div>
      </div>

      <div v-if="renderHistory.length" ref="historyScrollRef" class="history-scroll" @scroll="onHistoryScroll">
        <div class="history-list">
          <article v-for="item in visibleRenderHistory" :key="item.id" class="history-item">
            <div class="history-thumb">
              <img v-if="item.imagePath && historyHasImagePreview(item)" :src="historyImageUrl(item)" alt="history preview" />
              <span v-else class="history-thumb-empty">{{ historyPreviewLabel(item) }}</span>
            </div>
            <div class="history-meta">
              <strong>{{ item.plot }}</strong>
              <span>{{ item.title || "未命名标题" }}</span>
              <span>{{ formatHistoryTime(item.timestamp) }} · {{ String(item.fmt || "").toUpperCase() }}</span>
            </div>
            <div class="history-actions">
              <button class="ghost" @click="applyHistoryItem(item)">复用配置</button>
              <button class="ghost" @click="openHistoryResult(item)">打开结果</button>
              <button class="ghost" @click="deleteHistoryItem(item, { removeFile: true })">删除记录+文件</button>
            </div>
          </article>
        </div>
        <div v-if="hasMoreHistory" class="load-more-row">
          <button class="ghost" @click="loadMoreHistory">加载更多</button>
        </div>
      </div>
      <p v-else class="muted">暂无历史记录，完成一次渲染后会自动保存。</p>
    </div>

    <div class="render-files-card">
      <div class="render-files-head">
        <h3>本地渲染文件管理</h3>
        <div class="btn-row">
          <button class="ghost" :disabled="renderFilesLoading" @click="fetchRenderFiles">刷新</button>
          <button class="ghost" :disabled="renderFilesLoading || !renderFiles.length" @click="clearRenderHistoryAndLocalFiles">清空本地图像</button>
        </div>
      </div>
      <p v-if="renderFilesLoading" class="muted">正在读取本地渲染文件...</p>
      <div v-else-if="renderFiles.length" ref="renderFilesScrollRef" class="render-files-scroll" @scroll="onRenderFilesScroll">
        <div class="render-files-list">
          <article v-for="file in visibleRenderFiles" :key="file.filename" class="render-file-item">
            <div class="render-file-meta">
              <div class="render-file-name-row">
                <strong>{{ file.filename }}</strong>
                <span class="file-type-badge">{{ renderFileTypeBadge(file) }}</span>
              </div>
              <span>{{ renderFileTypeLabel(file) }} · {{ formatFileSize(file.size) }} · {{ formatHistoryTime(file.modified_at) }}</span>
            </div>
            <div class="render-file-actions">
              <button class="ghost" @click="openRenderFileItem(file)">打开</button>
              <button v-if="renderFilePreviewType(file) === 'pdf'" class="ghost" @click="openRenderFileInNewWindow(file)">新窗口</button>
              <button class="ghost" @click="deleteRenderFileItem(file)">删除</button>
            </div>
          </article>
        </div>
        <div v-if="hasMoreRenderFiles" class="load-more-row">
          <button class="ghost" @click="loadMoreRenderFiles">加载更多</button>
        </div>
      </div>
      <p v-else class="muted">暂无本地渲染文件。</p>
    </div>
  </section>
</template>
