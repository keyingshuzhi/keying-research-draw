<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";

const TOOL_NAME = "柯影智绘 Atlas";
const TOOL_SUBTITLE = "柯影数智团队开发";

const GROUP_ORDER = ["stats_2d", "domain_2d", "plots_3d", "maps"];

const GROUP_META_FALLBACK = {
  stats_2d: {
    label: "统计二维",
    description: "通用统计分析图型，适用于实验比较与相关分析。",
    scene: "实验组比较、差异分析、相关性分析",
    order: 10
  },
  domain_2d: {
    label: "学科二维",
    description: "生物、临床、材料、遥感、金融、心理等领域科研图型。",
    scene: "生信分析、临床评估、材料表征、遥感与金融时序",
    order: 20
  },
  plots_3d: {
    label: "三维图型",
    description: "科研常用三维可视化图型，支持轨迹、曲面、向量场等。",
    scene: "三维结构展示、体数据分析、向量场分析",
    order: 30
  },
  maps: {
    label: "地理地图",
    description: "离线地图绘图，支持底图、分级着色、栅格与点位叠加。",
    scene: "全球/中国空间分布、区域分级、点位与栅格叠加",
    order: 40
  }
};

const ABOUT_FEATURES = [
  {
    title: "数据输入",
    content: "支持上传 CSV/TSV/TXT/Excel 文件，或直接在页面表格录入并保存为数据集。"
  },
  {
    title: "智能字段匹配",
    content: "自动识别列名并映射常用字段（x/y/z、group/value、经纬度等），减少手工配置。"
  },
  {
    title: "科研图型渲染",
    content: "覆盖统计二维、领域二维、三维图型和离线地图绘图，可导出 PNG/SVG/PDF。"
  },
  {
    title: "结果与文件管理",
    content: "支持渲染历史复用、上传文件管理、本地渲染文件管理与一键清理。"
  },
  {
    title: "页面级信息中心",
    content: "提供关于页面、用户手册页面与联系方式展示，便于团队内外协同使用。"
  }
];

const FILE_TYPE_META = {
  png: { short: "PNG", long: "PNG 图片" },
  jpg: { short: "JPG", long: "JPG 图片" },
  jpeg: { short: "JPEG", long: "JPEG 图片" },
  webp: { short: "WEBP", long: "WEBP 图片" },
  gif: { short: "GIF", long: "GIF 图片" },
  bmp: { short: "BMP", long: "BMP 图片" },
  svg: { short: "SVG", long: "SVG 矢量图" },
  pdf: { short: "PDF", long: "PDF 文档" }
};

const FIELD_LABELS = {
  group_col: "分组列 (group_col)",
  value_col: "数值列 (value_col)",
  x_col: "X 列 (x_col)",
  y_col: "Y 列 (y_col)",
  z_col: "Z 列 (z_col)",
  u_col: "U 列 (u_col)",
  v_col: "V 列 (v_col)",
  w_col: "W 列 (w_col)",
  scalar_col: "标量列 (scalar_col)",
  label_col: "标签列 (label_col)",
  log2fc_col: "log2FC 列 (log2fc_col)",
  p_col: "P 值列 (p_col)",
  forest_label_col: "标签列 (forest_label_col)",
  effect_col: "效应量列 (effect_col)",
  ci_low_col: "CI 下限列 (ci_low_col)",
  ci_high_col: "CI 上限列 (ci_high_col)",
  key_col: "键列 (key_col)",
  lon_col: "经度列 (lon_col)",
  lat_col: "纬度列 (lat_col)"
};

const BASE_FIELDS = ["x_col", "y_col", "z_col", "group_col", "value_col", "label_col"];

