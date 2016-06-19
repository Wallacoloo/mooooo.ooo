#Build Requirements
In order to build the website, the following tools/libraries are needed:
```
# pacman -S python python-jinja python-pillow python-dateutil python-requests
```

If the `python-<x>` packages aren't available in your distribution, they may be
installed via pip instead:
```
$ pip install jinja2 Pillow python-dateutil requests
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

