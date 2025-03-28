#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "requests<3",
# ]
# ///
"""Google certified android devices tracker"""

import difflib
import json
import sys
from datetime import date
from os import environ, system
from pathlib import Path
from time import sleep

from requests import get, post

GIT_OAUTH_TOKEN = environ.get("GIT_OAUTH_TOKEN_XFU", "")
BOT_TOKEN = environ.get("BOTTOKEN", "")

LOCAL_MODE = "--local" in sys.argv or not GIT_OAUTH_TOKEN or not BOT_TOKEN
if LOCAL_MODE:
    print("Running in local mode - no GitHub or Telegram updates will be performed")

TODAY = str(date.today())

BY_DEVICE = {}
BY_MODEL = {}
BY_BRAND = {}
BY_NAME = {}


def add_device(brand, name, device, model):
    """add device to devices dict"""
    try:
        updated = BY_DEVICE[device] + [{"brand": brand, "name": name, "model": model}]
        BY_DEVICE.update({device: updated})
    except KeyError:
        BY_DEVICE.update({device: [{"brand": brand, "name": name, "model": model}]})


def add_model(brand, name, device, model):
    """add device to models dict"""
    try:
        updated = BY_MODEL[model] + [{"brand": brand, "name": name, "device": device}]
        BY_MODEL.update({model: updated})
    except KeyError:
        BY_MODEL.update({model: [{"brand": brand, "name": name, "device": device}]})


def add_brand(brand, name, device, model):
    """add device to brand dict"""
    try:
        updated = BY_BRAND[brand] + [{"device": device, "name": name, "model": model}]
        BY_BRAND.update({brand: updated})
    except KeyError:
        BY_BRAND.update({brand: [{"device": device, "name": name, "model": model}]})


def add_name(brand, name, device, model):
    """add device to names dict"""
    try:
        updated = BY_NAME[name] + [{"brand": brand, "device": device, "model": model}]
        BY_NAME.update({name: updated})
    except KeyError:
        BY_NAME.update({name: [{"brand": brand, "device": device, "model": model}]})


def save_data(data_list):
    """Save Data to various files"""
    with Path("README.md").open("w", encoding="utf-8") as markdown:
        markdown.write("# Google Play Certified Android devices\n")
        markdown.write(
            f"Last sync is {TODAY}\n\nhttps://support.google.com/googleplay/"
            "answer/1727131?hl=en\n\n"
        )
        markdown.write("|Retail Branding|Marketing Name|Device|Model|\n")
        markdown.write("|---|---|---|---|\n")
        for line in data_list[1:]:
            i = line.strip().replace('"', "").split(",")
            try:
                brand = i[0].strip()
                name = i[1].strip()
                device = i[2].strip()
                model = i[3].strip()
                markdown.write(f"|{brand}|{name}|{device}|{model}|\n")
                add_device(brand, name, device, model)
                add_model(brand, name, device, model)
                add_brand(brand, name, device, model)
                add_name(brand, name, device, model)
            except IndexError:
                pass

    Path("by_device.json").write_bytes(
        json.dumps(BY_DEVICE, indent=1, ensure_ascii=False).encode("utf-8")
    )
    Path("by_model.json").write_bytes(
        json.dumps(BY_MODEL, indent=1, ensure_ascii=False).encode("utf-8")
    )
    Path("by_brand.json").write_bytes(
        json.dumps(BY_BRAND, indent=1, ensure_ascii=False).encode("utf-8")
    )
    Path("by_name.json").write_bytes(
        json.dumps(BY_NAME, indent=1, ensure_ascii=False).encode("utf-8")
    )


def fetch():
    """
    Download latest and convert to utf-8
    """
    url = "http://storage.googleapis.com/play_public/supported_devices.csv"
    response = get(url)
    data = response.content.decode("utf-16")
    data_list = list(data.split("\n"))
    return data_list


def diff_files():
    """
    diff old and new README files
    """
    old_readme_path = Path("old.md")
    new_readme_path = Path("README.md")
    changes_path = Path("changes")

    if not old_readme_path.exists() or not new_readme_path.exists():
        return

    with (
        old_readme_path.open("r", encoding="utf-8") as old_file,
        new_readme_path.open("r", encoding="utf-8") as new_file,
    ):
        diff = difflib.unified_diff(
            old_file.readlines(), new_file.readlines(), fromfile="old", tofile="new"
        )
    changes_path.write_text(
        "".join(
            [
                line[1:]
                for line in diff
                if line.startswith("+") and not line.startswith("+++")
            ]
        ),
        encoding="utf-8",
    )


def post_to_tg():
    """
    post new devices to telegram channel
    """
    telegram_chat = "@CertifiedAndroidDevices"
    changes_path = Path("changes")

    if not changes_path.exists():
        return

    changes_content = changes_path.read_text(encoding="utf-8")
    for line in changes_content.strip().splitlines():
        if not line.startswith("|"):  # Skip non-table lines if any
            continue
        parts = line.strip("|").split("|")
        if len(parts) < 4:
            print(f"Skipping malformed line: {line}")
            continue
        brand = parts[0].strip()
        name = parts[1].strip()
        codename = parts[2].strip()
        model = parts[3].strip()

        telegram_message = (
            f"New certified device added:\n"
            f"Brand: *{brand}*\n"
            f"Name: *{name}*\n"
            f"*Codename:* `{codename}`\n"
            f"Model: *{model}*"
        )
        params = (
            ("chat_id", telegram_chat),
            ("text", telegram_message),
            ("parse_mode", "Markdown"),
            ("disable_web_page_preview", "yes"),
        )
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        telegram_req = post(telegram_url, params=params)
        telegram_status = telegram_req.status_code
        if telegram_status == 200:
            print("{0}: Telegram Message sent".format(name))
        else:
            print("Telegram Error")
        sleep(3)


def git_commit_push():
    """
    git add - git commit - git push
    """
    commit_message = f"[skip ci sync: {TODAY}"
    push_url = f"https://{GIT_OAUTH_TOKEN}@github.com/androidtrackers/certified-android-devices.git HEAD:master"

    system(
        f'git add README.md *.json && git -c "user.name=XiaomiFirmwareUpdater" '
        f'-c "user.email=xiaomifirmwareupdater@gmail.com" '
        f'commit -m "{commit_message}" && git push -q {push_url}'
    )


def main():
    """
    certified-android-devices tracker
    """
    readme_path = Path("README.md")
    old_readme_path = Path("old.md")

    if readme_path.exists():
        if old_readme_path.exists():
            old_readme_path.unlink()
        readme_path.rename(old_readme_path)

    data_list = fetch()
    save_data(data_list)
    diff_files()

    if not LOCAL_MODE:
        post_to_tg()
        git_commit_push()


if __name__ == "__main__":
    main()
