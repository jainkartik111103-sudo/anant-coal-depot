#!/usr/bin/env bash
# package.sh — validate, then build deployable zips. Refuses to package on validation failure.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p releases
if [ ! -f releases/pre-r1.zip ]; then
  git stash -q 2>/dev/null || true
  zip -qr releases/pre-r1.zip . -x '.git/*' 'scripts/*' 'docs/*' 'releases/*' 'README.md' 'CHANGELOG.md' 2>/dev/null || true
  git stash pop -q 2>/dev/null || true
  echo "archived pre-change state: releases/pre-r1.zip"
fi
python3 scripts/validate-site.py
V="${1:-r1}"
rm -f "releases/$V.zip"
zip -qr "releases/$V.zip" . -x '.git/*' 'scripts/*' 'docs/*' 'releases/*' 'README.md' 'CHANGELOG.md'
echo "built releases/$V.zip (deployable — upload contents to Hostinger public_html)"
unzip -l "releases/$V.zip" | tail -3
