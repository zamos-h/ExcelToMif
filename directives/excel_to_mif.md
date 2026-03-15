# SOP: Excel FRU List → MIF Conversion

## Purpose
Convert an Excel file containing FRU (Field Replaceable Unit) data into a FrameMaker MIF document using the standard Level-2 FRU Master List template. Replicates VBA macro `ButtonGenerateK3_2_Klepnut` (always in `L2_Checked=True` mode).

## Inputs
| File | Description |
|------|-------------|
| `<docnr>.xlsx` | Excel FRU list (sheet: `GenCh3`) |
| `Level 2 - FRU Master List_templ.mif` | MIF template (project root) |
| `Ch3 Generator.xlsm` | Block templates (sheet: `TblInsertNewTempl`) |

## Output
`<docnr>_d1.mif` – FrameMaker MIF document written to `L2 update/` subfolder (or specified path).

## Excel Sheet Structure (`GenCh3`)
| Row | Col A | Col B | Col C | Col D | Col E | Col F | Col G | Col L | Col M | Col N |
|-----|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| 1 (metadata) | doc_number | doc_type (`Chapter`/`Consumable`/`Overview`) | chapter_name | – | – | – | – | – | – | – |
| 2…N (data) | chapter / tag | description / type | order_code | WI ref path(s) | remark text | remark hyp file(s) | item_number | `Bullet` | bullet text | `AI` |

### Special `col A` values
- `No Chapter` – content rows without a chapter header (Note, Link, etc.)
- `System list` – rows added to a system applicability table (separate from FRU table)
- `Service Virtual Assistant Content` – sets `ai_content=True`; subsequent chapters use sub-chapter (V) blocks
- `MarkDown` – resets `ai_content`, inserts `# {chapter_name} {doc_type} FRU list` heading; resets AI counter
- Empty / `Not Used` – stop processing

### Special `col B` values
- `Note`, `Image`, `Chapter`, `Text` – add note/text blocks before EOF
- `Caution` – add caution block before EOF
- `Link` / `LinkFree` – add link block before EOF
- `Image Description` – add image description as note block
- `Bullet` marker in col L – add bullet block using col M text
- `AI` marker in col N – render row as markdown text block

## Substitutions Applied to Template
| Template value | Replaced with | Location |
|----------------|---------------|----------|
| `<FRU cross section\>` | `{chapter_name} {doc_type}` | CrossSection VariableDef |
| `xxxxxx` | `{doc_number}` | docnr VariableDef |
| `FRU list` (in PDFDocInfo Value) | `{chapter_name} {doc_type} FRU list` | PDF metadata |
| `Level 2 - FRU Master List` (in FileName) | `{doc_number}` | BookComponent filenames |
| `<Unique N>` (all occurrences) | Sequential IDs from 1030001 | Unique identifiers throughout |
| `<String 'Revision '>` (×2) | deleted | L2_Checked=True mode |
| `<String 'A'>` (×2) | deleted | L2_Checked=True mode |
| `[System A], [System B]` block (9 cells) | deleted | L2_Checked=True mode |

## FRU Table Generation
One `<Tbl>` block per chapter with data rows; first chapter creates full table (from `C_full` block), subsequent rows in same chapter append rows (`C_row` block). Table IDs start at 11 and increment.

Each data row produces 5 cells:
1. **CellBody** – item number (col G, or row counter when L2_Checked=False)
2. **Cell** – ` {description}` (leading space)
3. **CellLink** – hypertext marker `openlink ../../Database/L3/{order_code}_FRU.fm` + String `{order_code}`; blank if no order code
4. **CellLink** – WI/Replace Instruction: hypertext marker + display string; display string = `Right(D, Len(D) - pos_of_2nd_slash)` preserving embedded newlines; extra WI paths each get their own Para block
5. **CellText** – remark text (may include `(/text/)` hyperlink syntax)

## System List Table
When `col A = "System list"`, items are added to a separate system table (block `R`, rows from block `S`) placed before `> # end of Tbls`. Created once; subsequent rows just append.

## Insertion Mechanics (critical)
All "before EOF" insertions go **before `> # end of TextFlow`** (second-to-last line), NOT before `# End of MIFFile`. This keeps inserted content inside the last TextFlow, matching VBA `Range("A" & lastRow-1).Insert`.

Table blocks are inserted **at `> # end of Tbls`** (shifting it down), matching VBA `AddTbl2`/`AddNewRow2` mechanics.

## AI Content Sections
- `Service Virtual Assistant Content` chapter: sets `ai_content=True`; subsequent chapters rendered as sub-chapters (V block) instead of chapter headers (H block); `TblIdAI` counter increments for each new sub-chapter
- `MarkDown` row: resets `ai_content=False`, `chapter=''`, `TblIdAI=1`; inserts `# {chapter_name} {doc_type} FRU list` heading
- Post-MarkDown rows with `N='AI'`: chapter changes produce `## {N}) {chapter_name}` headings (N = counter, increments per chapter, resets at MarkDown); data rows produce markdown text blocks (Description, Order Code, WI, Remarks fields)

## Running the Converter

```powershell
# Activate venv
D:\.venvs\ExcelToMif\Scripts\activate

# Run
python execution\excel_to_mif.py <path\to\input.xlsx>

# Optional: specify template and/or output path
python execution\excel_to_mif.py input.xlsx template.mif output.mif
```

## Dependencies
- `openpyxl` – reads Excel files
- `Ch3 Generator.xlsm` – source of block templates (sheet `TblInsertNewTempl`, columns C/D/G/H/I/J/K/L/N/R/S/T/U/V/W)

## Notes
- Template encoding: `latin-1` (FrameMaker 7 MIF)
- Output encoding: `latin-1`, Unix line endings (`\n`), written to `L2 update/` folder
- Unique IDs are sequential from 1030001 and unique within the file; exact values don't affect document correctness
- `tbl_one=True` is only set for chapters that are NOT `No Chapter` or `System list` (per VBA: `If A <> "No Chapter" And A <> "System list"`)
- WI display string: `Right(D, Len(D) - InStr(2nd slash))` preserves embedded `\n` and subsequent WI paths in a single String spanning multiple output lines
- WI extra Para (2nd+ WI paths): `<Unique>` appears AFTER `> # end of Marker` (VBA double-insert-at-+8 artifact)
- Remark hyperlinks use `(/text/)` syntax in col E; col F provides hyperlink file paths (newline-separated)
- `TblInsertNewTempl` block columns (I, H, V, J, K, U, W) contain `=IF($B$1="AI","x","")` formula cells that return `None` with `data_only=True` (no cached value). Fix: `Blocks.__init__` opens a second workbook without `data_only` to detect these formula cells and returns `""` for them, allowing `get_contiguous` to read past them and capture the full block including closing tags (`> # end of PgfFont`, `> # end of Pgf`, `<ParaLine`, etc.). The `""` strings are filtered by `get_output`.
