"""Fetch and verify the CUAD dataset for local evaluation. Setup-time only; needs the internet.

CUAD (Hendrycks, Burns, Chen, Ball; NeurIPS 2021) is published by The Atticus Project.
  Repository: https://github.com/The-Atticus-Project/cuad   Project page: https://www.atticusprojectai.org/cuad
  The Participant Guide cites it as CC BY 4.0. The GitHub repo itself carries no LICENSE file, so
  CHECK the current terms on the project page before redistributing anything derived from it.

The data is NOT committed to this repository (eval/data/ is git-ignored). Run this once:

    python -m eval.cuad_setup                       # downloads data.zip from the pinned commit
    python -m eval.cuad_setup --zip path/to/data.zip   # or use a copy you already have
    git clone https://github.com/The-Atticus-Project/cuad && python -m eval.cuad_setup --zip cuad/data.zip

Pinned snapshot (the one this project's results were produced from):
    commit 67faa0e6023b04fcaae6cc09497ab00e5d63a2a2 (2021-10-21), data.zip sha256 f8161d18...b999a
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

COMMIT = "67faa0e6023b04fcaae6cc09497ab00e5d63a2a2"
URL = f"https://github.com/The-Atticus-Project/cuad/raw/{COMMIT}/data.zip"
SHA256 = "f8161d18bea4e9c05e78fa6dda61c19c846fb8087ea969c172753bc2f45b999a"
DEST = Path(__file__).resolve().parent / "data" / "cuad"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, help="use an existing data.zip instead of downloading")
    parser.add_argument("--allow-hash-mismatch", action="store_true")
    args = parser.parse_args(argv)
    DEST.mkdir(parents=True, exist_ok=True)
    archive = args.zip
    if archive is None:
        archive = DEST / "data.zip"
        print(f"Downloading {URL}\n(setup-time download; document processing itself never uses the network)")
        with urllib.request.urlopen(URL, timeout=120) as response, archive.open("wb") as out:  # noqa: S310
            shutil.copyfileobj(response, out)
    digest = sha256_of(archive)
    if digest != SHA256 and not args.allow_hash_mismatch:
        print(f"SHA-256 mismatch: expected {SHA256}, got {digest}. Use --allow-hash-mismatch to continue.", file=sys.stderr)
        return 1
    with zipfile.ZipFile(archive) as bundle:
        bundle.extract("CUADv1.json", DEST)
    data = json.loads((DEST / "CUADv1.json").read_text(encoding="utf-8"))
    (DEST / "SNAPSHOT.json").write_text(
        json.dumps(
            {
                "source": "https://github.com/The-Atticus-Project/cuad",
                "commit": COMMIT,
                "data_zip_sha256": digest,
                "sha256_matches_pinned": digest == SHA256,
                "dataset_version_field": data.get("version"),
                "contracts": len(data["data"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Ready: {DEST / 'CUADv1.json'} ({len(data['data'])} contracts, version {data.get('version')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
