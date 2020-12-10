"""
==================================
String coloration escape sequences
==================================
Brief:
------
    A set of string coloration escape sequences
Important
---------
    This project is published under **MIT License**
"""

# ╔══════════╦════════════════════════════════╦════════════════════════════════════════════╗
# ║  Code    ║             Effect             ║                  Note                      ║
# ╠══════════╬════════════════════════════════╬════════════════════════════════════════════╣
# ║ 0        ║  Reset / Normal                ║  All attributes off                        ║
# ║ 1        ║  Bold or increased intensity   ║                                            ║
# ║ 2        ║  Faint (decreased intensity)   ║  Not widely supported.                     ║
# ║ 3        ║  Italic                        ║  Not widely supported. Sometimes treated   ║
# ║          ║                                ║      as inverse.                           ║
# ║ 4        ║  Underline                     ║                                            ║
# ║ 5        ║  Slow Blink                    ║  Less than 150 per minute                  ║
# ║ 6        ║  Rapid Blink                   ║  MS-DOS ANSI.SYS; 150+ per minute;         ║
# ║          ║                                ║      not widely supported                  ║
# ║ 7        ║  [[reverse video]]             ║  Swap foreground and background colors     ║
# ║ 8        ║  Conceal                       ║  Not widely supported.                     ║
# ║ 9        ║  Crossed-out                   ║  Characters legible, but marked for        ║
# ║          ║                                ║      deletion.  Not widely supported.      ║
# ║ 10       ║  Primary(default) font         ║                                            ║
# ║ 11–19    ║  Alternate font                ║  Select alternate font `n-10`              ║
# ║ 20       ║  Fraktur                       ║  Hardly ever supported                     ║
# ║ 21       ║  Bold off or Double Underline  ║  Bold off not widely supported; double     ║
# ║          ║                                ║      underline hardly ever supported.      ║
# ║ 22       ║  Normal color or intensity     ║  Neither bold nor faint                    ║
# ║ 23       ║  Not italic, not Fraktur       ║                                            ║
# ║ 24       ║  Underline off                 ║  Not singly or doubly underlined           ║
# ║ 25       ║  Blink off                     ║                                            ║
# ║ 27       ║  Inverse off                   ║                                            ║
# ║ 28       ║  Reveal                        ║  Conceal off                               ║
# ║ 29       ║  Not crossed out               ║                                            ║
# ║ 30–37    ║  Set foreground color          ║  See color table below                     ║
# ║ 38       ║  Set foreground color          ║  Next arguments are `5;n` or `2;r;g;b`,    ║
# ║          ║                                ║      see below                             ║
# ║ 39       ║  Default foreground color      ║  Implementation defined (according to      ║
# ║          ║                                ║      standard)                             ║
# ║ 40–47    ║  Set background color          ║  See color table below                     ║
# ║ 48       ║  Set background color          ║  Next arguments are `5;n` or `2;r;g;b`,    ║
# ║          ║                                ║      see below                             ║
# ║ 49       ║  Default background color      ║  Implementation defined (according to      ║
# ║          ║                                ║      standard)                             ║
# ║ 51       ║  Framed                        ║                                            ║
# ║ 52       ║  Encircled                     ║                                            ║
# ║ 53       ║  Overlined                     ║                                            ║
# ║ 54       ║  Not framed or encircled       ║                                            ║
# ║ 55       ║  Not overlined                 ║                                            ║
# ║ 60       ║  Ideogram underline            ║  Hardly ever supported                     ║
# ║ 61       ║  Ideogram double underline     ║  Hardly ever supported                     ║
# ║ 62       ║  Ideogram overline             ║  Hardly ever supported                     ║
# ║ 63       ║  Ideogram double overline      ║  Hardly ever supported                     ║
# ║ 64       ║  Ideogram stress marking       ║  Hardly ever supported                     ║
# ║ 65       ║  Ideogram attributes off       ║  Reset the effects of all of 60-64         ║
# ║ 90–97    ║  Set bright foreground color   ║  aixterm (not in standard)                 ║
# ║ 100–107  ║  Set bright background color   ║  aixterm (not in standard)                 ║
# ╚══════════╩════════════════════════════════╩════════════════════════════════════════════╝

NORMAL = "\033[0m"
STRONG = "\033[1m"
SLANTED = "\033[3m"
UNDERLINED = "\033[4m"

# ╔═══════════╦══════════════╦══════════════════════════╗
# ║ Colour    ║ Numeral code ║ Alternative numeral code ║
# ╠═══════════╬══════════════╬══════════════════════════╣
# ║ Black     ║ 30           ║ 40                       ║
# ║ Red       ║ 31           ║ 41                       ║
# ║ Green     ║ 32           ║ 42                       ║
# ║ Yellow    ║ 33           ║ 43                       ║
# ║ Blue      ║ 34           ║ 44                       ║
# ║ Magenta   ║ 35           ║ 45                       ║
# ║ Cyan      ║ 36           ║ 46                       ║
# ║ White     ║ 37           ║ 47                       ║
# ║ Grey /    ║ 30;1         ║ 100                      ║
# ║   Bright  ║              ║                          ║
# ║   Black   ║              ║                          ║
# ║ Bright    ║ 31;1         ║ 100                      ║
# ║   Red     ║              ║                          ║
# ║ Bright    ║ 32;1         ║ 100                      ║
# ║   Green   ║              ║                          ║
# ║ Bright    ║ 33;1         ║ 100                      ║
# ║   Yellow  ║              ║                          ║
# ║ Bright    ║ 34;1         ║ 100                      ║
# ║   Blue    ║              ║                          ║
# ║ Bright    ║ 35;1         ║ 100                      ║
# ║   Magenta ║              ║                          ║
# ║ Bright    ║ 36;1         ║ 100                      ║
# ║   Cyan    ║              ║                          ║
# ╚═══════════╩══════════════╩══════════════════════════╝

RED = "\033[31m"
STRONG_RED = "\033[31;1m"
GREEN = "\033[32m"
STRONG_GREEN = "\033[32;1m"
SLANTED_GREEN = "\033[32;3m"
UNDERLINED_GREEN = "\033[32;4m"
YELLOW = "\033[33m"
SLANTED_YELLOW = "\033[33;3m"
BLUE = "\033[34m"
STRONG_BLUE = "\033[34;1m"
PURPLE = "\033[35;1m"   # Purple equals bright magenta