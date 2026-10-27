"""Write fictional sample artifacts to sample_data/the_last_process/."""
from pathlib import Path

from app.sample_investigation import ARTIFACTS, SAMPLE_META

ROOT = Path(__file__).resolve().parents[2] / "sample_data" / SAMPLE_META["id"]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for item in ARTIFACTS:
        path = ROOT / item["filename"]
        path.write_text(item["content"].strip() + "\n", encoding="utf-8")
    print(f"Wrote {len(ARTIFACTS)} files to {ROOT}")


if __name__ == "__main__":
    main()
