#!/usr/bin/env bash
# Pinned official Linux x86_64 release. The checksum is reviewed with the version.
set -euo pipefail
version='0.76.2'
checksum='bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf'
if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  echo 'This helper supports Linux x86_64. See docs for other platforms.' >&2
  exit 1
fi
destination="${1:-.tools}"
mkdir -p "$destination"
archive_dir="$(mktemp -d)"
trap 'rm -rf "$archive_dir"' EXIT
curl --fail --silent --show-error --location --retry 3 \
  "https://github.com/aquasecurity/trivy/releases/download/v${version}/trivy_${version}_Linux-64bit.tar.gz" \
  --output "$archive_dir/trivy.tar.gz"
printf '%s  %s\n' "$checksum" "$archive_dir/trivy.tar.gz" | sha256sum --check --strict
tar -xzf "$archive_dir/trivy.tar.gz" -C "$destination" trivy
"$destination/trivy" --version
