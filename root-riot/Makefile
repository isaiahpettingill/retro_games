CC65 ?= cc65
CA65 ?= ca65
LD65 ?= ld65
NESLIB ?= nes.lib
PYTHON ?= python3
all: release/RootRiot.nes
build/art.chr build/world.h build/art.h &: src/art.py src/menus.py src/world.py
	mkdir -p build
	$(PYTHON) src/art.py
	$(PYTHON) src/world.py
build/game.s: src/game.c build/world.h build/art.h
	$(CC65) -Cl -Oirs -t nes -I build -o $@ $<
build/game.o: build/game.s
	$(CA65) -t nes -o $@ $<
build/hardware.o: src/hardware.s build/art.chr
	$(CA65) --bin-include-dir build -o $@ $<
release/RootRiot.nes: build/hardware.o build/game.o src/cart.cfg
	mkdir -p release
	$(LD65) -C src/cart.cfg -m build/game.map -Ln build/game.lbl -o $@ build/hardware.o build/game.o $(NESLIB)
clean:
	rm -rf build release/RootRiot.nes
