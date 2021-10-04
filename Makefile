.PHONY: dist

dist:
	# make dist version="X.X.X"
	rm -rf dist
	mkdir dist
	make dist_source

dist_source:
	python3 setup.py sdist --formats=zip
	rm -rf *.egg-info

develop:
	pip3 install -e .

install:
	pip3 install .

test:
	pytest tests/