#!/usr/bin/env python3
"""Post newly published Quarto blog posts to Buffer."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


BUFFER_API = "https://api.buffer.com"


@dataclass(frozen=True)
class BlogPost:
    path: Path
    title: str
    date: datetime
    url: str
    description: str
    image: str
    author: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Post newly published Quarto posts through Buffer."
    )
    parser.add_argument("--posts-dir", default="posts")
    parser.add_argument("--site-url", default="https://spatialists.ch")
    parser.add_argument("--cache-file", default=".buffer-post-cache.json")
    parser.add_argument("--lookback-hours", type=int, default=72)
    parser.add_argument("--max-posts", type=int, default=3)
    parser.add_argument("--mode", default=os.getenv("BUFFER_SHARE_MODE", "shareNow"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing-on-first-run", action="store_true")
    parser.add_argument(
        "--bootstrap-before",
        help="On first run, mark posts before this local datetime as seen before publishing candidates.",
    )
    parser.add_argument("--timezone", default="Europe/Zurich")
    parser.add_argument("--api-key", default=os.getenv("BUFFER_API_KEY"))
    parser.add_argument("--channel-id", default=os.getenv("BUFFER_LINKEDIN_CHANNEL_ID"))
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value[0] in {"'", '"'}:
        try:
            return str(ast.literal_eval(value))
        except (SyntaxError, ValueError):
            if value[0] == "'" and value.endswith("'"):
                return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    lines = text[4:end].splitlines()
    data: dict[str, Any] = {}
    author_names: list[str] = []
    current_key = ""

    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match:
            current_key = key_match.group(1)
            raw_value = key_match.group(2)
            if raw_value:
                data[current_key] = unquote_yaml_scalar(raw_value)
            elif current_key not in data:
                data[current_key] = ""
            continue
        if current_key == "author":
            name_match = re.match(r"^\s*-?\s*name:\s*(.*)$", line)
            if name_match:
                author_names.append(unquote_yaml_scalar(name_match.group(1)))

    if author_names:
        data["author_names"] = author_names
    return data


def parse_date(value: str, timezone_name: str) -> datetime | None:
    if not value:
        return None
    site_timezone = ZoneInfo(timezone_name)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=site_timezone).astimezone(timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=site_timezone)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def post_url(site_url: str, post_file: Path) -> str:
    directory = post_file.parent.as_posix()
    return f"{site_url.rstrip('/')}/{directory}/"


def image_url(post: BlogPost) -> str:
    if not post.image:
        return ""
    if post.image.startswith(("http://", "https://")):
        return post.image
    return f"{post.url}{urllib.parse.quote(post.image)}"


def find_posts(posts_dir: Path, site_url: str, timezone_name: str) -> list[BlogPost]:
    posts: list[BlogPost] = []
    for post_file in posts_dir.glob("**/index.qmd"):
        metadata = parse_frontmatter(post_file)
        if str(metadata.get("draft", "")).lower() == "true":
            continue
        date = parse_date(str(metadata.get("date", "")), timezone_name)
        title = str(metadata.get("title", "")).strip()
        if not date or not title:
            continue
        authors = metadata.get("author_names") or []
        author = ", ".join(authors) if isinstance(authors, list) else ""
        posts.append(
            BlogPost(
                path=post_file,
                title=title,
                date=date,
                url=post_url(site_url, post_file),
                description=str(metadata.get("description", "")).strip(),
                image=str(metadata.get("image", "")).strip(),
                author=author,
            )
        )
    return sorted(posts, key=lambda post: post.date)


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"posted_urls": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def post_text(post: BlogPost) -> str:
    parts = [post.description or post.title, "#GIS #geospatial #SwissGIS", post.url]
    return " ".join(parts)


def buffer_graphql(api_key: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    request_body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(BUFFER_API, data=request_body, method="POST")
    request.add_header("Authorization", f"Bearer {api_key}")
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        fail(f"Buffer API returned HTTP {error.code}: {response_body}")

    if data.get("errors"):
        fail(f"Buffer GraphQL errors: {json.dumps(data['errors'])}")
    return data


def publish_post(post: BlogPost, api_key: str, channel_id: str, mode: str) -> str:
    assets = []
    featured_image = image_url(post)
    if featured_image:
        assets.append({"image": {"url": featured_image}})

    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            text
            dueAt
            status
            shareMode
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    variables = {
        "input": {
            "text": post_text(post),
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": mode,
            "assets": assets,
        }
    }
    data = buffer_graphql(api_key, query, variables)
    result = data.get("data", {}).get("createPost", {})
    if result.get("message"):
        fail(f"Buffer could not create post for {post.url}: {result['message']}")
    post_id = result.get("post", {}).get("id")
    if not post_id:
        fail(f"Buffer response did not include a post id: {json.dumps(result)}")
    return str(post_id)


def current_posts_seen(posts_dir: Path, site_url: str, timezone_name: str) -> set[str]:
    now = datetime.now(timezone.utc)
    return {
        post.url
        for post in find_posts(posts_dir, site_url, timezone_name)
        if post.date <= now
    }


def posts_before(
    posts_dir: Path, site_url: str, timezone_name: str, cutoff: datetime
) -> set[str]:
    return {
        post.url
        for post in find_posts(posts_dir, site_url, timezone_name)
        if post.date < cutoff
    }


def main() -> None:
    args = parse_args()
    cache_path = Path(args.cache_file)
    first_run = not cache_path.exists()
    cache = load_cache(cache_path)
    posted_urls = set(cache.get("posted_urls", []))
    now = datetime.now(timezone.utc)
    earliest = now - timedelta(hours=args.lookback_hours)
    posts_dir = Path(args.posts_dir)
    candidates = [
        post
        for post in find_posts(posts_dir, args.site_url, args.timezone)
        if earliest <= post.date <= now and post.url not in posted_urls
    ][-args.max_posts :]

    if first_run and args.bootstrap_before:
        cutoff = parse_date(args.bootstrap_before, args.timezone)
        if cutoff is None:
            fail(f"--bootstrap-before is not a valid date: {args.bootstrap_before}")
        seeded_urls = posts_before(posts_dir, args.site_url, args.timezone, cutoff)
        print(
            f"No Buffer cache found; marking {len(seeded_urls)} posts before "
            f"{args.bootstrap_before} as seen."
        )
        posted_urls.update(seeded_urls)
        cache["posted_urls"] = sorted(posted_urls)
        if not args.dry_run:
            save_cache(cache_path, cache)
        candidates = [post for post in candidates if post.url not in posted_urls]
    elif first_run and args.skip_existing_on_first_run:
        print("No Buffer cache found; marking current posts as seen without posting.")
        if not args.dry_run:
            cache["posted_urls"] = sorted(
                posted_urls | current_posts_seen(posts_dir, args.site_url, args.timezone)
            )
            save_cache(cache_path, cache)
        return

    if not candidates:
        print("No new posts to publish through Buffer.")
        return

    if not args.dry_run and (not args.api_key or not args.channel_id):
        fail("BUFFER_API_KEY and BUFFER_LINKEDIN_CHANNEL_ID are required.")

    for post in candidates:
        print(f"Publishing through Buffer: {post.title} ({post.url})")
        print(f"mode: {args.mode}")
        print(f"image: {image_url(post)}")
        if args.dry_run:
            print(post_text(post))
            continue

        post_id = publish_post(post, args.api_key, args.channel_id, args.mode)
        posted_urls.add(post.url)
        cache.setdefault("posts", {})[post.url] = {
            "title": post.title,
            "date": post.date.isoformat(),
            "buffer_post_id": post_id,
            "mode": args.mode,
        }
        cache["posted_urls"] = sorted(posted_urls)
        save_cache(cache_path, cache)


if __name__ == "__main__":
    main()