const FIELD_SUGGEST = {
  x_col: ["x", "x_col", "time", "date"],
  y_col: ["y", "y_col", "value", "score"],
  z_col: ["z", "z_col", "depth", "height"],
  group_col: ["group", "class", "category", "type"],
  value_col: ["value", "val", "count", "amount", "intensity"],
  label_col: ["label", "name", "id"],
  log2fc_col: ["log2fc", "logfc", "fc"],
  p_col: ["p", "pvalue", "p_val", "p_value"],
  forest_label_col: ["study", "label", "name"],
  effect_col: ["effect", "estimate", "beta"],
  ci_low_col: ["ci_low", "lower", "lcl"],
  ci_high_col: ["ci_high", "upper", "ucl"],
  key_col: ["key", "region", "name", "code"],
  lon_col: ["lon", "lng", "longitude"],
  lat_col: ["lat", "latitude"],
  u_col: ["u"],
  v_col: ["v"],
  w_col: ["w"],
  scalar_col: ["scalar", "density", "value"]
};

const DYNAMIC_ARG_DEFS = {
  scatter: [
    { key: "ci", label: "置信区间 (ci)", type: "number", min: 0, max: 1, step: 0.01, default: 0.95 },
    { key: "equal", label: "等比例坐标 (equal)", type: "bool", default: false }
  ],
  volcano: [
    { key: "fc_thresh", label: "FC 阈值 (fc_thresh)", type: "number", min: 0, step: 0.1, default: 1.0 },
    { key: "p_thresh", label: "P 阈值 (p_thresh)", type: "number", min: 0, max: 1, step: 0.01, default: 0.05 },
    { key: "top_n", label: "标注前 N 个点 (top_n)", type: "number", min: 0, step: 1, default: 10 }
  ],
  forest: [
    { key: "ref_line", label: "参考线位置 (ref_line)", type: "number", step: 0.1, default: 0.0 }
  ],
  surface3d: [
    { key: "elev", label: "仰角 (elev)", type: "number", step: 1, default: "" },
    { key: "azim", label: "方位角 (azim)", type: "number", step: 1, default: "" }
  ],
  wireframe3d: [
    { key: "rstride", label: "行步长 (rstride)", type: "number", min: 1, step: 1, default: 2 },
    { key: "cstride", label: "列步长 (cstride)", type: "number", min: 1, step: 1, default: 2 },
    { key: "elev", label: "仰角 (elev)", type: "number", step: 1, default: "" },
    { key: "azim", label: "方位角 (azim)", type: "number", step: 1, default: "" }
  ],
  contour3d: [
    { key: "levels", label: "等高层数 (levels)", type: "number", min: 3, step: 1, default: 18 },
    { key: "elev", label: "仰角 (elev)", type: "number", step: 1, default: "" },
    { key: "azim", label: "方位角 (azim)", type: "number", step: 1, default: "" }
  ],
  line3d: [
    { key: "elev", label: "仰角 (elev)", type: "number", step: 1, default: "" },
    { key: "azim", label: "方位角 (azim)", type: "number", step: 1, default: "" }
  ],
  quiver3d: [
    { key: "max_arrows", label: "最大箭头数 (max_arrows)", type: "number", min: 1, step: 1, default: 600 },
    { key: "elev", label: "仰角 (elev)", type: "number", step: 1, default: "" },
    { key: "azim", label: "方位角 (azim)", type: "number", step: 1, default: "" }
  ],
  isosurface3d: [
    { key: "iso_level", label: "等值面阈值 (iso_level)", type: "number", step: 0.1, default: "" }
  ],
  slice3d: [
    { key: "slice_x", label: "切片 X 位置 (slice_x)", type: "number", step: 0.1, default: "" },
    { key: "slice_y", label: "切片 Y 位置 (slice_y)", type: "number", step: 0.1, default: "" },
    { key: "slice_z", label: "切片 Z 位置 (slice_z)", type: "number", step: 0.1, default: "" }
  ],
  choropleth_world: [
    {
      key: "scheme",
      label: "分级方案 (scheme)",
      type: "select",
      default: "quantiles",
      options: [
        { value: "quantiles", label: "quantiles" },
        { value: "equal", label: "equal" },
        { value: "natural", label: "natural" }
      ]
    },
    { key: "k", label: "分级数 (k)", type: "number", min: 2, max: 9, step: 1, default: 5 }
  ],
  choropleth_china: [
    {
      key: "scheme",
      label: "分级方案 (scheme)",
      type: "select",
      default: "quantiles",
      options: [
        { value: "quantiles", label: "quantiles" },
        { value: "equal", label: "equal" },
        { value: "natural", label: "natural" }
      ]
    },
    { key: "k", label: "分级数 (k)", type: "number", min: 2, max: 9, step: 1, default: 5 }
  ],
  raster: [
    { key: "alpha", label: "栅格透明度 (alpha)", type: "number", min: 0, max: 1, step: 0.05, default: 0.65 }
  ],
  calibration: [
    { key: "n_bins", label: "分箱数 (n_bins)", type: "number", min: 2, step: 1, default: 10 },
    {
      key: "calib_strategy",
      label: "分箱策略 (calib_strategy)",
      type: "select",
      default: "uniform",
      options: [
        { value: "uniform", label: "uniform" },
        { value: "quantile", label: "quantile" }
      ]
    }
  ],
  rolling_stats: [
    { key: "window", label: "滚动窗口 (window)", type: "number", min: 2, step: 1, default: 20 }
  ],
  acf_pacf: [
    { key: "lags", label: "滞后阶数 (lags)", type: "number", min: 1, step: 1, default: 40 }
  ]
};

