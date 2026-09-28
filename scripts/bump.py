#!/usr/bin/env python3
"""Moves a formula to the newest stable sushi release; changes nothing when it is already there.

The newest release is the highest SemVer among the non-draft, non-prerelease releases that carry both the tarball
and its .sha256, the rule `sushi update` follows. The digest comes from the .sha256 asset and must match the digest
GitHub reports for the tarball when it reports one.

Usage: bump.py <formula.rb>
Env: GITHUB_TOKEN (optional, lifts the API rate limit), SUSHI_RELEASES_API (a test fixture's URL),
     GITHUB_OUTPUT (set by Actions: receives version=<v> and changed=true|false).
"""
import json
import os
import re
import sys
import urllib.request

REPO = "beamivalice/sushi"
ASSET = "sushi-bin-macos-arm64.tar.gz"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases?per_page=100"
DOWNLOAD = f"https://github.com/{REPO}/releases/download/"

URL_RX = re.compile(r'^(  url ")' + re.escape(DOWNLOAD) + r'v([^/"]+)/' + re.escape(ASSET) + r'(")$', re.M)
SHA_RX = re.compile(r'^(  sha256 ")([0-9a-f]{64})(")$', re.M)
VERSION_RX = re.compile(r'^(  version ")([^"]+)(")$', re.M)
SEMVER_RX = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sushi-tap-bump"})
    if url.startswith("https://api.github.com/"):
        req.add_header("Accept", "application/vnd.github+json")
        if os.environ.get("GITHUB_TOKEN"):
            req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def semver(tag):
    m = SEMVER_RX.match(tag)
    return tuple(int(x) for x in m.groups()) if m else None


def newest(releases):
    best = None
    for r in releases:
        v = semver(r.get("tag_name", ""))
        if r.get("draft") or r.get("prerelease") or v is None:
            continue
        assets = {a.get("name"): a for a in r.get("assets", [])}
        if ASSET not in assets or ASSET + ".sha256" not in assets:
            continue
        if best is None or v > best[0]:
            best = (v, r, assets)
    return best


def digest(sha_text, tarball):
    fields = sha_text.split()
    if not fields or not re.fullmatch(r"[0-9a-fA-F]{64}", fields[0]):
        sys.exit(f"bump: the .sha256 asset holds no SHA-256: {sha_text[:80]!r}")
    if len(fields) > 1 and fields[1].lstrip("*") != ASSET:
        sys.exit(f"bump: the .sha256 asset names {fields[1]!r}, not {ASSET}")
    sha = fields[0].lower()
    reported = tarball.get("digest") or ""
    if reported.startswith("sha256:") and reported[len("sha256:"):].lower() != sha:
        sys.exit(f"bump: the .sha256 asset ({sha}) disagrees with GitHub's digest ({reported})")
    return sha


def output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.writelines(f"{k}={v}\n" for k, v in kv.items())


def main(formula_path):
    text = open(formula_path).read()
    urls, shas = URL_RX.findall(text), SHA_RX.findall(text)
    if len(urls) != 1 or len(shas) != 1:
        sys.exit(f"bump: {formula_path} needs exactly one release url and one sha256 line")
    current = urls[0][1]
    if semver(current) is None:
        sys.exit(f"bump: the formula's version {current!r} is not SemVer")

    best = newest(json.loads(fetch(os.environ.get("SUSHI_RELEASES_API", RELEASES_API))))
    if best is None or best[0] <= semver(current):
        print(f"sushi {current} is current")
        output(version=current, changed="false")
        return

    v, release, assets = best
    tag = release["tag_name"]
    version = ".".join(map(str, v))
    url = assets[ASSET]["browser_download_url"]
    if url != f"{DOWNLOAD}{tag}/{ASSET}" or tag != "v" + version:
        sys.exit(f"bump: release {tag} serves its tarball from an unexpected URL: {url}")
    sha = digest(fetch(assets[ASSET + ".sha256"]["browser_download_url"]), assets[ASSET])

    text = URL_RX.sub(lambda m: f"{m[1]}{url}{m[3]}", text)
    text = SHA_RX.sub(lambda m: f"{m[1]}{sha}{m[3]}", text)
    text = VERSION_RX.sub(lambda m: f"{m[1]}{version}{m[3]}", text)
    with open(formula_path, "w") as f:
        f.write(text)
    print(f"sushi {current} -> {version} ({sha})")
    output(version=version, changed="true")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
