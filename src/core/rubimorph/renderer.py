"""Render RubiMorph intermediate tokens into target platform markup."""

from __future__ import annotations

from html import escape

from .platform_profiles import PLATFORM_PROFILES, is_render_supported
from .types import (
    AnnotationToken,
    BreakToken,
    EmphasisToken,
    HeadingToken,
    HorizontalRuleToken,
    MarkdownToken,
    PageBreakToken,
    PlatformSpecificToken,
    RawHtmlToken,
    RawToken,
    RenderOptions,
    RubyToken,
    StrongToken,
    TextToken,
    Token,
    UnknownMarkupToken,
    UnsupportedToken,
    ensure_plain_ruby_mode,
    ensure_platform,
)

PLAIN_RUBY_MODE_TARGET_PLATFORMS = frozenset({"plain"})


def target_uses_plain_ruby_mode(
    target_platform: str | None,
    target_profile: object | None = None,
) -> bool:
    """Return whether RenderOptions.plain_ruby_mode affects this target renderer."""

    if target_profile is not None:
        return custom_profile_uses_plain_ruby_mode(target_profile)
    if target_platform is None:
        return False
    ensure_platform(target_platform)
    return target_platform in PLAIN_RUBY_MODE_TARGET_PLATFORMS


def custom_profile_uses_plain_ruby_mode(profile: object) -> bool:
    """Custom renderers define ruby output with templates and do not consume this option."""

    capabilities = getattr(profile, "capabilities", None)
    if capabilities is not None and getattr(capabilities, "output", False) is not True:
        return False
    return False


def render_from_tokens(
    platform: str,
    tokens: list[Token],
    options: RenderOptions | None = None,
) -> str:
    """Render tokens for a target platform."""

    target_platform = ensure_platform(platform)
    render_options = options or RenderOptions()
    ensure_plain_ruby_mode(render_options.plain_ruby_mode)

    parts: list[str] = []
    for token in tokens:
        parts.append(_render_token(target_platform, token, render_options))
    return "".join(parts)


def _render_token(platform: str, token: Token, options: RenderOptions) -> str:
    if isinstance(token, TextToken):
        return _render_text(platform, token.value)
    if isinstance(token, RawToken):
        return _render_raw(platform, token.value)
    if isinstance(token, RawHtmlToken):
        return _render_raw_html(platform, token.value)
    if isinstance(token, RubyToken):
        return _render_ruby(platform, token, options)
    if isinstance(token, EmphasisToken):
        return _render_emphasis(platform, token, options)
    if isinstance(token, AnnotationToken):
        return _render_annotation(platform, token)
    if isinstance(token, StrongToken):
        return _render_strong(platform, token)
    if isinstance(token, BreakToken):
        return "\n" if token.kind == "line" else "\n\n"
    if isinstance(token, HeadingToken):
        return _render_heading(platform, token)
    if isinstance(token, HorizontalRuleToken):
        return "<hr>" if platform == "html" else "\n---\n"
    if isinstance(token, PageBreakToken):
        return "<hr class=\"page-break\">" if platform == "html" else "\n［＃改ページ］\n"
    if isinstance(token, MarkdownToken):
        return token.value if platform in {"markdown", "html"} else token.value
    if isinstance(token, PlatformSpecificToken):
        return token.value
    if isinstance(token, UnknownMarkupToken):
        return token.value
    if isinstance(token, UnsupportedToken):
        return token.value
    raise TypeError(f"unknown token type: {type(token)!r}")


def _render_text(platform: str, value: str) -> str:
    if platform in {"html", "epub_xhtml"}:
        return escape(value, quote=False)
    return value


def _render_raw(platform: str, value: str) -> str:
    return value


def _render_raw_html(platform: str, value: str) -> str:
    if platform in {"html", "epub_xhtml"}:
        return value
    if platform == "plain":
        return ""
    return value


def _render_ruby(platform: str, token: RubyToken, options: RenderOptions) -> str:
    if not is_render_supported(platform):
        return _render_plainish_ruby(token)
    if platform in {"kakuyomu", "narou", "estar", "aozora", "note", "novelup"}:
        return f"｜{token.base}《{token.ruby}》"
    if platform == "pixiv":
        return f"[[rb: {token.base} > {token.ruby}]]"
    if platform in {"html", "epub_xhtml"}:
        return (
            f"<ruby>{escape(token.base, quote=False)}"
            f"<rt>{escape(token.ruby, quote=False)}</rt></ruby>"
        )
    if platform == "markdown":
        return _render_plainish_ruby(token)
    if platform == "plain":
        if options.plain_ruby_mode == "parentheses":
            return _render_plainish_ruby(token)
        return token.base
    raise ValueError(f"unsupported platform: {platform}")


def _render_plainish_ruby(token: RubyToken) -> str:
    return f"{token.base}（{token.ruby}）"


def _render_emphasis(platform: str, token: EmphasisToken, options: RenderOptions) -> str:
    marker = token.marker or options.emphasis_marker
    if not is_render_supported(platform):
        return token.value
    if platform in {"kakuyomu", "estar", "note", "novelup"}:
        return f"《《{token.value}》》"
    if platform == "narou":
        return f"《《{token.value}》》"
    if platform == "pixiv":
        return f"[[emphasismark: {token.value} > {marker}]]"
    if platform == "aozora":
        return f"［＃「{token.value}」に傍点］"
    if platform in {"html", "epub_xhtml"}:
        return f'<span class="emphasis">{escape(token.value, quote=False)}</span>'
    if platform == "markdown":
        return f"**{token.value}**"
    if platform == "plain":
        return token.value
    raise ValueError(f"unsupported platform: {platform}")


def _render_annotation(platform: str, token: AnnotationToken) -> str:
    if platform == "aozora":
        return f"［＃{token.value}］"
    if platform in {"html", "epub_xhtml"}:
        return f"<!-- {escape(token.value, quote=False)} -->"
    if platform == "plain":
        return ""
    return f"［＃{token.value}］"


def _render_strong(platform: str, token: StrongToken) -> str:
    if platform == "pixiv":
        return f"[b:{token.value}]"
    if platform in {"html", "epub_xhtml"}:
        return f"<strong>{escape(token.value, quote=False)}</strong>"
    if platform == "markdown":
        return f"**{token.value}**"
    return token.value


def _render_heading(platform: str, token: HeadingToken) -> str:
    level = max(1, min(token.level, 6))
    if platform in {"html", "epub_xhtml"}:
        return f"<h{level}>{escape(token.value, quote=False)}</h{level}>"
    if platform == "markdown":
        return f"{'#' * level} {token.value}"
    return token.value


def render_platform_matrix() -> str:
    """Return a compact human-readable support matrix."""

    lines = ["platform\tstatus\truby\temphasis\tverification"]
    for profile in PLATFORM_PROFILES.values():
        ruby = "yes" if "ruby" in profile.output_markup else "no"
        emphasis = "yes" if "emphasis" in profile.output_markup else "no"
        lines.append(
            f"{profile.platform_id}\t{profile.status}\t{ruby}\t{emphasis}\t{profile.verification_status}"
        )
    return "\n".join(lines)
