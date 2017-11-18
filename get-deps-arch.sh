#!/bin/sh
# Installs the pre-requisites for Arch Linux
sudo pacman -Su --needed --noconfirm ffmpeg fontforge go-ipfs optipng python python-dateutil python-jinja python-pillow python-requests scour texlive-core
pacaur -S jpgcrush python-joblib webify woff2-git

# TODO: drop npm dependency by trying a different tex2svg script
sudo pacman -S npm
cd ../ && npm install tex-equation-to-svg
