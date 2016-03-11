#!/bin/sh
# Installs the pre-requisites for Arch Linux
pacman -Su --needed --noconfirm fontforge go-ipfs optipng python python-dateutil python-jinja python-pillow python-requests

alias makepkg="sudo -u nobody makepkg"

cd /tmp
rm -rf webify/ && sudo -u nobody git clone https://aur.archlinux.org/webify.git && cd webify/
makepkg
pacman --noconfirm -U *.pkg.tar.xz 

rm -rf woff2-git && sudo -u nobody git clone https://aur.archlinux.org/woff2-git.git && cd woff2-git
makepkg
pacman --noconfirm -U *.pkg.tar.xz 

rm -rf jpgcrush/ && sudo -u nobody git clone https://aur.archlinux.org/jpgcrush.git && cd jpgcrush/
makepkg
pacman --noconfirm -U *.pkg.tar.xz 
rm -rf $(pwd)
popd

