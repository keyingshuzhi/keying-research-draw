import { computed, reactive, ref } from "vue";

export function useResearchDrawState() {
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
    forest: [{ key: "ref_line", label: "参考线位置 (ref_line)", type: "number", step: 0.1, default: 0.0 }],
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
    isosurface3d: [{ key: "iso_level", label: "等值面阈值 (iso_level)", type: "number", step: 0.1, default: "" }],
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
    raster: [{ key: "alpha", label: "栅格透明度 (alpha)", type: "number", min: 0, max: 1, step: 0.05, default: 0.65 }],
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
    rolling_stats: [{ key: "window", label: "滚动窗口 (window)", type: "number", min: 2, step: 1, default: 20 }],
    acf_pacf: [{ key: "lags", label: "滞后阶数 (lags)", type: "number", min: 1, step: 1, default: 40 }]
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
  const tableRows = ref(Array.from({ length: 8 }, () => ["", "", ""]));

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
  const currentTaskId = ref("");
  const renderHistory = ref([]);
  const uploadFiles = ref([]);
  const renderFiles = ref([]);
  const uploadFilesLoading = ref(false);
  const renderFilesLoading = ref(false);
  const historyVisibleCount = ref(HISTORY_BATCH_SIZE);
  const renderFilesVisibleCount = ref(RENDER_FILES_BATCH_SIZE);
  const historyScrollRef = ref(null);
  const renderFilesScrollRef = ref(null);

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
  const missingRequiredFields = computed(() => requiredFields.value.filter((k) => !(String(mappings[k] || "").trim())));
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

  return {
    TOOL_NAME,
    TOOL_SUBTITLE,
    GROUP_ORDER,
    GROUP_META_FALLBACK,
    ABOUT_FEATURES,
    FILE_TYPE_META,
    FIELD_LABELS,
    BASE_FIELDS,
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
    missingRequiredFields,
    visibleMappingFields,
    activeDynamicArgDefs,
    visibleRenderHistory,
    hasMoreHistory,
    visibleRenderFiles,
    hasMoreRenderFiles,
    aboutPlotCatalog,
    aboutOverview,
    sectionStatus,
    applyRegistryDefaultsToDynamicArgs
  };
}
