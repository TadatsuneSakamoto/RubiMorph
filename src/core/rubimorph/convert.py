"""High-level RubiMorph conversion API."""

from __future__ import annotations

import multiprocessing

from .custom_profiles import (
    CustomFormatProfile,
    ProfileTimeoutError,
    parse_custom_tokens,
    render_custom_tokens,
)
from .diagnostics import diagnose
from .parser import parse_to_tokens
from .renderer import render_from_tokens
from .types import ConversionResult, RenderOptions, ensure_platform

DEFAULT_CUSTOM_PROFILE_TIMEOUT_SECONDS = 5.0


def convert_text(
    source_platform: str,
    target_platform: str,
    text: str,
    options: RenderOptions | None = None,
) -> ConversionResult:
    """Convert text from one platform markup to another."""

    source = ensure_platform(source_platform)
    target = ensure_platform(target_platform)
    render_options = options or RenderOptions()

    tokens = parse_to_tokens(source, text)
    diagnostics = diagnose(tokens, source, target, text)
    output = render_from_tokens(target, tokens, render_options)
    return ConversionResult(output=output, diagnostics=diagnostics, tokens=tokens)


def convert_text_flexible(
    text: str,
    *,
    source_platform: str | None = None,
    target_platform: str | None = None,
    source_profile: CustomFormatProfile | None = None,
    target_profile: CustomFormatProfile | None = None,
    options: RenderOptions | None = None,
    timeout_seconds: float = DEFAULT_CUSTOM_PROFILE_TIMEOUT_SECONDS,
) -> ConversionResult:
    """Convert using built-in platforms and/or custom profiles.

    Built-in to built-in conversion stays on the existing direct path. Any custom
    profile conversion runs in a child process so user-provided regular
    expressions cannot block the GUI or CLI indefinitely.
    """

    if source_platform and source_profile:
        raise ValueError("--from と --from-profile は同時に指定できません。")
    if target_platform and target_profile:
        raise ValueError("--to と --to-profile は同時に指定できません。")
    if not source_platform and source_profile is None:
        raise ValueError("変換元を指定してください。")
    if not target_platform and target_profile is None:
        raise ValueError("変換先を指定してください。")

    if source_profile is None and target_profile is None:
        assert source_platform is not None
        assert target_platform is not None
        return convert_text(source_platform, target_platform, text, options)

    return _convert_with_custom_profile_timeout(
        text=text,
        source_platform=source_platform,
        target_platform=target_platform,
        source_profile=source_profile,
        target_profile=target_profile,
        options=options or RenderOptions(),
        timeout_seconds=timeout_seconds,
    )


def _convert_with_custom_profile_timeout(
    *,
    text: str,
    source_platform: str | None,
    target_platform: str | None,
    source_profile: CustomFormatProfile | None,
    target_profile: CustomFormatProfile | None,
    options: RenderOptions,
    timeout_seconds: float,
) -> ConversionResult:
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(
        target=_custom_profile_worker,
        args=(queue, text, source_platform, target_platform, source_profile, target_profile, options),
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(1)
        names = [
            profile.profile_id
            for profile in (source_profile, target_profile)
            if profile is not None
        ]
        label = ", ".join(names) if names else "custom profile"
        raise ProfileTimeoutError(f"カスタム形式プロファイルの変換が時間上限を超えました: {label}")
    if queue.empty():
        raise RuntimeError("カスタム形式プロファイル変換プロセスから結果を受け取れませんでした。")
    status, payload = queue.get()
    if status == "ok":
        return payload
    raise payload


def _custom_profile_worker(
    queue,
    text: str,
    source_platform: str | None,
    target_platform: str | None,
    source_profile: CustomFormatProfile | None,
    target_profile: CustomFormatProfile | None,
    options: RenderOptions,
) -> None:
    try:
        result = _convert_with_custom_profile_direct(
            text=text,
            source_platform=source_platform,
            target_platform=target_platform,
            source_profile=source_profile,
            target_profile=target_profile,
            options=options,
        )
        queue.put(("ok", result))
    except Exception as exc:  # noqa: BLE001
        queue.put(("error", exc))


def _convert_with_custom_profile_direct(
    *,
    text: str,
    source_platform: str | None,
    target_platform: str | None,
    source_profile: CustomFormatProfile | None,
    target_profile: CustomFormatProfile | None,
    options: RenderOptions,
) -> ConversionResult:
    if source_profile is not None:
        tokens = parse_custom_tokens(source_profile, text)
    else:
        assert source_platform is not None
        tokens = parse_to_tokens(source_platform, text)

    diagnostics = []
    if source_profile is None and target_profile is None:
        assert source_platform is not None
        assert target_platform is not None
        diagnostics = diagnose(tokens, source_platform, target_platform, text)

    if target_profile is not None:
        output = render_custom_tokens(target_profile, tokens)
    else:
        assert target_platform is not None
        output = render_from_tokens(target_platform, tokens, options)

    return ConversionResult(output=output, diagnostics=diagnostics, tokens=tokens)
