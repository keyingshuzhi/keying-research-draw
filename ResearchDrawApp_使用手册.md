# ResearchDrawApp 使用手册（v0.1.0）

本手册覆盖当前项目的 CLI 与 Web 端能力，内容与仓库最新代码同步。

## 1. 工具概览

- CLI 入口：`python -m src.main` 或 `research-draw`
- Web 入口：`web/backend/app.py` + `web/frontend/`
- 支持图型：
  - 统计二维：`box` / `violin` / `scatter` / `volcano` / `forest`
  - 领域二维：`ma` / `enrich_dot` / `gsea` / `embedding` / `upset` / `km` / `roc` / `calibration` / `bland_altman` / `dca` / `stress_strain` / `xrd` / `raman` / `phase` / `hysteresis` / `spectral_signature` / `index_ts` / `confusion` / `class_dist` / `candlestick` / `cum_return` / `rolling_stats` / `frontier` / `acf_pacf` / `likert` / `raincloud` / `irt_icc` / `factor_loadings` / `interaction`
  - 三维：`scatter3d` / `surface3d` / `wireframe3d` / `contour3d` / `line3d` / `isosurface3d` / `slice3d` / `quiver3d` / `waterfall3d` / `embedding3d` / `mesh3d`
  - 地图：`world` / `world_admin1` / `china` / `choropleth_world` / `choropleth_china` / `raster` / `points`

## 2. 安装

推荐 Python `3.10+`。

```bash
# 基础安装
python -m pip install -e .

# 常用组合（Web + 数据 + ML + 地图）
python -m pip install -e ".[web,data,ml,maps,raster]"
```

说明：

- YAML 配置解析依赖 `PyYAML`，已在基础依赖中声明。
- `isosurface3d` 依赖 `scikit-image`（在 `.[ml]` / `.[all]` 中）。

## 3. CLI 快速使用

### 3.1 查看帮助

```bash
python -m src.main -h
python -m src.main --help-examples
```

### 3.2 Demo 示例

```bash
python -m src.main --mode demo --plot box --title "箱线图演示"
python -m src.main --mode demo --plot confusion --title "Confusion Demo"
python -m src.main --mode demo --plot scatter3d --title "3D Scatter"
python -m src.main --mode demo --plot quiver3d --title "3D Vector Field"
python -m src.main --mode demo --plot choropleth_world --title "World Choropleth"
```

### 3.3 文件模式示例

```bash
python -m src.main --mode file --plot scatter --file data/demo_scatter.csv --x-col x --y-col y
python -m src.main --mode file --plot scatter3d --file data/demo_scatter3d.csv --x-col x --y-col y --z-col z
python -m src.main --mode file --plot upset --file data/biomed/upset.csv
python -m src.main --mode file --plot confusion --file data/remote/confusion.csv
python -m src.main --mode file --plot choropleth_china --file data/china_values.csv --level 1 --key-col NAME_1 --value-col value
```

### 3.4 自定义模式示例

```bash
python -m src.main --mode custom --plot box --group "Ctrl:1,2,3" --group "A:2,3,4"
python -m src.main --mode custom --plot scatter --x "1,2,3,4" --y "1.1,2.4,2.8,4.2" --ci 0.95
python -m src.main --mode custom --plot volcano --log2fc "0.5,1.2,-1.1" --pvals "0.05,0.01,0.2"
```

## 4. Web 端使用

### 4.1 启动

```bash
# 后端（项目根目录）
python -m uvicorn web.backend.app:app --reload --host 127.0.0.1 --port 8000

# 前端
cd web/frontend
npm install
npm run dev
```

### 4.2 页面结构

- 顶部菜单栏：
  - `工作区`、`数据集`、`操作`
  - `关于页面`
  - `用户手册页面`
- 左侧导航栏：
  - 工作区模式：流程导航
  - 信息页模式：页面导航
