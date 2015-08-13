# VARS
# ====

NODE_BINDIR = $(abspath ./node_modules/.bin)

# JS toolchain: browserify concats, exorcist extracts maps, uglify minifies
BROWSERIFY = $(NODE_BINDIR)/browserify
UGLIFY = $(NODE_BINDIR)/uglifyjs
EXORCIST = $(NODE_BINDIR)/exorcist
EXORCIST_OPTIONS = --base $(abspath .)

# CSS toolchain: node-sass compiles, cleancss minifies
REWORK = $(NODE_BINDIR)/rework-npm
CLEANCSS = $(NODE_BINDIR)/cleancss

JS_LIBS = bootstrap jquery typeahead

APP_DIR = xelpaste/frontend
DIST_DIR = xelpaste/static/xelpaste
BUILD_DIR = build/frontend
DEPFILES = package.json

APP_JS_FILES = $(shell find $(APP_DIR) -name '*.js')
APP_CSS_FILES = $(shell find $(APP_DIR) -name '*.css')

default: build

install-deps:
	npm install

clean:
	rm -f $(BUILD_DIR)/* $(DIST_DIR)/*

.PHONY: default install-deps clean


# QUALITY
# =======

lint:


# BUILDING
# ========

build: build-vendorjs build-appjs build-appcss

build-vendorjs: $(DIST_DIR)/vendor.js

build-appjs: $(DIST_DIR)/app.js

build-appcss: $(DIST_DIR)/app.css

$(DIST_DIR)/%.js: $(BUILD_DIR)/%.js $(DEPFILES)
	$(UGLIFY) $< --output $@ \
	    --mangle --compress \
	    --source-map $@.map --source-map-url $(notdir $@).map --source-map-include-sources --in-source-map $<.map

$(DIST_DIR)/%.css: $(BUILD_DIR)/%.css $(DEPFILES)
	$(CLEANCSS) $< --output $@
#	\
#	--source-map --source-map-inline-sources

$(BUILD_DIR)/app.js: $(APP_DIR)/main.js $(APP_JS_FILES) $(DEPFILES)
	$(BROWSERIFY) --entry $< --debug --transform reactify \
	    $(addprefix --external=,$(JS_LIBS)) \
	    | $(EXORCIST) $(EXORCIST_OPTIONS) $@.map \
	    > $@

$(BUILD_DIR)/vendor.js: $(DEPFILES)
	$(BROWSERIFY) --debug \
	    $(addprefix --require=,$(JS_LIBS)) \
	    | $(EXORCIST) $(EXORCIST_OPTIONS) $@.map \
	    > $@

$(BUILD_DIR)/app.css: $(APP_CSS_FILES) $(DEPFILES)
	$(REWORK) $< \
	    > $@
#	    --sourcemap \
#	    | $(EXORCIST) $(EXORCIST_OPTIONS) $@.map \
#	    | sed '/sourceMappingURL/q' \

.PHONY: build build-appjs build-vendorjs


# MISC
# ====

runserver:
	cd dist/ && python3 -m http.server

.PHONY: runserver
