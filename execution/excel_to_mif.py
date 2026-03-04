"""
excel_to_mif.py  –  Convert an Excel FRU list to a MIF document.

Usage:
    python excel_to_mif.py <input.xlsx>  [template.mif]  [output.mif]

    • template.mif defaults to  ../Level 2 - FRU Master List_templ.mif
    • output.mif   defaults to  <input_basename>_d1.mif  (same folder as input)

Excel sheet  "GenCh3"  structure expected:
    Row 1       : metadata  – col A = doc_number, col B = doc_type ("Chapter"),
                              col C = chapter_name ("P-series G7")
    Rows 2 – N  : data rows until a row with col A in SKIP_CATEGORIES or col A is None
                  col A = category, col B = description, col C = order_code,
                  col D = reference path(s) newline-separated ("Database/L3/XXXXXX"),
                  col H = item_number (not used, kept for reference)
"""

import os
import re
import sys
import json
import openpyxl

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR  = os.path.dirname(SCRIPT_DIR)
DEFAULT_TMPL = os.path.join(PROJECT_DIR, "Level 2 - FRU Master List_templ.mif")
FRU_HDR_JSON = os.path.join(SCRIPT_DIR, "fru_header.json")

SKIP_CATEGORIES = {"Service Virtual Assistant Content", "MarkDown"}

# ---------------------------------------------------------------------------
# Load the pre-extracted FRU table header template
# (extracted from a reference output; contains __UNIQUE__ placeholders)
# ---------------------------------------------------------------------------

with open(FRU_HDR_JSON, encoding="utf-8") as _f:
    FRU_HEADER_LINES = json.load(_f)      # list[str]


# ---------------------------------------------------------------------------
# Excel reading
# ---------------------------------------------------------------------------

def read_excel(xlsx_path: str):
    """Return (doc_number, cross_section, data_rows).

    data_rows: list of (description, order_code, refs_list)
        refs_list: list of reference basenames like ['312867', '311903']
    """
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    # Try the known sheet name first
    if "GenCh3" in wb.sheetnames:
        ws = wb["GenCh3"]
    else:
        ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Empty spreadsheet")

    # Row 1: metadata
    meta = rows[0]
    doc_number   = str(meta[0])
    doc_type     = str(meta[1]) if meta[1] is not None else "Chapter"
    chapter_name = str(meta[2]) if meta[2] is not None else ""
    cross_section = f"{chapter_name} {doc_type}"   # e.g. "P-series G7 Chapter"

    # Data rows: read until a separator / empty row
    data_rows = []
    for row in rows[1:]:
        cat = row[0]
        if cat is None or str(cat) in SKIP_CATEGORIES:
            break
        order_code  = row[2]
        description = row[1] if row[1] is not None else ""
        ref_raw     = row[3]  # may be None or "Database/L3/XYZ\nDatabase/L3/ABC"

        refs = []
        if ref_raw:
            for part in str(ref_raw).split("\n"):
                part = part.strip()
                if part:
                    # basename is the last path component without extension
                    refs.append(part.split("/")[-1])

        data_rows.append((str(description), str(order_code) if order_code is not None else "", refs))

    return doc_number, cross_section, data_rows


# ---------------------------------------------------------------------------
# MIF generation helpers
# ---------------------------------------------------------------------------

def _u(counter: list) -> str:
    """Increment the unique counter and return the MIF <Unique N> line."""
    counter[0] += 1
    return f"<Unique {counter[0]}>"


