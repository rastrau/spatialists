# Usage on the command line (with `uv` installed):
# uv run draft.py
# uv run draft.py --days 3

import argparse
import os
import re
import unicodedata
from datetime import datetime, timedelta

# Default author details
DEFAULT_AUTHOR_NAME = "Ralph Straumann"
DEFAULT_AUTHOR_URL = "https://ralphstraumann.ch"

def normalize_special_chars(text):
    """
    Normalize a given text by converting it to NFKD Unicode form and removing 
    non-ASCII characters.

    Args:
        text (str): The input string to be normalized.

    Returns:
        str: A normalized string with non-ASCII characters removed.
    """
    # Normalize to NFKD form
    normalized = unicodedata.normalize('NFKD', text)
    # Remove non-ASCII characters
    ascii_text = re.sub(r'[^\x00-\x7F]+', '', normalized)
    return ascii_text

def create_blog_post(days_ahead=0):
    """
    Creates a draft blog post file with frontmatter metadata.

    This function prompts the user for a blog post title, generates a directory
    and file structure based on the target date and a slugified version of the
    title, and writes a frontmatter template to the file. If the file already
    exists, the user is prompted to confirm overwriting it.

    Args:
        days_ahead (int): Number of days to push the post into the future.
            Defaults to 0 (today + 15 minutes).

    Returns:
        None
    """
    # Prompt user for blog post title
    title = input("Enter the blog post title: ").strip()

    # Generate date components
    now = datetime.now() + timedelta(days=days_ahead)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    # Shift date_time 15 minutes into the future
    future_time = now + timedelta(minutes=15)
    date_time = future_time.strftime("%Y-%m-%d %H:%M")
    
    # Generate a slug for the title (lowercase, no special characters, hyphen-separated)
    slug = normalize_special_chars(title)
    slug = re.sub(r"[^\w\s-]", "", slug).strip().lower()
    slug = re.sub(r"[\s]+", "-", slug)
    
    # Define the file path
    directory_path = os.path.join("posts", year, month, f"{day}-{slug}")
    file_path = os.path.join(directory_path, "index.qmd")
    
    # Create directories if they don't exist
    os.makedirs(directory_path, exist_ok=True)
    
    # Frontmatter template
    frontmatter = f"""---
title: "{title}"
author:
  - name: {DEFAULT_AUTHOR_NAME}
    url: {DEFAULT_AUTHOR_URL}
date: "{date_time}"
image: ""
description: ""
---

Blog post...
"""
    
    # Write the frontmatter to the file
    if os.path.exists(file_path):
        overwrite = input(f"The file {file_path} already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite == 'y':
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter)
        else:
            print("Operation cancelled. No file was overwritten.") 
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter)
        
    print(f"Draft blog post created at: {file_path}")

# Run the program
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a draft blog post.")
    parser.add_argument(
        "--days", type=int, default=0,
        help="Number of days to push the post date into the future (default: 0)"
    )
    args = parser.parse_args()
    create_blog_post(days_ahead=args.days)
