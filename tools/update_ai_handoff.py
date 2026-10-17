"""Refresh the two portable context documents from canonical project docs.

Run from a Git checkout with Python 3.10+. Standard library only.
The current-state document is maintained manually; this tool does not verify it.
"""

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

PROJECT = Path(__file__).resolve().parents[1]
SOURCES = {
    "GIOI_THIEU_VA_GIAI_THICH_DO_AN.md": "02_GIOI_THIEU_DO_AN.md",
    "DIAGNOSIS_ENGINE_LOGIC_VA_PHAT_TRIEN.md": "03_LOGIC_DIAGNOSIS_ENGINE.md",
}
MANUAL = ("00_BAT_DAU_O_DAY.md", "01_HIEN_TRANG_VA_CACH_TIEP_TUC.md")


def git(*args):
    return (
        subprocess.check_output(
            ["git", "-C", str(PROJECT), *args], stderr=subprocess.PIPE
        )
        .decode("utf-8")
        .strip()
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-ref", default="HEAD", help="Committed source version for links"
    )
    parser.add_argument("--output", type=Path, default=PROJECT / "docs" / "AI_HANDOFF")
    args = parser.parse_args(argv)
    commit = git("rev-parse", args.source_ref + "^{commit}")
    tree = git("rev-parse", commit + ":diagnosis-engine")
    remote = git("remote", "get-url", "origin")
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?", remote
    )
    if not match:
        raise ValueError("Expected a GitHub origin without embedded credentials")
    base = "https://github.com/" + match.group(1)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in MANUAL:
        if not (output / name).is_file():
            raise ValueError(f"Missing manually maintained document: {name}")
        path = output / name
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))

    source_info = {}
    for name, destination in SOURCES.items():
        relative = "docs/" + name
        # Read committed bytes so linked evidence and descriptions refer to one version.
        data = subprocess.check_output(
            ["git", "-C", str(PROJECT), "show", commit + ":" + relative]
        )
        working = PROJECT / relative
        if working.is_file() and working.read_bytes().replace(
            b"\r\n", b"\n"
        ) != data.replace(b"\r\n", b"\n"):
            raise ValueError(
                f"Canonical document differs from {commit[:7]}: {relative}; commit it first"
            )

        def rewrite_link(match):
            label, target = match.groups()
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("#"):
                return match.group(0)
            path = PurePosixPath("docs") / unquote(parsed.path)
            # Resolve only inside the selected repository tree, independent of output location.
            parts = []
            for part in path.parts:
                if part == "..":
                    if not parts:
                        raise ValueError(f"Link escapes repository: {target}")
                    parts.pop()
                elif part != ".":
                    parts.append(part)
            normalized = "/".join(parts)
            suffix = ("?" + parsed.query if parsed.query else "") + (
                "#" + parsed.fragment if parsed.fragment else ""
            )
            if (
                normalized.startswith("docs/")
                and normalized.removeprefix("docs/") in SOURCES
            ):
                url = SOURCES[normalized.removeprefix("docs/")] + suffix
            else:
                kind = git("cat-file", "-t", commit + ":" + normalized)
                url = (
                    base
                    + ("/tree/" if kind == "tree" else "/blob/")
                    + commit
                    + "/"
                    + quote(normalized, safe="/")
                    + suffix
                )
            return f"[{label}]({url})"

        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            rewrite_link,
            data.decode("utf-8").replace("\r\n", "\n"),
        )
        header = (
            f"> Bản dùng để chuyển chat/tài khoản. Nguồn: `{relative}` tại `{commit}`.\n"
            "> Nội dung lấy từ tài liệu nguồn; các liên kết được đổi để dùng ngoài project. "
            "Đọc file 01 về trạng thái cuối phiên trước khi tiếp tục.\n\n"
        )
        (output / destination).write_bytes((header + text).encode("utf-8"))
        source_info[destination] = {
            "path": relative,
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    names = [*MANUAL, *SOURCES.values()]
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone(timedelta(hours=7))).isoformat(),
        "source_commit": commit,
        "engine_tree": tree,
        "repository": base,
        "state_document": "01_HIEN_TRANG_VA_CACH_TIEP_TUC.md",
        "state_requires_manual_update": True,
        "sources": source_info,
        "files": {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in names
        },
    }
    (output / "MANIFEST.json").write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "source_commit": commit,
                "markdown_files": len(names),
            }
        )
    )


if __name__ == "__main__":
    main()
