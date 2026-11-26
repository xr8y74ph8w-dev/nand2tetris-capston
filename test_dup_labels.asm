// Assembler validation test: duplicate labels should produce a warning
(LOOP)
@LOOP
0;JMP
(LOOP)
@0
