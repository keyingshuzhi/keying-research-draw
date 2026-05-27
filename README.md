# Research Draw（科研绘图）

Research Draw 是一个面向科研场景的可视化工具站，提供从数据输入、字段映射、图型渲染到结果管理的完整流程。

包含：

- Python CLI（`python -m src.main` / `research-draw`）
- Web 端（FastAPI + Vue3）

> 当前版本：`v0.1.0`

当前版本覆盖统计二维图、领域二维图、科研常用三维图、离线地图绘图，并支持文件上传、页面表格录入、历史记录与本地渲染文件管理。

## GitHub 展示文案

可用于 GitHub 仓库 `Description`（短描述）：

`Research Draw: 科研绘图工具站（CLI + Web），支持统计/学科/3D/离线地图可视化，提供上传、表格录入、渲染历史与本地文件管理。`

English version for GitHub `Description`:

`Research Draw: A scientific visualization toolkit (CLI + Web) for 2D stats, domain plots, 3D charts, and offline maps, with file upload, table input, render history, and local output management.`

推荐仓库 Topics：

`scientific-visualization` `data-visualization` `matplotlib` `fastapi` `vue3` `gis` `3d-plot` `research-tools` `python`

## 核心能力

- 统计二维：`box` / `violin` / `scatter` / `volcano` / `forest`
- 领域二维：
  - 生物：`ma` / `enrich_dot` / `gsea` / `embedding` / `upset`
  - 临床：`km` / `roc` / `calibration` / `bland_altman` / `dca`
  - 材料：`stress_strain` / `xrd` / `raman` / `phase` / `hysteresis`
  - 遥感：`spectral_signature` / `index_ts` / `confusion` / `class_dist`
  - 金融：`candlestick` / `cum_return` / `rolling_stats` / `frontier` / `acf_pacf`
  - 心理：`likert` / `raincloud` / `irt_icc` / `factor_loadings` / `interaction`
- 三维图：`scatter3d` / `surface3d` / `wireframe3d` / `contour3d` / `line3d` / `isosurface3d` / `slice3d` / `quiver3d` / `waterfall3d` / `embedding3d` / `mesh3d`
- 地图：`world` / `world_admin1` / `china` / `choropleth_world` / `choropleth_china` / `raster` / `points`

## 安装

推荐 Python `3.10+`。

基础安装：

```bash
python -m pip install -e .
```

按需安装扩展：

```bash
# 文件读取（CSV/Excel）
python -m pip install -e ".[data]"

# 统计增强
python -m pip install -e ".[stats]"

# 机器学习/高级图型（含 isosurface3d 依赖 scikit-image）
python -m pip install -e ".[ml]"

# 地图与栅格
python -m pip install -e ".[maps,raster]"

# Web 后端
python -m pip install -e ".[web]"

# 全量依赖
python -m pip install -e ".[all]"
```

## CLI 快速开始

```bash
# 查看帮助与示例
python -m src.main -h
python -m src.main --help-examples

# Demo
python -m src.main --mode demo --plot box --title "箱线图演示"
python -m src.main --mode demo --plot scatter3d --title "3D Scatter"
python -m src.main --mode demo --plot confusion --title "Confusion Matrix"

# 文件模式
python -m src.main --mode file --plot scatter --file data/demo_scatter.csv --x-col x --y-col y
python -m src.main --mode file --plot scatter3d --file data/demo_scatter3d.csv --x-col x --y-col y --z-col z

# 地图
python -m src.main --plot choropleth_world --file data/world_choropleth.csv --key-col ISO_A3 --value-col value --on iso_a3
python -m src.main --plot points --basemap china_l1 --file data/points_cn.csv --lon-col lon --lat-col lat
```

也可通过入口命令运行：

```bash
research-draw --help
```

## Web 快速开始

后端（项目根目录）：

```bash
python -m pip install -e ".[web,data,ml,maps,raster]"
python -m uvicorn web.backend.app:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd web/frontend
npm install
npm run dev
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

Web 端已支持：

- 顶部菜单 + 左侧导航
- 文件上传与表格录入
- 图标题与 `xlabel/ylabel/zlabel` 与数据分离
- 渲染历史管理、本地渲染文件管理
- 关于页面（读取 `web/assets` 联系方式素材）
- 用户手册页面（读取并渲染 `ResearchDrawApp_使用手册.md`）

## 测试

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest -q
```

说明：

- `tests/`：标准 pytest 自动化测试（CI 主入口）
- `scripts/`：运维与数据准备脚本（底图下载、demo 数据生成、手工 smoke）

## 配置

`PlotConfig` 支持 `.env`/环境变量，例如：

```bash
PLOT_BACKEND=TkAgg
PLOT_THEME=DEFAULT
PLOT_DPI=300
PLOT_FORMAT=PNG
PLOT_SAVE_DIR=outputs/figures
MAP_BASEMAP_ROOT=./data/geo
```

运行时可覆盖：

- `--outdir`：覆盖当前运行输出目录
- `--basemap-root`：覆盖离线底图目录
- `--config`：读取 JSON/YAML 配置（命令行参数优先级更高）

## 文档

- CLI/Web 详细手册：`ResearchDrawApp_使用手册.md`
- Web 模块说明：`web/README.md`
- 脚本层说明：`scripts/README.md`

## 项目结构

```text
research-draw/
├── src/
│   ├── main.py              # 入口（薄层）
│   ├── cli/                 # 参数解析与配置合并
│   ├── dispatch/            # 图型路由与执行
│   ├── registry/            # 图型注册中心（分组/别名/默认/依赖/demo）
│   ├── loaders/             # 文件/表格/JSON 数据读取
│   ├── plotters/            # Plotter 类发现
│   ├── save/                # 导出与保存
│   ├── chart/
│   │   ├── plot_2d/         # 2D 图（统计 + 地图）
│   │   └── plot_3d/         # 3D 图
│   └── util/                # 通用工具（含依赖提示、统计工具）
├── tests/                   # pytest 自动化测试
├── scripts/                 # 数据准备/底图下载/手工 smoke 脚本
├── web/                     # FastAPI + Vue3
├── data/                    # demo 数据与离线底图
├── outputs/                 # 输出目录
└── pyproject.toml           # 依赖与打包配置
```
