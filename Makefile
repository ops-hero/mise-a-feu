SHELL := /bin/bash
TESTS=$(shell find tests/ -name "*.py")
VERSION=$(shell python -c "from mise_a_feu.scripts.update_stack import get_version; print get_version()")

test:
	nosetests ${TESTS}
	python mise_a_feu/scripts/update_stack.py --test tests/data/manifest.cfg localhost

version:
	@echo ${VERSION}

release:
	git checkout master
	git fetch upstream
	git pull --rebase upstream master
	python setup.py sdist upload -r pypi && git tag ${VERSION} && git push upstream --tags
