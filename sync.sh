#Download latest list
wget http://storage.googleapis.com/play_public/supported_devices.csv

#Install csv2md
npm install -g csv2md

#Convert to MD
cat supported_devices.csv | iconv -f UTF-16 -t UTF-8 > devices.csv
csv2md devices.csv > README.md

#Add header
today=$(date +%d.%m.%Y)
cat << EOF >> head
# Google Play Certified Android devices

Last sync is $today

https://support.google.com/googleplay/answer/1727131?hl=en

EOF
cat head README.md > temp && mv temp README.md
git diff | grep -P '^\+(?:(?!\+\+))|^-(?:(?!--))' | sed -n '/-/!p' | sed -n '/sync/!p'| cut -d + -f2 > changes

#Push
git config --global user.email "$gitmail"; git config --global user.name "$gituser"
git add README.md; git commit -m $today
git push -q https://$GIT_OAUTH_TOKEN_XFU@github.com/yshalsager/certified-android-devices.git HEAD:master

#Telegram
cat changes | while read line; do
	brand=$(echo $line | cut -d '|' -f2)
	name=$(echo $line | cut -d '|' -f3)
	device=$(echo $line | cut -d '|' -f4)
	model=$(echo $line | cut -d '|' -f5)
	python telegram.py -t $bottoken -c @CertifiedAndroidDevices -M "New certified device added!
	Brand:*$brand*
	Name:*$name*
	Codename:*$device*
	Model:*$model* "
done
