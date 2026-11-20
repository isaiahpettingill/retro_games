.include "nes.inc"

.import _main
.importzp sp
.export __STARTUP__ : absolute
__STARTUP__ = 1
.export _present,_blank,_on,_bank,_readpads,_upload,_puttile
.export _vram_hi,_vram_lo,_stream,_streaming,_attr_lo,_sx,_nt,_frame,_pads,_edges
.export _oam,_menu_bytes
.segment "HEADER"
.byte "NES",$1a,2,4,$31,$08,0,0,0,0,0,0,0,2 ; NES 2.0, CNROM, vertical mirroring, Four Score
.segment "ZEROPAGE"
_vram_hi: .res 1
_vram_lo: .res 1
_attr_lo: .res 1
_streaming: .res 1
_menu_bytes: .res 1
_sx: .res 1
_nt: .res 1
_frame: .res 1
ready: .res 1
screen: .res 1
.segment "BSS"
_stream: .res 68
_pads: .res 4
_edges: .res 4
prev: .res 4
sig: .res 2
_oam=$0200
.segment "STARTUP"
reset:
    sei
    cld
    ldx #$40
    stx APU_FRAME
    ldx #$ff
    txs
    inx
    stx PPU_CONTROL
    stx PPU_MASK
    stx DMC_CONTROL
    bit PPU_STATUS
@warm:
    bit PPU_STATUS
    bpl @warm
    lda #0
@clear:
    sta $00,x
    sta $0100,x
    sta $0200,x
    sta $0300,x
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    inx
    bne @clear
@warm2:
    bit PPU_STATUS
    bpl @warm2
    lda #<$0800
    sta sp
    lda #>$0800
    sta sp+1
    lda #$80
    sta PPU_CONTROL
    lda #$0f
    sta APU_STATUS
    jmp _main
.segment "CODE"
_bank:
    tax
    sta bank_ids,x ; bus-conflict-safe latch
    rts
bank_ids: .byte 0,1,2,3
_blank:
    lda #0
    sta screen
    sta PPU_MASK
    sta ready
    sta _menu_bytes
    sta _streaming
    rts
_on:
    lda #1
    sta screen
    rts
_present:
    lda #1
    sta ready
@wait:
    lda ready
    bne @wait
    rts
_puttile:
    sta PPU_DATA
    rts

; Stream two tile columns followed by their attribute bytes.
_upload:
    bit PPU_STATUS
    upload_tile_column _stream, 0
    upload_tile_column _stream+30, 1
    lda _vram_hi
    ora #3
    tax
    .repeat 8,I
    stx PPU_ADDRESS
    lda _attr_lo
    clc
    adc #($c0+I*8)
    sta PPU_ADDRESS
    lda _stream+60+I
    sta PPU_DATA
    .endrepeat
    lda #$80
    sta PPU_CONTROL
    rts

; Read the Four Score streams and check their signatures before using pads 3 and 4.
_readpads:
    ldx #3
@old:
    lda _pads,x
    sta prev,x
    dex
    bpl @old
    lda #1
    sta JOYPAD_1
    lda #0
    sta JOYPAD_1
    ldx #0
@pair:
    ldy #8
@bits: read_pad_pair {_pads,x}, {_pads+1,x}
    dey
    bne @bits
    inx
    inx
    cpx #4
    bne @pair
    ldy #8
@sig: read_pad_pair sig, sig+1
    dey
    bne @sig
    lda sig
    cmp #$10
    bne @none
    lda sig+1
    cmp #$20
    beq @edges
@none:
    lda #0
    sta _pads+2
    sta _pads+3
@edges:
    ldx #3
@edge:
    lda prev,x
    eor #$ff
    and _pads,x
    sta _edges,x
    dex
    bpl @edge
    rts

; Only transfer a pending frame. The main loop can wait on ready.
nmi:
    pha
    txa
    pha
    tya
    pha
    inc _frame
    lda ready
    beq @done
    lda screen
    beq @ack
    lda #0
    sta OAM_ADDRESS
    lda #2
    sta OAM_DMA
    lda _streaming
    beq @scroll
    jsr _upload
    lda #0
    sta _streaming
@scroll:
    lda _menu_bytes
    beq @position
    bit PPU_STATUS
    ldx #0
@span:
    lda _stream,x
    sta PPU_ADDRESS
    lda _stream+1,x
    sta PPU_ADDRESS
    ldy _stream+2,x
    inx
    inx
    inx
@tile:
    lda _stream,x
    sta PPU_DATA
    inx
    dey
    bne @tile
    cpx _menu_bytes
    bcc @span
    lda #0
    sta _menu_bytes
@position:
    bit PPU_STATUS
    lda _nt
    ora #$a0 ; 8x16 sprites, bg table 0
    sta PPU_CONTROL
    lda _sx
    sta PPU_SCROLL
    lda #0
    sta PPU_SCROLL
    lda #$1e
    sta PPU_MASK
@ack:
    lda #0
    sta ready
@done:
    pla
    tay
    pla
    tax
    pla
irq:
    rti
.segment "VECTORS"
.addr nmi,reset,irq
.segment "CHARS"
.incbin "art.chr"
.segment "ZEROPAGE"
oi: .res 1
spr_x: .res 1
spr_y: .res 1
spr_t: .res 1
spr_p: .res 1
spr_flip: .res 1
.segment "CODE"
.export _piece,_figure,_hide
.import incsp3,incsp4
_hide:
    lda #$ff
    .repeat 64,I
    sta _oam+I*4
    .endrepeat
    lda #0
    sta oi
    rts

; cc65 passes the palette in A and the position and tile on its software stack.
_piece:
    ldx oi
    cpx #252
    bcs @end
    sta _oam+2,x
    ldy #0
    lda (sp),y
    asl a
    ora #1
    sta _oam+1,x
    iny
    lda (sp),y
    sec
    sbc #1
    sta _oam,x
    iny
    lda (sp),y
    sta _oam+3,x
    txa
    clc
    adc #4
    sta oi
@end:
    jmp incsp3
_figure:
    ldx oi
    cpx #248
    bcs @end
    sta spr_flip
    ldy #0
    lda (sp),y
    cpy spr_flip
    beq @palette
    ora #64
@palette:
    sta spr_p
    iny
    lda (sp),y
    asl a
    ora #1
    ldy spr_flip
    beq @tile
    eor #2
@tile:
    sta spr_t
    ldy #2
    lda (sp),y
    sec
    sbc #1
    sta spr_y
    iny
    lda (sp),y
    sta spr_x
    lda spr_p
    sta _oam+2,x
    sta _oam+6,x
    lda spr_y
    sta _oam,x
    sta _oam+4,x
    lda spr_t
    sta _oam+1,x
    eor #2
    sta _oam+5,x
    lda spr_x
    sta _oam+3,x
    clc
    adc #8
    bcs @single
    sta _oam+7,x
    txa
    clc
    adc #8
    sta oi
    jmp incsp4
@single:
    txa
    clc
    adc #4
    sta oi
@end:
    jmp incsp4
