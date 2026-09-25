#!/usr/bin/env python3
"""Refresh the avatar embedded in the profile hero when the GitHub photo changes."""

import base64
import pathlib
import re
import sys
import urllib.parse
import urllib.request


def image_mime(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("GitHub returned an unsupported avatar image format")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: sync_profile_avatar.py HERO_SVG GITHUB_USERNAME")

    svg_path = pathlib.Path(sys.argv[1])
    username = urllib.parse.quote(sys.argv[2], safe="")
    request = urllib.request.Request(
        f"https://github.com/{username}.png?size=256",
        headers={
            "User-Agent": "profile-readme-avatar-sync",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        avatar = response.read()

    if not avatar or len(avatar) > 1_000_000:
        raise ValueError("GitHub avatar response is empty or unexpectedly large")

    data_uri = f"data:{image_mime(avatar)};base64,{base64.b64encode(avatar).decode('ascii')}"
    current = svg_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<image\b[^>]*\bid="github-avatar"[^>]*\bhref=")'
        r'data:image/(?:jpeg|png|gif|webp);base64,[A-Za-z0-9+/=]+(")'
    )
    updated, count = pattern.subn(
        lambda match: match.group(1) + data_uri + match.group(2),
        current,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not find exactly one embedded GitHub avatar in the hero SVG")
    if updated != current:
        svg_path.write_text(updated, encoding="utf-8")
        print("GitHub avatar changed; updated profile hero.")
    else:
        print("GitHub avatar is unchanged.")


if __name__ == "__main__":
    main()
