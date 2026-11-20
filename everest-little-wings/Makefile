GBDK_HOME ?= /opt/gbdk
LCC := $(GBDK_HOME)/bin/lcc
SOURCES := $(wildcard src/*.c) $(wildcard art/*.c)
OBJS := $(patsubst %.c,build/%.o,$(SOURCES))
TARGET := build/Everest-Little-Wings.gbc

.PHONY: all clean art check-route check-hard
all: $(TARGET)
$(TARGET): $(OBJS)
	$(LCC) -Wl-m -Wl-j -Wm-yC -Wl-yt0x1B -Wm-yo16 -Wm-ya1 -Wm-yn"LITTLE WINGS" -o $@ $^
build/%.o: %.c art/assets.h src/game.h art/course.inc
	@mkdir -p $(dir $@)
	$(LCC) -Iart -Isrc -c -o $@ $<
art:
	python3 tools/art.py
	python3 tools/course.py
	python3 tools/export_duck.py
check-route:
	@mkdir -p build/checks
	$(CC) -O2 -std=c99 -Ichecks/host -Iart checks/course.c -o build/checks/course
	./build/checks/course
check-hard:
	@mkdir -p build/checks
	$(CC) -O2 -std=c99 -Ichecks/host -Iart checks/endless.c -o build/checks/endless
	./build/checks/endless
clean:
	rm -rf build
