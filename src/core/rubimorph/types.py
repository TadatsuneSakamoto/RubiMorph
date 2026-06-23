"""Shared data structures for the RubiMorph converter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union

from .platform_profiles import PLATFORM_PROFILES, get_platform_profile

PlainRubyMode = Literal["remove", "parentheses"]
PLAIN_RUBY_MODES: tuple[str, ...] = ("remove", "parentheses")
SUPPORTED_PLATFORMS: tuple[str, ...] = tuple(PLATFORM_PROFILES)
PLATFORM_LABELS: dict[str, str] = {
    platform_id: profile.label for platform_id, profile in PLATFORM_PROFILES.items()
}


@dataclass(frozen=True)
class TextToken:
    value: str


@dataclass(frozen=True)
class RubyToken:
    base: str
    ruby: str
    source_syntax: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EmphasisToken:
    value: str
    marker: str = "﹅"
    source_syntax: str = ""


@dataclass(frozen=True)
class AnnotationToken:
    value: str
    kind: str = "annotation"
    source_syntax: str = ""


@dataclass(frozen=True)
class StrongToken:
    value: str
    source_syntax: str = ""


@dataclass(frozen=True)
class BreakToken:
    kind: str = "line"


@dataclass(frozen=True)
class HeadingToken:
    level: int
    value: str
    source_syntax: str = ""


@dataclass(frozen=True)
class HorizontalRuleToken:
    source_syntax: str = ""


@dataclass(frozen=True)
class PageBreakToken:
    source_syntax: str = ""


@dataclass(frozen=True)
class RawToken:
    value: str


@dataclass(frozen=True)
class RawHtmlToken:
    value: str


@dataclass(frozen=True)
class MarkdownToken:
    value: str
    kind: str = "inline"


@dataclass(frozen=True)
class PlatformSpecificToken:
    value: str
    platform_id: str
    kind: str


@dataclass(frozen=True)
class UnknownMarkupToken:
    value: str
    reason: str


@dataclass(frozen=True)
class UnsupportedToken:
    value: str
    reason: str


Token = Union[
    TextToken,
    RubyToken,
    EmphasisToken,
    AnnotationToken,
    StrongToken,
    BreakToken,
    HeadingToken,
    HorizontalRuleToken,
    PageBreakToken,
    RawToken,
    RawHtmlToken,
    MarkdownToken,
    PlatformSpecificToken,
    UnknownMarkupToken,
    UnsupportedToken,
]


@dataclass(frozen=True)
class RenderOptions:
    plain_ruby_mode: PlainRubyMode = "remove"
    emphasis_marker: str = "﹅"


@dataclass(frozen=True)
class Diagnostic:
    level: str
    code: str
    message: str


@dataclass(frozen=True)
class ConversionResult:
    output: str
    diagnostics: list[Diagnostic]
    tokens: list[Token]


def ensure_platform(value: str) -> str:
    get_platform_profile(value)
    return value


def ensure_plain_ruby_mode(value: str) -> PlainRubyMode:
    if value not in PLAIN_RUBY_MODES:
        supported = ", ".join(PLAIN_RUBY_MODES)
        raise ValueError(f"unsupported plain ruby mode: {value!r}. supported: {supported}")
    return value  # type: ignore[return-value]
