from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional
from urllib.parse import quote
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Web service runs in headless mode by default.
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PLOT_BACKEND", "Agg")
os.environ.setdefault("HEADLESS", "1")

from src.main import ResearchDrawApp  # noqa: E402
from src.registry import canonical_plots_by_group, plot_registry_payload  # noqa: E402


WEB_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "web"
UPLOAD_DIR = WEB_OUTPUT_ROOT / "uploads"
RENDER_DIR = WEB_OUTPUT_ROOT / "renders"
WEB_ASSETS_DIR = PROJECT_ROOT / "web" / "assets"
USER_MANUAL_FILE = PROJECT_ROOT / "ResearchDrawApp_使用手册.md"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_UPLOAD_SUFFIX = {".csv", ".tsv", ".txt", ".xlsx", ".xls"}
CONTACT_IMAGE_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

class RenderRequest(BaseModel):
    mode: Literal["demo", "custom", "file"] = "demo"
    plot: str = "box"
    title: Optional[str] = None
    fmt: Literal["png", "svg", "pdf"] = "png"
    uploaded_file: Optional[str] = None
    args: Dict[str, Any] = Field(default_factory=dict)


class RenderResponse(BaseModel):
    ok: bool
    save_name: str
    fmt: str
    image_url: str
    argv: list[str]


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    columns: list[str] = Field(default_factory=list)
    preview_rows: list[dict[str, Any]] = Field(default_factory=list)


class UploadFileItem(BaseModel):
    file_id: str
    size: int
    modified_at: str


class UploadListResponse(BaseModel):
    items: list[UploadFileItem] = Field(default_factory=list)


class RenderFileItem(BaseModel):
    filename: str
    size: int
    modified_at: str
    image_url: str


class RenderListResponse(BaseModel):
    items: list[RenderFileItem] = Field(default_factory=list)


class DeleteResponse(BaseModel):
    ok: bool = True
    deleted: int = 0
    detail: str = ""


class ContactAssetItem(BaseModel):
    name: str
    url: str


class ContactAssetResponse(BaseModel):
    items: list[ContactAssetItem] = Field(default_factory=list)


class UserManualResponse(BaseModel):
    title: str
    content: str


def _safe_resolve_input_file(raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=400, detail=f"输入文件不存在: {candidate}")
    if not str(candidate).startswith(str(PROJECT_ROOT)):
        raise HTTPException(status_code=400, detail="只允许读取项目目录内文件")
    return candidate


def _safe_upload_file(file_id: str) -> Path:
    clean = Path(file_id).name
    p = (UPLOAD_DIR / clean).resolve()
    if not str(p).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=400, detail="非法上传文件标识")
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail=f"上传文件不存在: {file_id}")
    return p


