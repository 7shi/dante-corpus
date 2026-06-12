import argparse
import string
import sys
from pathlib import Path

from ._paths import SRC_DIR, QUOTES_DIR
from .tokenizer import has_alpha, tokenize

OPENERS = {"«": "»", "‘": "’", "“": "”"}
CLOSERS = {closer: opener for opener, closer in OPENERS.items()}


def build_tree(lines: list[str]) -> list[dict[str, object]]:
    root: list[dict[str, object]] = []
    stack: list[dict[str, object]] = []
    for ln, line in enumerate(lines, start=1):
        for col, ch in enumerate(line):
            if ch in OPENERS:
                node: dict[str, object] = {
                    "opener": ch,
                    "sline": ln,
                    "scol": col,
                    "children": [],
                }
                target = stack[-1]["children"] if stack else root
                target.append(node)
                stack.append(node)
            elif ch in CLOSERS:
                if not stack or stack[-1]["opener"] != CLOSERS[ch]:
                    raise ValueError(f"mismatched {ch!r} at line {ln}")
                node = stack.pop()
                node["eline"] = ln
                node["ecol"] = col
    if stack:
        raise ValueError(f"unclosed delimiters: {stack}")
    return root


def flatten(nodes: list[dict[str, object]], acc: list[dict[str, object]]) -> list[dict[str, object]]:
    for node in nodes:
        acc.append(node)
        flatten(node["children"], acc)
    return acc


def leading_tokens(lines: list[str], node: dict[str, object]) -> list[str]:
    rest = lines[node["sline"] - 1][node["scol"] + 1 :]
    return [token for token in tokenize(rest) if has_alpha(token)]


def _suffix(index: int) -> str:
    return string.ascii_uppercase[index] if index < 26 else str(index + 1)


def assign_ids(canto: int, lines: list[str], root: list[dict[str, object]]) -> None:
    groups: dict[int, list[dict[str, object]]] = {}
    for node in flatten(root, []):
        groups.setdefault(node["sline"], []).append(node)
    for sline, group in groups.items():
        group.sort(key=lambda node: node["scol"])
        if len(group) == 1:
            group[0]["id"] = f"{canto}:{sline}"
            continue
        token_groups = [leading_tokens(lines, node) for node in group]
        width = 1
        while width <= max(len(tokens) for tokens in token_groups):
            heads = [" ".join(tokens[:width]) for tokens in token_groups]
            if len(set(heads)) == len(heads):
                break
            width += 1
        for index, (node, tokens) in enumerate(zip(group, token_groups, strict=True)):
            node["id"] = f"{canto}:{sline}{_suffix(index)}"
            node["head"] = " ".join(tokens[:width]) or "?"


def parse_canto(canto: int, path: Path) -> list[dict[str, object]]:
    raw_lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    for ln, line in enumerate(raw_lines, start=1):
        assert line == line.strip(), f"unexpected leading/trailing whitespace at line {ln}: {line!r}"
    lines = raw_lines
    root = build_tree(lines)
    assign_ids(canto, lines, root)
    return root


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(node: dict[str, object], depth: int) -> list[str]:
    indent = "  " * depth
    sline = node["sline"]
    eline = node["eline"]
    line_attr = f"{sline}" if sline == eline else f"{sline}-{eline}"
    marker = node["opener"] + OPENERS[node["opener"]]
    col_attr = f'{node["scol"]}-{node["ecol"]}'
    attrs = f'id="{node["id"]}" line="{line_attr}" col="{col_attr}" marker="{_esc(marker)}"'
    if "head" in node:
        attrs += f' head="{_esc(node["head"])}"'
    children = node["children"]
    if children:
        out = [f"{indent}<q {attrs}>"]
        for child in children:
            out.extend(render(child, depth + 1))
        out.append(f"{indent}</q>")
        return out
    return [f"{indent}<q {attrs}/>"]


def emit_canticle(canticle: str, cantos: list[tuple[int, list[dict[str, object]]]]) -> str:
    out = [f'<canticle name="{canticle}">']
    for number, root in cantos:
        out.append(f'  <canto n="{number}">')
        for node in root:
            out.extend(render(node, 2))
        out.append("  </canto>")
    out.append("</canticle>")
    return "\n".join(out) + "\n"


def build_quotes(canticles: list[str]) -> int:
    QUOTES_DIR.mkdir(exist_ok=True)
    for canticle in canticles:
        sources = sorted((SRC_DIR / canticle).glob("[0-9][0-9].txt"))
        cantos = [(int(path.stem), parse_canto(int(path.stem), path)) for path in sources]
        output_path = QUOTES_DIR / f"{canticle}.xml"
        output_path.write_text(emit_canticle(canticle, cantos), encoding="utf-8")
        print(f"Wrote: quotes/{canticle}.xml")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    args = parser.parse_args()
    return build_quotes(args.canticles)


if __name__ == "__main__":
    sys.exit(main())
