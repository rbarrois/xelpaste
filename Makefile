# VARS
# ====

PACKAGE = xelpaste
EXTRA_PACKAGES = libpaste
PROJECT_DIR = xelpaste

GETCONF_PREFIX = $(shell echo $(PACKAGE) | tr '[a-z]' '[A-Z]')

# JS variables
# ------------

WEBPACK = npx webpack

FRONTEND_DIR = frontend

FRONTEND_DIST_DIR = $(PROJECT_DIR)/static/$(PACKAGE)

APP_JS_FILES = $(shell find $(FRONTEND_DIR) -name '*.js')
APP_CSS_FILES = $(shell find $(FRONTEND_DIR) -name '*.css')

NPM_INSTALL_SENTINEL = .success-npm-install


# Django variables
# ----------------

MANAGE_PY = python manage.py
DJANGO_ADMIN = django-admin.py
PO_FILES = $(shell find $(PACKAGE) $(EXTRA_PACKAGES) -name '*.po')
MO_FILES = $(PO_FILES:.po=.mo)

DJANGO_ASSETS_DIR = $(PROJECT_DIR)/assets

# Sentinel file: touch it when `collectstatic` has run, depend on sources for it.
DJANGO_ASSETS_SENTINEL = .success-collectstatic


# Build
# =====

.DEFAULT_GOAL := build

build: $(MO_FILES) $(DJANGO_ASSETS_SENTINEL)


JS_TARGETS = app.js

CSS_LIBS = bootstrap.css bootstrap.css.map
CSS_TARGETS = styles.css $(CSS_LIBS)
NPM_CSS_SOURCES = $(addprefix node_modules/bootstrap/dist/css/,$(CSS_LIBS))

FONTS = glyphicons-halflings-regular
FONT_EXTENSIONS = eot woff2 woff ttf svg
FONT_FILES = $(foreach ext,$(FONT_EXTENSIONS),$(addsuffix .$(ext),$(FONTS)))
NPM_FONT_SOURCES = $(addprefix node_modules/bootstrap/dist/fonts/,$(FONT_FILES))

FRONTEND_TARGETS = $(addprefix $(FRONTEND_DIST_DIR)/js/,$(JS_TARGETS)) $(addprefix $(FRONTEND_DIST_DIR)/css/,$(CSS_TARGETS)) $(addprefix $(FRONTEND_DIST_DIR)/fonts/,$(FONT_FILES))

$(DJANGO_ASSETS_SENTINEL): $(FRONTEND_TARGETS)
	$(GETCONF_PREFIX)_APP_MODE=dist $(MANAGE_PY) collectstatic --noinput --verbosity 2
	touch $@

$(FRONTEND_DIST_DIR)/js/%: $(FRONTEND_DIR)/% webpack.config.js $(NPM_INSTALL_SENTINEL)
	@# Build a module named 'app' from `app.js`
	$(WEBPACK) --entry $(basename $(notdir $@))=./$< --output-path $(dir $@)

# Copy styles and fonts directly
$(FRONTEND_DIST_DIR)/css/styles.css: $(FRONTEND_DIR)/app.css
	mkdir --parents $(dir $@)
	cp $< $@

$(FRONTEND_DIST_DIR)/css/%: node_modules/bootstrap/dist/css/%
	mkdir --parents $(dir $@)
	cp $< $@

$(FRONTEND_DIST_DIR)/fonts/%: node_modules/bootstrap/dist/fonts/%
	mkdir --parents $(dir $@)
	cp $< $@

# All NPM-based files, and the "NPM install has run" sentinel file, depend on
# package-lock.json as a proxy / side-effect of `npm install`.
$(NPM_FONT_SOURCES) $(NPM_CSS_SOURCES) $(NPM_INSTALL_SENTINEL): package-lock.json
	touch $(NPM_INSTALL_SENTINEL)
	touch $(NPM_FONT_SOURCES) $(NPM_CSS_SOURCES)

package-lock.json: package.json
	npm install


# Run DJANGO_ADMIN compilemessages for checkout/<project>/locale/<lang>/LC_MESSAGES/<name>.po
# Must run from checkout/<project>
%.mo: %.po
	cd $(abspath $(dir $<)/../../..) && $(DJANGO_ADMIN) compilemessages

.PHONY: build


# Clean
# =====


clean:
	-rm --recursive $(FRONTEND_DIST_DIR) $(DJANGO_ASSETS_SENTINEL) $(DJANGO_ASSETS_DIR)
	find $(PROJECT_DIR) -type f -name '*.pyc' -delete

distclean: clean
	-rm --recursive --force node_modules/
	-rm package-lock.json

.PHONY: clean distclean




# QUALITY
# =======

test: build
	$(MANAGE_PY) test $(PACKAGE) $(EXTRA_PACKAGES)
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

# MISC
# ====

runserver: $(DJANGO_ASSETS_SENTINEL)
	$(MANAGE_PY) runserver

.PHONY: runserver
