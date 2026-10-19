"""AI 使用报告一致性审计（提交前门禁）。

用法:
    python ai_report_audit.py <PROJECT_ROOT> [--report <报告.docx>] [--paper <论文.docx>]

检查:
   1. 论文「AI 工具使用声明」位于参考文献之前;
   2. 声明二选一且存在; 若 ai_usage_log.md 有使用记录则必须为"使用了 AI 工具";
   3. AI使用报告四大部分结构齐全, 与论文声明勾选一致;
   4. 报告"未使用任何 AI 工具"而留痕/工具清单显示使用 -> FAIL;
   5. AI工具使用详情.pdf 存在(若报告已冻结);
   6. 典型前后不一致只提示 WARN, 需人工确认。

退出码: 0=全部 PASS(允许 WARN), 1=存在 FAIL。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from docx import Document
except Exception as e:  # pragma: no cover
    print(f"[FATAL] 需要 python-docx: {e}", file=sys.stderr)
    sys.exit(2)


HEADINGS_REPORT = [
    "AI 工具使用声明",
    "所用 AI 工具清单",
    "使用概述",
    "分环节使用记录",
    "提示词",
    "人工贡献与核验",
]


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def docx_all_text(doc) -> list[str]:
    """返回正文段落 + 表格单元格文本（按出现先后）。"""
    texts: list[str] = []
    for p in doc.paragraphs:
        if p.text and p.text.strip():
            texts.append(p.text.strip())
    for tbl in doc.tables:
        for row in tbl.rows:
            cells = []
            for c in row.cells:
                t = c.text.strip()
                if t:
                    cells.append(t)
            if cells:
                texts.append(" | ".join(cells))
    return texts


def first_heading_index(texts: list[str], key: str) -> int:
    k = norm(key)
    for i, t in enumerate(texts):
        if k and k in norm(t):
            return i
    return -1


def selected_declaration(doc) -> str | None:
    """读第一个含'声明原文'的表，返回被勾选行的完整文本；找不到返回 None。"""
    for tbl in doc.tables:
        header = None
        for row in tbl.rows:
            cells = [c.text.strip() for c in row.cells]
            joined = " ".join(cells)
            if "声明原文" in joined and "AI 工具" in joined:
                header = row
                break
        if header is None:
            continue
        # 找勾选标记行：表头之后首列出现勾/是/使用等标记
        found = False
        for row in tbl.rows:
            if row is header:
                continue
            cells = [c.text.strip() for c in row.cells]
            if not cells:
                continue
            first = norm(cells[0])
            if any(m in first for m in ("√", "☑", "是", "✓", "使用", "勾选", "×")):
                found = True
                return " ".join(cells)
        if found:
            return None  # 表头在但勾选行解析不出 -> 后续按全文判定
    return None


def count_log_usage(log_path: Path) -> tuple[int, list[str]]:
    """统计留痕中的实质使用行（含论文部分编号/环节且有对应内容）。"""
    if not log_path.exists():
        return 0, []
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    used = []
    for ln in lines:
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        joined = norm(" ".join(cells))
        if re.match(r"^(S\d+|Q\d+)", norm(cells[0])):
            # 有工具/AI 参与或对应文件内容即视为该环节有记录
            body = norm(" ".join(cells[1:]))
            if any(k in body for k in ("AI", "工具", "脚本", "模型", "代码", "绘图", "草稿")):
                used.append(cells[0])
    return len(used), used


def audit(project: Path, report_docx: Path | None, paper_docx: Path | None) -> int:
    fails: list[str] = []
    warns: list[str] = []
    passes: list[str] = []

    # ---- 0. 输入 ----
    if not project.is_dir():
        print(f"[FAIL] PROJECT_ROOT 不存在: {project}")
        return 1
    paper = paper_docx or (project / "完整论文.docx")
    if not paper.exists():
        paper = project / "论文草稿.docx"
    if not paper.exists():
        print(f"[FAIL] 找不到论文 DOCX（完整论文.docx/论文草稿.docx）: {paper}")
        return 1

    paper_doc = Document(str(paper))
    p_texts = docx_all_text(paper_doc)

    # ---- 1. 声明位于参考文献之前 ----
    decl_idx = first_heading_index(p_texts, "AI 工具使用声明")
    ref_idx = first_heading_index(p_texts, "参考文献")
    if decl_idx < 0:
        fails.append("论文中未找到「AI 工具使用声明」标题")
    elif ref_idx < 0:
        fails.append("论文中未找到「参考文献」标题，无法核对声明位置")
    elif decl_idx > ref_idx:
        fails.append("「AI 工具使用声明」位于参考文献之后，官方要求位于参考文献之前")
    else:
        passes.append(f"声明位于参考文献之前（声明@{decl_idx} < 参考文献@{ref_idx}）")

    # ---- 2. 声明二选一与使用留痕一致性 ----
    used_decl = any("使用了 AI 工具" in norm(t) for t in p_texts)
    unused_decl = any("未使用任何 AI 工具" in norm(t) for t in p_texts)
    if not used_decl and not unused_decl:
        fails.append("论文 AI 使用声明未命中官方二选一文案（使用/未使用）")
    else:
        passes.append(f"声明文案: {'使用了 AI 工具' if used_decl else '未使用任何 AI 工具'}")

    log_path = project / "ai_usage_log.md"
    log_count, log_ids = count_log_usage(log_path)
    if log_count == 0:
        warns.append("ai_usage_log.md 缺失或无实质使用行——报告前需补留痕")
    else:
        passes.append(f"ai_usage_log.md 有 {log_count} 条使用记录（{', '.join(log_ids[:8])}）")
        if unused_decl and not used_decl:
            fails.append("论文声明『未使用任何 AI 工具』，但 ai_usage_log.md 存在使用记录——前后矛盾")

    # ---- 3. 报告结构 ----
    if report_docx is None or not report_docx.exists():
        warns.append("未提供 AI使用报告.docx（生成报告后再审计其结构）")
    else:
        rep_doc = Document(str(report_docx))
        rep_texts = docx_all_text(rep_doc)
        for key in HEADINGS_REPORT:
            if not any(norm(key) in norm(t) for t in rep_texts):
                fails.append(f"AI 使用报告缺少结构部分: {key}")
            else:
                passes.append(f"AI 使用报告包含: {key}")

        sel = selected_declaration(rep_doc)
        if sel:
            if "未使用任何 AI 工具" in norm(sel):
                if log_count > 0:
                    fails.append("报告勾选『未使用任何 AI 工具』，但留痕有使用记录")
                elif used_decl:
                    fails.append("报告勾选『未使用任何 AI 工具』，但论文声明为『使用了 AI 工具』")
                else:
                    passes.append("报告勾选『未使用任何 AI 工具』且无使用留痕")
            elif "使用了 AI 工具" in norm(sel):
                if unused_decl and not used_decl:
                    fails.append("报告勾选『使用了 AI 工具』，但论文声明为『未使用任何 AI 工具』")
                else:
                    passes.append("报告勾选『使用了 AI 工具』，与论文声明一致")
            else:
                warns.append("报告声明勾选行未命中官方文案，需人工核对")
        else:
            warns.append("未能从报告表解析勾选行，需人工核对声明选择")

        # 典型矛盾：报告某环节写"未使用"但留痕有该环节对应记录
        domain_map = {
            "模型建立": ("Q", "建模"),
            "问题理解": ("S1", "问题重述"),
            "编程实现": ("代码", "脚本", "py"),
            "数据处理": ("S2", "preprocess", "清洗"),
        }
        for keyword, clue in domain_map.items():
            for t in rep_texts:
                if keyword in t and "未使用" in t:
                    if any(k in norm(t) for k in clue if isinstance(k, str)):
                        warns.append(
                            f"报告中「{keyword}…未使用」与留痕线索({clue})冲突或口径需人工确认"
                        )

    # ---- 4. 导出 PDF 文件名 ----
    pdf = project / "AI工具使用详情.pdf"
    if pdf.exists():
        passes.append("AI工具使用详情.pdf 已存在")
    else:
        warns.append("AI工具使用详情.pdf 尚未生成（冻结并导出后再验）")

    # ---- 5. 输出 ----
    for p in passes:
        print(f"[PASS] {p}")
    for w in warns:
        print(f"[WARN] {w}")
    for f in fails:
        print(f"[FAIL] {f}")
    print(f"RESULT: PASS={len(passes)} WARN={len(warns)} FAIL={len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI 使用报告一致性审计")
    ap.add_argument("project", type=Path, help="PROJECT_ROOT")
    ap.add_argument("--report", type=Path, default=None, help="AI使用报告.docx 路径")
    ap.add_argument("--paper", type=Path, default=None, help="论文 DOCX 路径（默认自动找）")
    args = ap.parse_args()
    return audit(args.project, args.report, args.paper)


if __name__ == "__main__":
    raise SystemExit(main())
