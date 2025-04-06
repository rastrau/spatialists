# Usage on the command line (with `uv` installed): 
# uv run create-draft.py

import os
import re
import unicodedata
from datetime import datetime, timedelta

# Default author details
DEFAULT_AUTHOR_NAME = "Ralph Straumann"
DEFAULT_AUTHOR_URL = "https://ralphstraumann.ch"

def normalize_special_chars(text):
    # Normalize to NFKD form
    normalized = unicodedata.normalize('NFKD', text)
    # Remove non-ASCII characters
    ascii_text = re.sub(r'[^\x00-\x7F]+', '', normalized)
    return ascii_text

def create_blog_post():
    # Prompt user for blog post title
    title = input("Enter the blog post title: ").strip()
    
    # Generate date components
    now = datetime.now()
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
    slug = slug.replace("draft", "DRAFT")
    
    # Define the file path
    directory_path = os.path.join("posts", year, f"{month}-{day}-{slug}")
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
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    
    print(f"Draft blog post created at: {file_path}")

# Run the program
if __name__ == "__main__":
    create_blog_post()
