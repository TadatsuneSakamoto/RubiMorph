"""Diagnostics and warnings for RubiMorph conversions."""

from __future__ import annotations

import re

from .platform_profiles import get_platform_profile
from .types import (
    Diagnostic,
    EmphasisToken,
    PlatformSpecificToken,
    RawHtmlToken,
    RawToken,
    RubyToken,
    Token,
    ensure_platform,
)

_TAG_RE = re.compile(r"</?\s*([a-zA-Z][\w:-]*)(?:\s+[^<>]*)?/?>")
_RUBY_NEWLINE_RE = re.compile(
    r"[｜|][^《]*《[^》]*[\r\n][^》]*》|[｜|][^\r\n《]*[\r\n][^《]*《[^》]*》|[一-龯々〆ヵヶ]+《[^》]*[\r\n][^》]*》"
)
_EMPHASIS_NEWLINE_RE = re.compile(r"《《[^》]*[\r\n][^》]*》》")


def diagnose(
    tokens: list[Token],
    source_platform: str,
    target_platform: str,
    original_text: str,
) -> list[Diagnostic]:
    """Return warnings for likely conversion problems."""

    source = ensure_platform(source_platform)
    target = ensure_platform(target_platform)
    diagnostics: list[Diagnostic] = []

    if original_text == "":
        diagnostics.append(
            Diagnostic("warning", "empty_file", "入力が空です。変換結果も空になります。")
        )

    diagnostics.extend(_diagnose_platform_status(source, target))
    diagnostics.extend(_diagnose_delimiters(original_text))

    if _RUBY_NEWLINE_RE.search(original_text):
        diagnostics.append(
            Diagnostic(
                "warning",
                "ruby_may_cross_newline",
                "ルビ記法が改行をまたいでいる可能性があります。",
            )
        )

    if _EMPHASIS_NEWLINE_RE.search(original_text):
        diagnostics.append(
            Diagnostic(
                "warning",
                "emphasis_may_cross_newline",
                "傍点記法が改行をまたいでいる可能性があります。",
            )
        )

    diagnostics.extend(_diagnose_html_tags(original_text, source))
    diagnostics.extend(_diagnose_pixiv_tags(original_text))
    diagnostics.extend(_diagnose_aozora_annotations(original_text, source))
    diagnostics.extend(_diagnose_representation(tokens, source, target, original_text))
    diagnostics.extend(_diagnose_length_limits(tokens, target))
    return diagnostics


def _diagnose_platform_status(source: str, target: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for role, platform_id in (("source", source), ("target", target)):
        profile = get_platform_profile(platform_id)
        if profile.status == "partial":
            diagnostics.append(
                Diagnostic(
                    "info",
                    f"{role}_platform_partial",
                    f"{profile.label} は一部対応です。未対応記法は警告または簡略化されます。",
                )
            )
        elif profile.status in {"planned", "research-needed", "unsupported"}:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    f"{role}_platform_not_supported",
                    f"{profile.label} は現在の実装では変換未対応です。結果は参考出力です。",
                )
            )
    return diagnostics


