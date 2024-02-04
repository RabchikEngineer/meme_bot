#!/bin/sh

palette="tmp/palette.png"
temp_gif="tmp/temp.gif"
filters="fps=15,scale=320:-1:flags=lanczos"

ffmpeg -v warning -i "$1" -vf "$filters,palettegen" -y $palette
ffmpeg -v warning -i "$1" -i $palette -lavfi "$filters [x]; [x][1:v] paletteuse" -y $temp_gif
gifsicle -O3 --lossy=100 $temp_gif -o "$2"



