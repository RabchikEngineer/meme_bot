#!/bin/bash

palette="$2palette$3.png"
temp_gif="$2temp$3.gif"
filters="fps=$6,scale=$5:-1:flags=lanczos,format=rgb24"

ffmpeg -v warning -i "$1" -vf "$filters,palettegen" -y "$palette"
ffmpeg -v warning -i "$1" -i "$palette" -lavfi "$filters [x]; [x][1:v] paletteuse" -y "$temp_gif"
gifsicle -O3 --lossy=100 "$temp_gif" -o "$4"
rm "$temp_gif" "$palette"