def _diagnose_delimiters(text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []

    open_count = text.count("《")
    close_count = text.count("》")
    if open_count > close_count:
        diagnostics.append(
            Diagnostic("warning", "unclosed_open_bracket", "未閉じの `《` がある可能性があります。")
        )
    elif close_count > open_count:
        diagnostics.append(
            Diagnostic("warning", "unclosed_close_bracket", "未閉じの `》` がある可能性があります。")
        )

    emphasis_open_count = text.count("《《")
    emphasis_close_count = text.count("》》")
    if emphasis_open_count > emphasis_close_count:
        diagnostics.append(
            Diagnostic(
                "warning",
                "unclosed_emphasis_open",
                "未閉じの `《《` がある可能性があります。",
            )
        )
    elif emphasis_close_count > emphasis_open_count:
        diagnostics.append(
            Diagnostic(
                "warning",
                "unclosed_emphasis_close",
                "未閉じの `》》` がある可能性があります。",
            )
        )

    return diagnostics


def _diagnose_html_tags(text: str, source: str) -> list[Diagnostic]:
    unsupported_tags: list[str] = []
    for match in _TAG_RE.finditer(text):
        tag_name = match.group(1).lower()
        if tag_name not in {"ruby", "rt", "rp"} and tag_name not in unsupported_tags:
            unsupported_tags.append(tag_name)

    if not unsupported_tags:
        return []

    tag_list = ", ".join(unsupported_tags)
    level = "warning" if source in {"html", "epub_xhtml"} else "info"
    return [
        Diagnostic(
            level,
            "unsupported_html_tag",
            f"HTML ruby 以外のHTMLタグが含まれています: {tag_list}",
        )
    ]


def _diagnose_pixiv_tags(text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if "[[rb:" in text and "]]" not in text[text.find("[[rb:") :]:
        diagnostics.append(
            Diagnostic("warning", "pixiv_ruby_tag_invalid", "pixivルビタグが閉じていません。")
        )
    if "[[emphasismark:" in text and "]]" not in text[text.find("[[emphasismark:") :]:
        diagnostics.append(
            Diagnostic(
                "warning",
                "pixiv_emphasis_tag_invalid",
                "pixiv傍点タグが閉じていません。",
            )
        )
    return diagnostics


def _diagnose_aozora_annotations(text: str, source: str) -> list[Diagnostic]:
    if source != "aozora" or "［＃" not in text:
        return []
    known_fragments = ("」に傍点］", "改ページ", "ここから", "ここで")
    if any(fragment in text for fragment in known_fragments):
        return [
            Diagnostic(
                "info",
                "aozora_input_partial",
                "青空文庫入力の解析は現在の実装では一部対応です。",
            )
        ]
    return [
        Diagnostic(
            "warning",
            "aozora_unknown_annotation",
            "青空文庫注記のうち未対応の形式が含まれている可能性があります。",
        )
    ]


def _diagnose_representation(
    tokens: list[Token],
    source: str,
    target: str,
    original_text: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    has_ruby = any(isinstance(token, RubyToken) for token in tokens)
    has_emphasis = any(isinstance(token, EmphasisToken) for token in tokens)
    has_raw = any(isinstance(token, (RawToken, RawHtmlToken)) for token in tokens)
    has_platform_specific = any(isinstance(token, PlatformSpecificToken) for token in tokens)

    if target == "plain" and (has_ruby or has_emphasis):
        diagnostics.append(
            Diagnostic(
                "warning",
                "plain_formatting_simplified",
                "プレーンテキスト出力ではルビや傍点が削除または簡略化されます。",
            )
        )

    if target in {"markdown"} and (has_ruby or has_emphasis):
        diagnostics.append(
            Diagnostic(
                "warning",
                "markdown_formatting_simplified",
                "標準Markdownにはルビや傍点の同等表現がないため簡略化します。",
            )
        )

    if target in {"html", "epub_xhtml"} and has_emphasis:
        diagnostics.append(
            Diagnostic(
                "warning",
                "html_emphasis_approximated",
                "HTML出力の傍点は span 要素で近似します。",
            )
        )

    if target == "narou" and has_emphasis:
        diagnostics.append(
            Diagnostic(
                "warning",
                "narou_emphasis_requires_review",
                "小説家になろう向け傍点出力は公式本文内記法の確認が必要です。",
            )
        )

    if has_raw and target not in {"html", "epub_xhtml"}:
        diagnostics.append(
            Diagnostic(
                "warning",
                "raw_markup_may_remain",
                "未対応の生タグまたは記法が変換結果に残る可能性があります。",
            )
        )

    if has_platform_specific and target != source:
        diagnostics.append(
            Diagnostic(
                "warning",
                "platform_specific_markup_may_remain",
                "未対応のプラットフォーム独自タグが変換結果に残る可能性があります。",
            )
        )

    if source == "note" and ("**" in original_text or "[" in original_text):
        diagnostics.append(
            Diagnostic(
                "info",
                "note_ruby_with_formatting_needs_review",
                "note の太字・リンクとルビの組み合わせは目視確認してください。",
            )
        )

    return diagnostics


def _diagnose_length_limits(tokens: list[Token], target: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for token in tokens:
        if not isinstance(token, RubyToken):
            continue

        if target == "narou" and len(token.ruby) > 20:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "narou_ruby_may_be_long",
                    f"小説家になろう向け出力でルビが長すぎる可能性があります: {token.ruby}",
                )
            )

        if target in {"kakuyomu", "estar"} and (len(token.base) > 20 or len(token.ruby) > 50):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "ruby_component_may_be_long",
                    f"{target} 向け出力で親文字またはルビが長すぎる可能性があります。",
                )
            )

        if target == "estar" and (len(token.base) > 20 or len(token.ruby) > 50):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "estar_ruby_component_may_be_long",
                    "エブリスタ向け出力で親文字またはルビが長すぎる可能性があります。",
                )
            )

    return diagnostics