def _safe_render_file(filename: str) -> Path:
    clean = Path(filename).name
    p = (RENDER_DIR / clean).resolve()
    if not str(p).startswith(str(RENDER_DIR.resolve())):
        raise HTTPException(status_code=400, detail="非法渲染文件路径")
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail=f"渲染文件不存在: {filename}")
    return p


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def _sorted_files(root: Path) -> list[Path]:
    files = [p for p in root.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _asset_url(relative_path: Path) -> str:
    encoded = "/".join(quote(part) for part in relative_path.as_posix().split("/"))
    return f"/assets/{encoded}"


def _records_from_dataframe(df, limit: int = 5) -> tuple[list[str], list[dict[str, Any]]]:
    cols = [str(c) for c in df.columns]
    head = df.head(limit)
    try:
        head = head.where(head.notna(), None)
    except Exception:
        pass
    rows = head.to_dict(orient="records")
    return cols, rows


def _inspect_upload_file(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd  # type: ignore

            df = pd.read_excel(path)
            return _records_from_dataframe(df)
        except Exception:
            return [], []

    seps = [",", "\t", ";"] if suffix in {".csv", ".tsv", ".txt"} else [","]
    for sep in seps:
        for enc in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with path.open("r", encoding=enc, newline="") as f:
                    reader = csv.DictReader(f, delimiter=sep)
                    fieldnames = [str(c) for c in (reader.fieldnames or [])]
                    if not fieldnames:
                        continue
                    preview = []
                    for i, row in enumerate(reader):
                        if i >= 5:
                            break
                        clean = {str(k): (v if v != "" else None) for k, v in (row or {}).items()}
                        preview.append(clean)
                    return fieldnames, preview
            except Exception:
                continue

    try:
        import pandas as pd  # type: ignore

        df = pd.read_csv(path)
        return _records_from_dataframe(df)
    except Exception:
        return [], []


def _flag_name(dest_key: str) -> str:
    return f"--{dest_key.replace('_', '-')}"


def _append_arg(argv: list[str], key: str, value: Any) -> None:
    if value is None:
        return
    flag = _flag_name(key)
    if isinstance(value, bool):
        if value:
            argv.append(flag)
        return
    if isinstance(value, (list, tuple)):
        if key == "group":
            for item in value:
                argv.extend([flag, str(item)])
        elif key in {"x", "y", "z", "u", "v", "w", "scalar", "labels", "forest_labels", "effects", "ci_low", "ci_high", "weights"}:
            joined = ",".join(str(x) for x in value)
            argv.extend([flag, joined])
        else:
            argv.extend([flag, ",".join(str(x) for x in value)])
        return
    if isinstance(value, dict):
        argv.extend([flag, json.dumps(value, ensure_ascii=False)])
        return
    argv.extend([flag, str(value)])


def _build_argv(req: RenderRequest, save_name: str) -> list[str]:
    argv: list[str] = [
        "--mode",
        req.mode,
        "--plot",
        req.plot,
        "--no-show",
        "--outdir",
        str(RENDER_DIR),
        "--save-name",
        save_name,
        "--fmt",
        req.fmt,
    ]
    if req.title:
        argv.extend(["--title", req.title])

    payload_args = dict(req.args or {})
    if req.uploaded_file:
        payload_args["file"] = str(_safe_upload_file(req.uploaded_file))
    elif req.mode == "file" and "file" in payload_args and payload_args["file"]:
        payload_args["file"] = str(_safe_resolve_input_file(str(payload_args["file"])))

    if req.mode == "file" and not payload_args.get("file"):
        raise HTTPException(status_code=400, detail="file 模式需要上传文件或提供 args.file")

    reserved = {"mode", "plot", "title", "fmt", "outdir", "save_name", "no_show", "uploaded_file", "args"}
    for key, value in payload_args.items():
        if key in reserved:
            continue
        _append_arg(argv, key, value)
    return argv


app = FastAPI(title="Research Draw Web API", version="v0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

if WEB_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_ASSETS_DIR)), name="assets")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/plots")
def list_plots() -> Dict[str, list[str]]:
    return canonical_plots_by_group()


@app.get("/api/plot-registry")
def get_plot_registry() -> Dict[str, Any]:
    return plot_registry_payload()


