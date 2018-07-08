wget http://storage.googleapis.com/play_public/supported_devices.csv
npm install -g csv2md
cat supported_devices.csv | iconv -f UTF-16 -t UTF-8 > devices.csv
csv2md devices.csv > README.md
today=$(date +%d.%m.%Y)
cat << EOF >> head
# Google Play Certified Android devices

Last sync is $today

https://support.google.com/googleplay/answer/1727131?hl=en

EOF
cat head README.md > temp && mv temp README.md
git config --global user.email "$gitmail"; git config --global user.name "$gituser"
git add README.md; git commit -m "$(date +%d.%m.%Y)"
git push -q https://$GIT_OAUTH_TOKEN_XFU@github.com/yshalsager/certified-android-devices.git HEAD:master
