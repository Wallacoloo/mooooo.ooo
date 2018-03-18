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
BUILD_CACHE=$(BUILD_ROOT)/cache
BUILD_INTERMEDIATE=$(BUILD_ROOT)/intermediate
BUILD_OUTPUT=$(BUILD_ROOT)/output
CONFIG_JSON=$(BUILD_ROOT)/config.json

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid

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

all:

ifeq ($(filter-out all,$(MAKECMDGOALS)),)
DEFAULT_TARGET=index.html
#DEFAULT_TARGET=css/global.css
#DEFAULT_TARGET=css/fonts.css
include $(BUILD_INTERMEDIATE)/$(DEFAULT_TARGET).alldeps
PUB_TARGETS=$(call GET_RT_DEPS_$(BUILD_OUTPUT)/$(DEFAULT_TARGET),)
all: $(PUB_TARGETS)
endif


clean: ## Removes the FINAL outputs of the build, but not cached versions stored elsewhere or dependency info
	rm -rf $(BUILD_OUTPUT) $(BUILD_INTERMEDIATE)

clean-all: ## Remove ALL output files and temporaries, including dependency info
	rm -rf $(BUILD_ROOT)


## Create a file that contains the constant IPNS key that we associate with the website
$(IPNSID_FILE):
	@mkdir -p $(dir $@)
	ipfs id --format="<id>" > $@

## Build the site's config file, which holds secret keys, etc.
$(CONFIG_JSON): config.json $(IPNSID_FILE)
	@mkdir -p $(dir $@)
	sed  "s:<IPNS_ID>:$(shell cat $(IPNSID_FILE)):" $< |\
	sed  "s:<BUILD_OUTPUT>:$(BUILD_OUTPUT):" |\
	sed  "s:<BUILD_INTERMEDIATE>:$(BUILD_INTERMEDIATE):" |\
	sed  "s:<BUILD_ROOT>:$(BUILD_ROOT):" \
	> $@

publish-ipfs: $(PUB_TARGETS) ## Publish the site to IPFS
	ipfs add -r -q $(BUILD_OUTPUT) | tail -1 > $(BUILD_ROOT)/mooooo.ipfsid

publish-ipns: publish-ipfs ## Update the IPNS link to point to the newest version of the website
	ipfs name publish /ipfs/$(shell cat $(IPFSID_FILE))


publish-cf: publish-ipfs ## Update the DNS records for a cloudflare server
	./publish_cloudflare.py $(shell cat ../cloudflare_apikey) $(shell cat $(IPFSID_FILE))

publish-host: publish-ipfs ## Pin the new build to the remote host
	ssh $(HOST_ID_FILE) $(HOST_USER_DOMAIN) "ipfs get $(shell cat $(IPFSID_FILE)) && ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"
	#ssh $(HOST_ID_FILE) $(HOST_USER_DOMAIN) "ipfs pin add /ipfs/$(shell cat $(IPFSID_FILE))"

publish: publish-ipfs publish-cf publish-ipns publish-host ## Publish the site everywhere
	true

$(BUILD_INTERMEDIATE)/%.srcdeps: $(BUILD_INTERMEDIATE)/%.srcinfo ## Extract dependencies from a srcinfo object
	./extract_srcdeps.py $< $@
	@# Force all the files that the .srcdeps depends on to also be built now
	cat $@ | grep '^include ' | sed 's|include ||' | xargs --no-run-if-empty $(MAKE)

# %.HTML.JINJA.HTML -> %.HTML

$(BUILD_INTERMEDIATE)/%.srcinfo: $(BUILD_INTERMEDIATE)/%.jinja.html $(BUILD_INTERMEDIATE)/%.jinja.html.srcinfo $(CONFIG_JSON) ## Extract information about a html page
	./build_page.py $< $@

#$(BUILD_INTERMEDIATE)/%.html.build: $(BUILD_INTERMEDIATE)/%.html.jinja.html $(BUILD_INTERMEDIATE)/%.html.srcdeps $(CONFIG_JSON) ## Render html jinja templates
#	./build_page.py $< $@

$(BUILD_INTERMEDIATE)/%.jinja.html.srcinfo: pages/%.jinja.html $(CONFIG_JSON)
	@mkdir -p $(dir $@)
	./extract_git.py $< $@

# %.CSS.JINJA.CSS -> %.CSS

$(BUILD_INTERMEDIATE)/%.srcinfo: $(BUILD_INTERMEDIATE)/%.jinja.css $(BUILD_INTERMEDIATE)/%.jinja.css.srcinfo $(CONFIG_JSON) ## Extract information about a css page
	./build_page.py $< $@

