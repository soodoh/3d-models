.DEFAULT_GOAL := help

PYTHON ?= python
MODEL ?= gridfinity_box
VIEWS ?= isometric,top,front,right
PREVIEW_FORMAT ?= png
PARAMS ?=
PREVIEW_OUT ?= build/previews
EXPORT_OUT ?= build
EXPORT_FORMATS ?= stl step

PARAM_FLAGS = $(foreach param,$(PARAMS),--param $(param))
EXPORT_FLAGS = $(foreach format,$(EXPORT_FORMATS),--export $(format))

.PHONY: help setup list describe preview inspect export export-all all clean

help:
	@printf "CadQuery workflow targets:\n"
	@printf "  make setup                         Install editable package\n"
	@printf "  make list                          List registered models\n"
	@printf "  make describe MODEL=name           Show model parameters\n"
	@printf "  make preview MODEL=name            Render previews + inspect geometry\n"
	@printf "  make inspect MODEL=name            Inspect geometry without rendering\n"
	@printf "  make export MODEL=name             Export selected model formats\n"
	@printf "  make export-all                    Export every registered model\n"
	@printf "  make clean                         Remove generated build/export files\n"
	@printf "\nExamples:\n"
	@printf "  make preview MODEL=gridfinity_box VIEWS=top,front\n"
	@printf "  make preview MODEL=gridfinity_box PREVIEW_FORMAT=svg\n"
	@printf "  make preview MODEL=gridfinity_box PARAMS='unit_width=3 unit_depth=4'\n"
	@printf "  make export MODEL=gridfinity_box EXPORT_FORMATS='stl step'\n"

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

list:
	generate-model list

describe:
	generate-model describe $(MODEL)

preview:
	$(PYTHON) preview.py $(MODEL) --views $(VIEWS) --preview-format $(PREVIEW_FORMAT) --out-dir $(PREVIEW_OUT) $(PARAM_FLAGS)

inspect:
	$(PYTHON) preview.py $(MODEL) --no-preview $(PARAM_FLAGS)

export:
	$(PYTHON) preview.py $(MODEL) --no-preview --no-inspect --export-dir $(EXPORT_OUT) $(EXPORT_FLAGS) $(PARAM_FLAGS)

export-all:
	generate-model export --all $(foreach format,$(EXPORT_FORMATS),--format $(format)) --out-dir $(EXPORT_OUT)

all: export-all

clean:
	rm -rf build/* exports/*
	mkdir -p build exports
	touch build/.gitkeep exports/.gitkeep
