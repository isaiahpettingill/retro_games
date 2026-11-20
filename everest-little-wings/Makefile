GBDK_HOME ?= /opt/gbdk
LCC := $(GBDK_HOME)/bin/lcc
SOURCES := $(wildcard src/*.c) $(wildcard art/*.c)
OBJS := $(patsubst %.c,build/%.o,$(SOURCES))
TARGET := build/Climb-Ducky-Climb.gbc

.PHONY: all clean art check-route check-hard
all: $(TARGET)
$(TARGET): $(OBJS)
	$(LCC) -Wl-m -Wl-j -Wm-yC -Wl-yt0x1B -Wm-yo16 -Wm-ya1 -Wm-yn"CLIMB DUCKY" -o $@ $^
build/%.o: %.c art/assets.h src/game.h art/course.inc
	@mkdir -p $(dir $@)
	$(LCC) -Iart -Isrc -c -o $@ $<
art:
	python3 tools/art.py
	python3 tools/course.py
check-route: build/checks/course
	./$<
check-hard: build/checks/endless
	./$<
build/checks/%: checks/%.c src/physics.c src/game.h art/course.inc $(wildcard checks/host/gb/*.h)
	@mkdir -p $(dir $@)
	$(CC) -O2 -std=c99 -Ichecks/host -Iart $< -o $@
clean:
	rm -rf build
