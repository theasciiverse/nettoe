# Changes from upstream

This is the Asciiverse packaging of netToe 1.5.1 (GPL-2.0-or-later),
tic-tac-toe in the terminal against the computer, a second player at the
same keyboard, or another player over the network. Gabriele Giorgetti
wrote it in 2000 and 2001; Mats Erik Andersson maintained it from 2009 and
released 1.5.1 on 2014-03-21, the last release (nettoe.sourceforge.net).

History here starts from the release tarball (nettoe-1.5.1.tar.gz from
SourceForge, sha256
dbc2c08e7e0f7e60236954ee19a165a350ab3e0bcbbe085ecd687f39253881cb, the same
file Debian distributes as nettoe_1.5.1.orig.tar.gz), unchanged, tagged
`1.5.1`.

## Remotes

- `upstream`: github.com/gabgio/nettoe, Gabriele Giorgetti's own import of
  1.5.1 to GitHub (one commit, 2020-12-28). Its files are the tarball's
  without the generated autotools files (configure, Makefile.in,
  aclocal.m4, build-aux), and with an unexpanded CVS `$Revision$` in
  configure.ac; no newer code.
- `debian`: salsa.debian.org/games-team/nettoe, Debian's packaging
  (`Vcs-Git`), tags not fetched.
- `berger`: github.com/RobertBerger/nettoe, the tarball plus Robert
  Berger's GCC 10 fix (2021), taken below.

## Distribution patches

From Debian's 1.5.1-3 (nettoe_1.5.1-3.debian.tar.xz, sha256
132bf56b80c6cf580f392f2fa6ebb77f7980512b7b3b33701f8d7385b2d7a670), tagged
`debian/1.5.1-3`:

- `01_manpage.diff`: a dash in the man page escaped (Mats Erik Andersson).

FreeBSD's games/nettoe and Homebrew's formula carry no patches (Homebrew
adds `-fcommon` on Linux); Debian also builds with `-fcommon` because the shared globals were defined
in a header (GCC 10, #957602). Instead, Robert Berger's fix is taken as one
commit with his name: the header declares them `extern` and nettoe.c
defines them.

## Ours

- **Host shows addresses that work.** The host screen named one address,
  looked up from the host name, which on many Linux systems is 127.0.1.1
  and useless to anyone else. It now lists the network interfaces that are
  up (no loopback, no IPv6 link-local, IPv4 first, `-4` and `-6`
  respected) and the TCP port, falling back to the old lookup only when
  there are none.
- **Default colours through `op`.** Resetting to the default colours sent
  `setaf 9` and `setab 9`, ECMA-48's "default" in 8-colour terminfo
  entries but bright red in 16 and 256-colour ones: under
  `TERM=xterm-256color` every reset, and the one at exit, left bright red
  on bright red behind, in the shell too. It now sends the terminal's
  `op` (original pair) string when there is one.
- **Prompts shown before waiting.** Prompts end without a newline; glibc
  flushes stdout when a program reads stdin, musl (the static Linux build)
  does not, so the move prompt never appeared. stdout is flushed before
  each keyboard read and before waiting on the network.
- **Warnings.** A failed privilege drop (setuid and friends, whose results
  were ignored) now stops the game; the colour escape buffer is big enough
  for any value.

Unchanged: the game listens on TCP port 7501 (fixed at build time with
`configure --with-port`), and the host's firewall must let it in; play is
direct, host and guest on a LAN or with a reachable address. The protocol
is described in protocol.txt.

Windows: not built. The network code is BSD sockets (getaddrinfo, accept,
read/write on socket descriptors) and would need Winsock (WSAStartup,
closesocket, recv/send) and a getifaddrs replacement
(GetAdaptersAddresses); the screen code is plain escape codes, which the
Windows 10 console understands.

## Packaging (new files)

- `asciiverse/build.sh`: upstream's own configure and make, run in
  `build/`, the binary and man page copied to `out/`.
- `asciiverse/package.sh`: one archive per target with the binary, the
  man page, README, COPYING, protocol.txt and this file.
- `asciiverse/record-preview.py`, `asciiverse/nettoe.cast`: the catalog
  preview (100x30, 55 s) and the player that recorded it, reading the
  screen through pyte: games against the computer on its middle level,
  mostly with the best move from a small minimax, now and then a careless
  one.
- `.github/workflows/release.yml`: static Linux in Alpine (x86_64,
  aarch64) and macOS (x86_64, arm64), plus SHA256SUMS, on a tag.
