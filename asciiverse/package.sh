#!/bin/sh
# Packs the build into dist/nettoe-<target>.tar.gz for av: the binary at
# the top, with the man page, README, COPYING, protocol.txt and PATCHES.md.
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
stage=stage/nettoe
rm -rf "$stage" && mkdir -p "$stage" dist
cp out/nettoe out/nettoe.6 README COPYING protocol.txt PATCHES.md "$stage/"
tar -czf "dist/nettoe-$target.tar.gz" -C "$stage" .
ls dist