const RENDER_HISTORY_KEY = "kydz_research_draw_history_v1";
const RENDER_HISTORY_LIMIT = 20;

const sectionDefs = [
  { id: "section-data", key: "data", title: "数据输入", icon: "D" },
  { id: "section-plot", key: "plot", title: "图型选择", icon: "P" },
  { id: "section-figure", key: "figure", title: "图形设置", icon: "F" },
  { id: "section-result", key: "result", title: "渲染结果", icon: "R" }
];

const HISTORY_BATCH_SIZE = 8;
const RENDER_FILES_BATCH_SIZE = 10;

const apiBase = ref("http://127.0.0.1:8000");
const healthStatus = ref("unknown");
const healthText = computed(() => (healthStatus.value === "ok" ? "后端在线" : healthStatus.value === "down" ? "后端离线" : "状态未知"));

const plotsByGroup = ref({});
const plotRegistry = ref({});
const groupMeta = ref({ ...GROUP_META_FALLBACK });
const selectedGroup = ref("stats_2d");
const selectedPlot = ref("box");
const renderMode = ref("file");
const fmt = ref("png");

const dataSourceMode = ref("upload");
const pickedFile = ref(null);
const uploadedFileId = ref("");
const uploadedFileName = ref("");
const uploadColumns = ref([]);
const previewRows = ref([]);
const fileInputRef = ref(null);

const tableHeaders = ref(["x", "y", "z"]);
const tableRows = ref(
  Array.from({ length: 8 }, () => ["", "", ""])
);

const mappings = reactive({
  group_col: "",
  value_col: "",
  x_col: "",
  y_col: "",
  z_col: "",
  u_col: "",
  v_col: "",
  w_col: "",
  scalar_col: "",
  label_col: "",
  log2fc_col: "",
  p_col: "",
  forest_label_col: "",
  effect_col: "",
  ci_low_col: "",
  ci_high_col: "",
  key_col: "",
  lon_col: "",
  lat_col: ""
});

const figure = reactive({
  title: "",
  xlabel: "",
  ylabel: "",
  zlabel: ""
});