@app.get("/api/contact-assets", response_model=ContactAssetResponse)
def list_contact_assets() -> ContactAssetResponse:
    if not WEB_ASSETS_DIR.exists():
        return ContactAssetResponse(items=[])

    items: list[ContactAssetItem] = []
    for path in sorted(WEB_ASSETS_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in CONTACT_IMAGE_SUFFIX:
            continue
        relative = path.relative_to(WEB_ASSETS_DIR)
        items.append(ContactAssetItem(name=path.stem, url=_asset_url(relative)))
    return ContactAssetResponse(items=items)


@app.get("/api/user-manual", response_model=UserManualResponse)
def get_user_manual() -> UserManualResponse:
    if not USER_MANUAL_FILE.exists():
        return UserManualResponse(title="用户手册页面", content="用户手册文件不存在。")
    content = USER_MANUAL_FILE.read_text(encoding="utf-8")
    return UserManualResponse(title="用户手册页面", content=content)


@app.post("/api/upload", response_model=UploadResponse)
def upload_data(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIX:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {suffix}")

    file_id = f"{uuid4().hex}{suffix}"
    target = UPLOAD_DIR / file_id
    size = 0
    with target.open("wb") as out:
        chunk = file.file.read(1024 * 1024)
        while chunk:
            size += len(chunk)
            out.write(chunk)
            chunk = file.file.read(1024 * 1024)
    columns, preview_rows = _inspect_upload_file(target)
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=size,
        columns=columns,
        preview_rows=preview_rows,
    )


@app.get("/api/uploads", response_model=UploadListResponse)
def list_upload_files() -> UploadListResponse:
    items = [
        UploadFileItem(
            file_id=p.name,
            size=p.stat().st_size,
            modified_at=_mtime_iso(p),
        )
        for p in _sorted_files(UPLOAD_DIR)
    ]
    return UploadListResponse(items=items)


@app.get("/api/uploads/{file_id}/inspect", response_model=UploadResponse)
def inspect_upload_file(file_id: str) -> UploadResponse:
    fp = _safe_upload_file(file_id)
    columns, preview_rows = _inspect_upload_file(fp)
    return UploadResponse(
        file_id=fp.name,
        filename=fp.name,
        size=fp.stat().st_size,
        columns=columns,
        preview_rows=preview_rows,
    )


@app.delete("/api/uploads/{file_id}", response_model=DeleteResponse)
def delete_upload_file(file_id: str) -> DeleteResponse:
    fp = _safe_upload_file(file_id)
    fp.unlink(missing_ok=False)
    return DeleteResponse(ok=True, deleted=1, detail=f"已删除上传文件: {fp.name}")


@app.delete("/api/uploads", response_model=DeleteResponse)
def clear_upload_files() -> DeleteResponse:
    files = _sorted_files(UPLOAD_DIR)
    deleted = 0
    for fp in files:
        try:
            fp.unlink(missing_ok=True)
            deleted += 1
        except Exception:
            continue
    return DeleteResponse(ok=True, deleted=deleted, detail=f"已清空上传文件: {deleted} 个")


@app.post("/api/render", response_model=RenderResponse)
def render(req: RenderRequest) -> RenderResponse:
    save_name = f"web_{uuid4().hex[:10]}"
    argv = _build_argv(req, save_name)
    try:
        ResearchDrawApp(argv).run()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"渲染失败: {e}") from e

    outpath = (RENDER_DIR / f"{save_name}.{req.fmt}").resolve()
    if not outpath.exists():
        raise HTTPException(status_code=500, detail=f"渲染完成但未找到输出文件: {outpath}")
    return RenderResponse(
        ok=True,
        save_name=save_name,
        fmt=req.fmt,
        image_url=f"/api/files/{outpath.name}",
        argv=argv,
    )


@app.get("/api/renders", response_model=RenderListResponse)
def list_render_files() -> RenderListResponse:
    items = [
        RenderFileItem(
            filename=p.name,
            size=p.stat().st_size,
            modified_at=_mtime_iso(p),
            image_url=f"/api/files/{p.name}",
        )
        for p in _sorted_files(RENDER_DIR)
    ]
    return RenderListResponse(items=items)


@app.delete("/api/renders/{filename}", response_model=DeleteResponse)
def delete_render_file(filename: str) -> DeleteResponse:
    fp = _safe_render_file(filename)
    fp.unlink(missing_ok=False)
    return DeleteResponse(ok=True, deleted=1, detail=f"已删除渲染文件: {fp.name}")


@app.delete("/api/renders", response_model=DeleteResponse)
def clear_render_files() -> DeleteResponse:
    files = _sorted_files(RENDER_DIR)
    deleted = 0
    for fp in files:
        try:
            fp.unlink(missing_ok=True)
            deleted += 1
        except Exception:
            continue
    return DeleteResponse(ok=True, deleted=deleted, detail=f"已清空渲染文件: {deleted} 个")


@app.get("/api/files/{filename}")
def get_render_file(filename: str):
    fp = _safe_render_file(filename)
    return FileResponse(fp)
