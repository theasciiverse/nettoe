#!/bin/sh
# Builds netToe into out/ with upstream's own configure, run in build/ so
# the source tree stays clean. Compiler, flags and libraries come from the
# environment, so one script serves every target (see
# .github/workflows/release.yml):
#
#   asciiverse/build.sh                                   # Linux
#   LDFLAGS="-static -s" asciiverse/build.sh              # Alpine, static
#   CFLAGS="-O2 -arch arm64" LDFLAGS="-arch arm64" asciiverse/build.sh  # macOS
#
# make runs with at most JOBS (default 2) jobs, under nice.
set -eu
cd "$(dirname "$0")/.."
JOBS="${JOBS:-2}"
export CFLAGS="${CFLAGS:--O2}"
export LDFLAGS="${LDFLAGS:-}"
rm -rf build out
mkdir -p build out
(cd build && nice -n 10 ../configure --quiet --disable-desktop ${CONFIGURE_HOST:+--host=$CONFIGURE_HOST} \
  && nice -n 10 make -s -j"$JOBS")
cp build/src/nettoe out/nettoe
cp docs/nettoe.6 out/nettoe.6
out/nettoe --version | head -1 || true   # not when cross-built
