#!/bin/bash
set -e
msg_text=`echo $1 | tr '_' ' '`
google_speech -l vi "Cảnh báo: '$msg_text'" -o $1.mp3 && ffmpeg  -y -i $1.mp3  -f s16le -ac 1 -acodec pcm_s16le -ar 45000 ./sounds/msg/$2.raw  && rm -rf $1.mp3
#google_speech "Alert: '$msg_text'" -o $1.mp3 && ffmpeg  -y -i $1.mp3  -f s16le -ac 1 -acodec pcm_s16le -ar 45000 ./sounds/msg/$1.raw  && rm -rf $1.mp3