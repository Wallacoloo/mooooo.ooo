# Binaries:
OPTIPNG=optipng #Optional
JPGCRUSH=jpgcrush #Optional
#GIFSICLE=gifsicle #Optional
SCOUR=scour #Optional tool to compress svgs.

# jpegoptim provides 3~4% improvement (w/ -s)
# jpegrescan provides 6~7% (w/ -s)
# jpegcrush provides 6-8% (this is a wrapper around jpegrescan)


MAKE_DIR=$(shell pwd)
BUILD_ROOT=$(shell cd ../ && pwd)/build

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid

# For publishing to Amazon EC2
#HOST_ID_FILE=-i ../MOOOOOoooWebServer.pem
#HOST_USER_DOMAIN=root@ec2.mooooo.ooo
# For publish to Raspberry Pi:
HOST_ID_FILE=
#HOST_USER_DOMAIN=alarm@ssh.mooooo.ooo
HOST_USER_DOMAIN=alarm@192.168.1.11

define MKDIR_CP
	@# Copies the prerequisite to the target
	@mkdir -p $(dir $@)
	cp $< $@
endef

export PATH:=${PATH}:${PWD}/../node_modules/mathjax-node/bin

all: $(BUILD_ROOT)/intermediate/index.html.deps

-include $(BUILD_ROOT)/intermediate/index.html.deps
all: $(RT_DEPS$(BUILD_ROOT)/output/index.html)


clean: ## Removes the FINAL outputs of the build, but not cached versions stored elsewhere or dependency info
	rm -rf $(BUILD_ROOT)/output

clean-all: ## Remove ALL output files and temporaries, including dependency info
	rm -rf $(BUILD_ROOT)


## Create a file that contains the constant IPNS key that we associate with the website
$(IPNSID_FILE):
	@mkdir -p $(dir $@)
	ipfs id --format="<id>" > $@

## Build the site's config file, which holds secret keys, etc.
$(BUILD_ROOT)/config.json: config.json $(IPNSID_FILE)
	@mkdir -p $(dir $@)
	sed  "s:<IPNS_ID>:$(shell cat $(IPNSID_FILE)):" $< |\
	sed  "s:<BUILD_OUTPUT>:$(BUILD_ROOT)/output:" |\
	sed  "s:<BUILD_INTERMEDIATE>:$(BUILD_ROOT)/intermediate:" |\
	sed  "s:<BUILD_ROOT>:$(BUILD_ROOT):" \
	> $@

publish-ipfs: $(PUB_TARGETS) ## Publish the site to IPFS
	ipfs add -r -q $(BUILD_ROOT)/output | tail -1 > $(BUILD_ROOT)/mooooo.ipfsid

publish-ipns: publish-ipfs ## Update the IPNS link to point to the newest version of the website
	ipfs name publish /ipfs/$(shell cat $(IPFSID_FILE))


publish-cf: publish-ipfs ## Update the DNS records for a cloudflare server
	./publish_cloudflare.py $(shell cat ../cloudflare_apikey) $(shell cat $(IPFSID_FILE))

publish-host: publish-ipfs ## Pin the new build to the remote host
	ssh $(HOST_ID_FILE) $(HOST_USER_DOMAIN) "ipfs get $(shell cat $(IPFSID_FILE)) && ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"
	#ssh $(HOST_ID_FILE) $(HOST_USER_DOMAIN) "ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"

publish: publish-ipfs publish-cf publish-ipns publish-host ## Publish the site everywhere
	true

%.deps: %.pageinfo ## Extract dependencies from a pageinfo object
	@echo "Building $@ from $^"
	./extract_deps.py $< $@

%.html.pageinfo: %.html.jinja.html $(BUILD_ROOT)/config.json ## Extract information about a html page
	@echo "Building $@ from $^"
	./build_page.py $< $@

%.html: %.html.jinja.html $(BUILD_ROOT)/config.json ## Render html jinja templates
	@echo "Building $@ from $^"
	./build_page.py $< $@

