BUILD_DIR=../build/mooooo
RES_DIR=res

RES_TYPES=*.css
RESOURCES=$(wildcard $(addprefix $(RES_DIR)/**/,$(RES_TYPES)) $(addprefix $(RES_DIR)/,$(RES_TYPES))) 

PUB_TARGETS=$(addprefix $(BUILD_DIR)/,index.html $(RESOURCES))

all: $(PUB_TARGETS)

clean:
	rm -rf $(BUILD_DIR)

# Publish the site to IPFS / mooooo.ooo
publish: $(PUB_TARGETS)
	ipfs add -r $(BUILD_DIR)

$(BUILD_DIR)/$(RES_DIR)/%: $(RES_DIR)/%
	mkdir -p $(dir $@)
	cp $< $@

$(BUILD_DIR)/%.html: templates/%.html templates/base.html ./build_page.py
	mkdir -p $(dir $@)
	./build_page.py $< $@

.PHONY: clean publish

