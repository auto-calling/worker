#!/bin/bash
set -e
google_speech -l vi "Địa chỉ Server: '$1'" -o $1.mp3 
ffmpeg -y  -i $1.mp3  -f s16le -ac 1 -acodec pcm_s16le -ar 45000 ./sounds/host/$2.raw 
rm -rf $1.mp3