const extraArgsText = ref("{}");
const imageUrl = ref("");
const resultPreviewType = ref("image");
const resultFileName = ref("");
const currentResultFmt = ref("");
const lastSaveName = ref("");
const messageOk = ref("");
const messageErr = ref("");
const rendering = ref(false);
const renderProgress = ref(0);
const renderStatusText = ref("");
const lastFailedPayload = ref(null);
const renderHistory = ref([]);
const uploadFiles = ref([]);
const renderFiles = ref([]);
const uploadFilesLoading = ref(false);
const renderFilesLoading = ref(false);
const historyVisibleCount = ref(HISTORY_BATCH_SIZE);
const renderFilesVisibleCount = ref(RENDER_FILES_BATCH_SIZE);
const historyScrollRef = ref(null);
const renderFilesScrollRef = ref(null);
let renderProgressTimer = null;

const activeMenu = ref("");
const menuWrapRef = ref(null);
const activeSection = ref("data");
const mainView = ref("workspace");
const contactAssets = ref([]);
const contactLoading = ref(false);
const contactError = ref("");
const contactLoaded = ref(false);
const manualTitle = ref("用户手册页面");
const manualText = ref("");
const manualLoading = ref(false);
const manualError = ref("");
const manualLoaded = ref(false);

function buildDynamicArgDefaults() {
  const defaults = {};
  for (const defs of Object.values(DYNAMIC_ARG_DEFS)) {
    for (const def of defs) {
      if (!(def.key in defaults)) {
        if (def.type === "bool") defaults[def.key] = Boolean(def.default);
        else defaults[def.key] = def.default ?? "";
      }
    }
  }
  return defaults;
}

const dynamicArgs = reactive(buildDynamicArgDefaults());

function fallbackDefaultForDef(def) {
  if (def.type === "bool") return Boolean(def.default);
  return def.default ?? "";
}

function applyRegistryDefaultsToDynamicArgs() {
  for (const [plotName, defs] of Object.entries(DYNAMIC_ARG_DEFS)) {
    const specDefaults = plotRegistry.value?.[plotName]?.defaults;
    if (!specDefaults || typeof specDefaults !== "object") continue;
    for (const def of defs) {
      if (!(def.key in specDefaults)) continue;
      const fallback = fallbackDefaultForDef(def);
      const current = dynamicArgs[def.key];
      if (current === fallback || current === "" || current === null || typeof current === "undefined") {
        dynamicArgs[def.key] = specDefaults[def.key];
      }
    }
  }
}

const orderedGroups = computed(() => {
  const keys = Object.keys(plotsByGroup.value || {});
  const meta = groupMeta.value || {};
  const byMeta = keys.slice().sort((a, b) => {
    const ao = Number(meta[a]?.order ?? 999);
    const bo = Number(meta[b]?.order ?? 999);
    return ao - bo;
  });
  const preferred = GROUP_ORDER.filter((k) => keys.includes(k));
  const orderedByMeta = byMeta.filter((k) => !preferred.includes(k));
  const rest = keys.filter((k) => !preferred.includes(k));
  return [...preferred, ...orderedByMeta, ...rest.filter((k) => !orderedByMeta.includes(k))];
});

const plotsInSelectedGroup = computed(() => plotsByGroup.value[selectedGroup.value] || []);

const requiredFields = computed(() => plotRegistry.value[selectedPlot.value]?.required_fields || []);

const missingRequiredFields = computed(() =>
  requiredFields.value.filter((k) => !(String(mappings[k] || "").trim()))
);

const visibleMappingFields = computed(() => {
  const required = requiredFields.value;
  const merged = [...required, ...BASE_FIELDS];
  const unique = [];
  for (const key of merged) {
    if (!unique.includes(key)) unique.push(key);
  }
  return unique.map((k) => ({ key: k, label: FIELD_LABELS[k] || k }));
});

const activeDynamicArgDefs = computed(() => DYNAMIC_ARG_DEFS[selectedPlot.value] || []);

