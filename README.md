# beamivalice/tap

Homebrew formulae for [sushi](https://github.com/beamivalice/sushi), an LLM inference server for Apple Silicon with
OpenAI- and Anthropic-compatible APIs.

Needs an Apple Silicon Mac on macOS 26.2 or later.

## Install

```bash
brew install beamivalice/tap/sushi
```

This one command adds the tap and installs sushi. Then:

```bash
sushi --version
sushi run <model>
```

## Upgrade

```bash
brew upgrade sushi
```

The formula follows sushi's GitHub releases: a scheduled workflow moves it to a new release within the hour.

Update a Homebrew install with `brew upgrade sushi` only. From the release after 1.0.5 on, sushi knows when Homebrew
installed it: `sushi update` and `sushi update --rollback` leave the files alone and print `brew upgrade sushi`, and so
do the chat page's update banner and `/update` in `sushi run`. sushi 1.0.5 does not know this yet, so do not run
`sushi update` on it or use its "Update and restart" button.

## Uninstall

```bash
brew uninstall sushi
brew untap beamivalice/tap
```

Downloaded models, logs and caches stay in `~/.sushi`; delete that folder to remove them too.

## How the formula works

- It installs the release tarball, `sushi-bin-macos-arm64.tar.gz`, as it is: the binary with its `lib/` (MLX, mlx-c,
  libwebp and `mlx.metallib`) goes into the keg's `libexec`, and `bin/sushi` links to it. The binary finds its
  libraries and the metallib next to its real path, so the link works from anywhere on `PATH`.
- The binary is ad-hoc signed, not notarized, so a formula ships it rather than a cask: Homebrew disables casks that
  fail Gatekeeper.
- `.github/workflows/bump.yml` runs every hour and on demand. It takes the highest SemVer among the non-draft,
  non-prerelease releases that carry the tarball and its `.sha256` (the rule `sushi update` uses), checks that digest
  against the one GitHub reports for the tarball, rewrites the url and sha256, and commits. With nothing newer it
  changes nothing. `python3 scripts/test_bump.py` tests the rewrite against a fixture; the workflow runs it first.