def _cel1_lines(counter: list) -> list:
    """Cell 1: category placeholder (space). Returns list of raw lines."""
    return [
        "    <Cell",
        "     <CellContent",
        "      <Notes",
        "      > # end of Notes",
        "      <Para",
        _u(counter),
        "       <Pgf",
        "        <PgfTag `CellBody'>",
        "        <PgfFont",
        "         <FTag `'>",
        "         <FPlatformName `W.Arial.R.400'>",
        "         <FFamily `Arial'>",
        "         <FVar `Regular'>",
        "         <FWeight `Regular'>",
        "         <FAngle `Regular'>",
        "         <FEncoding `FrameRoman'>",
        "         <FSize  11.0 pt>",
        "         <FUnderlining FNoUnderlining>",
        "         <FOverline No>",
        "         <FStrike No>",
        "         <FChangeBar No>",
        "         <FOutline No>",
        "         <FShadow No>",
        "         <FPairKern Yes>",
        "         <FTsume No>",
        "         <FCase FAsTyped>",
        "         <FPosition FNormal>",
        "         <FDX  0.0%>",
        "         <FDY  0.0%>",
        "         <FDW  0.0%>",
        "         <FStretch  100.0%>",
        "         <FLanguage USEnglish>",
        "         <FLocked No>",
        "         <FSeparation 0>",
        "         <FColor `Black'>",
        "        > # end of PgfFont",
        "        <PgfHyphenate Yes>",
        "        <PgfPDFStructureLevel 15>",
        "        <PgfCellMargins  0.0 pt 0.0 pt 0.0 pt 0.0 pt>",
        "       > # end of Pgf",
        "       <ParaLine",
        "        <String ` '>",
        "       > # end of ParaLine",
        "      > # end of Para",
        "     > # end of CellContent",
        "    > # end of Cell",
    ]


def _cel2_lines(counter: list, description: str) -> list:
    """Cell 2: description with leading space."""
    return [
        "    <Cell",
        "     <CellContent",
        "      <Notes",
        "      > # end of Notes",
        "      <Para",
        _u(counter),
        "       <PgfReferenced Yes>",
        "       <ParaLine",
        f"        <String ` {description}'>",
        "       > # end of ParaLine",
        "      > # end of Para",
        "     > # end of CellContent",
        "    > # end of Cell",
    ]


def _cel3_lines(counter: list, order_code: str) -> list:
    """Cell 3: hyperlink to the FRU file + order_code string."""
    return [
        "    <Cell",
        "     <CellContent",
        "      <Notes",
        "      > # end of Notes",
        "      <Para",
        _u(counter),
        "       <PgfTag `CellLink'>",
        "       <PgfReferenced Yes>",
        "       <ParaLine",
        "        <Marker",
        "         <MType 8>",
        "         <MTypeName `Hypertext'>",
        f" <MText `openlink ../../Database/L3/{order_code}_FRU.fm'>",
        "         <MCurrPage `1'>",
        _u(counter),
        "        > # end of Marker",
        f"        <String `{order_code}'>",
        "       > # end of ParaLine",
        "      > # end of Para",
        "     > # end of CellContent",
        "    > # end of Cell",
    ]


def _cel4_lines(counter: list, refs: list) -> list:
    """Cell 4: zero or more hyperlinks to reference files."""
    lines = [
        "    <Cell",
        "     <CellContent",
        "      <Notes",
        "      > # end of Notes",
    ]

    if not refs:
        # Empty cell with no links
        lines += [
            "      <Para",
            _u(counter),
            "       <PgfTag `CellLink'>",
            "       <PgfReferenced Yes>",
            "       <ParaLine",
            "       > # end of ParaLine",
            "      > # end of Para",
        ]
    else:
        # First Para: marker for first ref + String with first basename
        # If >1 ref, the String also contains a newline + the full second ref path
        first_ref_basename = refs[0]
        first_ref_path = f"Database/L3/{refs[0]}"

        # Build the String content for the first Para
        if len(refs) == 1:
            string_content = first_ref_basename
        else:
            # The String in the reference output carries the first basename
            # followed by a literal newline and the second full path
            # e.g. "311903\nDatabase/L3/312392"
            extra = "\n".join(f"Database/L3/{r}" for r in refs[1:])
            string_content = f"{first_ref_basename}\n{extra}"

        lines += [
            "      <Para",
            _u(counter),
            "       <PgfTag `CellLink'>",
            "       <PgfReferenced Yes>",
            "       <ParaLine",
            "        <Marker",
            "         <MType 8>",
            "         <MTypeName `Hypertext'>",
            f" <MText `openlink ../../{first_ref_path}.fm'>",
            "         <MCurrPage `1'>",
            _u(counter),
            "        > # end of Marker",
            f"        <String `{string_content}'>",
            "       > # end of ParaLine",
            "      > # end of Para",
        ]

        # Additional Paras for refs[1:]
        for ref_basename in refs[1:]:
            lines += [
                "       <Para",
                "       <ParaLine",
                "        <Marker",
                "         <MType 8>",
                "         <MTypeName `Hypertext'>",
                f" <MText `openlink ../../Database/L3/{ref_basename}.fm'>",
                "         <MCurrPage `1'>",
                "        > # end of Marker",
                _u(counter),
                f"        <String `{ref_basename}'>",
                "       > # end of ParaLine",
                "      > # end of Para",
            ]

    lines += [
        "     > # end of CellContent",
        "    > # end of Cell",
    ]
    return lines


