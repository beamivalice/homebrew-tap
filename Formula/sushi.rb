class Sushi < Formula
  desc "LLM inference server for Apple Silicon with OpenAI and Anthropic APIs"
  homepage "https://github.com/beamivalice/sushi"
  url "https://github.com/beamivalice/sushi/releases/download/v1.2.0/sushi-bin-macos-arm64.tar.gz"
  sha256 "4314ca0bd4d3042e0fb9f8d752ca25ec8f71f8fd3be1a3dfc79f1b3dcb9b0472"
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
  end

  test do
    assert_match "sushi #{version}", shell_output("#{bin}/sushi --version")
  end
end
