"""检查数学建模工作流所需的环境与依赖。

用法:
    python check_env.py

退出码:
    0  核心依赖齐全
    1  缺少核心 Python 包（建议先安装再继续）
    2  仅缺少可选工具（可继续，但部分验证会受限）
"""

from __future__ import annotations

import importlib.util
import shutil
import sys


CORE_PACKAGES = [
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "sklearn",
    "openpyxl",
    "docx",          # python-docx（Word 论文草稿/公式 OMML）
    "lxml",          # OOXML/XML 处理
    "seaborn",       # 统计绘图
    "statsmodels",   # 回归/置信区间
    "pypdf",         # PDF 读取
    "pdfplumber",    # PDF 表格/文本
    "PIL",           # 图像处理/预览
]

OPTIONAL_TOOLS = [
    ("python", "数值计算与绘图"),
    ("typst", "Typst 论文编译（可选）"),
    ("xelatex", "LaTeX 论文编译（可选）"),
    ("drawio", "DrawIO 流程图导出（可选）"),
    ("draw.io", "DrawIO 备用命令（可选）"),
    ("pdftoppm", "PDF 转 PNG 视觉检查（可选）"),
    ("mutool", "PDF 转 PNG 备用（可选）"),
    ("magick", "PDF 转 PNG 备用（可选）"),
    ("pandoc", "文档转换（可选）"),
    ("soffice", "LibreOffice（Excel 公式重算，可选）"),
    ("matlab", "MATLAB 实现与绘图（可选）"),
]


def main() -> int:
    print("== Python ==")
    print(f"python: {sys.version.split()[0]}")

    print("\n== 核心 Python 包 ==")
    missing_core: list[str] = []
    for pkg in CORE_PACKAGES:
        ok = importlib.util.find_spec(pkg) is not None
        print(f"{pkg}: {'OK' if ok else 'MISSING'}")
        if not ok:
            missing_core.append(pkg)

    print("\n== 可选外部工具 ==")
    missing_tools: list[str] = []
    for tool, desc in OPTIONAL_TOOLS:
        path = shutil.which(tool)
        print(f"{tool}: {path or 'MISSING'}  ({desc})")
        if path is None:
            missing_tools.append(tool)
    if not (shutil.which("drawio") or shutil.which("draw.io")):
        import os
        drawio_known = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "draw.io", "draw.io.exe"),
            r"C:\Program Files\draw.io\draw.io.exe",
        ]
        extra = next((p for p in drawio_known if os.path.isfile(p)), None)
        if extra:
            print(f"drawio: 已知安装路径 {extra}（未在 PATH；技能已按此路径调用）")

    print("\n== 中文字体 ==")
    import os
    font_paths = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    found_font = next((p for p in font_paths if os.path.isfile(p)), None)
    print(f"中文字体: {found_font or 'MISSING（图/PDF 中文可能缺字）'}")

    print()
    if missing_core:
        print(f"缺少核心包: {', '.join(missing_core)}")
        print("建议安装: pip install -r <技能根目录>/requirements.txt")
        return 1
    if missing_tools:
        print(f"缺少可选工具: {', '.join(missing_tools)}")
        print("可继续，但相关验证会受限；请按 doctor 思路补齐需要的能力。")
        return 2
    print("环境完整。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
