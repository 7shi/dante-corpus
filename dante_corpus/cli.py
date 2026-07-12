import argparse
import json
import sys

from . import api
from . import dep as _dep
from . import hashes as _hashes
from . import morph as _morph
from . import np as _np
from . import skel as _skel


def _line_rows(lines: tuple[api.Line, ...]) -> str:
    return "\n".join(f"{line.no}: {line.text}" for line in lines)


def _token_rows(lines: tuple[api.Line, ...]) -> str:
    return "\n".join(f"{line.no}: {' | '.join(line.tokens)}" for line in lines)


def _morph_rows(selected: list[tuple[api.Line, tuple[api.MorphRow, ...]]]) -> str:
    out: list[str] = []
    for line, rows in selected:
        out.append(f"{line.no}: {line.text}")
        for row in rows:
            feats = " ".join(f for f in (row.gender, row.number, row.person, row.tense, row.mood) if f)
            cells = [row.word, row.lemma, row.pos, feats, row.note]
            out.append("    " + "  ".join(cell for cell in cells if cell))
    return "\n".join(out)


def _np_rows(
    lines: tuple[api.Line, ...],
    spans: tuple[api.NPSpan, ...],
    dep_idx: dict[tuple[int, int], api.DepRow] | None = None,
) -> str:
    by_line: dict[int, list[api.NPSpan]] = {}
    for span in spans:
        by_line.setdefault(span.line, []).append(span)

    out: list[str] = []
    for line in lines:
        out.append(f"{line.no}: {line.text}")
        for span in by_line.get(line.no, []):
            _append_np(out, line, span, depth=1, dep_idx=dep_idx)
    return "\n".join(out)


def _append_np(
    out: list[str],
    line: api.Line,
    span: api.NPSpan,
    depth: int,
    dep_idx: dict[tuple[int, int], api.DepRow] | None = None,
) -> None:
    head_word = line.tokens[span.head - 1] if 1 <= span.head <= len(line.tokens) else ""
    role = _dep.np_role(span, dep_idx) if dep_idx is not None else ""
    role_suffix = f" role={role}" if role else ""
    out.append(f"{'    ' * depth}[{span.text}]  ({span.np_id}) head={head_word}{role_suffix}")
    for child in span.children:
        _append_np(out, line, child, depth + 1, dep_idx=dep_idx)


def _np_to_dict(
    span: api.NPSpan, dep_idx: dict[tuple[int, int], api.DepRow] | None
) -> dict[str, object]:
    data = span.to_dict()
    if dep_idx is not None:
        role = _dep.np_role(span, dep_idx)
        if role:
            data["role"] = role
    if span.children:
        data["children"] = [_np_to_dict(child, dep_idx) for child in span.children]
    return data


def _dep_rows(
    canto: api.Canto, lines: tuple[api.Line, ...], data: dict[int, tuple[api.DepRow, ...]]
) -> str:
    out: list[str] = []
    for line in lines:
        out.append(f"{line.no}: {line.text}")
        for row in data.get(line.no, ()):
            if row.deprel == "root":
                out.append(f"    {row.word:<10} {row.deprel}")
                continue
            head_word = _head_word(canto, row.head_line, row.head_token)
            out.append(
                f"    {row.word:<10} {row.deprel:<10} -> {head_word} "
                f"({row.head_line}.{row.head_token})"
            )
    return "\n".join(out)


def _head_word(canto: api.Canto, head_line: int, head_token: int) -> str:
    if not head_line or not head_token:
        return ""
    tokens = canto.line(head_line).tokens
    return tokens[head_token - 1] if 1 <= head_token <= len(tokens) else ""


def _dep_row_dict(canto: api.Canto, row: api.DepRow) -> dict[str, object]:
    data = row.to_dict()
    head_word = _head_word(canto, row.head_line, row.head_token)
    if head_word:
        data["head_word"] = head_word
    return data


def _arg_repr(
    arg: api.SkelArg,
    np_idx: dict[tuple[int, int], api.NPSpan] | None,
) -> str:
    if arg.line == 0 and arg.token == 0:
        return "∅"
    span = np_idx.get((arg.line, arg.token)) if np_idx is not None else None
    if span is not None:
        return f"[{span.text}] ({span.np_id})"
    return f"{arg.line}.{arg.token}"


