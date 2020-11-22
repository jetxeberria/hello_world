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

help:
	@python3.6 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

find-pizarra-images:
	@[ "${TARGET_PATH}" ] || ( echo "TARGET_PATH is absent, set automatically to current folder")
	find $${TARGET_PATH:=.} -type f -print | xargs -I {} getfattr -d "{}" 2>/dev/null | grep -B 1 pizarra | grep file 

show-biggest-files:
	@[ "${TARGET_PATH}" ] || ( echo "TARGET_PATH is absent, set automatically to current folder")
	@[ "${NUM}" ] || ( echo "NUM is absent, set automatically to 50")
	find $${TARGET_PATH:=.} -exec du -ShL {} + 2>/dev/null | sort -rh | head -n $${NUM:=.}

backup-thunderbird-filters:
	cp ~/.thunderbird/e9yv6kk2.default-release/ImapMail/outlook.office365.com/msgFilterRules.dat computer_config/thunderbird_filters.dat