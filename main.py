import os
import re
import time
import requests
from typing import Iterable, Optional

OSU_TOKEN_URL = "https://osu.ppy.sh/oauth/token"
OSU_API_BASE = "https://osu.ppy.sh/api/v2"


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180] if len(name) > 180 else name


def get_client_credentials_token(client_id: str, client_secret: str) -> str:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "public",
    }
    r = requests.post(OSU_TOKEN_URL, data=data, timeout=30)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {r.text}")
    return token


def osu_api_get(token: str, path: str, params: Optional[dict] = None) -> dict | list:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    r = requests.get(f"{OSU_API_BASE}{path}", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_osu_top_plays(
    token: str,
    user_id: int,
    mode: str,
    limit_total: int
) -> list[dict]:
    scores: list[dict] = []
    offset = 0
    page_size = 100

    while offset < limit_total:
        params = {
            "mode": mode,
            "limit": min(page_size, limit_total - offset),
            "offset": offset,
            "legacy_only": 0,
            "include_fails": 0,
        }

        batch = osu_api_get(token, f"/users/{user_id}/scores/best", params=params)

        if not isinstance(batch, list) or not batch:
            break

        scores.extend(batch)
        offset += len(batch)
        time.sleep(0.2)

    return scores


def iter_beatmapsets_from_scores(scores: Iterable[dict]) -> list[tuple[int, str]]:
    seen: set[int] = set()
    result: list[tuple[int, str]] = []

    for s in scores:
        bms_id = None
        title = None

        beatmapset = s.get("beatmapset")
        if isinstance(beatmapset, dict):
            bms_id = beatmapset.get("id")
            artist = beatmapset.get("artist") or ""
            t = beatmapset.get("title") or ""
            title = f"{artist} - {t}".strip(" -")

        if bms_id is None:
            beatmap = s.get("beatmap")
            if isinstance(beatmap, dict):
                bms_id = beatmap.get("beatmapset_id")

        if bms_id is None:
            continue

        bms_id = int(bms_id)
        if bms_id in seen:
            continue
        seen.add(bms_id)

        if not title:
            title = f"beatmapset_{bms_id}"

        result.append((bms_id, title))

    return result


def download_beatconnect_osz(beatmapset_id: int, display_title: str) -> bool:
    # current directory (where script is run)
    out_dir = os.path.abspath(".")

    safe_title = sanitize_filename(display_title)
    out_path = os.path.join(out_dir, f"{beatmapset_id} - {safe_title}.osz")

    # skip if already exists
    if os.path.exists(out_path):
        print(f"[SKIP] {beatmapset_id} - {display_title}")
        return True

    url = f"https://beatconnect.io/b/{beatmapset_id}?n=1"

    try:
        r = requests.get(url, allow_redirects=True, timeout=60)
        if r.status_code != 200 or not r.content:
            print(f"[FAIL] {beatmapset_id} - {display_title}")
            return False

        with open(out_path, "wb") as f:
            f.write(r.content)

        print(f"[OK]   {beatmapset_id} - {display_title}")
        return True

    except Exception as e:
        print(f"[ERR]  {beatmapset_id} - {display_title} ({e})")
        return False


def main():
    print("=== osu! top plays downloader ===\n")

    user_id = int(input("osu! user id: ").strip())
    client_id = input("osu! client id: ").strip()
    client_secret = input("osu! client secret: ").strip()

    mode = input("mode (osu / mania / taiko / fruits) [osu]: ").strip().lower()
    if mode not in {"osu", "mania", "taiko", "fruits"}:
        mode = "osu"

    limit_total = int(input("number of top plays to fetch (max ~200): ").strip())

    print("\nRequesting OAuth token...")
    token = get_client_credentials_token(client_id, client_secret)

    print(f"Fetching {mode} top plays...")
    scores = fetch_osu_top_plays(token, user_id, mode, limit_total)
    print(f"Fetched {len(scores)} scores.")

    beatmapsets = iter_beatmapsets_from_scores(scores)
    print(f"Unique beatmapsets: {len(beatmapsets)}\n")

    failed: list[int] = []
    for bms_id, title in beatmapsets:
        if not download_beatconnect_osz(bms_id, title):
            failed.append(bms_id)
        time.sleep(0.2)

    if failed:
        with open("failed_downloads.txt", "w", encoding="utf-8") as f:
            for bms_id in failed:
                f.write(f"{bms_id}\n")
        print(f"\nFinished with {len(failed)} failures (see failed_downloads.txt)")
    else:
        print("\nFinished with no failures 🎉")


if __name__ == "__main__":
    main()

