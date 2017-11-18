#Build Requirements
In order to build the website, the following tools/libraries are needed:
```
# pacman -S fontforge imagemagick python python-jinja python-pillow python-dateutil python-requests python-pygments
$ pacaur -S jpgcrush scour webify woff2 python-joblib
```

If the `python-<x>` packages aren't available in your distribution, they may be
installed via pip instead:
```
$ pip install jinja2 Pillow python-dateutil requests
```

Additionally, the following npm utilities are needed:

```
$ pacman -S npm
# Do in mooooo/ directory; it should create node_modules/
$ npm install tex-equation-to-svg
```

Note: All python code is written for Python 3, *not* Python 2.x.

#Hosting Requirements
To host on IPFS, just install (and initialize) ipfs and pin the build directory:
```
# pacman -S go-ipfs
$ ipfs init
```

Then
```
$ ipfs add -r build/
[...]
/ipfs/Qmxxxxx
$ ipfs pin add /ipfs/Qmxxxxx
```