def _cel5_lines(counter: list) -> list:
    """Cell 5: empty remarks."""
    return [
        "    <Cell",
        "     <CellContent",
        "      <Notes",
        "      > # end of Notes",
        "      <Para",
        _u(counter),
        "       <PgfTag `CellText'>",
        "       <PgfReferenced Yes>",
        "       <ParaLine",
        "        <String `'>",
        "       > # end of ParaLine",
        "      > # end of Para",
        "     > # end of CellContent",
        "    > # end of Cell",
    ]


def _row_lines(counter: list, description: str, order_code: str, refs: list) -> list:
    """Full <Row … > # end of Row for one FRU data item."""
    lines = [
        "   <Row",
        "    <RowMaxHeight  35.56001 cm>",
        "    <RowHeight  1.44639 cm>",
    ]
    lines += _cel1_lines(counter)
    lines += _cel2_lines(counter, description)
    lines += _cel3_lines(counter, order_code)
    lines += _cel4_lines(counter, refs)
    lines += _cel5_lines(counter)
    lines.append("   > # end of Row")
    return lines


def _fru_table_lines(counter: list, data_rows: list) -> list:
    """Generate the complete <Tbl … > # end of Tbl block for FRU data."""
    lines = []

    # FRU table header (TblFormat + TblH), with __UNIQUE__ substituted
    for tmpl_line in FRU_HEADER_LINES:
        if tmpl_line == "__UNIQUE__":
            lines.append(_u(counter))
        else:
            lines.append(tmpl_line)

    # TblBody is already opened by the last line of FRU_HEADER_LINES ("  <TblBody ")
    for description, order_code, refs in data_rows:
        lines += _row_lines(counter, description, order_code, refs)

    lines.append("  > # end of TblBody")
    lines.append(" > # end of Tbl")
    return lines


# ---------------------------------------------------------------------------
# Template processing
# ---------------------------------------------------------------------------

# Patterns for simple one-liner substitutions in the template
_RE_CROSS_SECTION = re.compile(r"<VariableDef `<FRU cross section\\>`'>")
_RE_DOCNR         = re.compile(r"<VariableDef `xxxxxx`'>")
_RE_PDF_TITLE     = re.compile(r"<Value `FRU list`'>")
_RE_FILENAME      = re.compile(r"Level 2 - FRU Master List")
_RE_UNIQUE        = re.compile(r"^\s*<Unique \d+>$")


