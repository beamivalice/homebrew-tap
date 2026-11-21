class Sushi < Formula
  desc "LLM inference server for Apple Silicon with OpenAI and Anthropic APIs"
  homepage "https://github.com/beamivalice/sushi"
  url "https://github.com/beamivalice/sushi/releases/download/v1.7.3/sushi-bin-macos-arm64.tar.gz"
  sha256 "21cb50782f5dfcbc15e36019e320edf961cda63592bbbfb3a3a654f50fa5741a"
  license all_of: ["MIT", "Apache-2.0", "BSD-3-Clause"]

  livecheck do
    url :stable
    strategy :github_latest
  end

  depends_on arch: :arm64
  # The binary needs macOS 26.2; Homebrew's requirement only resolves to a major version.
  depends_on macos: :tahoe

  # The release tree loads its dylibs and mlx.metallib relative to itself; keep their @rpath IDs.
  preserve_rpath

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"sushi"
    # The menu bar app ships in the tarball from 1.5.0 on.
    bin.install_symlink libexec/"sushibar" if (libexec/"sushibar").exist?
  end

  test do
    assert_match "sushi #{version}", shell_output("#{bin}/sushi --version")
    assert_match "--port", shell_output("#{bin}/sushibar --help") if (bin/"sushibar").exist?
  end
end
