"""Render one or more .puml files to PNG via Kroki (no Java/Docker required)."""
from __future__ import annotations

import argparse
import pathlib
import sys
import time
import urllib.error
import urllib.request


def render(puml: pathlib.Path, timeout: int = 120) -> None:
    png = puml.with_suffix(".png")
    data = puml.read_text(encoding="utf-8").encode("utf-8")
    req = urllib.request.Request(
        "https://kroki.io/plantuml/png",
        data=data,
        headers={"Content-Type": "text/plain"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        png.write_bytes(resp.read())
    print(f"OK  {png}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render PlantUML to PNG via Kroki")
    parser.add_argument("paths", nargs="+", help=".puml file(s) or directory")
    args = parser.parse_args()

    files: list[pathlib.Path] = []
    for raw in args.paths:
        p = pathlib.Path(raw)
        if p.is_dir():
            files.extend(sorted(p.glob("*.puml")))
        elif p.suffix.lower() == ".puml":
            files.append(p)
        else:
            print(f"SKIP  {p} (not .puml)", file=sys.stderr)

    if not files:
        print("No .puml files found", file=sys.stderr)
        return 1

    ok = 0
    for puml in files:
        for attempt in range(3):
            try:
                render(puml)
                ok += 1
                break
            except urllib.error.HTTPError as exc:
                print(f"HTTP {exc.code}  {puml.name}  attempt {attempt + 1}", file=sys.stderr)
                time.sleep(2)
            except Exception as exc:
                print(f"ERR  {puml.name}: {exc}", file=sys.stderr)
                time.sleep(2)
        else:
            print(f"FAIL  {puml.name}", file=sys.stderr)

    print(f"Done: {ok}/{len(files)}")
    return 0 if ok == len(files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
