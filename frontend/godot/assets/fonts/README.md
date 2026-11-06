# UI typography

Pixelify Sans (variable weight font), downloaded 2026-10-13 from Google Fonts:
https://github.com/google/fonts/tree/main/ofl/pixelifysans

Redistributed under the SIL Open Font License 1.1; see OFL.txt for copyright,
license and reserved font names. The original font is unmodified.

`medieval_theme.gd` uses Pixelify Sans throughout, with an explicit SystemFont
fallback list: Arial Unicode MS, Noto Sans, Arial, sans-serif. Unsupported glyph
coverage depends on fonts installed on the host. Latin punctuation, numerals,
accented text, arrows and Chinese fallback were checked in rendered macOS output.
Font antialiasing uses Godot's font settings, independently of texture filtering.