def process_template(tmpl_path: str, doc_number: str, cross_section: str,
                     data_rows: list, out_path: str) -> None:
    """Read template, apply all substitutions, write output MIF."""

    counter  = [1030000]          # mutable unique-ID counter
    out_lines: list[str] = []

    with open(tmpl_path, encoding="latin-1") as f:
        tmpl_lines = f.readlines()

    i = 0
    # States for A-TextFlow injection
    in_a_textflow       = False
    a_tf_title_done     = False   # True after we emitted the Title Para close in 'A' TF
    atbl_injected       = False   # True after <ATbl 11> Para is injected
    skip_systemappl     = False   # True while absorbing the SystemAppl para

    while i < len(tmpl_lines):
        raw   = tmpl_lines[i].rstrip("\n")
        strip = raw.strip()

        # ── 1. Unique ID replacement ────────────────────────────────────────
        if _RE_UNIQUE.match(raw):
            out_lines.append(_u(counter) + "\n")
            i += 1
            continue

        # ── 2. Value substitutions ──────────────────────────────────────────
        # CrossSection VariableDef
        if strip.startswith("<VariableDef") and "<FRU cross section" in raw:
            raw = f" <VariableDef `{cross_section}'>"

        # docnr VariableDef
        elif strip.startswith("<VariableDef") and "xxxxxx" in raw:
            raw = f" <VariableDef `{doc_number}'>"

        # PDF Title Value
        elif strip.startswith("<Value") and "FRU list" in raw and "cross section" not in raw:
            raw = f"  <Value `{cross_section} FRU list'>"

        # BookComponent FileName (multiple occurrences)
        if "<FileName" in raw and "Level 2 - FRU Master List" in raw:
            raw = raw.replace("Level 2 - FRU Master List", doc_number)

        # ── 3. FRU table injection (before "> # end of Tbls") ──────────────
        if strip == "> # end of Tbls":
            # Emit FRU table then the closing tag
            for tbl_line in _fru_table_lines(counter, data_rows):
                out_lines.append(tbl_line + "\n")
            out_lines.append(raw + "\n")
            i += 1
            continue

        # ── 4. A TextFlow handling ──────────────────────────────────────────
        if strip == "<TextFlow":
            # Peek at next line for TFTag
            peek = tmpl_lines[i + 1].strip() if i + 1 < len(tmpl_lines) else ""
            if "`A'" in peek:
                in_a_textflow = True
                a_tf_title_done = False
                atbl_injected   = False
                skip_systemappl = False

        if in_a_textflow:
            # After the CrossSection/Title Para closes, inject <ATbl 11>
            if a_tf_title_done and not atbl_injected:
                if strip == "<Para":
                    # Check if next meaningful line is SystemAppl
                    j = i + 1
                    while j < len(tmpl_lines) and not tmpl_lines[j].strip():
                        j += 1
                    next_str = ""
                    for k in range(j, min(j + 5, len(tmpl_lines))):
                        if "<PgfTag" in tmpl_lines[k]:
                            next_str = tmpl_lines[k].strip()
                            break
                    if "SystemAppl" in next_str:
                        # Inject the ATbl 11 Para before absorbing SystemAppl
                        uid = _u(counter)
                        for atbl_line in [
                            "<Para",
                            uid,
                            "<PgfTag `Text(0)'>",
                            "<ParaLine",
                            "<ATbl 11>",
                            "> # end of ParaLine",
                            "> # end of Para",
                        ]:
                            out_lines.append(atbl_line + "\n")
                        atbl_injected   = True
                        skip_systemappl = True
                        # Don't emit the <Para start; skip to after this para
                        # Find the > # end of Para matching this <Para
                        depth = 1
                        i += 1
                        while i < len(tmpl_lines) and depth > 0:
                            s = tmpl_lines[i].strip()
                            if s == "<Para":
                                depth += 1
                            elif s == "> # end of Para":
                                depth -= 1
                            i += 1
                        continue

            # Detect end of the Title Para (CrossSection para close)
            if not a_tf_title_done and strip == "> # end of Para":
                # Check if we've seen CrossSection variable in preceding lines
                # Simple heuristic: check if a_tf_title_done state should flip
                # We look back in out_lines for CrossSection marker
                recent = "".join(out_lines[-30:]) if len(out_lines) >= 30 else "".join(out_lines)
                if "CrossSection" in recent and "`Title'" in recent:
                    a_tf_title_done = True

        # ── 5. Emit the (possibly modified) line ────────────────────────────
        out_lines.append(raw + "\n")
        i += 1

    with open(out_path, "w", encoding="latin-1", newline="\n") as f:
        f.writelines(out_lines)

    print(f"Written: {out_path}")
    print(f"  Lines: {len(out_lines)}")
    print(f"  Unique IDs assigned: {counter[0] - 1030000}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    xlsx_path = sys.argv[1]
    tmpl_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TMPL
    out_path  = sys.argv[3] if len(sys.argv) > 3 else None

    if out_path is None:
        base     = os.path.splitext(xlsx_path)[0]
        out_path = base + "_d1.mif"

    print(f"Excel   : {xlsx_path}")
    print(f"Template: {tmpl_path}")
    print(f"Output  : {out_path}")

    doc_number, cross_section, data_rows = read_excel(xlsx_path)
    print(f"  doc_number    = {doc_number}")
    print(f"  cross_section = {cross_section}")
    print(f"  data rows     = {len(data_rows)}")

    process_template(tmpl_path, doc_number, cross_section, data_rows, out_path)


if __name__ == "__main__":
    main()
