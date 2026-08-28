#!/bin/sh
set -eu

mode=${1:---all}
case "$mode" in
  --all|--staged) ;;
  *)
    echo "usage: $0 [--all|--staged]" >&2
    exit 2
    ;;
esac

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
repo_root=$(CDPATH= cd "$script_dir/.." && pwd)
cd "$repo_root"

exec ruby - "$mode" <<'RUBY'
# frozen_string_literal: true

require "open3"
require "pathname"

mode = ARGV.fetch(0)
root = Pathname.pwd
git_repo = system("git", "rev-parse", "--is-inside-work-tree", out: File::NULL, err: File::NULL)

if git_repo
  command = if mode == "--staged"
              ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
            else
              ["git", "ls-files", "-z"]
            end
  output, status = Open3.capture2(*command)
  abort "sensitive-pattern check: unable to list files" unless status.success?
  paths = output.split("\0").reject(&:empty?)
else
  warn "sensitive-pattern check: no Git metadata; scanning all repository files"
  paths = Dir.glob("**/*", File::FNM_DOTMATCH).select do |path|
    File.file?(path) && !path.split(File::SEPARATOR).include?(".git")
  end
end

banned_extensions = %w[
  .apk .apks .aab .ipa .dex .jar .so .dylib .dll .exe .elf .bin .img .fw .hex
  .zip .7z .rar .tar .gz .xz .dmg .pkg .p12 .pfx .pem .key .mobileprovision
]

local_path_pattern = Regexp.new(
  "(?:/" + "Users/|/" + "home/[^/]+/|/" + "Volumes/|/" + "private/var/folders/|[A-Za-z]:\\\\" + "Users\\\\)",
  Regexp::IGNORECASE
)
private_key_pattern = Regexp.new("BEGIN(?: [A-Z0-9]+)? " + "PRIVATE" + " KEY")
credential_patterns = {
  "bearer token" => Regexp.new("Authori" + "zation\\s*:\\s*Bearer\\s+\\S+", Regexp::IGNORECASE),
  "token assignment" => Regexp.new("(?:access|refresh|session|id)[_-]?" + "token\\s*[:=]\\s*[^[:space:],;]+", Regexp::IGNORECASE),
  "cookie header" => Regexp.new("(?:Set-)?" + "Coo" + "kie\\s*:\\s*\\S+", Regexp::IGNORECASE),
  "signed URL parameter" => Regexp.new("(?:X-Amz-Signature|X-Goog-Signature|Signature)=" + "[0-9A-Za-z%_-]{12,}", Regexp::IGNORECASE),
  "private key" => private_key_pattern
}.freeze
serial_pattern = Regexp.new(
  "(?:device[_ -]?(?:serial|sn)|fc[_ -]?sn|rc[_ -]?sn|serial(?:_number)?)\\s*[:=]\\s*(?!REDACTED|TEST)[A-Z0-9-]{8,}",
  Regexp::IGNORECASE
)
known_serial_fragments = ENV.fetch("SENSITIVE_SERIAL_FRAGMENTS", "")
                            .split(",")
                            .map(&:strip)
                            .reject(&:empty?)

failures = []
scanned = 0

paths.sort.each do |path|
  extension = File.extname(path).downcase
  if banned_extensions.include?(extension)
    failures << "#{path}: banned binary or credential extension #{extension}"
    next
  end

  content = if git_repo && mode == "--staged"
              data, status = Open3.capture2("git", "show", ":#{path}")
              status.success? ? data : nil
            else
              File.file?(path) ? File.binread(path) : nil
            end
  next unless content
  next if content.include?("\0")

  text = content.force_encoding(Encoding::UTF_8)
  next unless text.valid_encoding?

  scanned += 1
  text.each_line.with_index(1) do |line, line_number|
    failures << "#{path}:#{line_number}: host absolute path" if line.match?(local_path_pattern)
    failures << "#{path}:#{line_number}: possible device serial" if line.match?(serial_pattern)
    if known_serial_fragments.any? { |fragment| line.include?(fragment) }
      failures << "#{path}:#{line_number}: known sensitive serial fragment"
    end
    credential_patterns.each do |label, pattern|
      failures << "#{path}:#{line_number}: possible #{label}" if line.match?(pattern)
    end
  end
end

if failures.empty?
  puts "Sensitive patterns: #{scanned} text files checked (#{mode})"
  exit 0
end

warn failures.uniq.join("\n")
warn "Sensitive patterns: #{failures.uniq.length} failure(s)"
exit 1
RUBY
