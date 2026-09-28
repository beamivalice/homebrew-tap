#!/usr/bin/env python3
"""bump.py against a fixture release list: python3 scripts/test_bump.py"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
BUMP = HERE / "bump.py"
FORMULA = HERE.parent / "Formula" / "sushi.rb"
ASSET = "sushi-bin-macos-arm64.tar.gz"
SHA_A = "a" * 64
SHA_B = "b" * 64


class Bump(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.formula = self.tmp / "sushi.rb"
        self.formula.write_text(FORMULA.read_text())
        self.start = self.version()

    def version(self):
        text = self.formula.read_text()
        return text.split("/releases/download/v", 1)[1].split("/", 1)[0]

    def release(self, tag, sha=SHA_A, draft=False, prerelease=False, digest=None, sha_asset=True, sha_name=ASSET):
        sha_file = pathlib.Path(tempfile.mkstemp(dir=self.tmp, suffix=".sha256")[1])
        sha_file.write_text(f"{sha}  {sha_name}\n")
        tarball = {"name": ASSET, "browser_download_url": f"https://github.com/beamivalice/sushi/releases/download/{tag}/{ASSET}"}
        if digest:
            tarball["digest"] = digest
        assets = [tarball]
        if sha_asset:
            assets.append({"name": ASSET + ".sha256", "browser_download_url": sha_file.as_uri()})
        return {"tag_name": tag, "draft": draft, "prerelease": prerelease, "assets": assets}

    def run_bump(self, releases):
        api = self.tmp / "releases.json"
        api.write_text(json.dumps(releases))
        out = self.tmp / "github_output"
        out.write_text("")
        env = dict(os.environ, SUSHI_RELEASES_API=api.as_uri(), GITHUB_OUTPUT=str(out))
        env.pop("GITHUB_TOKEN", None)
        p = subprocess.run([sys.executable, str(BUMP), str(self.formula)], env=env, capture_output=True, text=True)
        return p, out.read_text()

    def test_moves_to_the_highest_stable_semver_and_is_idempotent(self):
        releases = [
            self.release("v99.0.0", draft=True),
            self.release("v98.0.0-rc.1", prerelease=True),
            self.release("v97.0.0", prerelease=True),
            self.release("nightly"),
            self.release("v96.0.0", sha_asset=False),
            self.release("v50.1.0", sha=SHA_B, digest="sha256:" + SHA_B),
            self.release("v50.0.9"),
            self.release("v" + self.start),
        ]
        p, out = self.run_bump(releases)
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.formula.read_text()
        self.assertIn(f'  url "https://github.com/beamivalice/sushi/releases/download/v50.1.0/{ASSET}"\n', text)
        self.assertIn(f'  sha256 "{SHA_B}"\n', text)
        self.assertEqual(out, "version=50.1.0\nchanged=true\n")

        p, out = self.run_bump(releases)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.formula.read_text(), text)
        self.assertEqual(out, "version=50.1.0\nchanged=false\n")

    def test_an_older_or_equal_release_changes_nothing(self):
        before = self.formula.read_text()
        p, out = self.run_bump([self.release("v0.0.1"), self.release("v" + self.start, sha=SHA_B)])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.formula.read_text(), before)
        self.assertEqual(out, f"version={self.start}\nchanged=false\n")

    def test_a_version_line_follows_the_url(self):
        text = self.formula.read_text().replace("  sha256 ", f'  version "{self.start}"\n  sha256 ', 1)
        self.formula.write_text(text)
        p, _ = self.run_bump([self.release("v50.1.0")])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('  version "50.1.0"\n', self.formula.read_text())

    def test_a_bad_digest_leaves_the_formula_untouched(self):
        before = self.formula.read_text()
        for release in (
            self.release("v50.1.0", sha="not-a-digest"),
            self.release("v50.1.0", sha_name="other.tar.gz"),
            self.release("v50.1.0", sha=SHA_A, digest="sha256:" + SHA_B),
        ):
            p, out = self.run_bump([release])
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("bump:", p.stderr)
            self.assertEqual(self.formula.read_text(), before)
            self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
