# SOP: Excel FRU List → MIF Conversion

## Purpose
Convert an Excel file containing FRU (Field Replaceable Unit) data into a FrameMaker MIF document using the standard Level-2 FRU Master List template.

## Inputs
| File | Description |
|------|-------------|
| `<docnr>.xlsx` | Excel FRU list (sheet: `GenCh3`) |
| `Level 2 - FRU Master List_templ.mif` | MIF template (project root) |

## Output
`<docnr>_d1.mif` – FrameMaker MIF document written to the same folder as the input Excel.

## Excel Sheet Structure (`GenCh3`)
| Row | Col A | Col B | Col C | Col D | Col H |
|-----|-------|-------|-------|-------|-------|
| 1 (metadata) | doc_number (e.g. `315459`) | doc_type (`Chapter`) | chapter_name (`P-series G7`) | – | – |
| 2…N (data) | category (e.g. `Spare parts`) | description | order_code / FRU number | reference path(s), newline-separated (e.g. `Database/L3/312867`) | item_number |

Data rows are read until a row with `col A == None` or `col A in {"Service Virtual Assistant Content", "MarkDown"}`.

## Substitutions Applied to Template
| Template value | Replaced with | Location |
|----------------|---------------|----------|
| `<FRU cross section\>` | `{chapter_name} {doc_type}` | CrossSection VariableDef |
| `xxxxxx` | `{doc_number}` | docnr VariableDef |
| `FRU list` (in PDFDocInfo Value) | `{chapter_name} {doc_type} FRU list` | PDF metadata |
| `Level 2 - FRU Master List` (in FileName) | `{doc_number}` | BookComponent filenames |
| `<Unique N>` (all occurrences) | Sequential IDs from 1030001 | Unique identifiers throughout |

## FRU Table Generation
A new `<Tbl>` block (`TblID 11`, `TblTag FRU`) is inserted before `> # end of Tbls`.

Each data row produces 5 cells:
1. **CellBody** – space placeholder
2. **Cell** – ` {description}` (leading space)
3. **CellLink** – hypertext marker `openlink ../../Database/L3/{order_code}_FRU.fm` + String `{order_code}`
4. **CellLink** – zero or more hypertext markers for reference paths; if multiple refs, first Para String contains first basename + `\n` + remaining full paths
5. **CellText** – empty remarks

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
- `fru_header.json` – pre-extracted FRU table header/TblH template (in `execution/`)

## Notes
- Template encoding: `latin-1` (FrameMaker 7 MIF)
- Output encoding: `latin-1`, Unix line endings (`\n`)
- Unique IDs are sequential and unique within the file; their exact values do not affect document correctness
- The A TextFlow in the output contains an `<ATbl 11>` paragraph that places the FRU table in the document body
