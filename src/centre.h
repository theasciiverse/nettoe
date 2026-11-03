/* Asciiverse: netToe's screens, centred in the terminal.
 *
 * netToe draws everything with printf, puts and putchar, against the left
 * edge, 61 columns wide (the banner). Included after a file's other
 * headers, this sends those calls through terminal.c's centre_* functions,
 * which put a left margin of half the spare width before every line; the
 * margin is measured again at every screen clear (nettoe_term_clear), so a
 * resized terminal gets it right from the next screen on. Reading input
 * ends a line too (the terminal echoes the Enter), so the reads mark it.
 * Output that is not a terminal gets no margin. See PATCHES.md. */

#ifndef NETTOE_CENTRE_H
#define NETTOE_CENTRE_H

#include <stdio.h>

int centre_printf(const char *fmt, ...);
int centre_puts(const char *s);
int centre_putchar(int c);
void centre_home(void);
int centre_read_int(int r);
char *centre_read_str(char *r);

#define printf(...) centre_printf(__VA_ARGS__)
#define puts(s) centre_puts(s)
#define putchar(c) centre_putchar(c)
#define scanf(...) centre_read_int(scanf(__VA_ARGS__))
#define getchar() centre_read_int(getchar())
#define fgets(b, n, f) centre_read_str(fgets(b, n, f))

#endif /* NETTOE_CENTRE_H */
