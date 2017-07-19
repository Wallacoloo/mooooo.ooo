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
# Directory in which to create the static website
BUILD_DIR=$(BUILD_ROOT)/mooooo

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid

# For publishing to Amazon EC2:
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


all: $(BUILD_ROOT)/all.depincludes
all: $(BUILD_DIR)/index.html

-include $(BUILD_ROOT)/all.depincludes

$(BUILD_ROOT)/all.depincludes: $(BUILD_ROOT)/config.json
	./make.py $@


clean: ## Removes the FINAL outputs of the build, but not cached versions stored elsewhere or dependency info
	rm -rf $(BUILD_DIR)

clean-all: ## Remove ALL output files and temporaries, including dependency info
	rm -rf $(BUILD_ROOT)

clean-deps: ## Remove dependency information, forcing it to be recomputed in the future
	rm -rf $(BUILD_ROOT)/all.depincludes $(BUILD_ROOT)/deps


## Create a file that contains the constant IPNS key that we associate with the website
$(IPNSID_FILE):
	@mkdir -p $(dir $@)
	ipfs id --format="<id>" > $@

## Build the site's config file, which holds secret keys, etc.
$(BUILD_ROOT)/config.json: config.json $(IPNSID_FILE)
	@mkdir -p $(dir $@)
	sed  "s:<IPNS_ID>:$(shell cat $(IPNSID_FILE)):" $< |\
	sed  "s:<BUILD_DIR>:$(BUILD_DIR):" |\
	sed  "s:<BUILD_ROOT>:$(BUILD_ROOT):" \
	> $@

publish-ipfs: $(PUB_TARGETS) ## Publish the site to IPFS
	ipfs add -r -q $(BUILD_DIR) | tail -1 > $(BUILD_ROOT)/mooooo.ipfsid

publish-ipns: publish-ipfs ## Update the IPNS link to point to the newest version of the website
	ipfs name publish /ipfs/$(shell cat $(IPFSID_FILE))


publish-cf: publish-ipfs ## Update the DNS records for a cloudflare server
	./publish_cloudflare.py $(shell cat ../cloudflare_apikey) $(shell cat $(IPFSID_FILE))

publish-host: publish-ipfs ## Pin the new build to the remote host
	ssh $(HOST_ID_FILE) $(HOST_USER_DOMAIN) "ipfs get $(shell cat $(IPFSID_FILE)) && ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"
	#ssh $(HOST_ID_FILE) $(HOST_USER_DOMAIN) "ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"

publish: publish-ipfs publish-cf publish-ipns publish-host ## Publish the site everywhere
	true

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

$(BUILD_DIR)/%.jpg: $(BUILD_ROOT)/images/%.jpg
	$(MKDIR_CP)

$(BUILD_DIR)/%.png: $(BUILD_ROOT)/images/%.png
	$(MKDIR_CP)

$(BUILD_DIR)/%.gif: $(BUILD_ROOT)/images/%.gif
	$(MKDIR_CP)

$(BUILD_DIR)/%.svg: $(BUILD_ROOT)/images/%.svg
	$(MKDIR_CP)

## Copy webm videos
$(BUILD_DIR)/%.webm: pages/%.webm
	$(MKDIR_CP)

## Copy ogg audio files
$(BUILD_DIR)/%.ogg: pages/%.ogg
	$(MKDIR_CP)

## Copy ICC color profiles
$(BUILD_DIR)/%.icc: pages/%.icc
	$(MKDIR_CP)

## Copy PDFs
$(BUILD_DIR)/%.pdf: pages/%.pdf
	$(MKDIR_CP)

## Copy Headers
$(BUILD_DIR)/%.h: pages/%.h
	$(MKDIR_CP)

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

## Copy generated fonts to the published directory (as the font generators may create extra files)
$(BUILD_DIR)/fonts/%: $(BUILD_ROOT)/fonts/%
	$(MKDIR_CP)

define BUILD_PAGE
	@mkdir -p $(dir $@)
	./build_page.py pages/$(subst $(BUILD_DIR)/,,$@) $@
endef

## Build any resources (webpages, css, images, fonts, etc)
$(BUILD_DIR)/%.html: pages/%.html
	$(BUILD_PAGE)
$(BUILD_DIR)/%.css: pages/%.css
	$(BUILD_PAGE)

# Self-documenting help function provided by http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -h -P '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.SECONDARY:
.PHONY: clean clean-all clean-deps help publish-ipfs publish-ipns publish-cf publish

