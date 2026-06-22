from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[2]
FINANCE_DIR = BASE_DIR / "40-finance"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from launcher_core.registry import load_registry_apps  # noqa: E402

HUB_ID = "analysis-hub"

HUB_META: dict[str, tuple[str, str]] = {
    "portfolio-analysis": ("Portfolio", "主要候補"),
    "portfolio-audit": ("Risk", "主要候補"),
    "factor-simulator": ("Factor", "実験寄り"),
    "regime-simulator": ("Regime", "実験寄り"),
    "bpp-tool": ("Lab", "実験置き場"),
    "saas-replacement-lab": ("Lab", "保留"),
}
DEFAULT_GROUP = "Lab"
DEFAULT_STATUS = "未分類"


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    group: str
    path: Path
    description: str
    status: str
    data: str = "共有ファクター/マーケットデータ"


def load_modules() -> list[ModuleInfo]:
    apps = load_registry_apps(BASE_DIR, BASE_DIR / "app-registry", include_hidden=True)
    modules: list[ModuleInfo] = []
    for app in apps:
        if app.merged_into != HUB_ID:
            continue
        group, status = HUB_META.get(app.id, (DEFAULT_GROUP, DEFAULT_STATUS))
        modules.append(
            ModuleInfo(
                name=app.name,
                group=group,
                path=app.entry,
                description=app.description or "（説明未設定）",
                status=status,
            )
        )
    modules.sort(key=lambda m: (m.group, m.name))
    return modules


def open_in_explorer(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"見つかりません: {path}"
    try:
        subprocess.Popen(["explorer", "/select,", str(path)])
        return True, f"開きました: {path}"
    except OSError as exc:
        return False, f"開けませんでした: {exc}"


def render_module(module: ModuleInfo) -> None:
    with st.container(border=True):
        cols = st.columns([3, 1.2, 1.4])
        with cols[0]:
            st.subheader(module.name)
            st.write(module.description)
            st.caption(f"データ: {module.data}")
            st.code(str(module.path), language="text")
        with cols[1]:
            st.metric("状態", module.status)
            st.caption(f"分類: {module.group}")
        with cols[2]:
            if st.button("ファイルを表示", key=f"open-{module.name}", use_container_width=True):
                ok, msg = open_in_explorer(module.path)
                (st.success if ok else st.error)(msg)
            if st.button("フォルダを表示", key=f"folder-{module.name}", use_container_width=True):
                ok, msg = open_in_explorer(module.path.parent)
                (st.success if ok else st.error)(msg)


def main() -> None:
    st.set_page_config(page_title="分析・予測・リスク母艦", page_icon="📊", layout="wide")
    st.title("分析・予測・リスク母艦")
    st.caption("未完成に近い金融分析コードを消さずに、ひとつの入口から見える形で束ねるための母艦です。")

    modules = load_modules()

    st.markdown("---")
    overview_cols = st.columns(4)
    overview_cols[0].metric("統合候補", len(modules))
    overview_cols[1].metric("主要候補", sum(1 for m in modules if m.status == "主要候補"))
    overview_cols[2].metric("実験寄り", sum(1 for m in modules if "実験" in m.status))
    overview_cols[3].metric("共有データ", "factor_data")

    st.info(
        "データ取得は別アプリに残し、この母艦は分析、将来予測、リスク分析、監査、実験コードの整理に集中します。"
        " 表示内容は `app-registry/*.json` のうち `merged_into: analysis-hub` のものを自動で集約しています。"
    )

    tabs = st.tabs(["Overview", "Portfolio", "Factor", "Regime", "Risk", "Forecast", "Lab", "Files"])

    with tabs[0]:
        st.subheader("統合方針")
        st.write(
            "ランチャーには個別の未完成アプリを並べすぎず、ここで役割別に束ねます。"
            "現段階では既存ファイルを移動せず、統合先と状態を見える化します。"
        )
        for module in modules:
            render_module(module)

    for tab, group in zip(tabs[1:7], ["Portfolio", "Factor", "Regime", "Risk", "Forecast", "Lab"]):
        with tab:
            st.subheader(group)
            if group == "Forecast":
                st.write("将来予測系は、レジーム分析とファクター分析を土台に後から追加する領域です。")
                shown = [m for m in modules if m.group in {"Regime", "Factor"}]
            elif group == "Risk":
                shown = [m for m in modules if m.group in {"Risk", "Portfolio"}]
            else:
                shown = [m for m in modules if m.group == group]
            if not shown:
                st.caption("このカテゴリに登録された統合候補はまだありません。")
            for module in shown:
                render_module(module)

    with tabs[7]:
        st.subheader("関連ファイル")
        rows = [
            {"name": m.name, "group": m.group, "status": m.status, "path": str(m.path), "exists": m.path.exists()}
            for m in modules
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(
            "ここに出ている既存コードは削除せず、段階的に共通モジュールへ寄せていく想定です。"
            " 新しい統合候補は `app-registry/<id>.json` に `merged_into: analysis-hub` を付けて追加します。"
        )


if __name__ == "__main__":
    main()
