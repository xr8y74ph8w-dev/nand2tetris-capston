#!/usr/bin/env python3
"""
Nand to Tetris - I (ETCCNT301) Capstone Project: Part B - Hack Assembler
Student  : Prabhat Tewatia
Roll No. : 2501730207
Personal Number K = 07  (K mod 3 = 0)

Assembler validation:
    Prints a clear warning whenever the same label (LABEL) is declared
    more than once, reporting both the duplicate line number and the
    original line number / ROM address.

Usage:
    python assembler.py <input.asm> [output.hack]

    If output.hack is omitted, writes <input_stem>.hack next to <input.asm>.
"""

from pathlib import Path
import sys


# ---------------------------------------------------------------------------
# Hack Machine Language Lookup Tables (Chapter 6 Specification)
# ---------------------------------------------------------------------------

PREDEFINED_SYMBOLS: dict[str, int] = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    **{f"R{i}": i for i in range(16)},
    "SCREEN": 16384,
    "KBD": 24576,
}

# comp -> 7-bit string: a c1 c2 c3 c4 c5 c6
COMP_TABLE: dict[str, str] = {
    # a = 0 (ALU operates on D and A)
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "A+D": "0000010",  # commutative alias
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "A&D": "0000000",  # commutative alias
    "D|A": "0010101",
    "A|D": "0010101",  # commutative alias
    # a = 1 (ALU operates on D and M)
    "M":   "1110000",
    "!M":  "1110001",
    "-M":  "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "M+D": "1000010",  # commutative alias
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "M&D": "1000000",  # commutative alias
    "D|M": "1010101",
    "M|D": "1010101",  # commutative alias
}

# dest -> 3-bit string: d1(A) d2(D) d3(M)
DEST_TABLE: dict[str, str] = {
    "":    "000",
    "M":   "001",
    "D":   "010",
    "MD":  "011",
    "DM":  "011",  # alternate ordering
    "A":   "100",
    "AM":  "101",
    "MA":  "101",  # alternate ordering
    "AD":  "110",
    "DA":  "110",  # alternate ordering
    "AMD": "111",
}

# jump -> 3-bit string: j1(<0) j2(==0) j3(>0)
JUMP_TABLE: dict[str, str] = {
    "":    "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def clean_line(raw_line: str) -> str:
    """Remove inline '//' comments and all whitespace from a source line."""
    no_comment = raw_line.split("//", 1)[0]
    return "".join(no_comment.split())


def encode_a_instruction(
    operand: str,
    symbol_table: dict[str, int],
    next_ram_addr: int,
    line_no: int,
) -> tuple[str, int]:
    """
    Translate an A-instruction (@value or @symbol) into a 16-bit binary string.
    Returns (binary_16bit, updated_next_ram_addr).
    """
    if not operand:
        raise ValueError(f"Line {line_no}: empty A-instruction '@'")

    if operand.isdigit():
        value = int(operand)
        if not (0 <= value <= 32767):
            raise ValueError(
                f"Line {line_no}: A-instruction constant '{value}' out of 15-bit range (0..32767)"
            )
    else:
        if operand not in symbol_table:
            symbol_table[operand] = next_ram_addr
            next_ram_addr += 1
        value = symbol_table[operand]

    return f"0{value:015b}", next_ram_addr


def encode_c_instruction(instruction: str, line_no: int) -> str:
    """
    Translate a C-instruction ([dest=]comp[;jump]) into a 16-bit binary string:
        111 + comp(7) + dest(3) + jump(3)
    """
    dest = ""
    jump = ""
    rest = instruction

    if "=" in rest:
        dest, rest = rest.split("=", 1)
    if ";" in rest:
        comp, jump = rest.split(";", 1)
    else:
        comp = rest

    if dest not in DEST_TABLE:
        raise ValueError(f"Line {line_no}: invalid dest field '{dest}' in '{instruction}'")
    if comp not in COMP_TABLE:
        raise ValueError(f"Line {line_no}: invalid comp field '{comp}' in '{instruction}'")
    if jump not in JUMP_TABLE:
        raise ValueError(f"Line {line_no}: invalid jump field '{jump}' in '{instruction}'")

    return f"111{COMP_TABLE[comp]}{DEST_TABLE[dest]}{JUMP_TABLE[jump]}"


# ---------------------------------------------------------------------------
# Two-Pass Assembler Core
# ---------------------------------------------------------------------------

def assemble(source_lines: list[str]) -> tuple[list[str], list[str], dict[str, int]]:
    """
    Run the two-pass Hack assembler over source_lines.

    Returns:
        machine_code : list of 16-bit binary strings
        warnings     : list of duplicate-label validation messages
        symbol_table : final symbol table (predefined + labels + variables)
    """
    symbol_table: dict[str, int] = dict(PREDEFINED_SYMBOLS)
    defined_labels: dict[str, tuple[int, int]] = {}  # label -> (first_line_no, rom_addr)
    warnings: list[str] = []
    instructions: list[tuple[int, str]] = []  # (original_line_no, cleaned_instruction)

    # ---------------- PASS 1: Strip comments & record (LABEL) positions ----------------
    rom_address = 0
    for line_no, raw_line in enumerate(source_lines, start=1):
        code = clean_line(raw_line)
        if not code:
            continue

        if code.startswith("(") and code.endswith(")"):
            label = code[1:-1]
            if not label:
                raise ValueError(f"Line {line_no}: empty label declaration '()'")

            # Duplicate-label validation:
            # Warn whenever the same label is written more than once.
            if label in defined_labels:
                first_line, first_rom = defined_labels[label]
                warnings.append(
                    f"WARNING (Line {line_no}): Duplicate label '({label})' — "
                    f"already declared at Line {first_line} (ROM address {first_rom}). "
                    f"Keeping first definition."
                )
            else:
                defined_labels[label] = (line_no, rom_address)
                symbol_table[label] = rom_address
        else:
            instructions.append((line_no, code))
            rom_address += 1

    # ---------------- PASS 2: Translate instructions & allocate variables --------------
    machine_code: list[str] = []
    next_ram_addr = 16  # User variables start at RAM[16]

    for line_no, code in instructions:
        if code.startswith("@"):
            binary, next_ram_addr = encode_a_instruction(
                code[1:], symbol_table, next_ram_addr, line_no
            )
        else:
            binary = encode_c_instruction(code, line_no)
        machine_code.append(binary)

    return machine_code, warnings, symbol_table


def assemble_file(input_path: Path, output_path: Path | None = None) -> tuple[Path, int, list[str]]:
    """Assemble an .asm file on disk and write the resulting .hack file."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".hack")

    source_lines = input_path.read_text(encoding="utf-8").splitlines()
    machine_code, warnings, _ = assemble(source_lines)

    for warning in warnings:
        print(warning, file=sys.stderr)

    output_text = "\n".join(machine_code) + ("\n" if machine_code else "")
    output_path.write_text(output_text, encoding="utf-8")
    return output_path, len(machine_code), warnings


def main(argv: list[str]) -> int:
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python assembler.py <input.asm> [output.hack]", file=sys.stderr)
        return 1

    input_path = Path(argv[1])
    output_path = Path(argv[2]) if len(argv) == 3 else None

    try:
        written_path, count, warnings = assemble_file(input_path, output_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Assembled {input_path.name} -> {written_path.name} "
        f"({count} instructions, {len(warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