#$(BUILD_INTERMEDIATE)/%.css.build: $(BUILD_INTERMEDIATE)/%.css.jinja.css $(BUILD_INTERMEDIATE)/%.css.srcdeps $(CONFIG_JSON) ## Render css jinja templates
#	./build_page.py $< $@

$(BUILD_INTERMEDIATE)/%.jinja.css.srcinfo: pages/%.jinja.css $(CONFIG_JSON)
	@mkdir -p $(dir $@)
	./extract_git.py $< $@

# %.SRC.BIN -> %

$(BUILD_INTERMEDIATE)/%.srcinfo: $(BUILD_INTERMEDIATE)/%.src.bin ## Extract info about a binary blob
	./build_page.py $< $@
#$(BUILD_INTERMEDIATE)/%.build: $(BUILD_INTERMEDIATE)/%.src.bin ## Build a binary blob
#	./build_page.py $< $@

# Extract binary data from a .build object
$(BUILD_INTERMEDIATE)/%: $(BUILD_INTERMEDIATE)/%.build
	./extract_build.py $< $@
# Extract dependency data from a .build objct
$(BUILD_INTERMEDIATE)/%.rtdeps: $(BUILD_INTERMEDIATE)/%.build
	./extract_rtdeps.py $< $@

# Make will autogenerate .srcdeps and .rtdeps. However, the .srcdeps file
# contains dep info about the .rtdeps file, so it must be built _and included_
# prior to building the .rtdeps file.
# The solution is to create a .alldeps file that includes them both, but for which
# its build depends on the .srcdeps file to be build. Then, include this .alldeps
# file instead of both .srcdeps and .rtdeps
$(BUILD_INTERMEDIATE)/%.alldeps: $(BUILD_INTERMEDIATE)/%.srcdeps
	echo "include $^" > $@
	echo "include $(^:.srcdeps=.rtdeps)" >> $@

# HOW TO COPY SOURCES INTO INTERMEDIATE/

$(BUILD_INTERMEDIATE)/%.html.jinja.html: pages/%.html.jinja.html
	$(MKDIR_CP)
$(BUILD_INTERMEDIATE)/%.css.jinja.css: pages/%.css.jinja.css
	$(MKDIR_CP)

## Build compressed png images
$(BUILD_CACHE)/%.png: pages/%.png
	$(MKDIR_CP)
	$(OPTIPNG) --quiet $@ || true

## Compress jpegs (losslessly), plus remove a lot of metadata
$(BUILD_CACHE)/%.jpg: pages/%.jpg
	$(MKDIR_CP)
	$(JPGCRUSH) $@ || true

## Strip SVGs
$(BUILD_CACHE)/%.svg: pages/%.svg
	$(MKDIR_CP)
	$(SCOUR) -i $^ --enable-comment-stripping --enable-id-stripping --create-groups --no-line-breaks --strip-xml-prolog -p 10 -o $@ || true

## Compress gifs (losslessly)
$(BUILD_CACHE)/%.gif: pages/%.gif
	$(MKDIR_CP)
	$(GIFSICLE) -O3 -b $@ || true


# Fallback for binary files
$(BUILD_CACHE)/%: pages/%
	$(MKDIR_CP)

$(BUILD_INTERMEDIATE)/%.src.bin: $(BUILD_CACHE)/%
	$(MKDIR_CP)

## Build TTF fonts from OTF
$(BUILD_CACHE)/%.ttf: $(BUILD_CACHE)/%.otf
	mkdir -p $(dir $@)
	fontforge -c 'import fontforge; font = fontforge.open("$<"); font.generate("$@")'

## Build WOFF, SVG, EOT fonts from TTF
$(BUILD_CACHE)/%.woff $(BUILD_CACHE)/%.eot $(BUILD_CACHE)/%.svg: $(BUILD_CACHE)/%.ttf
	webify $<

## Build WOFF2 fonts from WOFF
$(BUILD_CACHE)/%.woff2: $(BUILD_CACHE)/%.ttf
	woff2_compress $<


## Rasterize SVGs to PNG
$(BUILD_CACHE)/%.png: $(BUILD_CACHE)/%.svg
	convert $< $@
	# convert -density 144


## Files to be published can be copied from the intermediate folder
$(BUILD_OUTPUT)/%: $(BUILD_INTERMEDIATE)/%
	$(MKDIR_CP)

# Self-documenting help function provided by http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -h -P '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.SECONDARY:
.PHONY: clean clean-all clean-deps help publish-ipfs publish-ipns publish-cf publish