const visibleRenderHistory = computed(() => renderHistory.value.slice(0, historyVisibleCount.value));
const hasMoreHistory = computed(() => historyVisibleCount.value < renderHistory.value.length);
const visibleRenderFiles = computed(() => renderFiles.value.slice(0, renderFilesVisibleCount.value));
const hasMoreRenderFiles = computed(() => renderFilesVisibleCount.value < renderFiles.value.length);

const aboutPlotCatalog = computed(() => {
  const source = plotsByGroup.value || {};
  const meta = groupMeta.value || {};
  const keys = Object.keys(source);
  const ordered = [...GROUP_ORDER.filter((k) => keys.includes(k)), ...keys.filter((k) => !GROUP_ORDER.includes(k))];
  return ordered.map((groupKey) => {
    const plots = Array.isArray(source[groupKey]) ? source[groupKey] : [];
    return {
      key: groupKey,
      title: meta[groupKey]?.label || GROUP_META_FALLBACK[groupKey]?.label || groupKey,
      description: meta[groupKey]?.description || GROUP_META_FALLBACK[groupKey]?.description || "科研图型分组",
      scene: meta[groupKey]?.scene || GROUP_META_FALLBACK[groupKey]?.scene || "科研可视化分析",
      plots
    };
  });
});

const aboutOverview = computed(() => {
  const groups = aboutPlotCatalog.value.length;
  const totalPlots = aboutPlotCatalog.value.reduce((sum, group) => sum + group.plots.length, 0);
  return [
    { label: "图型分组", value: `${groups} 类` },
    { label: "可绘制图型", value: `${totalPlots} 种` },
    { label: "数据输入", value: "文件上传 + 表格录入" },
    { label: "输出格式", value: "PNG / SVG / PDF" }
  ];
});

const sectionStatus = computed(() => ({
  data: uploadedFileId.value ? "ready" : "pending",
  plot: selectedPlot.value ? "ready" : "pending",
  figure: "ready",
  result: imageUrl.value ? "ready" : "pending"
}));

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

async function fetchUploadFiles() {
  uploadFilesLoading.value = true;
  try {
    const res = await fetch(apiUrl("/api/uploads"));
    if (!res.ok) throw new Error("读取上传文件列表失败");
    const data = await res.json();
    uploadFiles.value = Array.isArray(data?.items) ? data.items : [];
  } catch (e) {
    messageErr.value = String(e);
  } finally {
    uploadFilesLoading.value = false;
  }
}

