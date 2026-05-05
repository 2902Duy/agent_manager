from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


def list_generated_images(limit: int = 5) -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []
    return sorted(OUTPUT_DIR.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
