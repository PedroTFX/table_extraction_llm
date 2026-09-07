"""
mineru_api.py — convert local PDFs to markdown via MinerU's hosted v4 API.

The SDK's local-file upload hangs on this setup, so this talks to the raw v4
REST endpoints directly, which DO support local files (via an upload URL):

  1. POST /api/v4/file-urls/batch   -> get presigned upload URL(s) + batch_id
  2. PUT  <upload_url>              -> upload each local PDF
  3. GET  /api/v4/extract-results/batch/{batch_id}  -> poll until done
  4. download each result zip, pull out the markdown

Usage:
    set MINERU_TOKEN=...           (do NOT hardcode the token)
    python mineru_api.py path/to/paper.pdf [more.pdf ...]
    python mineru_api.py --dir data/un_processed_papers   # all PDFs under a dir

Writes <name>_full.md next to each input (or into --out).

Docs: https://mineru.net/apiManage/docs
Notes: max 200MB / 600 pages per file; 2000 pages/day high-priority quota.
"""

import argparse
import io
import os
import sys
import time
import zipfile
from pathlib import Path

import httpx

BASE = "https://mineru.net/api/v4"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "*/*"}


def request_upload_urls(token: str, names: list[str], *,
                        model: str = "vlm", language: str = "en",
                        enable_table: bool = True,
                        ocr: bool = False) -> tuple[str, list[str]]:
    """Ask the API for presigned upload URLs. Returns (batch_id, [upload_urls]).

    ``ocr`` sets is_ocr per file. Default False: born-digital papers have a real
    text layer, and forcing OCR rasterizes the page and re-reads it geometrically,
    which splits multi-line headers into separate rows and merges tightly-spaced
    columns. Set True ONLY for papers whose tables MinerU cropped to images
    instead of transcribing (see scan_tables 'TABLES AS IMAGES') — there, an
    imperfect OCR transcription beats a table the pipeline cannot read at all.
    """
    payload = {
        "enable_formula": True,
        "enable_table": enable_table,
        "language": language,
        "model_version": model,   # "MinerU-HTML" = HTML/table-optimized backend
        "files": [{"name": n, "is_ocr": ocr} for n in names],
    }
    r = httpx.post(f"{BASE}/file-urls/batch", headers=_headers(token),
                   json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"file-urls/batch failed: {data}")
    d = data["data"]
    return d["batch_id"], d["file_urls"]


def upload_file(upload_url: str, path: Path) -> None:
    """PUT the raw bytes to the presigned URL. No auth header on this request."""
    with path.open("rb") as fh:
        # presigned URLs reject extra headers; send only the body
        r = httpx.put(upload_url, content=fh.read(), timeout=300)
    r.raise_for_status()


def poll_batch(token: str, batch_id: str, *, interval: int = 5,
               max_wait: int = 1200) -> list[dict]:
    """Poll until every file is done/failed. Returns the extract_result list."""
    url = f"{BASE}/extract-results/batch/{batch_id}"
    waited = 0
    while True:
        r = httpx.get(url, headers=_headers(token), timeout=60)
        r.raise_for_status()
        results = r.json()["data"]["extract_result"]
        states = {f["file_name"]: f.get("state") for f in results}
        done = all(s in ("done", "failed") for s in states.values())
        print(f"  [{waited}s] {states}")
        if done:
            return results
        if waited >= max_wait:
            raise TimeoutError(f"batch {batch_id} not done after {max_wait}s")
        time.sleep(interval)
        waited += interval


def download_markdown(result: dict) -> str | None:
    """Given one extract_result entry (state=done), download its zip and return
    the markdown text inside."""
    zip_url = result.get("full_zip_url")
    if not zip_url:
        return None
    r = httpx.get(zip_url, timeout=300)
    r.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    # the markdown file is usually 'full.md' or '<name>.md'
    md_names = [n for n in zf.namelist() if n.lower().endswith(".md")]
    if not md_names:
        return None
    # prefer one containing 'full', else the largest .md
    md_names.sort(key=lambda n: ("full" not in n.lower(), -zf.getinfo(n).file_size))
    return zf.read(md_names[0]).decode("utf-8", errors="ignore")


def extract_one(path, token: str, *, model: str = "vlm",
                language: str = "en", ocr: bool = False) -> str | None:
    """Convert ONE local PDF/image to markdown via the hosted API and return the
    markdown text (or None on failure). Convenience wrapper around the batch flow
    used by mineru_extract.doc_to_markdown."""
    path = Path(path)
    batch_id, urls = request_upload_urls(
        token, [path.name], model=model, language=language, ocr=ocr)
    upload_file(urls[0], path)
    results = poll_batch(token, batch_id)
    res = next((r for r in results
                if r["file_name"] in (path.name, path.stem)), None)
    if not res or res.get("state") == "failed":
        msg = res.get("err_msg") if res else "no result"
        print(f"  ! {path.name} failed: {msg}")
        return None
    return download_markdown(res)


def process(paths: list[Path], token: str, out_dir: Path | None,
            model: str, language: str, ocr: bool = False) -> None:
    names = [p.name for p in paths]
    print(f"Requesting upload URLs for {len(names)} file(s)... (ocr={ocr})")
    batch_id, urls = request_upload_urls(token, names, model=model,
                                         language=language, ocr=ocr)
    print(f"batch_id = {batch_id}")

    for p, u in zip(paths, urls):
        print(f"Uploading {p.name} ...")
        upload_file(u, p)

    print("Polling for results...")
    results = poll_batch(token, batch_id)

    by_name = {r["file_name"]: r for r in results}
    for p in paths:
        res = by_name.get(p.name) or by_name.get(p.stem)
        if not res:
            print(f"  ! no result for {p.name}")
            continue
        if res.get("state") == "failed":
            print(f"  ! {p.name} FAILED: {res.get('err_msg')}")
            continue
        md = download_markdown(res)
        if md is None:
            print(f"  ! {p.name}: no markdown in result zip")
            continue
        target_dir = out_dir or p.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        out = target_dir / f"{p.stem}_full.md"
        out.write_text(md, encoding="utf-8")
        print(f"  ✓ {out}  ({len(md)} chars)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="*", help="local PDF paths")
    ap.add_argument("--dir", help="process every *.pdf under this directory")
    ap.add_argument("--out", help="output directory (default: next to each PDF)")
    ap.add_argument("--model", default="vlm", choices=["vlm", "pipeline"],
                    help="extraction backend (default vlm = high accuracy)")
    ap.add_argument("--language", default="en")
    ap.add_argument("--ocr", action="store_true",
                    help="force is_ocr=True (for papers whose tables MinerU "
                         "cropped to images; default off = use the text layer)")
    args = ap.parse_args()

    token = os.environ.get("MINERU_TOKEN")
    if not token:
        print("Set MINERU_TOKEN first:  set MINERU_TOKEN=...")
        sys.exit(1)

    paths: list[Path] = [Path(p) for p in args.pdfs]
    if args.dir:
        paths += sorted(Path(args.dir).rglob("*.pdf"))
    paths = [p for p in paths if p.exists()]
    if not paths:
        print("No PDF files found.")
        sys.exit(1)

    out_dir = Path(args.out) if args.out else None
    # API allows batches; keep it simple and chunk to <=200 files per batch
    CH = 100
    for i in range(0, len(paths), CH):
        process(paths[i:i + CH], token, out_dir, args.model, args.language,
                ocr=args.ocr)


if __name__ == "__main__":
    main()