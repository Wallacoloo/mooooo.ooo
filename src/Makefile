BUILD_ROOT=../build
# Directory in which to create the static website
BUILD_DIR=$(BUILD_ROOT)/mooooo
# Directory where static resources are kept
RES_DIR=res

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid


# Which types of files to copy out of the resource directory
# (don't want to accidentally copy editor backups, etc)
RES_TYPES=*.css *.eot *.otf *.png *.svg *.ttf *.woff *.woff2
RESOURCES=$(shell find res -name . $(addprefix -o -name ,$(RES_TYPES)))
RESOURCES:=$(RESOURCES) $(subst pages/,,$(shell find pages -name . $(addprefix -o -name ,$(RES_TYPES))))

# All targets that should be publically visible when published
PUB_TARGETS:=$(RESOURCES) $(RES_DIR)/css/global.css index.html
PUB_TARGETS:=$(PUB_TARGETS) $(subst pages/,,$(shell find pages/*/index.html))
PUB_TARGETS:=$(addprefix $(BUILD_DIR)/,$(PUB_TARGETS))
all: $(PUB_TARGETS)

clean:
	rm -rf $(BUILD_DIR)

# Create a file that contains the constant IPNS key that we associate with the website
$(IPNSID_FILE):
	ipfs id --format="<id>" > $@

$(BUILD_ROOT)/config.json: config.json $(IPNSID_FILE)
	sed  "s:<IPNS_ID>:$(shell cat $(IPNSID_FILE)):" $< > $@

# Publish the site to IPFS
publish-ipfs: $(PUB_TARGETS)
	ipfs add -r -q $(BUILD_DIR) | tail -1 > $(BUILD_DIR)/../mooooo.ipfsid

# Update the IPNS link to point to the newest version of the website
publish-ipns: publish-ipfs
	ipfs name publish /ipfs/$(shell cat $(IPFSID_FILE))

# Update the DNS records for a cloudflare server
publish-cf: publish-ipfs
	./publish_cloudflare.py $(shell cat ../cloudflare_apikey) $(shell cat $(IPFSID_FILE))

# Publish the site everywhere
publish: publish-ipfs publish-cf publish-ipns 
	true

# Copy static resources into the build directory
$(BUILD_DIR)/$(RES_DIR)/%: $(RES_DIR)/%
	mkdir -p $(dir $@)
	cp $< $@

# Copy static images
$(BUILD_DIR)/%.png: pages/%.png
	mkdir -p $(dir $@)
	cp $< $@

# Turn any templates into actual pages
$(BUILD_DIR)/index.html: pages/index.html templates/base.html $(BUILD_ROOT)/config.json ./build_page.py
	mkdir -p $(dir $@)
	./build_page.py $< $(BUILD_ROOT)/config.json $(BUILD_DIR) $(subst $(BUILD_DIR)/,,$@)
$(BUILD_DIR)/%/index.html: pages/%/index.html templates/base.html $(BUILD_ROOT)/config.json ./build_page.py
	mkdir -p $(dir $@)
	./build_page.py $< $(BUILD_ROOT)/config.json $(BUILD_DIR) $(subst $(BUILD_DIR)/,,$@)
$(BUILD_DIR)/$(RES_DIR)/%.css: $(RES_DIR)/%.scss
	mkdir -p $(dir $@)
	scss $< $@

.PHONY: clean publish-ipfs publish-ipns publish-cf publish

