; Registers used by the CPU-side hardware routines.
PPU_CONTROL = $2000
PPU_MASK    = $2001
PPU_STATUS  = $2002
OAM_ADDRESS = $2003
PPU_SCROLL  = $2005
PPU_ADDRESS = $2006
PPU_DATA    = $2007
DMC_CONTROL = $4010
OAM_DMA     = $4014
APU_STATUS  = $4015
JOYPAD_1    = $4016
JOYPAD_2    = $4017
APU_FRAME   = $4017

; Caller resets the PPU address latch. Column zero selects 32-byte increments.
; Keep the transfer unrolled so both tile columns fit in vblank.
.macro upload_tile_column source, column
    lda _vram_hi
    sta PPU_ADDRESS
    lda _vram_lo
    .if column
        clc
        adc #column
    .endif
    sta PPU_ADDRESS
    .if column = 0
        lda #$84
        sta PPU_CONTROL
    .endif
    .repeat 30, row
        lda source+row
        sta PPU_DATA
    .endrepeat
.endmacro

; Shift the next serial bit from each port into its destination byte.
.macro read_pad_pair first, second
    lda JOYPAD_1
    lsr a
    rol first
    lda JOYPAD_2
    lsr a
    rol second
.endmacro
