import difflib
from datetime import date
from glob import glob
from os import remove, rename, path
from os import system, environ

from requests import get, post

GIT_OAUTH_TOKEN = environ['GIT_OAUTH_TOKEN_XFU']

if path.exists('README.md'):
    rename('README.md', 'old.md')
# Download latest and convert to utf-8
url = "http://storage.googleapis.com/play_public/supported_devices.csv"
r = get(url)
with open('supported_devices.csv', 'wb') as f:
    f.write(r.content.decode('utf-16').encode('utf-8'))
# convert to markdown
with open('supported_devices.csv', 'r') as f, open("tmp.md", 'w') as o:
    for line in f:
        o.write(line.replace(",", "|"))
# append '|' at the first and the end of each line
with open('tmp.md', 'r') as f, open("tmp2.md", 'a') as o:
    for line in f:
        o.write("|" + line.rstrip() + "|" + '\n')
# remove first line
with open('tmp2.md', 'r') as f, open("README.md", 'w') as o:
    content = f.readlines()
    o.writelines(content[1:])
# add header
today = str(date.today())
head = "# Google Play Certified Android devices" + '\n'" \
""Last sync is " + today + '\n' + '\n' + "https://support.google.com/googleplay/answer/1727131?hl=en" + '\n' + '\n'" \
""|Retail Branding|Marketing Name|Device|Model|" + '\n' + "|---|---|---|---|" + '\n'
with open("README.md", "r+") as f:
    content = f.read()
with open("README.md", "w+") as f:
    f.write(head + content)
# cleanup
for file in glob("tmp*"):
    remove(file)
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
       ""git push -q https://{1}@github.com/yshalsager/certified-android-devices.git HEAD:py"
       .format(today, GIT_OAUTH_TOKEN))
# tg
telegram_chat = "@CertifiedAndroidDevices"
bottoken = environ['bottoken']
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
