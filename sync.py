import difflib
from datetime import date
from glob import glob
from os import remove, rename, path, system, environ
from requests import get, post

try:
    GIT_OAUTH_TOKEN = environ['GIT_OAUTH_TOKEN_XFU']
    bottoken = environ['bottoken']
except KeyError:
    print("Key not found, skipping!")

today = str(date.today())

if path.exists('README.md'):
    rename('README.md', 'old.md')
# Download latest and convert to utf-8
url = "http://storage.googleapis.com/play_public/supported_devices.csv"
r = get(url)
data = (r.content.decode('utf-16'))
data_list = list(data.split('\n'))
with open('README.md', 'w+', encoding='UTF-8') as f:
    f.write('# Google Play Certified Android devices\n')
    f.write('Last sync is {}\n\nhttps://support.google.com/googleplay/answer/1727131?hl=en\n\n'.format(today))
    f.write('|Retail Branding|Marketing Name|Device|Model|\n')
    f.write('|---|---|---|---|\n')
    for line in data_list[1:]:
        i = line.strip().replace("  ", " ").split(",")
        try:
            brand = i[0]
            name = i[1]
            device = i[2]
            model = i[3]
        except IndexError:
            pass
        f.write('|{}|{}|{}|{}|\n'.format(brand, name, device, model))

# diff
with open('old.md', 'r') as old, open('README.md', 'r') as new:
    diff = difflib.unified_diff(old.readlines(), new.readlines(), fromfile='old', tofile='new')
    changes = []
    for line in diff:
        if line.startswith('+'):
            changes.append(str(line))
new = ''.join(changes[2:]).replace("+", "")
with open('changes', 'w') as o:
    o.write(new)
# push to github
system("git add README.md && git -c \"user.name=XiaomiFirmwareUpdater\" "
       "-c \"user.email=xiaomifirmwareupdater@gmail.com\" commit -m \"[skip ci] sync: {0}\" && "" \
       ""git push -q https://{1}@github.com/androidtrackers/certified-android-devices.git HEAD:master"
       .format(today, GIT_OAUTH_TOKEN))
# tg
telegram_chat = "@CertifiedAndroidDevices"
with open('changes', 'r') as c:
    for line in c:
        info = line.split("|")
        brand = info[1]
        name = info[2]
        codename = info[3]
        model = info[4]
        telegram_message = "New certified device added!: \n Brand: *{0}* \n Name: *{1}* \n *Codename:* `{2}` \n " \
                           "Model: *{3}*".format(brand, name, codename, model)
        params = (
            ('chat_id', telegram_chat),
            ('text', telegram_message),
            ('parse_mode', "Markdown"),
            ('disable_web_page_preview', "yes")
        )
        telegram_url = "https://api.telegram.org/bot" + bottoken + "/sendMessage"
        telegram_req = post(telegram_url, params=params)
        telegram_status = telegram_req.status_code
        if telegram_status == 200:
            print("{0}: Telegram Message sent".format(name))
        else:
            print("Telegram Error")
