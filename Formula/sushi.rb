class Sushi < Formula
  desc "LLM inference server for Apple Silicon with OpenAI and Anthropic APIs"
  homepage "https://github.com/beamivalice/sushi"
  url "https://github.com/beamivalice/sushi/releases/download/v1.2.2/sushi-bin-macos-arm64.tar.gz"
  sha256 "7bb7d48e7ccd45c087acbcedf5966cffaca663292782b5a0713c259830d1c454"
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
