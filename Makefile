.PHONY: setup list cube stand all clean

setup:
	python -m pip install --upgrade pip
	python -m pip install -e .

list:
	generate-model list

cube:
	generate-model export calibration_cube --format stl --format step

stand:
	generate-model export phone_stand --format stl --format step

all:
	generate-model export --all --format stl --format step

clean:
	rm -rf build/* exports/*
	touch build/.gitkeep exports/.gitkeep
