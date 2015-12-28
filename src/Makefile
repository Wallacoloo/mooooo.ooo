# Directory in which to create the static website
BUILD_DIR=../build/mooooo
# Directory where static resources are kept
RES_DIR=res

# Which types of files to copy out of the resource directory
# (don't want to accidentally copy editor backups, etc)
RES_TYPES=*.css
RESOURCES=$(wildcard $(addprefix $(RES_DIR)/**/,$(RES_TYPES)) $(addprefix $(RES_DIR)/,$(RES_TYPES))) 

# All targets that should be publically visible when published
PUB_TARGETS=$(addprefix $(BUILD_DIR)/,index.html about.html $(RESOURCES))

all: $(PUB_TARGETS)

clean:
	rm -rf $(BUILD_DIR)

# Publish the site to IPFS / mooooo.ooo
publish: $(PUB_TARGETS)
	ipfs add -r -q $(BUILD_DIR) | tail -1 > $(BUILD_DIR)/../mooooo.ipfsid

# Update the DNS records for a cloudflare server
publish-cf: publish
	./publish_cloudflare.py `cat ../cloudflare_apikey` `cat $(BUILD_DIR)/../mooooo.ipfsid`

# Copy static resources into the build directory
$(BUILD_DIR)/$(RES_DIR)/%: $(RES_DIR)/%
	mkdir -p $(dir $@)
	cp $< $@

# Turn any templates into actual pages
$(BUILD_DIR)/%.html: templates/%.html templates/base.html ./build_page.py
	mkdir -p $(dir $@)
	./build_page.py $< $@

.PHONY: clean publish

