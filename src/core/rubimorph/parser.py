"""Parsers that turn source text into RubiMorph intermediate tokens."""

from __future__ import annotations

import re
from html.parser import HTMLParser

from .platform_profiles import is_parse_supported
from .types import (
    EmphasisToken,
    PlatformSpecificToken,
    RawHtmlToken,
    RubyToken,
    StrongToken,
    TextToken,
    Token,
    ensure_platform,
)

_IMPLICIT_RUBY_RE = re.compile(r"([一-龯々〆ヵヶ]+)《([^《》\r\n]+)》")
_PAREN_RUBY_RE = re.compile(r"([一-龯々〆ヵヶ]{1,20})\(([ぁ-んァ-ヶー・\s]{1,50})\)")
_PIXIV_RUBY_RE = re.compile(r"\[\[rb:\s*([^\]\r\n>]+?)\s*>\s*([^\]\r\n]+?)\s*\]\]")
_PIXIV_EMPHASIS_RE = re.compile(
    r"\[\[emphasismark:\s*([^\]\r\n>]+?)\s*>\s*([^\]\r\n]+?)\s*\]\]"
)
_PIXIV_STRONG_RE = re.compile(r"\[b:([^\]\r\n]+)\]")
_AOZORA_EMPHASIS_PREFIX = "［＃「"
_AOZORA_EMPHASIS_END = "」に傍点］"


def parse_to_tokens(platform: str, text: str) -> list[Token]:
    """Parse text for a source platform into a token list."""

    source_platform = ensure_platform(platform)
    if not is_parse_supported(source_platform):
        return [TextToken(text)]
    if source_platform in {"html", "epub_xhtml"}:
        return _parse_html_ruby(text)
    return _parse_text_markup(text, source_platform)


def _parse_text_markup(text: str, platform: str) -> list[Token]:
    tokens: list[Token] = []
    buffer: list[str] = []
    i = 0

    def flush_text() -> None:
        if buffer:
            tokens.append(TextToken("".join(buffer)))
            buffer.clear()

    while i < len(text):
        pixiv_ruby = _PIXIV_RUBY_RE.match(text, i)
        if pixiv_ruby:
            flush_text()
            tokens.append(
                RubyToken(
                    base=pixiv_ruby.group(1).strip(),
                    ruby=pixiv_ruby.group(2).strip(),
                    source_syntax="pixiv-rb",
                )
            )
            i = pixiv_ruby.end()
            continue

        pixiv_emphasis = _PIXIV_EMPHASIS_RE.match(text, i)
        if pixiv_emphasis:
            flush_text()
            tokens.append(
                EmphasisToken(
                    value=pixiv_emphasis.group(1).strip(),
                    marker=pixiv_emphasis.group(2).strip() or "﹅",
                    source_syntax="pixiv-emphasismark",
                )
            )
            i = pixiv_emphasis.end()
            continue

        pixiv_strong = _PIXIV_STRONG_RE.match(text, i)
        if pixiv_strong:
            flush_text()
            tokens.append(StrongToken(value=pixiv_strong.group(1), source_syntax="pixiv-bold"))
            i = pixiv_strong.end()
            continue

        if platform == "aozora" and text.startswith(_AOZORA_EMPHASIS_PREFIX, i):
            end = text.find(_AOZORA_EMPHASIS_END, i + len(_AOZORA_EMPHASIS_PREFIX))
            if end != -1:
                flush_text()
                tokens.append(
                    EmphasisToken(
                        text[i + len(_AOZORA_EMPHASIS_PREFIX) : end],
                        marker="﹅",
                        source_syntax="aozora-emphasis",
                    )
                )
                i = end + len(_AOZORA_EMPHASIS_END)
                continue

        if text.startswith("《《", i):
            end = text.find("》》", i + 2)
            if end != -1:
                flush_text()
                tokens.append(EmphasisToken(text[i + 2 : end], source_syntax="double-bracket"))
                i = end + 2
                continue

        if text[i] in ("｜", "|"):
            open_index = text.find("《", i + 1)
            if open_index != -1:
                close_index = text.find("》", open_index + 1)
                if close_index != -1:
                    base = text[i + 1 : open_index]
                    ruby = text[open_index + 1 : close_index]
                    if base and ruby and "\n" not in base + ruby and "\r" not in base + ruby:
                        flush_text()
                        tokens.append(
                            RubyToken(base=base, ruby=ruby, source_syntax="explicit-ruby")
                        )
                        i = close_index + 1
                        continue

            buffer.append(text[i])
            i += 1
            continue

        implicit_match = _IMPLICIT_RUBY_RE.match(text, i)
        if implicit_match:
            flush_text()
            tokens.append(
                RubyToken(
                    base=implicit_match.group(1),
                    ruby=implicit_match.group(2),
                    source_syntax="implicit-kanji-ruby",
                )
            )
            i = implicit_match.end()
            continue

        paren_match = _PAREN_RUBY_RE.match(text, i)
        if paren_match:
            flush_text()
            tokens.append(
                RubyToken(
                    base=paren_match.group(1),
                    ruby=paren_match.group(2),
                    source_syntax="parentheses-ruby",
                )
            )
            i = paren_match.end()
            continue

        if text.startswith("[[", i):
            end = text.find("]]", i + 2)
            if end != -1:
                flush_text()
                tokens.append(
                    PlatformSpecificToken(
                        value=text[i : end + 2],
                        platform_id=platform,
                        kind="unknown-double-bracket-tag",
                    )
                )
                i = end + 2
                continue

        buffer.append(text[i])
        i += 1

    flush_text()
    return tokens


