SHELL := /bin/bash
.DEFAULT_GOAL := all

QT_ROOT ?= $(shell qmake -query QT_INSTALL_PREFIX 2>/dev/null)
ARCHS ?= arm64 x86_64
QT_HOST_ARCH ?= $(shell uname -m)
JOBS ?= 4
MACOS_MIN ?= 12.0
PYTHON ?= python3
ARCH_LABEL := $(if $(filter 2,$(words $(ARCHS))),Universal,$(firstword $(ARCHS)))
BUILD_DIR ?= build/macos-$(ARCH_LABEL)
DIST_DIR ?= dist
BUILD_ABS := $(abspath $(BUILD_DIR))
QT_ABS := $(abspath $(QT_ROOT))
APP := $(DIST_DIR)/QFGraph-$(ARCH_LABEL).app
ZIP := $(DIST_DIR)/QFGraph-macOS-$(ARCH_LABEL).zip
SDK := $(shell xcrun --sdk macosx --show-sdk-path 2>/dev/null)
SDK_VERSION := $(shell xcrun --sdk macosx --show-sdk-version 2>/dev/null)
DEVELOPER := $(shell xcode-select --print-path 2>/dev/null)
CLANG := $(shell xcrun --find clang 2>/dev/null)
CLANGXX := $(shell xcrun --find clang++ 2>/dev/null)

.PHONY: all universal check build package verify smoke clean help
all: package
universal: package

check:
	@test "$$(uname -s)" = Darwin || { echo 'This Makefile builds macOS applications. Use the Windows workflow for Windows.'; exit 1; }
	@test -n "$(QT_ROOT)" -a -x "$(QT_ABS)/bin/qmake" || { echo 'Set QT_ROOT to a Qt installation containing bin/qmake.'; exit 1; }
	@$(PYTHON) scripts/macos.py check "$(QT_ABS)" $(ARCHS)

build: check
	@mkdir -p "$(BUILD_ABS)/host-tools"
	@$(PYTHON) scripts/macos.py tools "$(QT_ABS)" "$(BUILD_ABS)/host-tools" "$(QT_HOST_ARCH)"
	cd "$(BUILD_ABS)" && arch -$(QT_HOST_ARCH) "$(QT_ABS)/bin/qmake" "$(CURDIR)/QFGraph.pro" -early \
		'QMAKE_MAC_SDK.macosx.Path=$(SDK)' \
		'QMAKE_MAC_SDK.macosx.PlatformPath=$(DEVELOPER)' \
		'QMAKE_MAC_SDK.macosx.SDKVersion=$(SDK_VERSION)' \
		'QMAKE_CC=$(CLANG)' 'QMAKE_CXX=$(CLANGXX)' 'QMAKE_LINK=$(CLANGXX)' \
		-before CONFIG+=release CONFIG-=debug 'QMAKE_APPLE_DEVICE_ARCHS=$(ARCHS)' \
		QMAKE_MACOSX_DEPLOYMENT_TARGET=$(MACOS_MIN) \
		'QMAKE_CXXFLAGS+=-include $(BUILD_ABS)/host-tools/compiler-compat.h'
	@$(PYTHON) scripts/macos.py sdk "$(BUILD_ABS)/Makefile" "$(SDK)" "$(QT_ABS)" "$(BUILD_ABS)/host-tools"
	$(MAKE) -C "$(BUILD_ABS)" -j$(JOBS)

package: build
	@mkdir -p "$(DIST_DIR)"
	@$(PYTHON) scripts/macos.py copy "$(BUILD_ABS)/QFGraph.app" "$(APP)"
	PATH="$(BUILD_ABS)/host-tools:$$PATH" arch -$(QT_HOST_ARCH) "$(QT_ABS)/bin/macdeployqt" "$(APP)" -libpath="$(QT_ABS)/lib"
	@$(PYTHON) scripts/macos.py verify "$(APP)" $(ARCHS)
	codesign --force --deep --sign - "$(APP)"
	codesign --verify --deep --strict "$(APP)"
	ditto -c -k --sequesterRsrc --keepParent "$(APP)" "$(ZIP)"
	@echo "Created $(ZIP)"

verify:
	@$(PYTHON) scripts/macos.py verify "$(APP)" $(ARCHS)
	codesign --verify --deep --strict "$(APP)"

# Runs the actual Cocoa application; requires a macOS graphical login session.
# Intel execution on Apple Silicon requires Rosetta. Tests every requested slice.
smoke: verify
	@$(PYTHON) scripts/macos.py smoke "$(APP)" $(ARCHS)

clean:
	@$(PYTHON) scripts/macos.py clean "$(BUILD_ABS)"

help:
	@echo 'make QT_ROOT=/path/to/Qt/6.8.3/macos         Build and package Universal'
	@echo 'make QT_ROOT=/path/to/Qt ARCHS=arm64        Build Apple Silicon only'
	@echo 'make QT_ROOT=/path/to/Qt QT_HOST_ARCH=x86_64  Run Qt tools under Rosetta'
	@echo 'make verify / make smoke                   Check package / test startup'
	@echo 'make clean                                 Remove this build directory'
