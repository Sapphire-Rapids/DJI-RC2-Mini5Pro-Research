#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "pathname"

ROOT = Pathname.new(File.expand_path("..", __dir__))
ALLOWED_STATUSES = %w[
  OBSERVED STATIC CORROBORATED NEGATIVE INFERENCE HYPOTHESIS UNKNOWN RETRACTED NOT\ ADMITTED
].freeze

SCHEMAS = {
  "evidence/claims.csv" => %w[
    id status subject version_or_date statement boundary source_refs privacy
  ],
  "evidence/artifacts.csv" => %w[
    id name kind subject_version sha256 size_bytes audit_state device_use_state disposition source_refs privacy
  ]
}.freeze

errors = []
all_ids = {}

def present?(value)
  !value.nil? && !value.strip.empty?
end

SCHEMAS.each do |relative_name, expected_headers|
  path = ROOT.join(relative_name)
  unless path.file?
    errors << "#{relative_name}: file is missing"
    next
  end

  begin
    table = CSV.read(path, headers: true, encoding: "bom|utf-8")
  rescue CSV::MalformedCSVError => e
    errors << "#{relative_name}: malformed CSV (#{e.message})"
    next
  end

  errors << "#{relative_name}: expected header #{expected_headers.join(',')}" unless table.headers == expected_headers
  prefix = relative_name.end_with?("claims.csv") ? "C" : "A"
  local_ids = {}

  table.each_with_index do |row, index|
    line = index + 2
    id = row["id"].to_s.strip
    unless id.match?(/\A#{prefix}-\d{3}\z/)
      errors << "#{relative_name}:#{line}: invalid id #{id.inspect}"
    end
    if local_ids.key?(id)
      errors << "#{relative_name}:#{line}: duplicate id #{id.inspect}"
    else
      local_ids[id] = line
    end
    if all_ids.key?(id)
      errors << "#{relative_name}:#{line}: id also used by #{all_ids[id]}"
    else
      all_ids[id] = "#{relative_name}:#{line}"
    end

    status_field = prefix == "C" ? "status" : "audit_state"
    status = row[status_field].to_s.strip
    unless ALLOWED_STATUSES.include?(status)
      errors << "#{relative_name}:#{line}: invalid #{status_field} #{status.inspect}"
    end

    required = expected_headers - %w[sha256 size_bytes]
    required.each do |field|
      errors << "#{relative_name}:#{line}: #{field} is empty" unless present?(row[field])
    end

    row["source_refs"].to_s.split(";").map(&:strip).reject(&:empty?).each do |source_ref|
      next if source_ref.match?(%r{\Ahttps?://})

      source_path = source_ref.split("#", 2).first
      errors << "#{relative_name}:#{line}: missing source_ref #{source_ref.inspect}" unless ROOT.join(source_path).file?
    end

    next unless prefix == "A"

    kind = row["kind"].to_s.strip
    errors << "#{relative_name}:#{line}: invalid kind #{kind.inspect}" unless %w[self-developed input-sample].include?(kind)
    sha256 = row["sha256"].to_s.strip
    errors << "#{relative_name}:#{line}: invalid SHA-256" unless sha256.empty? || sha256.match?(/\A[0-9a-f]{64}\z/)
    size = row["size_bytes"].to_s.strip
    errors << "#{relative_name}:#{line}: invalid size_bytes" unless size.empty? || size.match?(/\A[1-9]\d*\z/)
  end
end

REGISTER_MIRRORS = {
  "evidence/claims.csv" => ["docs/02_EVIDENCE_REGISTER.md", /\bC-\d{3}\b/],
  "evidence/artifacts.csv" => ["docs/11_ARTIFACT_REGISTER.md", /\bA-\d{3}\b/]
}.freeze

REGISTER_MIRRORS.each do |csv_name, (markdown_name, id_pattern)|
  csv_path = ROOT.join(csv_name)
  markdown_path = ROOT.join(markdown_name)
  next unless csv_path.file? && markdown_path.file?

  csv_ids = CSV.read(csv_path, headers: true).map { |row| row["id"] }.uniq
  markdown_ids = markdown_path.read.scan(id_pattern).uniq
  (csv_ids - markdown_ids).each do |id|
    errors << "#{markdown_name}: missing canonical id #{id} from #{csv_name}"
  end
  (markdown_ids - csv_ids).each do |id|
    errors << "#{markdown_name}: id #{id} is not registered in #{csv_name}"
  end
end

if errors.empty?
  claim_count = CSV.read(ROOT.join("evidence/claims.csv"), headers: true).length
  artifact_count = CSV.read(ROOT.join("evidence/artifacts.csv"), headers: true).length
  puts "Evidence CSV: #{claim_count} claims and #{artifact_count} artifacts checked"
  exit 0
end

warn errors.join("\n")
warn "Evidence CSV: #{errors.length} failure(s)"
exit 1
