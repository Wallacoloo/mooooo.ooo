#!/bin/sh
# Installs the pre-requisites for Arch Linux
pacman -Su --needed --noconfirm fontforge go-ipfs optipng python python-dateutil python-jinja python-pillow python-requests
pacaur -S jpgcrush python-joblib webify woff2-git