def _skel_rows(
    lines: tuple[api.Line, ...],
    tuples: tuple[api.SkelTuple, ...],
    np_idx: dict[tuple[int, int], api.NPSpan] | None,
    dep_idx: dict[tuple[int, int], api.DepRow] | None,
    morph_idx: dict[tuple[int, int], api.MorphRow] | None,
    children_idx: dict[tuple[int, int], list] | None,
) -> str:
    by_line: dict[int, list[api.SkelTuple]] = {}
    for t in tuples:
        by_line.setdefault(t.line, []).append(t)

    out: list[str] = []
    for line in lines:
        out.append(f"{line.no}: {line.text}")
        for t in sorted(by_line.get(line.no, ()), key=lambda t: t.token):
            suffix = ""
            if dep_idx is not None:
                ante = _skel.antecedent(t, dep_idx)
                if ante is not None:
                    ante_span = np_idx.get(ante) if np_idx is not None else None
                    shown = f"[{ante_span.text}] ({ante_span.np_id})" if ante_span else f"{ante[0]}.{ante[1]}"
                    suffix = f" (antecedent {shown})"
            out.append(f"    ({t.skel_id}) {t.word}{suffix}")
            for arg in t.args:
                shown = _arg_repr(arg, np_idx)
                if (arg.line, arg.token) == (0, 0) and morph_idx is not None and children_idx is not None:
                    feats = _skel.pro_drop_features(t, morph_idx, children_idx)
                    if feats:
                        shown = f"∅ ({feats})"
                out.append(f"        {arg.role:<8} {shown}")
    return "\n".join(out)


def _skel_tuple_to_dict(
    t: api.SkelTuple,
    np_idx: dict[tuple[int, int], api.NPSpan] | None,
    dep_idx: dict[tuple[int, int], api.DepRow] | None,
    morph_idx: dict[tuple[int, int], api.MorphRow] | None,
    children_idx: dict[tuple[int, int], list] | None,
) -> dict[str, object]:
    data = t.to_dict()
    if dep_idx is not None:
        ante = _skel.antecedent(t, dep_idx)
        if ante is not None:
            data["antecedent"] = {"line": ante[0], "token": ante[1]}
    for arg_data, arg in zip(data["args"], t.args):
        if np_idx is not None:
            span = _skel.arg_np(arg, np_idx)
            if span is not None:
                arg_data["np_id"] = span.np_id
        if (arg.line, arg.token) == (0, 0) and morph_idx is not None and children_idx is not None:
            feats = _skel.pro_drop_features(t, morph_idx, children_idx)
            if feats:
                arg_data["features"] = feats
    return data


def _dump_json(data: object) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _add_format_argument(parser: argparse.ArgumentParser, *choices: str, default: str) -> None:
    parser.add_argument("--format", choices=choices, default=default)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dante-corpus")
    roots = parser.add_subparsers(dest="root", required=True)

    list_parser = roots.add_parser("list")
    list_sub = list_parser.add_subparsers(dest="action", required=True)
    list_sub.add_parser("canticles")
    list_cantos = list_sub.add_parser("cantos")
    list_cantos.add_argument("canticle")

    text_parser = roots.add_parser("text")
    text_sub = text_parser.add_subparsers(dest="action", required=True)
    text_lines = text_sub.add_parser("lines")
    text_lines.add_argument("canticle")
    text_lines.add_argument("reference", help="canto or canto:start-end")
    _add_format_argument(text_lines, "text", "json", default="text")
    text_tokens = text_sub.add_parser("tokens")
    text_tokens.add_argument("canticle")
    text_tokens.add_argument("reference", help="canto or canto:start-end")
    _add_format_argument(text_tokens, "text", "json", default="text")
    text_morph = text_sub.add_parser("morph")
    text_morph.add_argument("canticle")
    text_morph.add_argument("reference", help="canto or canto:start-end")
    _add_format_argument(text_morph, "text", "json", default="text")
    text_np = text_sub.add_parser("np")
    text_np.add_argument("canticle")
    text_np.add_argument("reference", help="canto or canto:start-end")
    _add_format_argument(text_np, "text", "json", default="text")
    text_dep = text_sub.add_parser("dep")
    text_dep.add_argument("canticle")
    text_dep.add_argument("reference", help="canto or canto:start-end")
    _add_format_argument(text_dep, "text", "json", default="text")
    text_skel = text_sub.add_parser("skel")
    text_skel.add_argument("canticle")
    text_skel.add_argument("reference", help="canto or canto:start-end")
    _add_format_argument(text_skel, "text", "json", default="text")

    hash_parser = roots.add_parser("hash")
    hash_parser.add_argument("canticle")
    hash_parser.add_argument("canto", type=int)
    _add_format_argument(hash_parser, "text", "json", default="text")

    quote_parser = roots.add_parser("quote")
    quote_sub = quote_parser.add_subparsers(dest="action", required=True)
    quote_show = quote_sub.add_parser("show")
    quote_show.add_argument("canticle")
    quote_show.add_argument("canto", type=int)
    _add_format_argument(quote_show, "xml", "json", default="xml")

    canto_parser = roots.add_parser("canto")
    canto_sub = canto_parser.add_subparsers(dest="action", required=True)
    canto_show = canto_sub.add_parser("show")
    canto_show.add_argument("canticle")
    canto_show.add_argument("canto", type=int)
    _add_format_argument(canto_show, "text", "json", default="json")

    return parser


