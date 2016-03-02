BUILD_ROOT=$(shell cd ../ && pwd)/build
# Directory in which to create the static website
BUILD_DIR=$(BUILD_ROOT)/mooooo
# Directory where static resources are kept

IPFSID_FILE=$(BUILD_ROOT)/mooooo.ipfsid
IPNSID_FILE=$(BUILD_ROOT)/mooooo.ipnsid


all: $(BUILD_ROOT)/all.depincludes
all: $(BUILD_DIR)/index.html

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
	sed  "s:<IPNS_ID>:$(shell cat $(IPNSID_FILE)):" $< |\
	sed  "s:<BUILD_DIR>:$(BUILD_DIR):" $< \
	> $@

publish-ipfs: $(PUB_TARGETS) ## Publish the site to IPFS
	ipfs add -r -q $(BUILD_DIR) | tail -1 > $(BUILD_ROOT)/mooooo.ipfsid

publish-ipns: publish-ipfs ## Update the IPNS link to point to the newest version of the website
	ipfs name publish /ipfs/$(shell cat $(IPFSID_FILE))


publish-cf: publish-ipfs ## Update the DNS records for a cloudflare server
	./publish_cloudflare.py $(shell cat ../cloudflare_apikey) $(shell cat $(IPFSID_FILE))

publish: publish-ipfs publish-cf publish-ipns ## Publish the site everywhere
	true

## Build any resources (webpages, css, images, fonts, etc)
$(BUILD_DIR)/%: pages/%
	mkdir -p $(dir $@)
	./build_page.py pages/$(subst $(BUILD_DIR)/,,$@) $@

# Self-documenting help function provided by http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -h -P '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: clean help publish-ipfs publish-ipns publish-cf publish

