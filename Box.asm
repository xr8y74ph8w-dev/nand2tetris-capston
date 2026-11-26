// Box.asm — Nand to Tetris I (ETCCNT301) Capstone Project
// Name: Prabhat Tewatia | Roll No: 2501730207 | K = 07
//
// Hold ANY keyboard key: draw a 16x20 black box at row 24 and show "07"
// in white pixels inside it. Release the key: clear the box and the number.
// Start address: SCREEN (16384) + 32 * 24 = 17152
// Box height: 20 rows (24..43); width: 1 word = 16 pixels.
// The 5x7 digits are centered in the 16x20 box.

    @17152          // Row 24 start address
    D=A
    @start_addr
    M=D

    @20             // Box height
    D=A
    @height
    M=D

    @1              // Box width: one 16-pixel word
    D=A
    @width
    M=D

    @prev_color
    M=0

// Poll keyboard continuously.
(MAIN_LOOP)
    @KBD
    D=M
    @SET_WHITE
    D;JEQ
    @color
    M=-1             // Key pressed: black background
    @CHECK_CHANGE
    0;JMP

(SET_WHITE)
    @color
    M=0              // Key released: clear to white

(CHECK_CHANGE)
    @color
    D=M
    @prev_color
    D=D-M
    @MAIN_LOOP
    D;JEQ             // Redraw only when key state changes

    @color
    D=M
    @prev_color
    M=D

// Fill the 16x20 rectangle with the selected color.
(DRAW_BOX)
    @start_addr
    D=M
    @row_base
    M=D
    @height
    D=M
    @rows_left
    M=D

(ROW_LOOP)
    @rows_left
    D=M
    @DRAW_NUMBER
    D;JEQ
    @row_base
    D=M
    @addr
    M=D
    @width
    D=M
    @cols_left
    M=D

(COL_LOOP)
    @cols_left
    D=M
    @NEXT_ROW
    D;JEQ
    @color
    D=M
    @addr
    A=M
    M=D
    @addr
    M=M+1
    @cols_left
    M=M-1
    @COL_LOOP
    0;JMP

(NEXT_ROW)
    @32
    D=A
    @row_base
    M=D+M
    @rows_left
    M=M-1
    @ROW_LOOP
    0;JMP

// Overlay white 5x7 digits "07" only on the black box.
(DRAW_NUMBER)
    @color
    D=M
    @MAIN_LOOP
    D;JEQ             // White state: no number to draw

    // Start at row 30 (row 24 + 6), centered vertically.
    @17152
    D=A
    @192
    D=D+A
    @glyph_addr
    M=D

    // Each complement is loaded then inverted to create the 16-bit screen word.
    @3708            // Row 1: top strokes of 2 and 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @32
    D=A
    @glyph_addr
    M=D+M
    @4356            // Row 2: upper right of 2 and both sides of 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @32
    D=A
    @glyph_addr
    M=D+M
    @4872            // Row 3: upper right of 2 and both sides of 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @32
    D=A
    @glyph_addr
    M=D+M
    @5392            // Row 4: middle bars of 2 and 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @32
    D=A
    @glyph_addr
    M=D+M
    @6432            // Row 5: lower left of 2 and lower right of 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @32
    D=A
    @glyph_addr
    M=D+M
    @4384            // Row 6: lower left of 2 and lower right of 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @32
    D=A
    @glyph_addr
    M=D+M
    @3616            // Row 7: bottom of 2 and foot of 4
    D=A
    D=!D
    @glyph_addr
    A=M
    M=D
    @MAIN_LOOP
    0;JMP
