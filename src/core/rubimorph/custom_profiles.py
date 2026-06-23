"""Declarative custom format profiles for RubiMorph."""

from __future__ import annotations

import json
import os
import re
import string
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from .types import EmphasisToken, RubyToken, TextToken, Token

SUPPORTED_SCHEMA_VERSION = 1
PROFILE_EXTENSION = ".rubimorph-profile.json"
MAX_PROFILE_BYTES = 256 * 1024
MAX_RULES = 100
MAX_PATTERN_LENGTH = 512
MAX_TEMPLATE_LENGTH = 512
MAX_REPLACEMENT_LENGTH = 1024
PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
KNOWN_KINDS = {"ruby", "emphasis"}
KNOWN_FLAGS = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
    "ASCII": re.ASCII,
}
TRANSFORM_POSITIONS = ("before_parse", "after_render")
TRANSFORM_TYPES = ("literal", "regex")
ALLOWED_TOP_KEYS = {
    "schema_version",
    "profile_id",
    "name",
    "description",
    "enabled",
    "capabilities",
    "parser",
    "renderer",
    "transforms",
}
ALLOWED_CAPABILITY_KEYS = {"input", "output"}
ALLOWED_PARSER_KEYS = {"rules"}
ALLOWED_RULE_KEYS = {"id", "name", "kind", "enabled", "priority", "pattern", "flags"}
ALLOWED_RENDERER_KEYS = {"templates"}
ALLOWED_TEMPLATE_KEYS = {"ruby", "emphasis"}
ALLOWED_TRANSFORMS_KEYS = set(TRANSFORM_POSITIONS)
ALLOWED_TRANSFORM_KEYS = {
    "id",
    "name",
    "enabled",
    "type",
    "pattern",
    "replacement",
    "flags",
}


class ProfileError(ValueError):
    """Raised when a profile cannot be loaded or used."""


class ProfileTimeoutError(TimeoutError):
    """Raised when profile conversion exceeds the configured timeout."""


@dataclass(frozen=True)
class ProfileIssue:
    level: Literal["error", "warning"]
    path: str
    message: str
    rule_id: str = ""
    hint: str = ""

    def format(self, filename: str | None = None) -> str:
        location = filename or "<profile>"
        rule = f" rule={self.rule_id}" if self.rule_id else ""
        hint = f" ({self.hint})" if self.hint else ""
        return f"{location}:{self.path}{rule}: {self.message}{hint}"


@dataclass(frozen=True)
class ProfileValidationResult:
    issues: list[ProfileIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ProfileIssue]:
        return [issue for issue in self.issues if issue.level == "error"]

    @property
    def warnings(self) -> list[ProfileIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class ProfileCapabilities:
    input: bool
    output: bool


@dataclass(frozen=True)
class CustomParserRule:
    rule_id: str
    name: str
    kind: Literal["ruby", "emphasis"]
    enabled: bool
    priority: int
    pattern: str
    flags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CustomTransformRule:
    rule_id: str
    name: str
    enabled: bool
    transform_type: Literal["literal", "regex"]
    pattern: str
    replacement: str
    flags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CustomFormatProfile:
    schema_version: int
    profile_id: str
    name: str
    description: str
    enabled: bool
    capabilities: ProfileCapabilities
    parser_rules: tuple[CustomParserRule, ...] = field(default_factory=tuple)
    renderer_templates: dict[str, str] = field(default_factory=dict)
    before_parse: tuple[CustomTransformRule, ...] = field(default_factory=tuple)
    after_render: tuple[CustomTransformRule, ...] = field(default_factory=tuple)
    path: Path | None = None

    def to_json_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "capabilities": {
                "input": self.capabilities.input,
                "output": self.capabilities.output,
            },
        }
        if self.capabilities.input:
            data["parser"] = {
                "rules": [
                    {
                        "id": rule.rule_id,
                        "name": rule.name,
                        "kind": rule.kind,
                        "enabled": rule.enabled,
                        "priority": rule.priority,
                        "pattern": rule.pattern,
                        "flags": list(rule.flags),
                    }
                    for rule in self.parser_rules
                ]
            }
        if self.capabilities.output:
            data["renderer"] = {"templates": dict(self.renderer_templates)}
        transforms: dict[str, Any] = {}
        if self.before_parse:
            transforms["before_parse"] = [_transform_to_json(rule) for rule in self.before_parse]
        if self.after_render:
            transforms["after_render"] = [_transform_to_json(rule) for rule in self.after_render]
        if transforms:
            data["transforms"] = transforms
        return data


