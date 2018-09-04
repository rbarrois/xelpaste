# VARS
# ====

NODE_BINDIR = $(abspath ./node_modules/.bin)
MANAGE_PY = python manage.py

# JS toolchain: browserify concats, exorcist extracts maps, uglify minifies
BROWSERIFY = $(NODE_BINDIR)/browserify
UGLIFY = $(NODE_BINDIR)/uglifyjs
EXORCIST = $(NODE_BINDIR)/exorcist
EXORCIST_OPTIONS = --base $(abspath .)

# CSS toolchain: node-sass compiles, cleancss minifies
REWORK = $(NODE_BINDIR)/rework-npm
CLEANCSS = $(NODE_BINDIR)/cleancss

JS_LIBS = bootstrap jquery typeahead
BOOSTRAP_SRC = $(abspath ./node_modules/bootstrap/dist)

APP_DIR = frontend
DIST_DIR = xelpaste/static/xelpaste
BUILD_DIR = build/frontend
PUB_DIR = xelpaste/assets
DEPFILES = package.json

APP_JS_FILES = $(shell find $(APP_DIR) -name '*.js')
LIB_CSS_FILES = $(BOOSTRAP_SRC)/css/bootstrap.css
APP_CSS_FILES = $(shell find $(APP_DIR) -name '*.css')
FONTS_SRC_FILES = $(shell find $(BOOSTRAP_SRC)/fonts -type f)
FONTS_FILES = $(FONTS_SRC_FILES:$(BOOSTRAP_SRC)/%=%)
FONTS_DST_FILES = $(addprefix $(DIST_DIR)/, $(FONTS_FILES))


default: build

clean:
	rm -rf $(BUILD_DIR)/* $(DIST_DIR)/* $(PUB_DIR)/*
	find $(PACKAGE_DIR) -type f -name '*.pyc' -delete

.PHONY: default clean


# QUALITY
# =======

test: build
	$(MANAGE_PY) test libpaste xelpaste
	check-manifest

.PHONY: test


# DEPENDENCIES
# ============

update: update-js
	pip install --upgrade -r requirements.txt
update-js:
	npm install

release:
	fullrelease


.PHONY: update update-js release

# BUILDING
# ========

build: build-vendorjs build-appjs build-appcss build-fonts
	XELPASTE_APP_MODE=dist $(MANAGE_PY) collectstatic --noinput --verbosity 2

build-vendorjs: $(DIST_DIR)/js/vendor.js

build-appjs: $(DIST_DIR)/js/app.js

build-appcss: $(DIST_DIR)/css/app.css

build-fonts: $(FONTS_DST_FILES)

$(DIST_DIR)/fonts/%: $(BOOSTRAP_SRC)/fonts/%
	@mkdir -p $$(dirname $@)
	cp $< $@

$(DIST_DIR)/js/%.js: $(BUILD_DIR)/%.js $(DEPFILES)
	@mkdir -p $$(dirname $@)
	$(UGLIFY) $< --output $@ \
	    --mangle --compress \
	    --source-map $@.map --source-map-url $(notdir $@).map --source-map-include-sources --in-source-map $<.map

$(DIST_DIR)/css/%.css: $(BUILD_DIR)/%.css $(DEPFILES)
	@mkdir -p $$(dirname $@)
	$(CLEANCSS) $< \
	    --source-map \
	    --skip-rebase \
	    --output $@

$(BUILD_DIR)/app.js: $(APP_DIR)/main.js $(APP_JS_FILES) $(DEPFILES)
	@mkdir -p $$(dirname $@)
	$(BROWSERIFY) --entry $< --debug --transform reactify \
	    $(addprefix --external=,$(JS_LIBS)) \
	    | $(EXORCIST) $(EXORCIST_OPTIONS) $@.map \
	    > $@

$(BUILD_DIR)/vendor.js: $(DEPFILES)
	@mkdir -p $$(dirname $@)
	$(BROWSERIFY) --debug \
	    $(addprefix --require=,$(JS_LIBS)) \
	    | $(EXORCIST) $(EXORCIST_OPTIONS) $@.map \
	    > $@

$(BUILD_DIR)/app.css: $(APP_CSS_FILES) $(DEPFILES)
	@mkdir -p $$(dirname $@)
	$(REWORK) $< --sourcemap \
	    | $(EXORCIST) $(EXORCIST_OPTIONS) $@.map \
	    | grep -v 'bootstrap.css.map' \
	    > $@

.PHONY: build build-appjs build-vendorjs build-fonts build-appcss


# MISC
# ====

runserver:
	cd dist/ && python3 -m http.server

.PHONY: runserver
