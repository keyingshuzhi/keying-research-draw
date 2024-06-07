from __future__ import annotations

from pathlib import Path

from src.dispatch.handlers.base import HandlerContext, HandlerResult
from src.dispatch.handlers.helpers import apply_demo_map_defaults
from src.loaders.data_loader import auto_sep, parse_csv_list, parse_size_range, read_dataframe, read_points_from_table


class MapHandler:
    key = "map"

    def __init__(self, ctx: HandlerContext) -> None:
        self.ctx = ctx
        self.args = ctx.args

    def _decorate_axes(self, plotter, ax) -> None:
        if hasattr(plotter, "add_north_arrow"):
            plotter.add_north_arrow(ax)
        if hasattr(plotter, "add_scalebar"):
            plotter.add_scalebar(ax)

    def render(self, plot_key: str, mode: str) -> HandlerResult:
        if self.ctx.map_plotter_cls is None:
            raise ImportError("地图模块未找到：请确认存在 src/chart/plot_2d/geo_atlas.py（或 cartography/geo_thematic/domain_analysis）")

        if mode == "demo":
            apply_demo_map_defaults(self.args, plot_key, self.ctx.project_root)
        title = self.args.title

        kwargs = {
            "theme": self.args.map_theme,
            "include_taiwan": bool(getattr(self.args, "include_taiwan", True)),
            "include_hk_mo": bool(getattr(self.args, "include_hk_mo", True)),
        }
        if self.args.basemap_root:
            kwargs["basemap_root"] = Path(self.args.basemap_root)
        if getattr(self.args, "taiwan_name", None):
            kwargs["taiwan_name"] = self.args.taiwan_name

        p = self.ctx.map_plotter_cls(**kwargs)
        rendered = self._render_plot(p, plot_key, title)
        return HandlerResult(plotter=p, rendered=rendered, plot_key=plot_key, title=title)

    def _render_plot(self, p, plot: str, title: str | None):
        import matplotlib.pyplot as plt

        if plot == "map_world":
            ret = p.plot_world_admin0(
                title=title or "World Countries",
                crs=self.args.crs,
                highlight_countries=parse_csv_list(self.args.highlight),
                label=self.args.label_names,
            )
            self._decorate_axes(p, ret[1])
            return ret
        if plot == "map_world_admin1":
            ret = p.plot_world_admin1(
                countries=parse_csv_list(self.args.countries),
                title=title or "World Admin1",
                crs=self.args.crs,
                label=self.args.label_names,
                country_field=self.args.country_field,
                case_insensitive=not self.args.case_sensitive,
            )
            self._decorate_axes(p, ret[1])
            return ret
        if plot == "map_china":
            ret = p.plot_china(
                level=int(self.args.level or 1),
                title=title or f"China L{int(self.args.level or 1)}",
                crs=self.args.crs,
                highlight_names=parse_csv_list(self.args.highlight),
                label=self.args.label_names,
            )
            self._decorate_axes(p, ret[1])
            return ret
        if plot == "map_choropleth_world":
            if not self.args.file:
                raise ValueError("choropleth_world 需要 --file 指向含数据的 CSV/TSV/Excel")
            path = Path(self.args.file).expanduser().resolve()
            df = read_dataframe(path, auto_sep(path, self.args.sep))
            key_col = self.args.key_col or "ISO_A3"
            value_col = self.args.value_col or "value"
            on = (self.args.on or "iso_a3").lower()
            cmap = self.args.cmap or self.args.map_theme
            ret = p.choropleth_world(
                df,
                key_col=key_col,
                value_col=value_col,
                on="name" if on == "name" else "iso_a3",
                scheme=self.args.scheme,
                k=int(self.args.k or 5),
                cmap=cmap,
                title=title or "World Choropleth",
                crs=self.args.crs,
                label_top_n=int(self.args.label_top_n or 0),
            )
            self._decorate_axes(p, ret[1])
            return ret
        if plot == "map_choropleth_china":
            if not self.args.file:
                raise ValueError("choropleth_china 需要 --file 指向含数据的 CSV/TSV/Excel")
            path = Path(self.args.file).expanduser().resolve()
            df = read_dataframe(path, auto_sep(path, self.args.sep))
            key_col = self.args.key_col or (f"NAME_{int(self.args.level or 1)}")
            value_col = self.args.value_col or "value"
            on = (self.args.on or "NAME").upper()
            cmap = self.args.cmap or "Reds"
            ret = p.choropleth_china(
                df,
                key_col=key_col,
                value_col=value_col,
                level=int(self.args.level or 1),
                on="GID" if on == "GID" else "NAME",
                scheme=self.args.scheme,
                k=int(self.args.k or 5),
                cmap=cmap,
                title=title or "China Choropleth",
                crs=self.args.crs,
                label_top_n=int(self.args.label_top_n or 0),
            )
            self._decorate_axes(p, ret[1])
            return ret
        if plot == "map_raster":
            raster_path = self.args.raster_file or ""
            if not raster_path:
                raise ValueError("raster 模式需要提供 --raster-file")
            ret = p.raster_on_map(
                raster_path=raster_path,
                title=title or "Raster Overlay",
                alpha=float(self.args.alpha or 0.65),
                basemap=self.args.basemap,
            )
            self._decorate_axes(p, ret[1])
            return ret
        if plot == "map_points":
            base = (self.args.basemap or "world_admin0").lower()
            if base == "china_l1":
                fig, ax, _ = p.plot_china(level=1, title=title or "Points on China", crs=self.args.crs)
            elif base == "none":
                fig = plt.figure(figsize=(9.5, 5.8))
                ax = plt.gca()
                ax.set_axis_off()
            else:
                fig, ax, _ = p.plot_world_admin0(title=title or "Points on World", crs=self.args.crs)

            if not self.args.file:
                raise ValueError("points 模式需要 --file（CSV/TSV/Excel/GeoJSON/GPKG/SHP）与 --lon-col/--lat-col（表格）")
            data_path = Path(self.args.file).expanduser().resolve()
            if data_path.suffix.lower() in {".csv", ".tsv", ".txt", ".xlsx", ".xls"}:
                if not (self.args.lon_col and self.args.lat_col):
                    raise ValueError("表格叠加请提供 --lon-col 与 --lat-col")
                gpts = read_points_from_table(data_path, self.args.lon_col, self.args.lat_col)
            else:
                import geopandas as gpd

                gpts = gpd.read_file(data_path)
                if gpts.crs is None:
                    gpts.set_crs("EPSG:4326", inplace=True)

            p.overlay_points(
                ax,
                gpts,
                size_col=self.args.size_col,
                size_range=parse_size_range(self.args.size_range),
                hue_col=self.args.hue_col,
                label_col=self.args.label_col,
                legend=True,
            )
            self._decorate_axes(p, ax)
            return fig, ax
        raise ValueError(f"未知地图类型 / Unknown map plot: {self.args.plot}")
