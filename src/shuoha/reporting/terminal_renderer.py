from shuoha.reporting.markdown_renderer import render_elevator_summary
from shuoha.schemas import AnalysisResult


def _strip_inline_markdown(text: str) -> str:
    return text.replace("`", "")


def _format_title(title: str) -> str:
    return f"================ 股票报告 | {title} ================"


def render_terminal_summary(result: AnalysisResult) -> str:
    lines = render_elevator_summary(result).splitlines()
    body = []
    for line in lines[1:]:
        if "：" not in line:
            continue
        label, value = line.split("：", 1)
        body.append(f"[{label}] {_strip_inline_markdown(value)}")
    top = "================ 电梯摘要 ================"
    bottom = "=" * len(top)
    return "\n".join([top, *body, bottom])


def render_terminal_report(markdown: str) -> str:
    rendered_lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            rendered_lines.append(_format_title(_strip_inline_markdown(line.removeprefix("# ").strip())))
            continue
        if line.startswith("## "):
            if rendered_lines and rendered_lines[-1] != "":
                rendered_lines.append("")
            rendered_lines.append(f"[{_strip_inline_markdown(line.removeprefix('## ').strip())}]")
            continue
        rendered_lines.append(_strip_inline_markdown(line))
    return "\n".join(rendered_lines)
