## Spatialists blog

This is a Quarto-based microblog about geospatial news. Posts live in `posts/` as `.qmd` files, organized by `posts/YEAR/MONTH/DD-slug/index.qmd`.

## Footnotes

`footnotes.txt` at the repo root is a manually curated glossary of reusable footnote definitions. When helping write or review a `.qmd` post:

1. Read `footnotes.txt` and check if any terms, abbreviations, or concepts in the draft have a matching entry.
2. Suggest inserting matching footnotes where appropriate — don't add footnotes the author hasn't used before without asking.
3. Use **reference-style footnotes** as the default format: `[^label]` in the text body and `[^label]: definition` at the end of the post.
4. When a matching entry exists in `footnotes.txt`, reuse its definition verbatim (the author has already curated the wording).

## Blurb

Every blog post needs a blurb. Blurbs are 2 sentences long and should advertise the blog post's contents in an interesting way to geospatial professionals. Key terms (individual words or groups of words) should be turned into hashtags. The hashtags "#GIS", "#geospatial", and "#SwissGIS" will be added to the RSS feed and social posts by default, i.e. these terms do not need to be marked as hashtags in the blurb. The blurb for the blogpost goes into "description" field in the YAML frontmatter.