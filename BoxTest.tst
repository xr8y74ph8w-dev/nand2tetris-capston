// Automated CPUEmulator test for Box.hack (display 07: row 24..43, width 16 px = 1 word)
load Box.hack,
output-file BoxTest.out,
compare-to BoxTest.cmp,
output-list RAM[24576]%D2.6.2 RAM[17151]%D2.6.2 RAM[17152]%D2.6.2 RAM[17153]%D2.6.2 RAM[17759]%D2.6.2 RAM[17760]%D2.6.2 RAM[17761]%D2.6.2;

// Phase 1: no key pressed -> box remains white
set RAM[24576] 0,
repeat 200 { ticktock; }
output;

// Phase 2: key pressed -> black box appears across rows 24..43 with white number 07 inside
set RAM[24576] 65,
repeat 2000 { ticktock; }
output;

// Phase 3: key released -> box clears
set RAM[24576] 0,
repeat 2000 { ticktock; }
output;

// Phase 4: another key pressed -> box appears again
set RAM[24576] 32,
repeat 2000 { ticktock; }
output;
