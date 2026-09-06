#!/usr/bin/env python3
"""Dependency-free structural checks for qiuqiu-travel-image."""

from pathlib import Path
import re
import sys


MODES = (
    "perler-companion",
    "minimal-sketchbook",
    "watercolor-ticket",
    "memory-scrapbook",
    "enamel-souvenir",
    "map-miniature",
)

REQUIRED_FILES = (
    "SKILL.md",
    "README.md",
    "agents/openai.yaml",
    "references/modes.md",
    "references/prompt-recipes.md",
    "references/quality-checklist.md",
    "references/model-validation.md",
)


def local_targets(document: Path) -> list[str]:
    """Return local Markdown links and HTML image sources."""
    text = document.read_text(encoding="utf-8")
    targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
    targets.extend(re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', text, re.IGNORECASE))
    return [target.split("#", 1)[0].strip() for target in targets]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    skill = root / "SKILL.md"
    if skill.is_file():
        skill_text = skill.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
        if not frontmatter:
            errors.append("SKILL.md must start with closed YAML frontmatter")
        else:
            for field in ("name", "description"):
                if not re.search(rf"^{field}:\s*\S.+$", frontmatter.group(1), re.MULTILINE):
                    errors.append(f"SKILL.md is missing frontmatter field: {field}")
        for mode in MODES:
            if f"`{mode}`" not in skill_text:
                errors.append(f"SKILL.md is missing mode: {mode}")

    for relative in ("references/modes.md", "references/prompt-recipes.md"):
        document = root / relative
        if document.is_file():
            text = document.read_text(encoding="utf-8")
            for mode in MODES:
                if f"`{mode}`" not in text:
                    errors.append(f"{relative} is missing mode: {mode}")

    config = root / "agents" / "openai.yaml"
    if config.is_file():
        config_text = config.read_text(encoding="utf-8")
        for field in ("interface:", "display_name:", "short_description:", "default_prompt:"):
            if field not in config_text:
                errors.append(f"agents/openai.yaml is missing {field}")

    documents = [root / "SKILL.md", root / "README.md"]
    documents.extend(sorted((root / "references").glob("*.md")))
    for document in documents:
        if not document.is_file():
            continue
        for target in local_targets(document):
            if not target or target.startswith(("http://", "https://", "mailto:", "/")):
                continue
            if not (document.parent / target).exists():
                errors.append(f"broken relative link in {document.relative_to(root)}: {target}")

    examples = root / "assets" / "examples"
    if not examples.is_dir() or not any(examples.iterdir()):
        errors.append("assets/examples must contain public examples")

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Skill validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
