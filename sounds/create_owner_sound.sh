#!/bin/bash
set -e
owner_text=`echo $1 | tr '_' ' '`
google_speech -l vi "Người phụ trách: '$owner_text'" -o $1.mp3 && ffmpeg -y -i $1.mp3  -f s16le -ac 1 -acodec pcm_s16le -ar 46000 ./sounds/owner/$1.raw && rm -rf $1.mp3