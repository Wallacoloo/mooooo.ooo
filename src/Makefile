BUILD_DIR=../build/mooooo
RES_DIR=res

RES_TYPES=*.css
RESOURCES=$(wildcard $(addprefix $(RES_DIR)/**/,$(RES_TYPES)) $(addprefix $(RES_DIR)/,$(RES_TYPES))) 

all: $(BUILD_DIR)/index.html $(addprefix $(BUILD_DIR)/,$(RESOURCES))

clean:
	rm -rf $(BUILD_DIR)

$(BUILD_DIR)/$(RES_DIR)/%: $(RES_DIR)/%
	mkdir -p $(dir $@)
	cp $^ $@

$(BUILD_DIR)/%.html: templates/%.html
	mkdir -p $(dir $@)
	./build_page.py $^ $@

.PHONY: clean

