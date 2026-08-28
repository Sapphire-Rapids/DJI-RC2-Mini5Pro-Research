#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
require "uri"

ROOT = Pathname.new(File.expand_path("..", __dir__))
MARKDOWN_FILES = Dir.glob(ROOT.join("**", "*.md")).sort

def relative_target(raw)
  target = raw.strip
  target = target[1...target.index(">")].to_s if target.start_with?("<") && target.include?(">")
  target = target.split(/\s+/, 2).first.to_s
  return nil if target.empty? || target.start_with?("#")
  return nil if target.match?(/\A[a-z][a-z0-9+.-]*:/i)

  target
end

def decoded_path(target)
  URI::DEFAULT_PARSER.unescape(target.split(/[?#]/, 2).first.to_s)
rescue ArgumentError
  target.split(/[?#]/, 2).first.to_s
end

errors = []
checked = 0

MARKDOWN_FILES.each do |file_name|
  file = Pathname.new(file_name)
  text = file.read(encoding: "UTF-8")
  targets = text.scan(/!?\[[^\]]*\]\(([^)]+)\)/).flatten
  targets.concat(text.scan(/^\s*\[[^\]]+\]:\s*(\S+)/).flatten)

  targets.each do |raw|
    target = relative_target(raw)
    next unless target

    path_text = decoded_path(target)
    next if path_text.empty?

    checked += 1
    candidate = file.dirname.join(path_text).cleanpath
    unless candidate.to_s == ROOT.to_s || candidate.to_s.start_with?(ROOT.to_s + File::SEPARATOR)
      display_file = file.relative_path_from(ROOT)
      errors << "#{display_file}: relative link escapes repository #{path_text.inspect}"
      next
    end
    next if candidate.exist?

    display_file = file.relative_path_from(ROOT)
    errors << "#{display_file}: missing relative link target #{path_text.inspect}"
  end
end

if errors.empty?
  puts "Markdown links: #{checked} relative targets checked"
  exit 0
end

warn errors.join("\n")
warn "Markdown links: #{errors.length} failure(s)"
exit 1
