#

PYPROGS := $(wildcard *.py)
PROGS := $(basename $(PYPROGS))

all: lint
lint: $(PYPROGS)
relint: rmlint lint
rmlint:
	@printf '>>> rmlinks...'
	@for base in *.py; do rm -f $$(basename $$base .py); done
	@echo done

# we target symlinks pointing to the .py file;
# removing the symlink will re-lint the .py
#
$(PROGS): ;
$(PYPROGS): %.py: %
	@echo '>>> linting $@...'
	flake8 $@
	pylint3 $@
	ln -s $@ $<
	@echo '>>> done'

.PHONY: lint all relint rmlint
