"""Regression locks for the vendored AGENTROPOLIS loop baseline.

These checks stay offline. They fail when HTML points a script tag at the
remote loop-baseline file, or when the vendored bytes no longer match the
digest pinned for fleet blob 15254b442f33e009f4c78a1c19568e75ea2121b2.

GitHub Pages for this repo is a legacy build of `/` with `.nojekyll`, so the
publish tree is the git archive of HEAD. The archive check proves the path
referenced by index.html exists in that tree and carries the same digest.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "agentropolis-loop-baseline.js"
EXPECTED_SHA256 = "df28604ae9462594df48aa6fa05d9a77a3ca02e2f74c29aa3ba264da6e4d7224"
EXPECTED_BLOB = "15254b442f33e009f4c78a1c19568e75ea2121b2"
FORBIDDEN_SCRIPT = (
    "https://agentropolis-city-of-agents.github.io/"
    "AGENTROPOLIS-DESIGN-SYSTEM/js/loop-baseline.js"
)
LOCAL_SCRIPT = "./agentropolis-loop-baseline.js"


class ScriptSrcParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        for key, value in attrs:
            if key.lower() == "src" and value is not None:
                self.srcs.append(value)


def script_srcs(html: str) -> list[str]:
    parser = ScriptSrcParser()
    parser.feed(html)
    return parser.srcs


def is_remote_loop_baseline(src: str) -> bool:
    """True when a script src would load loop-baseline from another origin."""
    value = src.strip()
    lowered = value.lower()
    if "loop-baseline" not in lowered and "agentropolis-design-system" not in lowered:
        return False
    if value.startswith("//"):
        return True
    return urlsplit(value).scheme in {"http", "https"}


def git_blob_sha1(data: bytes) -> str:
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def html_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.html"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        files.append(path)
    return files


class VendorLoopBaselineTests(unittest.TestCase):
    def test_detector_flags_remote_script_and_accepts_local(self) -> None:
        remote = f'<script src="{FORBIDDEN_SCRIPT}" defer></script>'
        local = f'<script src="{LOCAL_SCRIPT}" defer></script>'
        self.assertEqual(script_srcs(remote), [FORBIDDEN_SCRIPT])
        self.assertTrue(is_remote_loop_baseline(script_srcs(remote)[0]))
        self.assertEqual(script_srcs(local), [LOCAL_SCRIPT])
        self.assertFalse(is_remote_loop_baseline(script_srcs(local)[0]))
        self.assertTrue(is_remote_loop_baseline("//cdn.example/js/loop-baseline.js"))
        self.assertFalse(is_remote_loop_baseline("./vendor/loop-baseline.js"))

    def test_vendored_file_digest_and_blob(self) -> None:
        data = VENDORED.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        blob = git_blob_sha1(data)
        print(f"VENDORED_SHA256 {sha256}")
        print(f"VENDORED_BLOB {blob}")
        self.assertEqual(sha256, EXPECTED_SHA256)
        self.assertEqual(blob, EXPECTED_BLOB)

    def test_html_does_not_reference_remote_loop_baseline(self) -> None:
        pages = html_files(ROOT)
        self.assertIn(ROOT / "index.html", pages)
        found_local = False
        for path in pages:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                FORBIDDEN_SCRIPT,
                text,
                f"{path.relative_to(ROOT)} still references the remote loop-baseline script",
            )
            for src in script_srcs(text):
                self.assertFalse(
                    is_remote_loop_baseline(src),
                    f"{path.relative_to(ROOT)} loads a remote loop-baseline script: {src}",
                )
                if path.name == "index.html" and src.endswith("agentropolis-loop-baseline.js"):
                    self.assertFalse(urlsplit(src).scheme, src)
                    self.assertFalse(src.startswith("//"), src)
                    found_local = True
                    self.assertEqual(src, LOCAL_SCRIPT)
        self.assertTrue(found_local, "index.html does not reference the vendored script")

    def test_pages_archive_serves_vendored_script_at_html_path(self) -> None:
        """Reproduce the legacy Pages publish tree and resolve the script src."""
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "pages.tar"
            subprocess.run(
                ["git", "archive", "--format=tar", "--output", str(archive), "HEAD"],
                cwd=ROOT,
                check=True,
            )
            subprocess.run(["tar", "-xf", str(archive), "-C", tmp], check=True)
            publish = Path(tmp)
            self.assertTrue((publish / ".nojekyll").is_file(), "Pages would run Jekyll without .nojekyll")
            html_path = publish / "index.html"
            self.assertTrue(html_path.is_file())
            srcs = [src for src in script_srcs(html_path.read_text(encoding="utf-8")) if "loop-baseline" in src]
            self.assertEqual(srcs, [LOCAL_SCRIPT])
            published = (publish / LOCAL_SCRIPT).resolve()
            self.assertEqual(published, (publish / "agentropolis-loop-baseline.js").resolve())
            data = published.read_bytes()
            sha256 = hashlib.sha256(data).hexdigest()
            print(f"PUBLISH_PATH agentropolis-loop-baseline.js")
            print(f"PUBLISH_SHA256 {sha256}")
            self.assertEqual(sha256, EXPECTED_SHA256)
            self.assertEqual(git_blob_sha1(data), EXPECTED_BLOB)


if __name__ == "__main__":
    unittest.main(verbosity=2)
