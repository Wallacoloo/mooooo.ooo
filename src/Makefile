# Binaries:
EPLOT=eplot
OPTIPNG=optipng #Optional
JPGCRUSH=jpgcrush #Optional

# jpegoptim provides 3~4% improvement (w/ -s)
# jpegrescan provides 6~7% (w/ -s)
# jpegcrush provides 6-8% (this is a wrapper around jpegrescan)


MAKE_DIR=$(shell pwd)
BUILD_ROOT=$(shell cd ../ && pwd)/build
# Directory in which to create the static website
BUILD_DIR=$(BUILD_ROOT)/mooooo

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid

EC2_ID_FILE=../MOOOOOoooWebServer.pem
EC2_USER_DOMAIN=root@ec2.mooooo.ooo


all: $(BUILD_ROOT)/all.depincludes
all: $(BUILD_DIR)/index.html

-include $(BUILD_ROOT)/all.depincludes

$(BUILD_ROOT)/all.depincludes: $(BUILD_ROOT)/config.json
	./make.py $@


clean: ## Remove ALL output files and temporaries, including dependency info
	rm -rf $(BUILD_ROOT)

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

publish-ec2: publish-ipfs ## Pin the new build to the Amazon EC2 instance
	ssh -i $(EC2_ID_FILE) $(EC2_USER_DOMAIN) "ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"

publish: publish-ipfs publish-cf publish-ipns publish-ec2 ## Publish the site everywhere
	true

## Plot PNGs
%.png: %.eplot
	@# The first line of the text file encodes flags to pass to eplot; the rest is data
	tail -n +2 "$^" | exec eplot $(shell head -1 "$^") -P -o $@

## Build compressed png images
$(BUILD_DIR)/%.png: pages/%.png
	@mkdir -p $(dir $@)
	@# Copy the image, then run optipng (but don't abort if optipng isn't found.
	cp $^ $@
	$(OPTIPNG) --quiet $@ || true

## Compress jpegs (losslessly), plus remove a lot of metadata
$(BUILD_DIR)/%.jpg: pages/%.jpg
	@mkdir -p $(dir $@)
	@# Copy the image, then run jpegoptim (but don't abort if binary doesn't exist)
	cp $^ $@
	$(JPGCRUSH) $@ || true

# If the font already exists, just directly copy it
$(BUILD_ROOT)/fonts/%: fonts/%
	mkdir -p $(dir $@)
	cp $< $@

## Build TTF fonts from OTF
$(BUILD_ROOT)/fonts/%.ttf: fonts/%.otf
	mkdir -p $(dir $@)
	fontforge -c 'import fontforge; font = fontforge.open("$(MAKE_DIR)/$<"); font.generate("$@")'

## Build WOFF, SVG, EOT fonts from TTF
$(BUILD_ROOT)/fonts/%.woff $(BUILD_ROOT)/fonts/%.eot $(BUILD_ROOT)/fonts/%.svg: $(BUILD_ROOT)/fonts/%.ttf
	mkdir -p $(dir $@)
	webify $<

## Build WOFF2 fonts from WOFF
%.woff2: %.ttf
	woff2_compress $<

## Copy generated fonts to the published directory (as the font generators may create extra files)
$(BUILD_DIR)/fonts/%: $(BUILD_ROOT)/fonts/%
	mkdir -p $(dir $@)
	cp $< $@

## Build any resources (webpages, css, images, fonts, etc)
$(BUILD_DIR)/%: pages/%
	@mkdir -p $(dir $@)
	./build_page.py pages/$(subst $(BUILD_DIR)/,,$@) $@

# Self-documenting help function provided by http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -h -P '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: clean help publish-ipfs publish-ipns publish-cf publish