%.png.pageinfo: %.png ## Extract information about an image
	# TODO
	@echo "Building $@ from $^"
	./build_page.py $< $@

# HOW TO COPY SOURCES INTO INTERMEDIATE/

$(BUILD_ROOT)/intermediate/%.html.jinja.html: pages/%.html.jinja.html
	$(MKDIR_CP)

$(BUILD_ROOT)/intermediate/%.jpg: $(BUILD_ROOT)/images/%.jpg
	$(MKDIR_CP)

$(BUILD_ROOT)/intermediate/%.png: $(BUILD_ROOT)/images/%.png
	$(MKDIR_CP)

$(BUILD_ROOT)/intermediate/%.gif: $(BUILD_ROOT)/images/%.gif
	$(MKDIR_CP)

$(BUILD_ROOT)/intermediate/%.svg: $(BUILD_ROOT)/images/%.svg
	$(MKDIR_CP)

## Copy webm videos
$(BUILD_ROOT)/intermediate/%.webm: pages/%.webm
	$(MKDIR_CP)

## Copy ogg audio files
$(BUILD_ROOT)/intermediate/%.ogg: pages/%.ogg
	$(MKDIR_CP)

## Copy ICC color profiles
$(BUILD_ROOT)/intermediate/%.icc: pages/%.icc
	$(MKDIR_CP)

## Copy PDFs
$(BUILD_ROOT)/intermediate/%.pdf: pages/%.pdf
	$(MKDIR_CP)

## Copy Headers
$(BUILD_ROOT)/intermediate/%.h: pages/%.h
	$(MKDIR_CP)

## Copy generated fonts to the intermediate directory (as the font generators may create extra files)
$(BUILD_ROOT)/intermediate/fonts/%: $(BUILD_ROOT)/fonts/%
	$(MKDIR_CP)


# COMPRESSION / GENERATION OF MEDIA FILES

## Rasterize SVGs to PNG
%.png: %.svg
	convert $< $@
	# convert -density 144

## Build compressed png images
$(BUILD_ROOT)/images/%.png: pages/%.png
	$(MKDIR_CP)
	$(OPTIPNG) --quiet $@ || true

## Compress jpegs (losslessly), plus remove a lot of metadata
$(BUILD_ROOT)/images/%.jpg: pages/%.jpg
	$(MKDIR_CP)
	$(JPGCRUSH) $@ || true

$(BUILD_ROOT)/images/%.svg: pages/%.svg
	$(MKDIR_CP)
	$(SCOUR) -i $^ --enable-comment-stripping --enable-id-stripping --create-groups --no-line-breaks --strip-xml-prolog -p 10 -o $@ || true

## Compress gifs (losslessly)
$(BUILD_ROOT)/images/%.gif: pages/%.gif
	$(MKDIR_CP)
#	$(GIFSICLE) -O3 -b $@


# If the font already exists, just directly copy it
$(BUILD_ROOT)/fonts/%: fonts/%
	$(MKDIR_CP)

## Build TTF fonts from OTF
$(BUILD_ROOT)/fonts/%.ttf: fonts/%.otf
	mkdir -p $(dir $@)
	fontforge -c 'import fontforge; font = fontforge.open("$(MAKE_DIR)/$<"); font.generate("$@")'

## Build WOFF, SVG, EOT fonts from TTF
$(BUILD_ROOT)/fonts/%.woff $(BUILD_ROOT)/fonts/%.eot $(BUILD_ROOT)/fonts/%.svg: $(BUILD_ROOT)/fonts/%.ttf
	mkdir -p $(dir $@)
	webify $<

## Build WOFF2 fonts from WOFF
$(BUILD_ROOT)/fonts/%.woff2: $(BUILD_ROOT)/fonts/%.ttf
	woff2_compress $<



## Files to be published can be copied from the intermediate folder
$(BUILD_ROOT)/output/%: $(BUILD_ROOT)/intermediate/%
	$(MKDIR_CP)

# Self-documenting help function provided by http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -h -P '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.SECONDARY:
.PHONY: clean clean-all clean-deps help publish-ipfs publish-ipns publish-cf publish

