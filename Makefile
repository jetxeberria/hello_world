.PHONY: docs test help
.DEFAULT_GOAL := help

SHELL := /bin/bash

define PRINT_HELP_PYSCRIPT
import re, sys
print("You can run the following targets (with make <target>): \r\n")
for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

SHELL_ENVIRONMENT := $(echo $$- | sed "s/i//;s/s//")

clean: clean-build clean-dist clean-pyc clean-test clean-docs ## remove all build, test, coverage and Python artifacts

clean-docs: ## remove auto-generated docs
	rm -fr docs/_build

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr .eggs/
	find . ! -path './.tox/*' -name '*.egg-info' -exec rm -fr {} +
	find . ! -path './.tox/*' -name '*.egg' -exec rm -f {} +
	find hello_world -name '*.c' -exec rm -f {} +

clean-dist: ## remove dist packages
	rm -fr dist/

clean-pyc: ## remove Python file artifacts
	find . ! -path './.tox/*' -name '*.pyc' -exec rm -f {} +
	find . ! -path './.tox/*' -name '*.pyo' -exec rm -f {} +
	find . ! -path './.tox/*' -name '*~' -exec rm -f {} +
	find . ! -path './.tox/*' -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -rf .pytest_cache
	rm -f .coverage

clean-env: ## remove virtual environments (created by tox)
	rm -fr .tox/

help:
	@python3.6 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)


test: ## run tests with pytest
	py.test

find-pizarra-images:
	@[ "${TARGET_PATH}" ] || ( echo "TARGET_PATH is absent, set automatically to current folder")
	find $${TARGET_PATH:=.} -type f -print | xargs -I {} getfattr -d "{}" 2>/dev/null | grep -B 1 pizarra | grep file 

show-file-size:
	@[ "${TARGET_PATH}" ] || ( echo "TARGET_PATH is absent, set automatically to current folder")
	du -hs $${TARGET_PATH:=.}

show-biggest-files:
	@[ "${TARGET_PATH}" ] || ( echo "TARGET_PATH is absent, set automatically to current folder")
	@[ "${NUM}" ] || ( echo "NUM is absent, set automatically to 50")
	find $${TARGET_PATH:=.} -exec du -ahL {} + 2>/dev/null | sort -rh | head -n $${NUM:=50}

backup-thunderbird-filters:
	cp ~/.thunderbird/e9yv6kk2.default-release/ImapMail/outlook.office365.com/msgFilterRules.dat computer_config/thunderbird_filters.dat

print-installed-packages:
	apt list | awk '/installed/{print $$1}'
	
remove-old-snaps: enable-sudo
	@set -eu;
	snap list --all | awk '/disabled/{print $$1, $$3}' | while read snapname revision; do sudo snap remove "$$snapname" --revision="$$revision"; done
	@set +eu;
	@set -$$SHELL_ENVIRONMENT

remove-snaps-cache: enable-sudo
	@echo "Currently, /var/lib/snapd/cache has a size of:"
	@sudo du -hs /var/lib/snapd/cache
	@sudo rm -r /var/lib/snapd/cache
	@sudo mkdir /var/lib/snapd/cache
	@sudo chmod 700 /var/lib/snapd/cache
	@echo "/var/lib/snapd/cache has been recreated and it's empty now"

remove-old-journals: enable-sudo
	@[ "${DAYS}" ] || ( echo "DAYS is absent, set automatically to 10 days")
	sudo journalctl --vacuum-time=$${DAYS:=10}d

enable-sudo:
	@sudo echo "sudo enabled"

recover-sound: enable-sudo
	pulseaudio -k


recover-sound2: enable-sudo
	@sudo alsa force-reload

recover-underscores:
	@echo "Sometimes underscores dissapear in VSC, well in editor or in integrated terminal"
	@echo "To recover them we have 3 choices"
	@echo "Choice 1: zoom-in or out"
	@echo "Choice 2: Force Font Family 'Ubuntu Mono'"
	@echo "Choice 3: Modify window.zoomLevel (-0.4)"

open-svg:
	@[ "${PATH}" ] || ( echo "PATH is not set"; exit 1 )
	display $${PATH}


env-create: ## (re)create a development environment using tox
	tox -e hello_world --recreate
	@echo -e "\r\nYou can activate the environment with:\r\n\r\n$$ source ./.tox/hello_world/bin/activate\r\n"
	./.tox/hello_world/bin/pip install pip==20.2.4

env-compile: ## compile requirements.txt / requirements-dev.txt using pip-tools
	pip-compile --no-index --no-header --no-emit-trusted-host --output-file requirements.txt requirements.in
	pip-compile --no-index --no-header --no-emit-trusted-host --output-file requirements-dev.txt requirements-dev.in

env-sync: ## synchornize requirements.txt /requirements-dev.txt with tox virtualenv using pip tools
	pip-sync requirements.txt requirements-dev.txt

