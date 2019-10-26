#!/usr/bin/env python3.7
"""Google certified android devices tracker"""

import difflib
import json
import codecs
from datetime import date
from os import rename, path, system, environ
from requests import get, post

GIT_OAUTH_TOKEN = environ['GIT_OAUTH_TOKEN_XFU']
BOT_TOKEN = environ['bottoken']
TODAY = str(date.today())


def fetch():
    """
    Download latest and convert to utf-8
    """
    url = "http://storage.googleapis.com/play_public/supported_devices.csv"
    response = get(url)
    data = codecs.escape_decode(response.content)[0].decode('utf-16')
    data_list = list(data.split('\n'))
    with open('README.md', 'w', encoding="utf-8") as markdown,\
            open('devices.json', 'w') as json_out:
        markdown.write('# Google Play Certified Android devices\n')
        markdown.write('Last sync is {}\n\nhttps://support.google.com/googleplay/'
                       'answer/1727131?hl=en\n\n'.format(TODAY))
        markdown.write('|Retail Branding|Marketing Name|Device|Model|\n')
        markdown.write('|---|---|---|---|\n')
        devices = []
        for line in data_list[1:]:
            i = line.strip().replace("  ", " ").split(",")
            try:
                brand = i[0]
                name = i[1]
                device = i[2]
                model = i[3]
                markdown.write('|{}|{}|{}|{}|\n'.format(brand, name, device, model))
                devices.append({'brand': brand, 'name': name, 'device': device, 'model': model})
            except IndexError:
                pass
        json.dump(devices, json_out, indent=1)


def diff_files():
    """
    diff
    """
    with open('old.md', 'r') as old, open('README.md', 'r') as new:
        diff = difflib.unified_diff(old.readlines(), new.readlines(), fromfile='old', tofile='new')
        changes = []
        for line in diff:
            if line.startswith('+'):
                changes.append(str(line))
    new = ''.join(changes[2:]).replace("+", "")
    with open('changes', 'w') as out:
        out.write(new)


def post_to_tg():
    """
    post new devices to telegram channel
    """
    # tg
    telegram_chat = "@CertifiedAndroidDevices"
    with open('changes', 'r') as changes:
        for line in changes:
            info = line.split("|")
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
                print("{0}: Telegram Message sent".format(name))
            else:
                print("Telegram Error")


def git_commit_push():
    """
    git add - git commit - git push
    """
    system("git add README.md devices.json && git -c \"user.name=XiaomiFirmwareUpdater\" "
           "-c \"user.email=xiaomifirmwareupdater@gmail.com\" "
           "commit -m \"[skip ci] sync: {0}\" && "" \
           ""git push -q https://{1}@github.com/androidtrackers/"
           "certified-android-devices.git HEAD:master"
           .format(TODAY, GIT_OAUTH_TOKEN))


def main():
    """
    certified-android-devices tracker
    """
    if path.exists('README.md'):
        rename('README.md', 'old.md')
    fetch()
    diff_files()
    post_to_tg()
    git_commit_push()


if __name__ == '__main__':
    main()