- 主面板：
  - 工作区（数据输入、图型选择、图形设置、渲染结果）
  - 关于页面（展示 `web/assets` 联系方式）
  - 用户手册页面（读取并渲染本手册 Markdown）

### 4.3 用户手册页面说明

- 后端接口：`GET /api/user-manual`
- 返回内容：手册 Markdown 文本
- 前端渲染：按 Markdown 语义展示（标题、段落、列表、代码块、引用、链接）

## 5. 数据格式要求

### 5.1 通用文件格式

- 支持：`.csv` / `.tsv` / `.txt` / `.xlsx` / `.xls`
- 文件建议 UTF-8 编码；分隔符可自动推断，也可通过 `--sep` 指定

### 5.2 常用二维图

- `scatter`：至少 `x_col` + `y_col`
- `box` / `violin`：
  - 长表：`group_col` + `value_col`
  - 宽表：自动读取所有数值列
- `volcano`：`log2fc_col` + `p_col`，可选 `label_col`
- `forest`：`forest_label_col` + `effect_col` + `ci_low_col` + `ci_high_col`

### 5.3 常用三维图

- `scatter3d` / `line3d` / `surface3d` / `wireframe3d` / `contour3d` / `waterfall3d` / `mesh3d`：
  - `x_col` + `y_col` + `z_col`
- `quiver3d`：
  - `x_col` + `y_col` + `z_col` + `u_col` + `v_col` + `w_col`
- `isosurface3d` / `slice3d`：
  - 体素坐标和标量（常用 `x_col` + `y_col` + `z_col` + `scalar_col`）

### 5.4 地图相关

- `choropleth_world` / `choropleth_china`：
  - `key_col` + `value_col`
- `points`：
  - `lon_col` + `lat_col`
  - 可选：`hue_col` / `size_col` / `label_col`
- `raster`：
  - 需提供 `--raster-file`（GeoTIFF 等）

## 6. 配置文件（JSON/YAML）

可通过 `--config` 读取配置：

```bash
python -m src.main --config path/to/config.yaml
```

规则：

- 配置中的键名与 CLI 参数对应（下划线形式）
- 命令行显式传入的参数优先级高于配置文件

## 7. Web API 概览

- 健康检查：`GET /api/health`
- 图型列表：`GET /api/plots`
- 上传文件：`POST /api/upload`
- 上传文件管理：`GET /api/uploads` / `GET /api/uploads/{file_id}/inspect` / `DELETE /api/uploads/{file_id}` / `DELETE /api/uploads`
- 渲染：`POST /api/render`
- 渲染文件管理：`GET /api/renders` / `DELETE /api/renders/{filename}` / `DELETE /api/renders`
- 文件访问：`GET /api/files/{filename}`
- 联系方式素材：`GET /api/contact-assets`
- 用户手册：`GET /api/user-manual`
- 静态素材：`GET /assets/...`

## 8. 测试与回归

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest -q
```

- `tests/`：标准 pytest 测试集合
- `scripts/`：底图下载、数据生成与手工 smoke 脚本
- 脚本入口与用途说明：`scripts/README.md`

## 9. 常见问题

- 提示缺少可选依赖：
  - 请按报错提示安装对应 extras，例如 `.[ml]`、`.[maps]`、`.[raster]`
- 地图底图缺失：
  - 检查 `MAP_BASEMAP_ROOT` 或 `--basemap-root`
- Web 端无法连接后端：
  - 在左侧“后端连接（高级设置）”中确认 API 地址
- 用户手册页面为空：
  - 检查项目根目录是否存在 `ResearchDrawApp_使用手册.md`

## 10. 建议实践

- 产出论文图建议使用：`--fmt pdf --dpi 300 --tight`
- 对复杂流程优先用 YAML 配置固定参数，命令行只覆盖少量差异参数
- 在 CI 中至少保留一个 smoke 渲染流程，尽早发现依赖与回归问题
