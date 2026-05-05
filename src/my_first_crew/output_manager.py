from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


def list_generated_images(limit: int = 5) -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []
    return sorted(OUTPUT_DIR.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def list_generated_files(limit: int = 20) -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []
    files = [path for path in OUTPUT_DIR.iterdir() if path.is_file()]
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def resolve_output_reference(reference: str) -> Path:
    raw_path = Path(reference.strip().strip("`'\""))
    if raw_path.is_absolute():
        return raw_path
    if raw_path.parts and raw_path.parts[0] == "output":
        return PROJECT_ROOT / raw_path
    return OUTPUT_DIR / raw_path.name


def missing_output_references(text: str) -> list[str]:
    references = set(re.findall(r"`([^`]+\.(?:png|jpg|jpeg|pdf|xlsx|csv|md))`", text, flags=re.IGNORECASE))
    references.update(
        re.findall(r"(?<![\w/\\.-])([\w./\\:-]+\.(?:png|jpg|jpeg|pdf|xlsx|csv|md))", text, flags=re.IGNORECASE)
    )
    missing: list[str] = []
    for reference in references:
        path = resolve_output_reference(reference)
        if not path.exists():
            missing.append(reference.strip())
    return sorted(missing)


def output_references(text: str) -> list[str]:
    references = set(re.findall(r"`([^`]+\.(?:png|jpg|jpeg|pdf|xlsx|csv|md))`", text, flags=re.IGNORECASE))
    references.update(
        re.findall(r"(?<![\w/\\.-])([\w./\\:-]+\.(?:png|jpg|jpeg|pdf|xlsx|csv|md))", text, flags=re.IGNORECASE)
    )
    return sorted(reference.strip() for reference in references)


def references_outside_output_dir(text: str) -> list[str]:
    outside: list[str] = []
    for reference in output_references(text):
        raw = reference.strip().strip("`'\"")
        path = Path(raw)
        if path.is_absolute():
            try:
                path.relative_to(OUTPUT_DIR)
            except ValueError:
                outside.append(reference)
        elif raw.startswith(("/tmp/", "tmp/", "../")) or raw.startswith("..\\"):
            outside.append(reference)
    return sorted(set(outside))
