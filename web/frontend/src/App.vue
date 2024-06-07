<script setup>
import { computed, nextTick, onMounted, onUnmounted, provide, watch } from "vue";
import AboutPage from "./components/AboutPage.vue";
import DataInput from "./components/DataInput.vue";
import ManualPage from "./components/ManualPage.vue";
import PlotSelector from "./components/PlotSelector.vue";
import RenderPanel from "./components/RenderPanel.vue";
import TopBar from "./components/TopBar.vue";
import { useResearchDrawState } from "./composables/useResearchDrawState";
import { RESEARCH_DRAW_STORE_KEY } from "./composables/useResearchDrawStore";

const state = useResearchDrawState();

const {
  TOOL_NAME,
  TOOL_SUBTITLE,
  GROUP_META_FALLBACK,
  ABOUT_FEATURES,
  FILE_TYPE_META,
  FIELD_LABELS,
  FIELD_SUGGEST,
  DYNAMIC_ARG_DEFS,
  RENDER_HISTORY_KEY,
  RENDER_HISTORY_LIMIT,
  sectionDefs,
  HISTORY_BATCH_SIZE,
  RENDER_FILES_BATCH_SIZE,
  apiBase,
  healthStatus,
  healthText,
  plotsByGroup,
  plotRegistry,
  groupMeta,
  selectedGroup,
  selectedPlot,
  renderMode,
  fmt,
  dataSourceMode,
  pickedFile,
  uploadedFileId,
  uploadedFileName,
  uploadColumns,
  previewRows,
  fileInputRef,
  tableHeaders,
  tableRows,
  mappings,
  figure,
  extraArgsText,
  imageUrl,
  resultPreviewType,
  resultFileName,
  currentResultFmt,
  lastSaveName,
  messageOk,
  messageErr,
  rendering,
  renderProgress,
  renderStatusText,
  lastFailedPayload,
  currentTaskId,
  renderHistory,
  uploadFiles,
  renderFiles,
  uploadFilesLoading,
  renderFilesLoading,
  historyVisibleCount,
  renderFilesVisibleCount,
  historyScrollRef,
  renderFilesScrollRef,
  activeMenu,
  menuWrapRef,
  activeSection,
  mainView,
  contactAssets,
  contactLoading,
  contactError,
  contactLoaded,
  manualTitle,
  manualText,
  manualLoading,
  manualError,
  manualLoaded,
  dynamicArgs,
  orderedGroups,
  plotsInSelectedGroup,
  requiredFields,
  activeDynamicArgDefs,
  visibleRenderHistory,
  hasMoreHistory,
  visibleRenderFiles,
  hasMoreRenderFiles,
  aboutPlotCatalog,
  aboutOverview,
  sectionStatus,
  applyRegistryDefaultsToDynamicArgs
} = state;

let renderProgressTimer = null;

function escapeHtml(raw) {
  return String(raw ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttr(raw) {
  return escapeHtml(raw);
}

function parseInlineMarkdown(text) {
  let out = escapeHtml(text);

  const codeTokens = [];
  out = out.replace(/`([^`]+)`/g, (_m, code) => {
    const token = `@@CODETOKEN${codeTokens.length}@@`;
    codeTokens.push(`<code>${code}</code>`);
    return token;
  });

  out = out.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]+)")?\)/g, (_m, label, href, title) => {
    const hrefText = String(href || "").replace(/&amp;/g, "&");
    const safeHref = /^(https?:\/\/|\/|#)/i.test(hrefText) ? href : "#";
    const safeTitle = title ? ` title="${escapeAttr(title)}"` : "";
    const extAttrs = /^https?:\/\//i.test(hrefText) ? ' target="_blank" rel="noopener noreferrer"' : "";
    return `<a href="${safeHref}"${safeTitle}${extAttrs}>${label}</a>`;
  });

  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  out = out.replace(/(^|[^\*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>");
  out = out.replace(/(^|[^_])_([^_]+)_(?!_)/g, "$1<em>$2</em>");

  for (let i = 0; i < codeTokens.length; i += 1) {
    out = out.replace(`@@CODETOKEN${i}@@`, codeTokens[i]);
  }
  return out;
}

function markdownToHtml(markdownText) {
  const lines = String(markdownText ?? "").replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let paragraph = [];
  let listType = "";
  let inCode = false;
  let codeLang = "";
  let codeLines = [];
  let inQuote = false;

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${parseInlineMarkdown(paragraph.join(" "))}</p>`);
    paragraph = [];
  };

  const closeList = () => {
    if (!listType) return;
    html.push(`</${listType}>`);
    listType = "";
  };

  const closeQuote = () => {
    if (!inQuote) return;
    flushParagraph();
    closeList();
    html.push("</blockquote>");
    inQuote = false;
  };

  const flushCode = () => {
    const safeLang = String(codeLang || "").toLowerCase().replace(/[^a-z0-9_-]/g, "");
    const classAttr = safeLang ? ` class="language-${escapeAttr(safeLang)}"` : "";
    html.push(`<pre><code${classAttr}>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    inCode = false;
    codeLang = "";
    codeLines = [];
  };

  for (const line of lines) {
    if (inCode) {
      if (/^```/.test(line.trim())) {
        flushCode();
      } else {
        codeLines.push(line);
      }
      continue;
    }

    const trimmed = line.trim();
    const quoteMatch = line.match(/^>\s?(.*)$/);

    if (/^```/.test(trimmed)) {
      flushParagraph();
      closeList();
      closeQuote();
      inCode = true;
      codeLang = trimmed.slice(3).trim();
      codeLines = [];
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      closeList();
      closeQuote();
      continue;
    }

    if (quoteMatch) {
      if (!inQuote) {
        flushParagraph();
        closeList();
        html.push("<blockquote>");
        inQuote = true;
      }
      const quoteBody = String(quoteMatch[1] || "").trim();
      if (!quoteBody) {
        flushParagraph();
        closeList();
      } else {
        paragraph.push(quoteBody);
      }
      continue;
    }

    if (inQuote) {
      closeQuote();
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      closeList();
      const level = headingMatch[1].length;
      html.push(`<h${level}>${parseInlineMarkdown(headingMatch[2].trim())}</h${level}>`);
      continue;
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      flushParagraph();
      closeList();
      html.push("<hr />");
      continue;
    }

    const ulMatch = trimmed.match(/^[-*+]\s+(.+)$/);
    const olMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (ulMatch || olMatch) {
      flushParagraph();
      const nextType = ulMatch ? "ul" : "ol";
      if (listType && listType !== nextType) {
        closeList();
      }
      if (!listType) {
        listType = nextType;
        html.push(`<${listType}>`);
      }
      html.push(`<li>${parseInlineMarkdown((ulMatch || olMatch)[1].trim())}</li>`);
      continue;
    }

    closeList();
    paragraph.push(trimmed);
  }

  if (inCode) {
    flushCode();
  }
  flushParagraph();
  closeList();
  closeQuote();
  return html.join("\n");
}

const manualHtml = computed(() => markdownToHtml(manualText.value));

function normalizeApiBase() {
  return apiBase.value.replace(/\/+$/, "");
}

function apiUrl(path) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${normalizeApiBase()}${path}`;
}

