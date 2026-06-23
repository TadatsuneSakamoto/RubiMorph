"""Command line interface for RubiMorph."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import APP_NAME, RenderOptions, __version__, convert_text_flexible
from .custom_profiles import ProfileError, load_profile, validate_profile_file
from .fileops import TEXT_EXTENSIONS, convert_directory, convert_file
from .platform_profiles import PLATFORM_PROFILES, list_platform_profiles
from .types import Diagnostic


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"{APP_NAME} {__version__}")
        return 0

    if args.list_platforms:
        print(_format_platforms())
        return 0

    if args.matrix:
        print(_format_matrix())
        return 0

    if args.validate_profile:
        return _handle_validate_profile(args.validate_profile)

    if args.source_platform and args.source_profile:
        parser.error("--from と --from-profile は同時に指定できません。")
    if args.target_platform and args.target_profile:
        parser.error("--to と --to-profile は同時に指定できません。")
    if args.source_platform is None and args.source_profile is None:
        parser.error("--from または --from-profile を指定してください。")
    if args.target_platform is None and args.target_profile is None:
        parser.error("--to または --to-profile を指定してください。")

    selected_inputs = [
        args.text is not None,
        args.input is not None,
        args.input_dir is not None,
    ]
    if sum(selected_inputs) != 1:
        parser.error("--text, --input, --input-dir のいずれか1つを指定してください。")

    options = RenderOptions(
        plain_ruby_mode=args.plain_ruby_mode,
        emphasis_marker=args.emphasis_marker,
    )
    try:
        source_profile = load_profile(args.source_profile) if args.source_profile else None
        target_profile = load_profile(args.target_profile) if args.target_profile else None
    except ProfileError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.text is not None:
        try:
            result = convert_text_flexible(
                args.text,
                source_platform=args.source_platform,
                target_platform=args.target_platform,
                source_profile=source_profile,
                target_profile=target_profile,
                options=options,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        print(result.output)
        _print_diagnostics(result.diagnostics)
        _write_report(
            args.report,
            {
                "mode": "text",
                "source_platform": args.source_platform,
                "target_platform": args.target_platform,
                "source_profile": args.source_profile,
                "target_profile": args.target_profile,
                "diagnostics": _diagnostics_to_dicts(result.diagnostics),
                "warning_count": _warning_count(result.diagnostics),
            },
        )
        return 0

    if args.input is not None:
        if args.output is None:
            parser.error("--input を使う場合は --output を指定してください。")
        try:
            result = convert_file(
                source=Path(args.input),
                destination=Path(args.output),
                source_platform=args.source_platform,
                target_platform=args.target_platform,
                options=options,
                dry_run=args.dry_run,
                source_profile=source_profile,
                target_profile=target_profile,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {args.input}: {exc}", file=sys.stderr)
            return 1

        verb = "DRY-RUN" if args.dry_run else "OK"
        print(f"[{verb}] {result.source} -> {result.destination}")
        _print_diagnostics(result.diagnostics)
        _write_report(
            args.report,
            {
                "mode": "file",
                "source_platform": args.source_platform,
                "target_platform": args.target_platform,
                "source_profile": args.source_profile,
                "target_profile": args.target_profile,
                "dry_run": args.dry_run,
                "files": [_file_result_to_dict(result)],
            },
        )
        return 0

    if args.output_dir is None:
        parser.error("--input-dir を使う場合は --output-dir を指定してください。")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if not input_dir.is_dir():
        print(f"[ERROR] 入力フォルダが見つかりません: {input_dir}", file=sys.stderr)
        return 1

    try:
        results = convert_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            source_platform=args.source_platform,
            target_platform=args.target_platform,
            options=options,
            dry_run=args.dry_run,
            source_profile=source_profile,
            target_profile=target_profile,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {input_dir}: {exc}", file=sys.stderr)
        return 1

    if not results:
        print(f"[INFO] 対象ファイルがありません: {input_dir}")
        return 0

    total_warnings = 0
    for result in results:
        warning_count = _warning_count(result.diagnostics)
        total_warnings += warning_count
        verb = "DRY-RUN" if args.dry_run else "OK"
        print(f"[{verb}] {result.source} -> {result.destination} (warnings: {warning_count})")
        _print_diagnostics(result.diagnostics, prefix=str(result.source))

    print(f"変換対象ファイル数: {len(results)}")
    print(f"警告件数: {total_warnings}")
    _write_report(
        args.report,
        {
            "mode": "directory",
            "source_platform": args.source_platform,
            "target_platform": args.target_platform,
            "source_profile": args.source_profile,
            "target_profile": args.target_profile,
            "dry_run": args.dry_run,
            "files": [_file_result_to_dict(result) for result in results],
        },
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubimorph",
        description=(
            "ルビ・傍点・注記などの小説投稿サイト記法をローカルで変換します。"
            "原稿本文を外部サーバーへ送信しません。"
        ),
    )
    parser.add_argument("--from", dest="source_platform", choices=tuple(PLATFORM_PROFILES))
    parser.add_argument("--to", dest="target_platform", choices=tuple(PLATFORM_PROFILES))
    parser.add_argument("--from-profile", dest="source_profile", help="変換元カスタム形式プロファイル")
    parser.add_argument("--to-profile", dest="target_profile", help="変換先カスタム形式プロファイル")
    parser.add_argument("--validate-profile", help="カスタム形式プロファイルを検証して終了")
    parser.add_argument("--text", help="直接変換する本文")
    parser.add_argument("--input", help="入力ファイル")
    parser.add_argument("--output", help="出力ファイル")
    parser.add_argument("--input-dir", help="入力フォルダ")
    parser.add_argument("--output-dir", help="出力フォルダ")
    parser.add_argument(
        "--plain-ruby-mode",
        choices=("remove", "parentheses"),
        default="remove",
        help="plain 出力時のルビ扱い。remove または parentheses",
    )
    parser.add_argument(
        "--emphasis-marker",
        default="﹅",
        help="pixiv 傍点タグなどへ出力する傍点記号",
    )
    parser.add_argument("--dry-run", action="store_true", help="ファイルを書き込まず変換計画だけ確認")
    parser.add_argument("--report", help="診断レポートJSONの出力先")
    parser.add_argument("--version", action="store_true", help="バージョンを表示")
    parser.add_argument("--list-platforms", action="store_true", help="platform profile 一覧を表示")
    parser.add_argument("--matrix", action="store_true", help="変換対応マトリクスを表示")
    return parser


def _handle_validate_profile(path: str) -> int:
    result = validate_profile_file(path)
    if result.is_valid:
        print(f"[OK] profile valid: {path}")
        for issue in result.warnings:
            print(f"[WARNING] {issue.format(path)}")
        return 0
    print(f"[ERROR] profile invalid: {path}", file=sys.stderr)
    for issue in result.errors:
        print(f"[ERROR] {issue.format(path)}", file=sys.stderr)
    for issue in result.warnings:
        print(f"[WARNING] {issue.format(path)}")
    return 1


def _format_platforms() -> str:
    lines = ["platform\tlabel\tstatus\tverification"]
    for profile in list_platform_profiles():
        lines.append(
            f"{profile.platform_id}\t{profile.label}\t{profile.status}\t{profile.verification_status}"
        )
    return "\n".join(lines)


def _format_matrix() -> str:
    lines = ["source -> target\truby\temphasis\tnote"]
    for source in list_platform_profiles():
        for target in list_platform_profiles():
            if source.platform_id == target.platform_id:
                state = "not-applicable"
            elif source.status in {"research-needed", "unsupported"}:
                state = "research-needed"
            elif target.status in {"research-needed", "unsupported", "planned"}:
                state = "warning-required"
            elif target.platform_id in {"plain", "markdown"}:
                state = "lossy"
            else:
                state = "partial" if "emphasis" not in target.output_markup else "supported"
            emphasis_state = "yes" if "emphasis" in target.output_markup else "warning"
            lines.append(
                f"{source.platform_id} -> {target.platform_id}\t{state}\t{emphasis_state}\t{target.status}"
            )
    return "\n".join(lines)


def _print_diagnostics(diagnostics: list[Diagnostic], prefix: str | None = None) -> None:
    for diagnostic in diagnostics:
        head = f"{prefix}: " if prefix else ""
        print(
            f"[{diagnostic.level.upper()}] {head}{diagnostic.code}: {diagnostic.message}",
            file=sys.stderr,
        )


def _warning_count(diagnostics: list[Diagnostic]) -> int:
    return sum(1 for diagnostic in diagnostics if diagnostic.level == "warning")


def _diagnostics_to_dicts(diagnostics: list[Diagnostic]) -> list[dict[str, str]]:
    return [asdict(diagnostic) for diagnostic in diagnostics]


def _file_result_to_dict(result) -> dict[str, object]:
    return {
        "source": str(result.source),
        "destination": str(result.destination),
        "written": result.written,
        "diagnostics": _diagnostics_to_dicts(result.diagnostics),
        "warning_count": _warning_count(result.diagnostics),
    }


def _write_report(path: str | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _configure_stdio() -> None:
    import sys

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
