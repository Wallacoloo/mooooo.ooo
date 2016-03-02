BUILD_ROOT=../build
# Directory in which to create the static website
BUILD_DIR=$(BUILD_ROOT)/mooooo
# Directory where static resources are kept
RES_DIR=res

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid


# Which types of files to copy out of the resource directory
# (don't want to accidentally copy editor backups, etc)
#RES_TYPES=*.css *.eot *.otf *.png *.svg *.ttf *.woff *.woff2
#RESOURCES=$(shell find res -name . $(addprefix -o -name ,$(RES_TYPES)))
#RESOURCES:=$(RESOURCES) $(subst pages/,,$(shell find pages -name . $(addprefix -o -name ,$(RES_TYPES))))

# All targets that should be publically visible when published
#PUB_TARGETS:=$(RESOURCES) $(RES_DIR)/css/global.css index.html
#PUB_TARGETS:=$(PUB_TARGETS) $(subst pages/,,$(shell find pages/*/index.html))
#PUB_TARGETS:=$(addprefix $(BUILD_DIR)/,$(PUB_TARGETS))
#all: $(PUB_TARGETS)

all: $(BUILD_ROOT)/all.depincludes

-include $(BUILD_ROOT)/all.depincludes

$(BUILD_ROOT)/all.depincludes: $(BUILD_ROOT)/config.json
	./make.py $@


clean:
	rm -rf $(BUILD_ROOT)

## Create a file that contains the constant IPNS key that we associate with the website
$(IPNSID_FILE):
	mkdir -p $(dir $@)
	ipfs id --format="<id>" > $@

## Build the site's config file, which holds secret keys, etc.
$(BUILD_ROOT)/config.json: config.json $(IPNSID_FILE)
	mkdir -p $(dir $@)
	sed  "s:<IPNS_ID>:$(shell cat $(IPNSID_FILE)):" $< > $@

publish-ipfs: $(PUB_TARGETS) ## Publish the site to IPFS
	ipfs add -r -q $(BUILD_DIR) | tail -1 > $(BUILD_DIR)/../mooooo.ipfsid

publish-ipns: publish-ipfs ## Update the IPNS link to point to the newest version of the website
	ipfs name publish /ipfs/$(shell cat $(IPFSID_FILE))


publish-cf: publish-ipfs ## Update the DNS records for a cloudflare server
	./publish_cloudflare.py $(shell cat ../cloudflare_apikey) $(shell cat $(IPFSID_FILE))

publish: publish-ipfs publish-cf publish-ipns ## Publish the site everywhere
	true

## Copy static resources into the build directory
$(BUILD_DIR)/$(RES_DIR)/%: $(RES_DIR)/%
	mkdir -p $(dir $@)
	cp $< $@

## Copy static images to the build directory
$(BUILD_DIR)/%.png: pages/%.png
	mkdir -p $(dir $@)
	cp $< $@

## Build the top-level index.html page
$(BUILD_DIR)/index.html:
	mkdir -p $(dir $@)
	./build_page.py pages/$(subst $(BUILD_DIR)/,,$@) $@

## Build any non-root webpage or css document
$(BUILD_DIR)/%/index.html $(BUILD_DIR)/%.css:
	mkdir -p $(dir $@)
	./build_page.py pages/$(subst $(BUILD_DIR)/,,$@) $@

# Self-documenting help function provided by http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -h -P '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: clean help publish-ipfs publish-ipns publish-cf publish

