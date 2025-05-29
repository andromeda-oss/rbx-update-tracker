import aiohttp
import os
import json
import hashlib
from deepdiff import DeepDiff

API_URL = "https://clientsettings.roblox.com/v2/client-version/WindowsPlayer"
DUMP_URL = "https://anaminus.github.io/rbx/json/api/latest.json"

CACHE_VERSION_FILE = "latest_version.txt"
CACHE_DUMP_FILE = "latest_api_dump.json"
CACHE_HASH_FILE = "latest_hash.txt"
DIFF_FILE = "diff.txt"

# --------------- File Helpers ---------------

def save_file(path, data, json_mode=True):
    with open(path, "w", encoding="utf-8") as f:
        if json_mode:
            json.dump(data, f, indent=2)
        else:
            f.write(data)

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_cached_version():
    if not os.path.exists(CACHE_VERSION_FILE):
        return None
    with open(CACHE_VERSION_FILE, "r") as f:
        return f.read().strip()

def get_cached_hash():
    if not os.path.exists(CACHE_HASH_FILE):
        return None
    with open(CACHE_HASH_FILE, "r") as f:
        return f.read().strip()

def compute_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

# --------------- Fetchers ---------------

async def fetch_latest_version_id():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            data = await resp.json()
            return data.get("clientVersionUpload")

async def fetch_api_dump():
    async with aiohttp.ClientSession() as session:
        async with session.get(DUMP_URL) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

# --------------- Diff Formatter ---------------

def format_diff(diff):
    lines = []

    if "values_changed" in diff:
        for path, change in diff["values_changed"].items():
            old = change["old_value"]
            new = change["new_value"]
            lines.append(f"~ {path} changed:")
            lines.append(f"  - {old}")
            lines.append(f"  + {new}")

    if "dictionary_item_added" in diff:
        for path in diff["dictionary_item_added"]:
            lines.append(f"+ Added: {path}")

    if "dictionary_item_removed" in diff:
        for path in diff["dictionary_item_removed"]:
            lines.append(f"- Removed: {path}")

    if "iterable_item_added" in diff:
        for path, value in diff["iterable_item_added"].items():
            lines.append(f"+ Added at {path}: {value}")

    if "iterable_item_removed" in diff:
        for path, value in diff["iterable_item_removed"].items():
            lines.append(f"- Removed from {path}: {value}")

    return "\n".join(lines)

# --------------- Core Update Logic ---------------

async def check_for_update():
    new_version = await fetch_latest_version_id()
    if not new_version:
        print("❌ Failed to fetch version.")
        return False, None, None, None

    old_version = get_cached_version()
    if old_version == new_version:
        print("No new version detected.")
        return False, new_version, None, None

    print(f"[CHECK] New version: {new_version}")

    new_dump = await fetch_api_dump()
    if not new_dump:
        print("❌ Failed to fetch new API dump.")
        return False, new_version, None, None

    old_dump = load_json(CACHE_DUMP_FILE) or {}
    diff = DeepDiff(old_dump, new_dump, ignore_order=True, verbose_level=2)

    formatted_diff = format_diff(diff)
    save_file(DIFF_FILE, formatted_diff, json_mode=False)

    new_hash = compute_hash(new_dump)
    save_file(CACHE_DUMP_FILE, new_dump)
    save_file(CACHE_VERSION_FILE, new_version, json_mode=False)
    save_file(CACHE_HASH_FILE, new_hash, json_mode=False)

    print("✅ New version and dump saved.")
    return True, new_version, new_hash, formatted_diff

def get_diff_output():
    if not os.path.exists(DIFF_FILE):
        return "No diff available."
    with open(DIFF_FILE, "r", encoding="utf-8") as f:
        return f.read()
