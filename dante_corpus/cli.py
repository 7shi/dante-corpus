import argparse
import json
import sys

from . import api


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

    raise ValueError(f"unknown text action: {args.action}")


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
        if args.root == "quote":
            return _handle_quote(args)
        if args.root == "canto":
            return _handle_canto(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unknown command group: {args.root}")
    return 2
