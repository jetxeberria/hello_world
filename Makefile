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

help:
	@python3.6 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

find-pizarra-images:
	@[ "${TARGET_PATH}" ] || ( echo "TARGET_PATH is absent, set automatically to current folder")
	find $${TARGET_PATH:=.} -type f -print | xargs -I {} getfattr -d "{}" 2>/dev/null | grep -B 1 pizarra | grep file 

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

enable-sudo:
	@sudo echo "sudo enabled"


