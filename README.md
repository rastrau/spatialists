# Spatialists

This repository contains the Quarto source for
[spatialists.ch](https://spatialists.ch), a geospatial news blog.

Posts live in `posts/YYYY/MM/DD-slug/index.qmd`. Each post keeps its images and
other local assets next to the post source.

## Local Setup

Install:

- [Quarto](https://quarto.org/)
- Python 3
- [`uv`](https://docs.astral.sh/uv/) if you want to use the draft helper exactly
  as shown below

Useful local commands:

```sh
uv run draft.py
uv run draft.py --days 1
quarto preview
```

## Writing A Post

Create a draft:

```sh
uv run draft.py
```

The helper asks for a title and creates a new post at:

```text
posts/YYYY/MM/DD-slug/index.qmd
```

The generated frontmatter contains the expected fields (pre-filled with default author):

```yaml
---
title: "Post title"
author:
  - name: "Ralph Straumann"
    url: "https://ralphstraumann.ch"
date: "YYYY-MM-DD HH:MM"
image: ""
description: ""
---
```

Before publishing, check:

- `title` is final.
- `date` is the intended publication date and time in Europe/Switzerland local time.
- `image` points to a local image in the post folder.
- `description` is a two-sentence blurb for the homepage, RSS feed, Mastodon,
  and LinkedIn.
- Links are reference-style where useful and resolve correctly.
- Reusable footnotes from `footnotes.txt` are used where they fit.

The writing guidance in `.claude/CLAUDE.md` describes the preferred blurb and
footnote conventions.

## Images And Assets

Put post-specific images next to the post's `index.qmd` and reference them by
filename:

```markdown
![Caption](image.jpg "Caption")
```

Use the post `image` frontmatter field for the title card and social previews.
The home page falls back to `assets/titlecard.jpg` if a listing needs a
placeholder.

## Rendering

Preview locally while writing:

```sh
quarto preview
```

Render the whole site before publishing when you want to catch Quarto issues
locally:

```sh
quarto render
```

The rendered site is written to `_site/`. Quarto execution freezing is enabled
in `_quarto.yml` and `posts/_metadata.yml`.

## Publishing

Publishing is handled by GitHub Actions in
`.github/workflows/render-publish-post.yml`.

On every push to `main`, the workflow:

1. Checks out the repository.
2. Sets up Quarto.
3. Restores the Quarto freeze cache.
4. Renders the site into `_site/`.
5. Uploads `_site/` to the FTP server via FTPS.
6. Posts new RSS items to Mastodon.
7. Posts recent new posts to LinkedIn through Buffer.

Required GitHub secrets:

- `FTP_SERVER`
- `FTP_USER`
- `FTP_PASSWORD`
- `MASTODON_ACCESS_TOKEN`
- `BUFFER_API_KEY`
- `BUFFER_LINKEDIN_CHANNEL_ID`

Optional GitHub variable:

- `BUFFER_SHARE_MODE`, defaulting to `shareNow`

## Social Posting

Mastodon posting is driven from the rendered RSS feed at
`https://spatialists.ch/index.xml`.

LinkedIn posting uses `scripts/post_to_buffer.py`, which scans recent published
posts and creates Buffer posts. Run a dry run locally with:

```sh
python3 scripts/post_to_buffer.py --dry-run
```

The Buffer script uses a cache file in GitHub Actions so the same post is not
sent repeatedly.

## External Contributions

Post suggestions can be submitted through the GitHub issue template at
`.github/ISSUE_TEMPLATE/submit-post.yml` or <https://github.com/rastrau/spatialists/issues>.
