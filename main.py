import os
import re
import time
import requests
from typing import Iterable, Optional

OSU_TOKEN_URL = "https://osu.ppy.sh/oauth/token"
OSU_API_BASE = "https://osu.ppy.sh/api/v2"

# CHANGE THESE TO YOURS
OSU_CLIENT_ID = "0"
OSU_CLIENT_SECRET = "0"

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
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    r = requests.get(f"{OSU_API_BASE}{path}", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_osu_top_plays(token: str, user_id: int, limit_total: int = 1000) -> list[dict]:
    """
    Fetches osu top plays (best scores) for a user.
    Uses pagination with limit/offset.
    """
    scores: list[dict] = []
    offset = 0
    page_size = 100

    while offset < limit_total:
        params = {
            "mode": "osu",
            "limit": min(page_size, limit_total - offset),
            "offset": offset,
            "legacy_only": 0,
            "include_fails": 0,
        }
        batch = osu_api_get(token, f"/users/{user_id}/scores/best", params=params)

        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected response: {batch}")

        if not batch:
            break

        scores.extend(batch)
        offset += len(batch)

        time.sleep(0.2)

    return scores


def iter_beatmapsets_from_scores(scores: Iterable[dict]) -> list[tuple[int, str]]:
    """
    Returns list of (beatmapset_id, display_title) from score objects.
    Deduped by beatmapset_id.
    """
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

        # Fallback: beatmap -> beatmapset_id
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


def download_beatconnect_osz(beatmapset_id: int, display_title: str, out_dir: str = "downloads") -> bool:
    """
    Downloads a beatmapset .osz from beatconnect.
    """
    os.makedirs(out_dir, exist_ok=True)
    safe_title = sanitize_filename(display_title)
    out_path = os.path.join(out_dir, f"{beatmapset_id} - {safe_title}.osz")

    url = f"https://beatconnect.io/b/{beatmapset_id}?n=1"
    try:
        r = requests.get(url, allow_redirects=True, timeout=60)
        if r.status_code != 200 or not r.content:
            print(f"[FAIL] {beatmapset_id} - {display_title} (status {r.status_code})")
            return False

        with open(out_path, "wb") as f:
            f.write(r.content)

        print(f"[OK]   {beatmapset_id} - {display_title}")
        return True
    except Exception as e:
        print(f"[ERR]  {beatmapset_id} - {display_title} ({e})")
        return False


def main():
    # ---- CONFIG ----
    user_id = 0  # your osu! user id
    limit_total = 200  # how many top plays to scan (200 max)
    out_dir = "downloads"

    client_id = os.getenv("OSU_CLIENT_ID")
    client_secret = os.getenv("OSU_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit(
            "Missing OSU_CLIENT_ID / OSU_CLIENT_SECRET env vars.\n"
            "Set them in CMD (Windows):\n"
            "  setx OSU_CLIENT_ID \"your_id\"\n"
            "  setx OSU_CLIENT_SECRET \"your_secret\"\n"
            "Then reopen CMD.\n"
        )

    # ---- RUN ----
    token = get_client_credentials_token(client_id, client_secret)

    scores = fetch_osu_top_plays(token, user_id=user_id, limit_total=limit_total)
    print(f"Fetched {len(scores)} osu top-play scores.")

    beatmapsets = iter_beatmapsets_from_scores(scores)
    print(f"Unique beatmapsets to download: {len(beatmapsets)}")

    failed: list[int] = []
    for bms_id, title in beatmapsets:
        ok = download_beatconnect_osz(bms_id, title, out_dir=out_dir)
        if not ok:
            failed.append(bms_id)
        time.sleep(0.2)

    if failed:
        with open("failed_downloads_osu_topplays.txt", "w", encoding="utf-8") as f:
            for bms_id in failed:
                f.write(f"{bms_id}\n")
        print(f"Done with failures: {len(failed)} (see failed_downloads_osu_topplays.txt)")
    else:
        print("Done! No failures.")


if __name__ == "__main__":
    main()


