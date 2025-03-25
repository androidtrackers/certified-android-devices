#!/usr/bin/env python3
"""Google certified android devices tracker"""

import difflib
import json
import sys
from datetime import date
from os import rename, path, system, environ
from time import sleep
from requests import get, post

# Check for --local argument
LOCAL_MODE = '--local' in sys.argv

# Use environment variables or dummy tokens based on local mode
if LOCAL_MODE:
    GIT_OAUTH_TOKEN = 'dummy_token'
    BOT_TOKEN = 'dummy_token'
    print("Running in local mode - no GitHub or Telegram updates will be performed")
else:
    # Use environment variables if available, otherwise default to local mode
    try:
        GIT_OAUTH_TOKEN = environ['GIT_OAUTH_TOKEN_XFU']
        BOT_TOKEN = environ['BOTTOKEN']
    except KeyError:
        print("Warning: Required environment variables not found. Running in local mode.")
        LOCAL_MODE = True
        GIT_OAUTH_TOKEN = 'dummy_token'
        BOT_TOKEN = 'dummy_token'

TODAY = str(date.today())

BY_DEVICE = {}
BY_MODEL = {}
BY_BRAND = {}
BY_NAME = {}


def save_data(data_list):
    """Save Data to various files"""
    markdown = open('README.md', 'w', encoding="utf-8")
    markdown.write('# Google Play Certified Android devices\n')
    markdown.write('Last sync is {}\n\nhttps://support.google.com/googleplay/'
                   'answer/1727131?hl=en\n\n'.format(TODAY))
    markdown.write('|Retail Branding|Marketing Name|Device|Model|\n')
    markdown.write('|---|---|---|---|\n')
    for line in data_list[1:]:
        i = line.strip().split(",")
        try:
            brand = i[0].strip()
            name = i[1].strip()
            device = i[2].strip()
            model = i[3].strip()
            markdown.write('|{}|{}|{}|{}|\n'.format(brand, name, device, model))
            add_device(brand, name, device, model)
            add_model(brand, name, device, model)
            add_brand(brand, name, device, model)
            add_name(brand, name, device, model)
        except IndexError:
            pass
    
    # Explicitly specify UTF-8 encoding for all JSON files
    with open("by_device.json", "w", encoding="utf-8") as json_file:
        json.dump(BY_DEVICE, json_file, indent=1, ensure_ascii=False)
    with open("by_model.json", "w", encoding="utf-8") as json_file:
        json.dump(BY_MODEL, json_file, indent=1, ensure_ascii=False)
    with open("by_brand.json", "w", encoding="utf-8") as json_file:
        json.dump(BY_BRAND, json_file, indent=1, ensure_ascii=False)
    with open("by_name.json", "w", encoding="utf-8") as json_file:
        json.dump(BY_NAME, json_file, indent=1, ensure_ascii=False)


def add_device(brand, name, device, model):
    """add device to devices dict"""
    try:
        updated = BY_DEVICE[device] + [{'brand': brand, 'name': name, 'model': model}]
        BY_DEVICE.update({
            device: updated
        })
    except KeyError:
        BY_DEVICE.update({
            device: [{'brand': brand, 'name': name, 'model': model}]
        })


def add_model(brand, name, device, model):
    """add device to models dict"""
    try:
        updated = BY_MODEL[model] + [{'brand': brand, 'name': name, 'device': device}]
        BY_MODEL.update({
            model: updated
        })
    except KeyError:
        BY_MODEL.update({
            model: [{'brand': brand, 'name': name, 'device': device}]
        })


def add_brand(brand, name, device, model):
    """add device to brand dict"""
    try:
        updated = BY_BRAND[brand] + [{'device': device, 'name': name, 'model': model}]
        BY_BRAND.update({
            brand: updated
        })
    except KeyError:
        BY_BRAND.update({
            brand: [{'device': device, 'name': name, 'model': model}]
        })


def add_name(brand, name, device, model):
    """add device to names dict"""
    try:
        updated = BY_NAME[name] + [{'brand': brand, 'device': device, 'model': model}]
        BY_NAME.update({
            name: updated
        })
    except KeyError:
        BY_NAME.update({
            name: [{'brand': brand, 'device': device, 'model': model}]
        })


def fetch():
    """
    Download latest and convert to utf-8
    """
    url = "http://storage.googleapis.com/play_public/supported_devices.csv"
    response = get(url)
    data = (response.content.decode('utf-16'))
    data_list = list(data.split('\n'))
    return data_list


def diff_files():
    """
    diff
    """
    with open('old.md', 'r', encoding="utf-8") as old, open('README.md', 'r', encoding="utf-8") as new:
        diff = difflib.unified_diff(old.readlines(), new.readlines(), fromfile='old', tofile='new')
        changes = []
        for line in diff:
            if line.startswith('+'):
                changes.append(str(line))
    new = ''.join(changes[2:]).replace("+", "")
    with open('changes', 'w', encoding="utf-8") as out:
        out.write(new)


def post_to_tg():
    """
    post new devices to telegram channel
    """
    # Skip if running in local mode
    if LOCAL_MODE:
        print("Skipping Telegram notifications (local mode)")
        return
        
    # tg
    telegram_chat = "@CertifiedAndroidDevices"
    with open('changes', 'r', encoding="utf-8") as changes:
        for line in changes:
            info = line.split("|")
            try:
                brand = info[1]
                name = info[2]
                codename = info[3]
                model = info[4]
                telegram_message = f"New certified device added!: \n" \
                                  f"Brand: *{brand}*\n" \
                                  f"Name: *{name}*\n" \
                                  f"*Codename:* `{codename}`\n" \
                                  f"Model: *{model}*"
                params = (
                    ('chat_id', telegram_chat),
                    ('text', telegram_message),
                    ('parse_mode', "Markdown"),
                    ('disable_web_page_preview', "yes")
                )
                telegram_url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
                telegram_req = post(telegram_url, params=params)
                telegram_status = telegram_req.status_code
                if telegram_status == 200:
                    print(f"{name}: Telegram Message sent")
                else:
                    print("Telegram Error")
                sleep(3)
            except IndexError:
                # Skip malformed lines
                continue


def git_commit_push():
    """
    git add - git commit - git push
    """
    # Skip if running in local mode
    if LOCAL_MODE:
        print("Skipping Git push (local mode)")
        return
        
    system("git add README.md *.json && git -c \"user.name=XiaomiFirmwareUpdater\" "
           "-c \"user.email=xiaomifirmwareupdater@gmail.com\" "
           "commit -m \"[skip ci] sync: {0}\" && "" \
           ""git push -q https://{1}@github.com/androidtrackers/"
           "certified-android-devices.git HEAD:master"
           .format(TODAY, GIT_OAUTH_TOKEN))


def main():
    """
    certified-android-devices tracker
    """
    # Check if README.md exists and prepare for diff
    if path.exists('README.md'):
        # If old.md already exists, remove it
        if path.exists('old.md'):
            from os import remove
            remove('old.md')
        # Now rename README.md to old.md
        rename('README.md', 'old.md')
    else:
        # Create an empty old.md file if README.md doesn't exist yet
        # This avoids diff errors on first run
        with open('old.md', 'w', encoding="utf-8") as f:
            f.write('# Google Play Certified Android devices\n')

    data_list = fetch()
    save_data(data_list)
    
    # Only run diff if old.md exists
    if path.exists('old.md'):
        diff_files()
    else:
        # Create empty changes file
        with open('changes', 'w', encoding="utf-8") as f:
            pass
            
    post_to_tg()
    git_commit_push()


if __name__ == '__main__':
    main()