async function fetchRenderFiles() {
  renderFilesLoading.value = true;
  try {
    const res = await fetch(apiUrl("/api/renders"));
    if (!res.ok) throw new Error("读取渲染文件列表失败");
    const data = await res.json();
    renderFiles.value = Array.isArray(data?.items) ? data.items : [];
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

async function renderImage(retryPayload = null) {
  messageErr.value = "";
  messageOk.value = "";
  rendering.value = true;
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

    setRenderProgressText("正在调用渲染引擎...");
    const res = await fetch(apiUrl("/api/render"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail || "渲染失败";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    setResultPreview({
      url: `${apiUrl(data.image_url)}?t=${Date.now()}`,
      filename: data.save_name ? `${data.save_name}.${data.fmt || payload.fmt || fmt.value}` : "",
      fmt: data.fmt || payload.fmt || fmt.value
    });
    lastSaveName.value = data.save_name || "";
    messageOk.value = safeRetryPayload ? "重试成功，渲染完成" : "渲染完成";
    lastFailedPayload.value = null;
    pushRenderHistory(payload, data);
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
  }
}

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
    <header class="topbar">
      <div class="brand">
        <div class="brand-title">{{ TOOL_NAME }}</div>
        <div class="brand-sub">{{ TOOL_SUBTITLE }}</div>
      </div>

      <nav ref="menuWrapRef" class="menu-wrap">
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
        <section id="section-data" class="panel section-card">
          <div class="section-head">
            <h2>数据输入</h2>
            <div class="segmented">
              <button :class="{ active: dataSourceMode === 'upload' }" @click="dataSourceMode = 'upload'">文件上传</button>
              <button :class="{ active: dataSourceMode === 'table' }" @click="dataSourceMode = 'table'">表格录入</button>
            </div>
          </div>

          <div v-if="dataSourceMode === 'upload'" class="upload-card">
            <input ref="fileInputRef" class="hidden-file-input" type="file" accept=".csv,.tsv,.txt,.xlsx,.xls" @change="onFileChosen" />
            <div class="upload-action-row">
              <button class="ghost upload-pick-btn" @click="triggerFilePick">
                {{ pickedFile ? `已选文件：${pickedFile.name}` : "上传数据文件" }}
              </button>
              <button class="primary upload-parse-btn" @click="uploadSelectedFile">文件解析</button>
            </div>
            <p v-if="pickedFile" class="muted">待解析文件：{{ pickedFile.name }}</p>
            <p class="muted" v-if="uploadedFileId">
              当前数据集：{{ uploadedFileName }}（ID: {{ uploadedFileId }}）
            </p>
          </div>

          <div v-else class="table-editor-card">
            <div class="btn-row">
              <button class="ghost" @click="addTableColumn">加一列</button>
              <button class="ghost" @click="removeTableColumn">减一列</button>
              <button class="ghost" @click="addTableRow">加一行</button>
              <button class="ghost" @click="removeTableRow">减一行</button>
              <button class="primary" @click="uploadTableDataset">保存为数据集</button>
            </div>
            <div class="table-wrap">
              <table class="editor-table">
                <thead>
                  <tr>
                    <th v-for="(h, hi) in tableHeaders" :key="`h-${hi}`">
                      <input v-model="tableHeaders[hi]" />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in tableRows" :key="`r-${ri}`">
                    <td v-for="(cell, ci) in row" :key="`c-${ri}-${ci}`">
                      <input v-model="tableRows[ri][ci]" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="preview-card">
            <h3>数据预览</h3>
            <div v-if="uploadColumns.length" class="table-wrap">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th v-for="col in uploadColumns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in previewRows" :key="idx">
                    <td v-for="col in uploadColumns" :key="`${idx}-${col}`">
                      {{ row[col] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="muted">上传或保存表格后，会显示列名与前 5 行数据。</p>
          </div>

          <div class="upload-files-card">
            <div class="upload-files-head">
              <h3>上传文件管理</h3>
              <div class="btn-row">
                <button class="ghost" :disabled="uploadFilesLoading" @click="fetchUploadFiles">刷新</button>
                <button class="ghost" :disabled="uploadFilesLoading || !uploadFiles.length" @click="clearUploadedFiles">清空上传文件</button>
              </div>
            </div>

            <p v-if="uploadFilesLoading" class="muted">正在读取上传文件列表...</p>
            <div v-else-if="uploadFiles.length" class="upload-files-list">
              <article v-for="item in uploadFiles" :key="item.file_id" class="upload-file-item">
                <div class="upload-file-meta">
                  <strong>{{ item.file_id }}</strong>
                  <span>{{ formatFileSize(item.size) }} · {{ formatHistoryTime(item.modified_at) }}</span>
                  <span v-if="uploadedFileId === item.file_id" class="active-badge">当前使用中</span>
                </div>
                <div class="upload-file-actions">
                  <button class="ghost" @click="useUploadedFile(item.file_id)">使用</button>
                  <button class="ghost" @click="deleteUploadedFile(item.file_id)">删除</button>
                </div>
              </article>
            </div>
            <p v-else class="muted">暂无上传文件。</p>
          </div>
        </section>

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
              <iframe
                class="result-pdf-frame"
                :src="imageUrl"
                title="pdf result"
              ></iframe>
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

        <section v-else-if="mainView === 'about'" class="panel page-card">
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

        <section v-else class="panel page-card manual-page">
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