@dataclass(frozen=True)
class RegisteredProfile:
    path: Path
    profile: CustomFormatProfile | None
    validation: ProfileValidationResult
    enabled: bool
    modified_at: float | None = None


def load_profile(path: str | Path) -> CustomFormatProfile:
    profile_path = Path(path)
    payload = _read_profile_json(profile_path)
    result = validate_profile_data(payload, filename=str(profile_path))
    if not result.is_valid:
        raise ProfileError(_format_issues(result.errors, str(profile_path)))
    profile = profile_from_data(payload, path=profile_path)
    return profile


def save_profile(profile: CustomFormatProfile, path: str | Path) -> None:
    destination = Path(path)
    result = validate_profile_data(profile.to_json_data(), filename=str(destination))
    if not result.is_valid:
        raise ProfileError(_format_issues(result.errors, str(destination)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(profile.to_json_data(), ensure_ascii=False, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=str(destination.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, destination)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def registered_profile_path(profile_id: str, profiles_dir: str | Path | None = None) -> Path:
    if not PROFILE_ID_RE.match(profile_id):
        raise ProfileError(f"profile_id の形式が不正です: {profile_id}")
    base_dir = Path(profiles_dir) if profiles_dir is not None else user_profiles_dir()
    return base_dir / f"{profile_id}{PROFILE_EXTENSION}"


def register_profile(
    profile: CustomFormatProfile,
    profiles_dir: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    destination = registered_profile_path(profile.profile_id, profiles_dir)
    if destination.exists() and not overwrite:
        raise ProfileError(f"同じ profile_id のプロファイルが既に登録されています: {profile.profile_id}")
    save_profile(replace(profile, path=destination), destination)
    return destination


def import_profile_file(
    source: str | Path,
    profiles_dir: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    profile = load_profile(source)
    return register_profile(profile, profiles_dir, overwrite=overwrite)


def export_registered_profile(
    profile_id: str,
    destination: str | Path,
    profiles_dir: str | Path | None = None,
) -> Path:
    source = registered_profile_path(profile_id, profiles_dir)
    profile = load_profile(source)
    save_profile(profile, destination)
    return Path(destination)


def set_registered_profile_enabled(
    profile_id: str,
    enabled: bool,
    profiles_dir: str | Path | None = None,
) -> Path:
    path = registered_profile_path(profile_id, profiles_dir)
    profile = load_profile(path)
    save_profile(replace(profile, enabled=enabled, path=path), path)
    return path


def delete_registered_profile(profile_id: str, profiles_dir: str | Path | None = None) -> None:
    path = registered_profile_path(profile_id, profiles_dir)
    try:
        path.unlink()
    except FileNotFoundError as exc:
        raise ProfileError(f"登録済みプロファイルが見つかりません: {profile_id}") from exc


def load_registered_profiles(profiles_dir: str | Path | None = None) -> list[RegisteredProfile]:
    base_dir = Path(profiles_dir) if profiles_dir is not None else user_profiles_dir()
    if not base_dir.exists():
        return []
    records: list[RegisteredProfile] = []
    for path in sorted(base_dir.glob(f"*{PROFILE_EXTENSION}")):
        validation = validate_profile_file(path)
        profile: CustomFormatProfile | None = None
        enabled = False
        if validation.is_valid:
            try:
                profile = load_profile(path)
                enabled = profile.enabled
            except ProfileError as exc:
                validation = ProfileValidationResult([ProfileIssue("error", "$", str(exc))])
        try:
            modified_at = path.stat().st_mtime
        except OSError:
            modified_at = None
        records.append(
            RegisteredProfile(
                path=path,
                profile=profile,
                validation=validation,
                enabled=enabled,
                modified_at=modified_at,
            )
        )
    return _mark_duplicate_registered_profiles(records)


def list_enabled_registered_profiles(profiles_dir: str | Path | None = None) -> list[CustomFormatProfile]:
    return [
        record.profile
        for record in load_registered_profiles(profiles_dir)
        if record.profile is not None and record.validation.is_valid and record.enabled
    ]


def validate_profile_file(path: str | Path) -> ProfileValidationResult:
    profile_path = Path(path)
    issues: list[ProfileIssue] = []
    try:
        payload = _read_profile_json(profile_path)
    except ProfileError as exc:
        return ProfileValidationResult([ProfileIssue("error", "$", str(exc))])
    issues.extend(validate_profile_data(payload, filename=str(profile_path)).issues)
    return ProfileValidationResult(issues)


def validate_profile_data(data: Any, filename: str | None = None) -> ProfileValidationResult:
    issues: list[ProfileIssue] = []
    if not isinstance(data, dict):
        return ProfileValidationResult(
            [ProfileIssue("error", "$", "トップレベルはJSONオブジェクトにしてください。")]
        )

    _check_unknown_keys(data, ALLOWED_TOP_KEYS, "$", issues)
    schema_version = data.get("schema_version")
    if schema_version is None:
        issues.append(ProfileIssue("error", "$.schema_version", "schema_version は必須です。"))
    elif schema_version != SUPPORTED_SCHEMA_VERSION:
        issues.append(
            ProfileIssue(
                "error",
                "$.schema_version",
                f"未対応の schema_version です: {schema_version!r}",
                hint=f"{SUPPORTED_SCHEMA_VERSION} を指定してください。",
            )
        )

    profile_id = data.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        issues.append(ProfileIssue("error", "$.profile_id", "profile_id は必須の文字列です。"))
    elif not PROFILE_ID_RE.match(profile_id):
        issues.append(
            ProfileIssue(
                "error",
                "$.profile_id",
                "profile_id の形式が不正です。",
                hint="英数字で始め、英数字・ハイフン・アンダースコアだけを使います。",
            )
        )

    if not isinstance(data.get("name"), str) or not data.get("name"):
        issues.append(ProfileIssue("error", "$.name", "name は必須の文字列です。"))
    if "description" in data and not isinstance(data.get("description"), str):
        issues.append(ProfileIssue("error", "$.description", "description は文字列にしてください。"))
    if "enabled" in data and not isinstance(data.get("enabled"), bool):
        issues.append(ProfileIssue("error", "$.enabled", "enabled は真偽値です。"))

    capabilities = data.get("capabilities")
    input_enabled = False
    output_enabled = False
    if not isinstance(capabilities, dict):
        issues.append(ProfileIssue("error", "$.capabilities", "capabilities は必須のオブジェクトです。"))
    else:
        _check_unknown_keys(capabilities, ALLOWED_CAPABILITY_KEYS, "$.capabilities", issues)
        input_enabled = capabilities.get("input") is True
        output_enabled = capabilities.get("output") is True
        if not isinstance(capabilities.get("input"), bool):
            issues.append(ProfileIssue("error", "$.capabilities.input", "input は真偽値です。"))
        if not isinstance(capabilities.get("output"), bool):
            issues.append(ProfileIssue("error", "$.capabilities.output", "output は真偽値です。"))
        if isinstance(capabilities.get("input"), bool) and isinstance(capabilities.get("output"), bool):
            if not input_enabled and not output_enabled:
                issues.append(
                    ProfileIssue(
                        "error",
                        "$.capabilities",
                        "input または output の少なくとも一方を true にしてください。",
                    )
                )

    _validate_parser(data, input_enabled, issues)
    _validate_renderer(data, output_enabled, issues)
    _validate_transforms(data, issues)
    return ProfileValidationResult(issues)


def profile_from_data(data: dict[str, Any], path: Path | None = None) -> CustomFormatProfile:
    capabilities_data = data["capabilities"]
    capabilities = ProfileCapabilities(
        input=bool(capabilities_data["input"]),
        output=bool(capabilities_data["output"]),
    )
    parser_rules: list[CustomParserRule] = []
    for rule in data.get("parser", {}).get("rules", []):
        parser_rules.append(
            CustomParserRule(
                rule_id=rule["id"],
                name=rule.get("name", rule["id"]),
                kind=rule["kind"],
                enabled=rule.get("enabled", True),
                priority=rule["priority"],
                pattern=rule["pattern"],
                flags=tuple(rule.get("flags", [])),
            )
        )
    transforms = data.get("transforms", {})
    return CustomFormatProfile(
        schema_version=data["schema_version"],
        profile_id=data["profile_id"],
        name=data["name"],
        description=data.get("description", ""),
        enabled=data.get("enabled", True),
        capabilities=capabilities,
        parser_rules=tuple(parser_rules),
        renderer_templates=dict(data.get("renderer", {}).get("templates", {})),
        before_parse=tuple(_transform_from_json(item) for item in transforms.get("before_parse", [])),
        after_render=tuple(_transform_from_json(item) for item in transforms.get("after_render", [])),
        path=path,
    )


def parse_custom_tokens(profile: CustomFormatProfile, text: str) -> list[Token]:
    if not profile.capabilities.input:
        raise ProfileError(f"{profile.profile_id} は入力形式として使用できません。")
    transformed = apply_transforms(text, profile.before_parse)
    return _parse_with_rules(profile, transformed)


def render_custom_tokens(profile: CustomFormatProfile, tokens: list[Token]) -> str:
    if not profile.capabilities.output:
        raise ProfileError(f"{profile.profile_id} は出力形式として使用できません。")
    parts: list[str] = []
    for token in tokens:
        if isinstance(token, TextToken):
            parts.append(token.value)
        elif isinstance(token, RubyToken):
            template = profile.renderer_templates.get("ruby", "{base}（{reading}）")
            parts.append(_render_template(template, {"base": token.base, "reading": token.ruby}))
        elif isinstance(token, EmphasisToken):
            template = profile.renderer_templates.get("emphasis", "{text}")
            parts.append(_render_template(template, {"text": token.value}))
        else:
            parts.append(getattr(token, "value", ""))
    return apply_transforms("".join(parts), profile.after_render)


def apply_transforms(text: str, transforms: tuple[CustomTransformRule, ...]) -> str:
    value = text
    for rule in transforms:
        if not rule.enabled:
            continue
        if rule.transform_type == "literal":
            value = value.replace(rule.pattern, rule.replacement)
        elif rule.transform_type == "regex":
            regex = re.compile(rule.pattern, _flag_value(rule.flags))
            value = regex.sub(rule.replacement, value)
        else:
            raise ProfileError(f"不明な置換種別です: {rule.transform_type}")
    return value


def validate_profile_collection(profiles: list[CustomFormatProfile]) -> ProfileValidationResult:
    issues: list[ProfileIssue] = []
    seen: dict[str, CustomFormatProfile] = {}
    for profile in profiles:
        if profile.profile_id in seen:
            issues.append(
                ProfileIssue(
                    "error",
                    "$.profile_id",
                    f"profile_id が重複しています: {profile.profile_id}",
                    hint="同じ登録領域では profile_id を一意にしてください。",
                )
            )
        seen[profile.profile_id] = profile
    return ProfileValidationResult(issues)


def user_profiles_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "RubiMorph" / "profiles"
    return Path.home() / ".rubimorph" / "profiles"


def _mark_duplicate_registered_profiles(records: list[RegisteredProfile]) -> list[RegisteredProfile]:
    by_id: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        if record.profile is None:
            continue
        by_id.setdefault(record.profile.profile_id, []).append(index)

    updated = list(records)
    for profile_id, indexes in by_id.items():
        if len(indexes) <= 1:
            continue
        for index in indexes:
            record = updated[index]
            duplicate_issue = ProfileIssue(
                "error",
                "$.profile_id",
                f"profile_id が重複しています: {profile_id}",
                hint="同じ登録領域では profile_id を一意にしてください。",
            )
            updated[index] = replace(
                record,
                validation=ProfileValidationResult(record.validation.issues + [duplicate_issue]),
            )
    return updated


def _read_profile_json(path: Path) -> Any:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ProfileError(f"ファイルを読み込めません: {exc}") from exc
    if size > MAX_PROFILE_BYTES:
        raise ProfileError(f"ファイルサイズが上限を超えています: {size} bytes")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ProfileError(f"ファイルを読み込めません: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProfileError(f"UTF-8として読み込めません: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProfileError(f"JSONとして正しくありません: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def _parse_with_rules(profile: CustomFormatProfile, text: str) -> list[Token]:
    candidates: list[tuple[int, int, int, int, CustomParserRule, re.Match[str]]] = []
    for order, rule in enumerate(profile.parser_rules):
        if not rule.enabled:
            continue
        regex = re.compile(rule.pattern, _flag_value(rule.flags))
        for match in regex.finditer(text):
            start, end = match.span()
            if end <= start:
                raise ProfileError(f"ゼロ文字一致が発生しました: {rule.rule_id}")
            candidates.append((start, -rule.priority, -(end - start), order, rule, match))
    candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    tokens: list[Token] = []
    cursor = 0
    for start, _priority, _length, _order, rule, match in candidates:
        end = match.end()
        if start < cursor:
            continue
        if start > cursor:
            tokens.append(TextToken(text[cursor:start]))
        if rule.kind == "ruby":
            tokens.append(
                RubyToken(
                    base=match.group("base"),
                    ruby=match.group("reading"),
                    source_syntax=f"custom:{profile.profile_id}:{rule.rule_id}",
                )
            )
        elif rule.kind == "emphasis":
            tokens.append(
                EmphasisToken(
                    value=match.group("text"),
                    source_syntax=f"custom:{profile.profile_id}:{rule.rule_id}",
                )
            )
        cursor = end
    if cursor < len(text):
        tokens.append(TextToken(text[cursor:]))
    return tokens


def _validate_parser(data: dict[str, Any], input_enabled: bool, issues: list[ProfileIssue]) -> None:
    parser = data.get("parser")
    if input_enabled and not isinstance(parser, dict):
        issues.append(ProfileIssue("error", "$.parser", "入力対応の場合は parser が必須です。"))
        return
    if parser is None:
        return
    if not isinstance(parser, dict):
        issues.append(ProfileIssue("error", "$.parser", "parser はオブジェクトにしてください。"))
        return
    _check_unknown_keys(parser, ALLOWED_PARSER_KEYS, "$.parser", issues)
    rules = parser.get("rules")
    if not isinstance(rules, list):
        issues.append(ProfileIssue("error", "$.parser.rules", "rules は配列にしてください。"))
        return
    if len(rules) > MAX_RULES:
        issues.append(ProfileIssue("error", "$.parser.rules", "規則数が上限を超えています。"))
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        path = f"$.parser.rules[{index}]"
        if not isinstance(rule, dict):
            issues.append(ProfileIssue("error", path, "規則はオブジェクトにしてください。"))
            continue
        _check_unknown_keys(rule, ALLOWED_RULE_KEYS, path, issues)
        rule_id = _validate_rule_common(rule, path, issues, seen)
        kind = rule.get("kind")
        if kind not in KNOWN_KINDS:
            issues.append(ProfileIssue("error", f"{path}.kind", "不明な kind です。", rule_id))
        pattern = rule.get("pattern")
        flags = _validate_flags(rule.get("flags", []), f"{path}.flags", issues, rule_id)
        if not isinstance(pattern, str):
            issues.append(ProfileIssue("error", f"{path}.pattern", "pattern は文字列です。", rule_id))
            continue
        _validate_pattern(pattern, flags, f"{path}.pattern", issues, rule_id)
        if isinstance(kind, str) and kind in KNOWN_KINDS:
            _validate_groups(pattern, flags, kind, f"{path}.pattern", issues, rule_id)


def _validate_renderer(data: dict[str, Any], output_enabled: bool, issues: list[ProfileIssue]) -> None:
    renderer = data.get("renderer")
    if output_enabled and not isinstance(renderer, dict):
        issues.append(ProfileIssue("error", "$.renderer", "出力対応の場合は renderer が必須です。"))
        return
    if renderer is None:
        return
    if not isinstance(renderer, dict):
        issues.append(ProfileIssue("error", "$.renderer", "renderer はオブジェクトにしてください。"))
        return
    _check_unknown_keys(renderer, ALLOWED_RENDERER_KEYS, "$.renderer", issues)
    templates = renderer.get("templates")
    if not isinstance(templates, dict):
        issues.append(ProfileIssue("error", "$.renderer.templates", "templates はオブジェクトです。"))
        return
    _check_unknown_keys(templates, ALLOWED_TEMPLATE_KEYS, "$.renderer.templates", issues)
    for kind, allowed in (("ruby", {"base", "reading"}), ("emphasis", {"text"})):
        value = templates.get(kind)
        if value is None:
            continue
        if not isinstance(value, str):
            issues.append(ProfileIssue("error", f"$.renderer.templates.{kind}", "テンプレートは文字列です。"))
            continue
        if len(value) > MAX_TEMPLATE_LENGTH:
            issues.append(ProfileIssue("error", f"$.renderer.templates.{kind}", "テンプレート長が上限を超えています。"))
        _validate_template(value, allowed, f"$.renderer.templates.{kind}", issues)


def _validate_transforms(data: dict[str, Any], issues: list[ProfileIssue]) -> None:
    transforms = data.get("transforms")
    if transforms is None:
        return
    if not isinstance(transforms, dict):
        issues.append(ProfileIssue("error", "$.transforms", "transforms はオブジェクトです。"))
        return
    _check_unknown_keys(transforms, ALLOWED_TRANSFORMS_KEYS, "$.transforms", issues)
    for position in TRANSFORM_POSITIONS:
        rules = transforms.get(position, [])
        if not isinstance(rules, list):
            issues.append(ProfileIssue("error", f"$.transforms.{position}", "置換規則は配列です。"))
            continue
        seen: set[str] = set()
        for index, rule in enumerate(rules):
            path = f"$.transforms.{position}[{index}]"
            if not isinstance(rule, dict):
                issues.append(ProfileIssue("error", path, "置換規則はオブジェクトです。"))
                continue
            _check_unknown_keys(rule, ALLOWED_TRANSFORM_KEYS, path, issues)
            rule_id = _validate_rule_common(rule, path, issues, seen)
            transform_type = rule.get("type")
            if transform_type not in TRANSFORM_TYPES:
                issues.append(ProfileIssue("error", f"{path}.type", "不明な置換種別です。", rule_id))
            pattern = rule.get("pattern")
            replacement = rule.get("replacement")
            if not isinstance(pattern, str) or pattern == "":
                issues.append(ProfileIssue("error", f"{path}.pattern", "pattern は空でない文字列です。", rule_id))
            elif len(pattern) > MAX_PATTERN_LENGTH:
                issues.append(ProfileIssue("error", f"{path}.pattern", "pattern 長が上限を超えています。", rule_id))
            if not isinstance(replacement, str):
                issues.append(ProfileIssue("error", f"{path}.replacement", "replacement は文字列です。", rule_id))
            elif len(replacement) > MAX_REPLACEMENT_LENGTH:
                issues.append(ProfileIssue("error", f"{path}.replacement", "replacement 長が上限を超えています。", rule_id))
            flags = _validate_flags(rule.get("flags", []), f"{path}.flags", issues, rule_id)
            if transform_type == "regex" and isinstance(pattern, str):
                _validate_pattern(pattern, flags, f"{path}.pattern", issues, rule_id)


def _validate_rule_common(
    rule: dict[str, Any],
    path: str,
    issues: list[ProfileIssue],
    seen: set[str],
) -> str:
    rule_id = rule.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        issues.append(ProfileIssue("error", f"{path}.id", "id は必須の文字列です。"))
        rule_id = ""
    elif rule_id in seen:
        issues.append(ProfileIssue("error", f"{path}.id", f"規則IDが重複しています: {rule_id}", rule_id))
    else:
        seen.add(rule_id)
    if "name" in rule and not isinstance(rule.get("name"), str):
        issues.append(ProfileIssue("error", f"{path}.name", "name は文字列です。", rule_id))
    if "enabled" in rule and not isinstance(rule.get("enabled"), bool):
        issues.append(ProfileIssue("error", f"{path}.enabled", "enabled は真偽値です。", rule_id))
    priority = rule.get("priority", 0)
    if not isinstance(priority, int) or isinstance(priority, bool):
        issues.append(ProfileIssue("error", f"{path}.priority", "priority は整数です。", rule_id))
    return rule_id


def _validate_pattern(
    pattern: str,
    flags: tuple[str, ...],
    path: str,
    issues: list[ProfileIssue],
    rule_id: str,
) -> None:
    if pattern == "":
        issues.append(ProfileIssue("error", path, "空の正規表現は禁止です。", rule_id))
        return
    if len(pattern) > MAX_PATTERN_LENGTH:
        issues.append(ProfileIssue("error", path, "正規表現パターン長が上限を超えています。", rule_id))
        return
    try:
        regex = re.compile(pattern, _flag_value(flags))
    except re.error as exc:
        issues.append(ProfileIssue("error", path, f"正規表現をコンパイルできません: {exc}", rule_id))
        return
    if _can_match_zero_length(regex):
        issues.append(ProfileIssue("error", path, "ゼロ文字一致する正規表現は禁止です。", rule_id))


def _validate_groups(
    pattern: str,
    flags: tuple[str, ...],
    kind: str,
    path: str,
    issues: list[ProfileIssue],
    rule_id: str,
) -> None:
    try:
        regex = re.compile(pattern, _flag_value(flags))
    except re.error:
        return
    required = {"ruby": {"base", "reading"}, "emphasis": {"text"}}[kind]
    missing = sorted(required - set(regex.groupindex))
    if missing:
        issues.append(
            ProfileIssue(
                "error",
                path,
                f"必須の名前付きグループがありません: {', '.join(missing)}",
                rule_id,
            )
        )


def _validate_template(
    template: str,
    allowed: set[str],
    path: str,
    issues: list[ProfileIssue],
) -> None:
    formatter = string.Formatter()
    try:
        parsed = list(formatter.parse(template))
    except ValueError as exc:
        issues.append(ProfileIssue("error", path, f"テンプレート構文が不正です: {exc}"))
        return
    for _literal, field_name, format_spec, conversion in parsed:
        if field_name is None:
            continue
        if field_name not in allowed:
            issues.append(
                ProfileIssue(
                    "error",
                    path,
                    f"使用できないプレースホルダーです: {{{field_name}}}",
                    hint=f"使用可能: {', '.join('{' + name + '}' for name in sorted(allowed))}",
                )
            )
        if format_spec or conversion:
            issues.append(ProfileIssue("error", path, "書式指定や変換指定は使用できません。"))


def _render_template(template: str, values: dict[str, str]) -> str:
    return template.format(**values)


def _validate_flags(
    flags: Any,
    path: str,
    issues: list[ProfileIssue],
    rule_id: str,
) -> tuple[str, ...]:
    if flags is None:
        return ()
    if not isinstance(flags, list):
        issues.append(ProfileIssue("error", path, "flags は配列です。", rule_id))
        return ()
    result: list[str] = []
    for index, flag in enumerate(flags):
        if flag not in KNOWN_FLAGS:
            issues.append(ProfileIssue("error", f"{path}[{index}]", f"不明なflagsです: {flag!r}", rule_id))
        elif flag not in result:
            result.append(flag)
    return tuple(result)


def _flag_value(flags: tuple[str, ...] | list[str]) -> int:
    value = 0
    for flag in flags:
        value |= KNOWN_FLAGS[flag]
    return value


def _check_unknown_keys(
    data: dict[str, Any],
    allowed: set[str],
    path: str,
    issues: list[ProfileIssue],
) -> None:
    for key in sorted(set(data) - allowed):
        issues.append(ProfileIssue("error", f"{path}.{key}", "不明なJSON項目です。"))


def _can_match_zero_length(regex: re.Pattern[str]) -> bool:
    for sample in ("", "a", "あ", "\n", "abc"):
        match = regex.search(sample)
        if match and match.end() == match.start():
            return True
    return False


def _transform_from_json(data: dict[str, Any]) -> CustomTransformRule:
    return CustomTransformRule(
        rule_id=data["id"],
        name=data.get("name", data["id"]),
        enabled=data.get("enabled", True),
        transform_type=data["type"],
        pattern=data["pattern"],
        replacement=data.get("replacement", ""),
        flags=tuple(data.get("flags", [])),
    )


def _transform_to_json(rule: CustomTransformRule) -> dict[str, Any]:
    return {
        "id": rule.rule_id,
        "name": rule.name,
        "enabled": rule.enabled,
        "type": rule.transform_type,
        "pattern": rule.pattern,
        "replacement": rule.replacement,
        "flags": list(rule.flags),
    }


def _format_issues(issues: list[ProfileIssue], filename: str | None = None) -> str:
    return "\n".join(issue.format(filename) for issue in issues)