class _RubyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[Token] = []
        self._text_buffer: list[str] = []
        self._in_ruby = False
        self._in_rt = False
        self._in_rp = False
        self._ruby_base: list[str] = []
        self._ruby_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower_tag = tag.lower()
        if lower_tag == "ruby" and not self._in_ruby:
            self._flush_text()
            self._in_ruby = True
            self._in_rt = False
            self._in_rp = False
            self._ruby_base = []
            self._ruby_text = []
            return

        if self._in_ruby:
            if lower_tag == "rt":
                self._in_rt = True
            elif lower_tag == "rp":
                self._in_rp = True
            return

        self._flush_text()
        raw = self.get_starttag_text() or f"<{tag}>"
        self.tokens.append(RawHtmlToken(raw))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._in_ruby:
            return
        self._flush_text()
        raw = self.get_starttag_text() or f"<{tag} />"
        self.tokens.append(RawHtmlToken(raw))

    def handle_endtag(self, tag: str) -> None:
        lower_tag = tag.lower()
        if self._in_ruby:
            if lower_tag == "rt":
                self._in_rt = False
            elif lower_tag == "rp":
                self._in_rp = False
            elif lower_tag == "ruby":
                base = "".join(self._ruby_base)
                ruby = "".join(self._ruby_text)
                if base and ruby:
                    self.tokens.append(RubyToken(base=base, ruby=ruby, source_syntax="html-ruby"))
                else:
                    self.tokens.append(TextToken(base + ruby))
                self._in_ruby = False
                self._in_rt = False
                self._in_rp = False
            return

        self._flush_text()
        self.tokens.append(RawHtmlToken(f"</{tag}>"))

    def handle_data(self, data: str) -> None:
        if self._in_ruby:
            if self._in_rp:
                return
            if self._in_rt:
                self._ruby_text.append(data)
            else:
                self._ruby_base.append(data)
            return

        self._text_buffer.append(data)

    def finish(self) -> list[Token]:
        if self._in_ruby:
            self.tokens.append(TextToken("".join(self._ruby_base + self._ruby_text)))
            self._in_ruby = False
        self._flush_text()
        return self.tokens

    def _flush_text(self) -> None:
        if self._text_buffer:
            self.tokens.append(TextToken("".join(self._text_buffer)))
            self._text_buffer.clear()


def _parse_html_ruby(text: str) -> list[Token]:
    parser = _RubyHTMLParser()
    parser.feed(text)
    parser.close()
    return parser.finish()