function toggleMenu(name) {
  activeMenu.value = activeMenu.value === name ? "" : name;
}

function closeMenu() {
  activeMenu.value = "";
}

function openMainView(view) {
  mainView.value = view;
  closeMenu();
}

function onDocClick(event) {
  if (!menuWrapRef.value) return;
  if (!menuWrapRef.value.contains(event.target)) {
    closeMenu();
  }
}

async function scrollToSection(sectionId, sectionKey) {
  if (mainView.value !== "workspace") {
    mainView.value = "workspace";
    await nextTick();
  }
  const node = document.getElementById(sectionId);
  if (node) {
    node.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  activeSection.value = sectionKey;
}

function prettifyContactName(name) {
  const key = String(name || "").replace(/\.[^.]+$/, "");
  const known = {
    小红书: "小红书",
    微信公众号: "微信公众号",
    微信服务号: "微信服务号",
    粉丝群: "粉丝群"
  };
  return known[key] || key.replace(/[_-]+/g, " ");
}

async function fetchContactAssets(force = false) {
  if (contactLoaded.value && !force) return;
  contactLoading.value = true;
  contactError.value = "";
  try {
    const res = await fetch(apiUrl("/api/contact-assets"));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "读取联系方式失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    const items = Array.isArray(data?.items) ? data.items : [];
    contactAssets.value = items.map((item) => ({
      ...item,
      displayName: prettifyContactName(item.name)
    }));
    contactLoaded.value = true;
  } catch (e) {
    contactError.value = String(e);
  } finally {
    contactLoading.value = false;
  }
}

async function fetchUserManual(force = false) {
  if (manualLoaded.value && !force) return;
  manualLoading.value = true;
  manualError.value = "";
  try {
    const res = await fetch(apiUrl("/api/user-manual"));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "读取用户手册失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    manualTitle.value = data?.title || "用户手册页面";
    manualText.value = String(data?.content || "");
    manualLoaded.value = true;
  } catch (e) {
    manualError.value = String(e);
  } finally {
    manualLoading.value = false;
  }
}

async function fetchHealth() {
  try {
    const res = await fetch(apiUrl("/api/health"));
    healthStatus.value = res.ok ? "ok" : "down";
  } catch {
    healthStatus.value = "down";
  }
}

async function fetchPlotRegistry() {
  try {
    const res = await fetch(apiUrl("/api/plot-registry"));
    if (!res.ok) throw new Error("加载图型注册中心失败");
    const data = await res.json();
    if (data?.plots_by_group && typeof data.plots_by_group === "object") {
      plotsByGroup.value = data.plots_by_group;
    }
    plotRegistry.value = data?.plots && typeof data.plots === "object" ? data.plots : {};
    const groups = Array.isArray(data?.groups) ? data.groups : [];
    if (groups.length) {
      const nextMeta = { ...GROUP_META_FALLBACK };
      for (const group of groups) {
        if (!group?.key) continue;
        nextMeta[group.key] = {
          label: group.label || GROUP_META_FALLBACK[group.key]?.label || group.key,
          description: group.description || GROUP_META_FALLBACK[group.key]?.description || "科研图型分组",
          scene: group.scene || GROUP_META_FALLBACK[group.key]?.scene || "科研可视化分析",
          order: Number(group.order ?? GROUP_META_FALLBACK[group.key]?.order ?? 999)
        };
      }
      groupMeta.value = nextMeta;
    }
    applyRegistryDefaultsToDynamicArgs();
  } catch (e) {
    // graceful fallback: keep local fallback metadata
    plotRegistry.value = {};
    groupMeta.value = { ...GROUP_META_FALLBACK };
    console.warn(e);
  }
}

async function fetchPlots() {
  try {
    const res = await fetch(apiUrl("/api/plots"));
    if (!res.ok) throw new Error("加载图型列表失败");
    const data = await res.json();
    plotsByGroup.value = data || {};
    const groups = orderedGroups.value;
    if (groups.length) {
      selectedGroup.value = groups[0];
      selectedPlot.value = (plotsByGroup.value[selectedGroup.value] || [])[0] || "box";
    }
  } catch (e) {
    messageErr.value = String(e);
  }
}

function pickBestColumn(candidates) {
  const cols = uploadColumns.value || [];
  if (!cols.length) return "";
  const lowerMap = cols.map((c) => ({ raw: c, lower: c.toLowerCase() }));
  for (const key of candidates) {
    const hit = lowerMap.find((it) => it.lower === key.toLowerCase());
    if (hit) return hit.raw;
  }
  for (const key of candidates) {
    const hit = lowerMap.find((it) => it.lower.includes(key.toLowerCase()));
    if (hit) return hit.raw;
  }
  return "";
}

function autoMapColumns() {
  const keys = Object.keys(mappings);
  for (const key of keys) {
    if (String(mappings[key] || "").trim()) continue;
    const suggest = FIELD_SUGGEST[key] || [];
    const hit = pickBestColumn(suggest);
    if (hit) mappings[key] = hit;
  }
}

function onFileChosen(event) {
  const file = event.target.files?.[0];
  pickedFile.value = file || null;
}

function triggerFilePick() {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
}

function onDynamicArgChange(def, rawValue) {
  if (def.type === "bool") {
    dynamicArgs[def.key] = Boolean(rawValue);
    return;
  }
  if (def.type === "number") {
    if (rawValue === "" || rawValue === null || typeof rawValue === "undefined") {
      dynamicArgs[def.key] = "";
      return;
    }
    const n = Number(rawValue);
    dynamicArgs[def.key] = Number.isFinite(n) ? n : "";
    return;
  }
  dynamicArgs[def.key] = String(rawValue ?? "");
}

function collectDynamicArgs() {
  const out = {};
  for (const def of activeDynamicArgDefs.value) {
    const val = dynamicArgs[def.key];
    if (def.type === "bool") {
      if (Boolean(val)) out[def.key] = true;
      continue;
    }
    if (val === "" || val === null || typeof val === "undefined") continue;
    out[def.key] = val;
  }
  return out;
}

function startRenderProgress(text = "准备渲染...") {
  if (renderProgressTimer) {
    clearInterval(renderProgressTimer);
    renderProgressTimer = null;
  }
  renderProgress.value = 6;
  renderStatusText.value = text;
  renderProgressTimer = setInterval(() => {
    if (renderProgress.value >= 90) return;
    const delta = Math.max(1.2, (92 - renderProgress.value) / 9);
    renderProgress.value = Math.min(90, renderProgress.value + delta);
  }, 180);
}

function setRenderProgressText(text) {
  renderStatusText.value = text;
}

function finishRenderProgress(ok) {
  if (renderProgressTimer) {
    clearInterval(renderProgressTimer);
    renderProgressTimer = null;
  }
  if (ok) {
    renderProgress.value = 100;
    renderStatusText.value = "渲染完成";
    setTimeout(() => {
      renderProgress.value = 0;
      renderStatusText.value = "";
    }, 900);
  } else {
    renderProgress.value = 100;
    renderStatusText.value = "渲染失败";
    setTimeout(() => {
      renderProgress.value = 0;
    }, 1200);
  }
}

function persistRenderHistory() {
  try {
    localStorage.setItem(RENDER_HISTORY_KEY, JSON.stringify(renderHistory.value));
  } catch {
    // ignore storage errors
  }
}

function loadRenderHistory() {
  try {
    const raw = localStorage.getItem(RENDER_HISTORY_KEY);
    if (!raw) {
      renderHistory.value = [];
      return;
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      renderHistory.value = [];
      return;
    }
    renderHistory.value = parsed.slice(0, RENDER_HISTORY_LIMIT);
    historyVisibleCount.value = Math.min(HISTORY_BATCH_SIZE, renderHistory.value.length);
  } catch {
    renderHistory.value = [];
  }
}

function snapshotCurrentConfig() {
  return {
    selectedGroup: selectedGroup.value,
    selectedPlot: selectedPlot.value,
    renderMode: renderMode.value,
    fmt: fmt.value,
    dataSourceMode: dataSourceMode.value,
    mappings: { ...mappings },
    dynamicArgs: { ...dynamicArgs },
    figure: { ...figure },
    extraArgsText: extraArgsText.value
  };
}

function applyConfigSnapshot(config) {
  if (!config || typeof config !== "object") return;
  if (config.selectedGroup) selectedGroup.value = config.selectedGroup;
  if (config.selectedPlot) selectedPlot.value = config.selectedPlot;
  if (config.renderMode) renderMode.value = config.renderMode;
  if (config.fmt) fmt.value = config.fmt;
  if (config.dataSourceMode) dataSourceMode.value = config.dataSourceMode;
  if (config.mappings && typeof config.mappings === "object") {
    for (const key of Object.keys(mappings)) {
      if (key in config.mappings) mappings[key] = config.mappings[key];
    }
  }
  if (config.dynamicArgs && typeof config.dynamicArgs === "object") {
    for (const [key, value] of Object.entries(config.dynamicArgs)) {
      dynamicArgs[key] = value;
    }
  }
  if (config.figure && typeof config.figure === "object") {
    figure.title = config.figure.title || "";
    figure.xlabel = config.figure.xlabel || "";
    figure.ylabel = config.figure.ylabel || "";
    figure.zlabel = config.figure.zlabel || "";
  }
  if (typeof config.extraArgsText === "string") {
    extraArgsText.value = config.extraArgsText;
  }
}

function pushRenderHistory(payload, data) {
  const item = {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    timestamp: new Date().toISOString(),
    plot: payload.plot,
    title: payload.title || "",
    fmt: payload.fmt,
    saveName: data.save_name || "",
    imagePath: data.image_url || "",
    argv: (data.argv || []).join(" "),
    config: snapshotCurrentConfig(),
    uploadedFile: payload.uploaded_file || ""
  };
  renderHistory.value = [item, ...renderHistory.value].slice(0, RENDER_HISTORY_LIMIT);
  persistRenderHistory();
}

function formatHistoryTime(ts) {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return String(ts || "");
  return d.toLocaleString();
}

function formatFileSize(bytes) {
  const n = Number(bytes || 0);
  if (!Number.isFinite(n) || n <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let value = n;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  const fixed = value >= 100 || i === 0 ? value.toFixed(0) : value.toFixed(1);
  return `${fixed} ${units[i]}`;
}

function extractRenderFilename(imagePath) {
  if (!imagePath) return "";
  const raw = String(imagePath);
  const marker = "/api/files/";
  const idx = raw.lastIndexOf(marker);
  if (idx < 0) return "";
  const tail = raw.slice(idx + marker.length).split("?")[0];
  try {
    return decodeURIComponent(tail);
  } catch {
    return tail;
  }
}

function extFromFilename(filename) {
  const raw = String(filename || "");
  const part = raw.split("?")[0].trim();
  const dot = part.lastIndexOf(".");
  if (dot < 0) return "";
  return part.slice(dot + 1).toLowerCase();
}

function extFromUrl(url) {
  return extFromFilename(extractRenderFilename(url));
}

function normalizeExt(ext) {
  return String(ext || "").trim().toLowerCase();
}

function fileTypeShort(ext) {
  const normalized = normalizeExt(ext);
  if (!normalized) return "文件";
  return FILE_TYPE_META[normalized]?.short || normalized.toUpperCase();
}

function fileTypeLong(ext) {
  const normalized = normalizeExt(ext);
  if (!normalized) return "未知格式";
  return FILE_TYPE_META[normalized]?.long || `${normalized.toUpperCase()} 文件`;
}

function inferPreviewType({ filename = "", url = "", fmt = "" } = {}) {
  const ext = String(fmt || "").toLowerCase() || extFromFilename(filename) || extFromUrl(url);
  if (ext === "pdf") return "pdf";
  if (["png", "jpg", "jpeg", "webp", "gif", "svg", "bmp"].includes(ext)) return "image";
  return "unsupported";
}

function setResultPreview({ url = "", filename = "", fmt = "" } = {}) {
  imageUrl.value = String(url || "");
  resultFileName.value = String(filename || extractRenderFilename(url) || "");
  const ext = String(fmt || "").toLowerCase() || extFromFilename(resultFileName.value) || extFromUrl(url);
  currentResultFmt.value = ext;
  resultPreviewType.value = imageUrl.value ? inferPreviewType({ filename: resultFileName.value, url, fmt: ext }) : "image";
}

function historyImageUrl(item) {
  if (!item?.imagePath) return "";
  return `${apiUrl(item.imagePath)}?h=${encodeURIComponent(item.id || "")}`;
}

function historyHasImagePreview(item) {
  return inferPreviewType({ filename: item?.saveName ? `${item.saveName}.${item.fmt || ""}` : "", url: item?.imagePath || "", fmt: item?.fmt || "" }) === "image";
}

function historyPreviewLabel(item) {
  const ext = String(item?.fmt || "").toLowerCase() || extFromUrl(item?.imagePath || "");
  return fileTypeShort(ext);
}

function renderFileExt(item) {
  return extFromFilename(item?.filename || "");
}

function renderFilePreviewType(item) {
  return inferPreviewType({ filename: item?.filename || "", url: item?.image_url || "", fmt: renderFileExt(item) });
}

function renderFileTypeLabel(item) {
  return fileTypeLong(renderFileExt(item));
}

function renderFileTypeBadge(item) {
  return fileTypeShort(renderFileExt(item));
}

function openRenderFileInNewWindow(item) {
  if (!item?.image_url) return;
  window.open(apiUrl(item.image_url), "_blank", "noopener,noreferrer");
}

function openHistoryResult(item) {
  if (!item) return;
  if (item.imagePath) {
    setResultPreview({
      url: `${historyImageUrl(item)}&t=${Date.now()}`,
      filename: item.saveName ? `${item.saveName}.${item.fmt || ""}` : "",
      fmt: item.fmt || ""
    });
  }
  lastSaveName.value = item.saveName || "";
  messageErr.value = "";
  messageOk.value = "已打开历史结果";
  scrollToSection("section-result", "result");
}

function applyHistoryItem(item) {
  if (!item) return;
  applyConfigSnapshot(item.config);
  if (item.uploadedFile) {
    uploadedFileId.value = item.uploadedFile;
    if (!uploadedFileName.value) uploadedFileName.value = item.uploadedFile;
  }
  openHistoryResult(item);
  messageOk.value = "已复用历史配置";
}

function clearRenderHistory() {
  renderHistory.value = [];
  persistRenderHistory();
  historyVisibleCount.value = HISTORY_BATCH_SIZE;
}

async function retryLastRender() {
  if (!lastFailedPayload.value) {
    messageErr.value = "当前没有可重试的失败任务";
    return;
  }
  await renderImage(lastFailedPayload.value);
}

const FILE_LIST_PAGE_SIZE = 200;
const FILE_LIST_PAGE_CAP = 200;

async function fetchPagedItems(endpoint, fallbackErrorMessage) {
  const merged = [];
  let page = 1;
  while (page <= FILE_LIST_PAGE_CAP) {
    const url = apiUrl(`${endpoint}?page=${page}&page_size=${FILE_LIST_PAGE_SIZE}`);
    const res = await fetch(url);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || fallbackErrorMessage;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    const items = Array.isArray(data?.items) ? data.items : [];
    merged.push(...items);
    if (!data?.has_next) break;
    page += 1;
  }
  return merged;
}

async function fetchUploadFiles() {
  uploadFilesLoading.value = true;
  try {
    uploadFiles.value = await fetchPagedItems("/api/uploads", "读取上传文件列表失败");
  } catch (e) {
    messageErr.value = String(e);
  } finally {
    uploadFilesLoading.value = false;
  }
}

async function fetchRenderFiles() {
  renderFilesLoading.value = true;
  try {
    renderFiles.value = await fetchPagedItems("/api/renders", "读取渲染文件列表失败");
    renderFilesVisibleCount.value = Math.min(RENDER_FILES_BATCH_SIZE, renderFiles.value.length);
  } catch (e) {
    messageErr.value = String(e);
  } finally {
    renderFilesLoading.value = false;
  }
}

async function useUploadedFile(fileId) {
  if (!fileId) return;
  messageErr.value = "";
  try {
    const res = await fetch(apiUrl(`/api/uploads/${encodeURIComponent(fileId)}/inspect`));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "读取上传文件详情失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    uploadedFileId.value = data.file_id || fileId;
    uploadedFileName.value = data.filename || fileId;
    uploadColumns.value = data.columns || [];
    previewRows.value = data.preview_rows || [];
    autoMapColumns();
    messageOk.value = `已切换数据集：${uploadedFileName.value}`;
    scrollToSection("section-data", "data");
  } catch (e) {
    messageErr.value = String(e);
  }
}

async function deleteUploadedFile(fileId) {
  if (!fileId) return;
  messageErr.value = "";
  try {
    const res = await fetch(apiUrl(`/api/uploads/${encodeURIComponent(fileId)}`), { method: "DELETE" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "删除上传文件失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    if (uploadedFileId.value === fileId) {
      uploadedFileId.value = "";
      uploadedFileName.value = "";
      uploadColumns.value = [];
      previewRows.value = [];
    }
    messageOk.value = `已删除上传文件：${fileId}`;
    await fetchUploadFiles();
  } catch (e) {
    messageErr.value = String(e);
  }
}

async function clearUploadedFiles() {
  messageErr.value = "";
  try {
    const res = await fetch(apiUrl("/api/uploads"), { method: "DELETE" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "清空上传文件失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    uploadFiles.value = [];
    uploadedFileId.value = "";
    uploadedFileName.value = "";
    uploadColumns.value = [];
    previewRows.value = [];
    messageOk.value = `已清空上传文件（${Number(data?.deleted || 0)} 个）`;
  } catch (e) {
    messageErr.value = String(e);
  }
}

async function deleteRenderFileByName(filename, { silent = false } = {}) {
  if (!filename) return;
  const res = await fetch(apiUrl(`/api/renders/${encodeURIComponent(filename)}`), { method: "DELETE" });
  if (!res.ok && res.status !== 404 && !silent) {
    const data = await res.json().catch(() => ({}));
    const detail = data?.detail || "删除渲染文件失败";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
}

async function deleteHistoryItem(item, { removeFile = true } = {}) {
  if (!item) return;
  messageErr.value = "";
  try {
    if (removeFile) {
      const filename = extractRenderFilename(item.imagePath);
      if (filename) {
        await deleteRenderFileByName(filename);
      }
    }
    renderHistory.value = renderHistory.value.filter((it) => it.id !== item.id);
    persistRenderHistory();
    if (lastSaveName.value && item.saveName === lastSaveName.value) {
      setResultPreview({});
      lastSaveName.value = "";
    }
    if (removeFile) {
      await fetchRenderFiles();
      messageOk.value = "已删除历史记录并清理本地图像";
    } else {
      messageOk.value = "已删除历史记录";
    }
  } catch (e) {
    messageErr.value = String(e);
  }
}

async function clearRenderHistoryAndLocalFiles() {
  messageErr.value = "";
  try {
    const res = await fetch(apiUrl("/api/renders"), { method: "DELETE" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "清空本地渲染文件失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    renderHistory.value = [];
    persistRenderHistory();
    historyVisibleCount.value = HISTORY_BATCH_SIZE;
    setResultPreview({});
    lastSaveName.value = "";
    await fetchRenderFiles();
    messageOk.value = `已清空历史并删除本地图像（${Number(data?.deleted || 0)} 个文件）`;
  } catch (e) {
    messageErr.value = String(e);
  }
}

function openRenderFileItem(item) {
  if (!item?.image_url) return;
  setResultPreview({
    url: `${apiUrl(item.image_url)}?rf=${Date.now()}`,
    filename: item.filename || "",
    fmt: extFromFilename(item.filename || "")
  });
  lastSaveName.value = String(item.filename || "").replace(/\.[^.]+$/, "");
  messageOk.value = "已打开本地渲染文件";
  scrollToSection("section-result", "result");
}

async function deleteRenderFileItem(item) {
  if (!item?.filename) return;
  messageErr.value = "";
  try {
    await deleteRenderFileByName(item.filename);
    renderHistory.value = renderHistory.value.filter((it) => extractRenderFilename(it.imagePath) !== item.filename);
    persistRenderHistory();
    if (extractRenderFilename(imageUrl.value) === item.filename) {
      setResultPreview({});
      lastSaveName.value = "";
    }
    await fetchRenderFiles();
    messageOk.value = `已删除本地渲染文件：${item.filename}`;
  } catch (e) {
    messageErr.value = String(e);
  }
}

async function uploadFileObject(fileObj) {
  const formData = new FormData();
  formData.append("file", fileObj);
  const res = await fetch(apiUrl("/api/upload"), {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "上传失败");
  }
  return res.json();
}

async function uploadSelectedFile() {
  messageErr.value = "";
  messageOk.value = "";
  if (!pickedFile.value) {
    messageErr.value = "请先选择数据文件";
    return;
  }
  try {
    const data = await uploadFileObject(pickedFile.value);
    uploadedFileId.value = data.file_id;
    uploadedFileName.value = data.filename;
    uploadColumns.value = data.columns || [];
    previewRows.value = data.preview_rows || [];
    autoMapColumns();
    messageOk.value = `上传成功：${data.filename}`;
    await fetchUploadFiles();
  } catch (e) {
    messageErr.value = String(e);
  }
}

function ensureRowWidth() {
  const width = tableHeaders.value.length;
  tableRows.value = tableRows.value.map((r) => {
    const next = [...r];
    while (next.length < width) next.push("");
    return next.slice(0, width);
  });
}

function addTableRow() {
  tableRows.value.push(Array.from({ length: tableHeaders.value.length }, () => ""));
}

function removeTableRow() {
  if (tableRows.value.length > 1) {
    tableRows.value.pop();
  }
}

function addTableColumn() {
  tableHeaders.value.push(`col_${tableHeaders.value.length + 1}`);
  ensureRowWidth();
}

function removeTableColumn() {
  if (tableHeaders.value.length <= 1) return;
  tableHeaders.value.pop();
  ensureRowWidth();
}

function tableToCsv() {
  const escape = (val) => {
    const text = String(val ?? "");
    if (text.includes(",") || text.includes("\"") || text.includes("\n")) {
      return `"${text.replace(/"/g, "\"\"")}"`;
    }
    return text;
  };
  const head = tableHeaders.value.map((h) => escape(h || "")).join(",");
  const body = tableRows.value
    .filter((row) => row.some((v) => String(v || "").trim() !== ""))
    .map((row) => row.map((cell) => escape(cell || "")).join(","))
    .join("\n");
  return body ? `${head}\n${body}\n` : `${head}\n`;
}

async function uploadTableDataset() {
  const csv = tableToCsv();
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const file = new File([blob], "inline_table.csv", { type: "text/csv" });
  const data = await uploadFileObject(file);
  uploadedFileId.value = data.file_id;
  uploadedFileName.value = "inline_table.csv";
  uploadColumns.value = data.columns || [];
  previewRows.value = data.preview_rows || [];
  autoMapColumns();
  await fetchUploadFiles();
  return data.file_id;
}

function chooseGroup(group) {
  selectedGroup.value = group;
  const list = plotsByGroup.value[group] || [];
  if (!list.includes(selectedPlot.value)) {
    selectedPlot.value = list[0] || "";
  }
}

function resetResult() {
  setResultPreview({});
  lastSaveName.value = "";
  messageOk.value = "";
  messageErr.value = "";
}

function loadMoreHistory() {
  historyVisibleCount.value = Math.min(renderHistory.value.length, historyVisibleCount.value + HISTORY_BATCH_SIZE);
}

function loadMoreRenderFiles() {
  renderFilesVisibleCount.value = Math.min(renderFiles.value.length, renderFilesVisibleCount.value + RENDER_FILES_BATCH_SIZE);
}

function onHistoryScroll(event) {
  const el = event?.target;
  if (!el || !hasMoreHistory.value) return;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 24) {
    loadMoreHistory();
  }
}

function onRenderFilesScroll(event) {
  const el = event?.target;
  if (!el || !hasMoreRenderFiles.value) return;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 24) {
    loadMoreRenderFiles();
  }
}

function parseExtraArgs() {
  const text = extraArgsText.value.trim();
  if (!text) return {};
  const data = JSON.parse(text);
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("高级参数必须是 JSON 对象");
  }
  return data;
}

function buildRenderArgs() {
  const args = {};
  for (const [k, v] of Object.entries(mappings)) {
    const val = String(v || "").trim();
    if (val) args[k] = val;
  }
  Object.assign(args, collectDynamicArgs());
  if (figure.xlabel.trim()) args.xlabel = figure.xlabel.trim();
  if (figure.ylabel.trim()) args.ylabel = figure.ylabel.trim();
  if (figure.zlabel.trim()) args.zlabel = figure.zlabel.trim();
  Object.assign(args, parseExtraArgs());
  return args;
}

function sanitizeRetryPayload(retryPayload) {
  if (!retryPayload || typeof retryPayload !== "object") return null;
  if (retryPayload instanceof Event) return null;
  const required = ["mode", "plot", "fmt", "args"];
  const hasAllKeys = required.every((k) => Object.prototype.hasOwnProperty.call(retryPayload, k));
  if (!hasAllKeys) return null;
  return retryPayload;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollRenderTask(taskId) {
  let retries = 0;
  while (true) {
    const res = await fetch(apiUrl(`/api/tasks/${encodeURIComponent(taskId)}`));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "读取任务状态失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    const status = String(data?.status || "");
    const detail = String(data?.detail || "");
    if (status === "queued") {
      setRenderProgressText(detail || "任务排队中...");
    } else if (status === "running") {
      setRenderProgressText(detail || "任务执行中...");
    }

    if (status === "success") {
      return data;
    }
    if (status === "failed") {
      throw new Error(String(data?.error || data?.detail || "渲染任务失败"));
    }
    if (status === "cancelled") {
      throw new Error(String(data?.detail || "任务已取消"));
    }

    retries += 1;
    await sleep(Math.min(1600, 700 + retries * 40));
  }
}

async function cancelCurrentRenderTask() {
  if (!currentTaskId.value) return;
  try {
    const taskId = currentTaskId.value;
    const res = await fetch(apiUrl(`/api/tasks/${encodeURIComponent(taskId)}/cancel`), { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "取消任务失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    messageOk.value = "已发送取消请求，任务将在可中断点停止。";
  } catch (e) {
    messageErr.value = String(e);
  }
}

async function renderImage(retryPayload = null) {
  messageErr.value = "";
  messageOk.value = "";
  rendering.value = true;
  currentTaskId.value = "";
  const safeRetryPayload = sanitizeRetryPayload(retryPayload);
  let payload = safeRetryPayload ? JSON.parse(JSON.stringify(safeRetryPayload)) : null;
  startRenderProgress(safeRetryPayload ? "重试任务准备中..." : "准备渲染任务...");
  try {
    if (!payload) {
      let mode = renderMode.value;
      let uploadId = "";

      if (mode !== "demo") {
        setRenderProgressText("正在准备数据...");
        if (dataSourceMode.value === "table") {
          uploadId = await uploadTableDataset();
        } else {
          uploadId = uploadedFileId.value;
        }
        if (!uploadId) {
          throw new Error("file 模式下需要先上传文件或保存表格数据");
        }
        autoMapColumns();
        const missing = requiredFields.value.filter((k) => !(String(mappings[k] || "").trim()));
        if (missing.length) {
          const missingText = missing.map((f) => FIELD_LABELS[f] || f).join("、");
          throw new Error(`当前数据缺少可识别字段：${missingText}。请检查列名后重试。`);
        }
        mode = "file";
      }

      payload = {
        mode,
        plot: selectedPlot.value,
        title: figure.title.trim() || null,
        fmt: fmt.value,
        uploaded_file: uploadId || null,
        args: buildRenderArgs()
      };
    }

    setRenderProgressText("任务提交中...");
    const submitRes = await fetch(apiUrl("/api/tasks/render/submit"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const submitData = await submitRes.json().catch(() => ({}));
    if (!submitRes.ok) {
      const detail = submitData?.detail || "任务提交失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    currentTaskId.value = String(submitData?.task_id || "");
    if (!currentTaskId.value) {
      throw new Error("任务提交成功但未返回 task_id");
    }

    setRenderProgressText("任务已提交，正在等待执行...");
    const taskData = await pollRenderTask(currentTaskId.value);

    setResultPreview({
      url: `${apiUrl(taskData.image_url)}?t=${Date.now()}`,
      filename: taskData.save_name ? `${taskData.save_name}.${taskData.fmt || payload.fmt || fmt.value}` : "",
      fmt: taskData.fmt || payload.fmt || fmt.value
    });
    lastSaveName.value = taskData.save_name || "";
    messageOk.value = safeRetryPayload ? "重试成功，渲染完成" : "渲染完成";
    lastFailedPayload.value = null;
    pushRenderHistory(payload, taskData);
    await fetchRenderFiles();
    finishRenderProgress(true);
    scrollToSection("section-result", "result");
  } catch (e) {
    messageErr.value = String(e);
    if (payload) {
      lastFailedPayload.value = payload;
    }
    finishRenderProgress(false);
  } finally {
    rendering.value = false;
    currentTaskId.value = "";
  }
}

const appStore = {
  ...state,
  manualHtml,
  escapeHtml,
  escapeAttr,
  parseInlineMarkdown,
  markdownToHtml,
  normalizeApiBase,
  apiUrl,
  toggleMenu,
  closeMenu,
  openMainView,
  onDocClick,
  scrollToSection,
  prettifyContactName,
  fetchContactAssets,
  fetchUserManual,
  fetchHealth,
  fetchPlotRegistry,
  fetchPlots,
  pickBestColumn,
  autoMapColumns,
  onFileChosen,
  triggerFilePick,
  onDynamicArgChange,
  collectDynamicArgs,
  startRenderProgress,
  setRenderProgressText,
  finishRenderProgress,
  persistRenderHistory,
  loadRenderHistory,
  snapshotCurrentConfig,
  applyConfigSnapshot,
  pushRenderHistory,
  formatHistoryTime,
  formatFileSize,
  extractRenderFilename,
  extFromFilename,
  extFromUrl,
  normalizeExt,
  fileTypeShort,
  fileTypeLong,
  inferPreviewType,
  setResultPreview,
  historyImageUrl,
  historyHasImagePreview,
  historyPreviewLabel,
  renderFileExt,
  renderFilePreviewType,
  renderFileTypeLabel,
  renderFileTypeBadge,
  openRenderFileInNewWindow,
  openHistoryResult,
  applyHistoryItem,
  clearRenderHistory,
  retryLastRender,
  fetchUploadFiles,
  fetchRenderFiles,
  useUploadedFile,
  deleteUploadedFile,
  clearUploadedFiles,
  deleteRenderFileByName,
  deleteHistoryItem,
  clearRenderHistoryAndLocalFiles,
  openRenderFileItem,
  deleteRenderFileItem,
  uploadFileObject,
  uploadSelectedFile,
  ensureRowWidth,
  addTableRow,
  removeTableRow,
  addTableColumn,
  removeTableColumn,
  tableToCsv,
  uploadTableDataset,
  chooseGroup,
  resetResult,
  loadMoreHistory,
  loadMoreRenderFiles,
  onHistoryScroll,
  onRenderFilesScroll,
  parseExtraArgs,
  buildRenderArgs,
  sanitizeRetryPayload,
  cancelCurrentRenderTask,
  renderImage
};

provide(RESEARCH_DRAW_STORE_KEY, appStore);

watch(
  () => selectedGroup.value,
  () => {
    const list = plotsByGroup.value[selectedGroup.value] || [];
    if (list.length && !list.includes(selectedPlot.value)) {
      selectedPlot.value = list[0];
    }
  }
);

watch(
  () => selectedPlot.value,
  () => {
    activeSection.value = "plot";
    autoMapColumns();
  }
);

watch(
  () => mainView.value,
  async (view) => {
    if (view === "about") {
      await fetchContactAssets();
    } else if (view === "manual") {
      await fetchUserManual();
    }
  }
);

watch(
  () => renderHistory.value.length,
  (len) => {
    historyVisibleCount.value = Math.min(Math.max(historyVisibleCount.value, HISTORY_BATCH_SIZE), len);
  }
);

watch(
  () => renderFiles.value.length,
  (len) => {
    renderFilesVisibleCount.value = Math.min(Math.max(renderFilesVisibleCount.value, RENDER_FILES_BATCH_SIZE), len);
  }
);

onMounted(async () => {
  document.addEventListener("click", onDocClick);
  loadRenderHistory();
  await fetchHealth();
  await fetchPlotRegistry();
  await fetchPlots();
  await fetchUploadFiles();
  await fetchRenderFiles();
});

onUnmounted(() => {
  document.removeEventListener("click", onDocClick);
  if (renderProgressTimer) {
    clearInterval(renderProgressTimer);
    renderProgressTimer = null;
  }
});
</script>

<template>
  <div class="app-shell">
    <TopBar />

    <div class="main-layout">
      <aside class="sidebar panel">
        <div class="side-head">
          <h3>{{ mainView === "workspace" ? "流程导航" : "页面导航" }}</h3>
          <span :class="['health-pill', healthStatus]">{{ healthText }}</span>
        </div>

        <div v-if="mainView === 'workspace'" class="side-nav-list">
          <button
            v-for="section in sectionDefs"
            :key="section.id"
            class="side-nav-btn"
            :class="{ active: activeSection === section.key }"
            @click="scrollToSection(section.id, section.key)"
          >
            <span class="side-nav-main">
              <span class="side-icon">{{ section.icon }}</span>
              <span>{{ section.title }}</span>
            </span>
            <span :class="['status-dot', sectionStatus[section.key] === 'ready' ? 'ready' : 'pending']"></span>
          </button>
        </div>
        <div v-else class="side-nav-list">
          <button class="side-nav-btn" :class="{ active: mainView === 'workspace' }" @click="openMainView('workspace')">
            <span class="side-nav-main">
              <span class="side-icon">W</span>
              <span>工作区</span>
            </span>
          </button>
          <button class="side-nav-btn" :class="{ active: mainView === 'about' }" @click="openMainView('about')">
            <span class="side-nav-main">
              <span class="side-icon">A</span>
              <span>关于页面</span>
            </span>
          </button>
          <button class="side-nav-btn" :class="{ active: mainView === 'manual' }" @click="openMainView('manual')">
            <span class="side-nav-main">
              <span class="side-icon">M</span>
              <span>用户手册</span>
            </span>
          </button>
        </div>

        <div class="server-advanced-card">
          <details class="advanced-panel">
            <summary>后端连接（高级设置）</summary>
            <div class="advanced-body">
              <label>
                服务地址
                <input v-model="apiBase" placeholder="http://127.0.0.1:8000" />
              </label>
              <div class="btn-row">
                <button class="ghost" @click="fetchHealth">检查连接</button>
                <button class="ghost" @click="fetchPlotRegistry(); fetchPlots()">刷新图型</button>
              </div>
            </div>
          </details>
          <p class="muted">默认用户无需调整。仅在后端地址或部署环境变更时使用。</p>
        </div>
      </aside>

      <main :class="['workspace', { 'single-view': mainView !== 'workspace' }]">
        <template v-if="mainView === 'workspace'">
          <DataInput />
          <PlotSelector />

          <section id="section-figure" class="panel section-card">
            <div class="section-head">
              <h2>图形设置（独立于数据）</h2>
            </div>
            <div class="mapping-grid">
              <label>
                图标题 (title)
                <input v-model="figure.title" placeholder="例如：样本三维结构分析" />
              </label>
              <label>
                X 轴标题 (xlabel)
                <input v-model="figure.xlabel" placeholder="例如：Temperature (°C)" />
              </label>
              <label>
                Y 轴标题 (ylabel)
                <input v-model="figure.ylabel" placeholder="例如：Intensity" />
              </label>
              <label>
                Z 轴标题 (zlabel)
                <input v-model="figure.zlabel" placeholder="例如：Depth" />
              </label>
            </div>
          </section>

          <RenderPanel />
        </template>

        <AboutPage v-else-if="mainView === 'about'" />
        <ManualPage v-else />
      </main>
    </div>

    <footer class="app-footer">
      <div class="footer-inner">
        <span>开发团队：柯影数智团队</span>
        <span>ICP备案号：待填写（占位）</span>
        <span>公网安备号：待填写（占位）</span>
      </div>
    </footer>
  </div>
</template>