def _handle_list(args: argparse.Namespace) -> int:
    if args.action == "canticles":
        for canticle in api.canticles():
            print(canticle)
        return 0

    if args.action == "cantos":
        for canto_no in api.cantos(args.canticle):
            print(canto_no)
        return 0

    raise ValueError(f"unknown list action: {args.action}")


def _handle_text(args: argparse.Namespace) -> int:
    lines = api.ref(f"{args.canticle} {args.reference}")
    if args.action == "lines":
        if args.format == "json":
            _dump_json([line.to_dict() for line in lines])
        else:
            print(_line_rows(lines))
        return 0

    if args.action == "tokens":
        if args.format == "json":
            _dump_json([line.to_dict() for line in lines])
        else:
            print(_token_rows(lines))
        return 0

    if args.action == "morph":
        canto_no = int(str(args.reference).split(":")[0])
        data = api.canto(args.canticle, canto_no).morph()
        selected = [(line, data.get(line.no, ())) for line in lines]
        if args.format == "json":
            _dump_json(
                [{"no": line.no, "rows": [row.to_dict() for row in rows]} for line, rows in selected]
            )
        else:
            print(_morph_rows(selected))
        return 0

    if args.action == "np":
        canto_no = int(str(args.reference).split(":")[0])
        canto = api.canto(args.canticle, canto_no)
        nos = {line.no for line in lines}
        spans = tuple(s for s in canto.np() if s.line in nos)
        dep_idx = _dep.index(canto.dep()) if _dep.has_dep(args.canticle, canto_no) else None
        if args.format == "json":
            _dump_json([_np_to_dict(span, dep_idx) for span in spans])
        else:
            print(_np_rows(lines, spans, dep_idx=dep_idx))
        return 0

    if args.action == "dep":
        canto_no = int(str(args.reference).split(":")[0])
        canto = api.canto(args.canticle, canto_no)
        data = canto.dep()
        nos = {line.no for line in lines}
        selected = {no: rows for no, rows in data.items() if no in nos}
        if args.format == "json":
            _dump_json([
                {"no": no, "rows": [_dep_row_dict(canto, row) for row in rows]}
                for no, rows in sorted(selected.items())
            ])
        else:
            print(_dep_rows(canto, lines, selected))
        return 0

    if args.action == "skel":
        canto_no = int(str(args.reference).split(":")[0])
        canto = api.canto(args.canticle, canto_no)
        nos = {line.no for line in lines}
        tuples = tuple(t for t in canto.skel() if t.line in nos)
        np_idx = _skel.np_head_index(canto.np()) if _np.has_np(args.canticle, canto_no) else None
        dep_idx = _dep.index(canto.dep()) if _dep.has_dep(args.canticle, canto_no) else None
        morph_idx = (
            _skel.morph_index(canto.morph()) if _morph.has_morph(args.canticle, canto_no) else None
        )
        children_idx = (
            _skel.children_index(canto.dep()) if _dep.has_dep(args.canticle, canto_no) else None
        )
        if args.format == "json":
            _dump_json([
                _skel_tuple_to_dict(t, np_idx, dep_idx, morph_idx, children_idx) for t in tuples
            ])
        else:
            print(_skel_rows(lines, tuples, np_idx, dep_idx, morph_idx, children_idx))
        return 0

    raise ValueError(f"unknown text action: {args.action}")


def _handle_hash(args: argparse.Namespace) -> int:
    data = api.canto(args.canticle, args.canto).hashes()
    if args.format == "json":
        _dump_json(data)
    else:
        for layer, digest in data.items():
            print(f"{layer}\t{digest}")
    return 0


def _handle_quote(args: argparse.Namespace) -> int:
    if args.action == "show":
        if args.format == "json":
            _dump_json([quote.to_dict() for quote in api.canto(args.canticle, args.canto).quotes()])
        else:
            print(api.quote_xml(args.canticle, args.canto))
        return 0
    raise ValueError(f"unknown quote action: {args.action}")


def _handle_canto(args: argparse.Namespace) -> int:
    selected = api.canto(args.canticle, args.canto)
    if args.action == "show":
        if args.format == "json":
            _dump_json(selected.to_dict())
        else:
            print(f"{selected.canticle.capitalize()} {selected.number:02d}")
            print()
            print(_line_rows(selected.lines()))
        return 0
    raise ValueError(f"unknown canto action: {args.action}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.root == "list":
            return _handle_list(args)
        if args.root == "text":
            return _handle_text(args)
        if args.root == "hash":
            return _handle_hash(args)
        if args.root == "quote":
            return _handle_quote(args)
        if args.root == "canto":
            return _handle_canto(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unknown command group: {args.root}")
    return 2
