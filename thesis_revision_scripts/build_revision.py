#!/usr/bin/env python
"""Build JW_Thesis_revised_v7_with_insert.docx from original_copy.docx.

- Inserts the methods-contrast insert as new Section 3.6 before the
  '4. Discussion' heading.
- Applies the three per-branch qualifications.
- Insert text is parsed from reports/METHODS_CONTRAST_INSERT_v1.md so no
  manual transcription occurs. Spelling conversions to the thesis's
  demonstrated conventions (American -ize spelling; '%' for 'per cent')
  are applied through an explicit, asserted replacement list.
"""
import re, copy, json
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import parse_xml

WS = '/home/hatch/workspace/jeremy_wu_redteam'
SRC = WS + '/thesis_revision/original_copy.docx'
OUT = WS + '/thesis_revision/JW_Thesis_revised_v7_with_insert.docx'
INSERT_MD = WS + '/reports/METHODS_CONTRAST_INSERT_v1.md'

# ---------- 1. Parse the insert text out of the markdown ----------
md = open(INSERT_MD, encoding='utf-8').read()
body = md.split('## Insert text', 1)[1].split('\n---\n', 1)[0]
blocks = [b.strip() for b in re.split(r'\n\s*\n', body) if b.strip()]

heads, paras, table_rows = [], [], None
for b in blocks:
    if b.startswith('### '):
        heads.append(b[4:].strip())
    elif b.startswith('|'):
        rows = []
        for line in b.splitlines():
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(set(c) <= set('-: ') for c in cells):
                continue
            rows.append(cells)
        table_rows = rows
    else:
        paras.append(re.sub(r'\s+', ' ', b).strip())

assert heads == ['Robustness of the post hoc treatments to grid-cell selection',
                 'Results of the perturbation experiments',
                 'What the perturbation establishes about the two treatments'], heads
assert len(paras) == 10, len(paras)         # 3 methods + 5 results + 2 discussion
assert table_rows is not None and len(table_rows) == 5 and len(table_rows[0]) == 8

# Split explicitly by first words to avoid index slips:
def by_start(prefix):
    return next(p for p in paras if p.startswith(prefix))
methods_paras = [by_start('The model series used in this study'),
                 by_start('At Fergus, the experiment arose'),
                 by_start('That absorption is most of the story')]
results_paras_a = [by_start('The bounding classification is moved'),
                   by_start('The arrow presentation moves in far more places')]
h1_para = by_start('The H1 rows restate')
fisher_para = by_start("The bounding framework's own threshold statistic")
three_para = by_start('Three printed statements beyond the p-value')
discussion_paras = [by_start('The conclusion these experiments support'),
                    by_start('The scope of these conclusions is the scope')]

# ---------- 2. Spelling / style conversions (asserted, listed for the change note) ----------
CONVERSIONS = [
    ('their homogenisation', 'their homogenization'),
    ('reviewed-breaks homogenisation layer', 'reviewed-breaks homogenization layer'),
    ('between about 51 and 60 per cent of days', 'between about 51% and 60% of days'),
    ('by about 1 to 7 per cent of the ten-model spread', 'by about 1% to 7% of the ten-model spread'),
]
def convert(p):
    for old, new in CONVERSIONS:
        if old in p:
            assert p.count(old) == 1, (old, p.count(old))
            p = p.replace(old, new)
            converted.append((old, new))
    return p

converted = []
methods_paras    = [convert(p) for p in methods_paras]
results_paras_a  = [convert(p) for p in results_paras_a]
h1_para          = convert(h1_para)
fisher_para      = convert(fisher_para)
three_para       = convert(three_para)
discussion_paras = [convert(p) for p in discussion_paras]
all_insert_paras = methods_paras + results_paras_a + [h1_para, fisher_para, three_para] + discussion_paras
for old, new in CONVERSIONS:
    assert (old, new) in converted, f'conversion not applied: {old}'
joined = ' '.join(all_insert_paras)
for pat in [r'per cent', r'homogenisation', r'behaviour', r'summaris\w+', r'labelled', r'characteris\w+', r'organis\w+']:
    assert not re.search(pat, joined), (pat, re.search(pat, joined).group(0))
print('conversions applied:', converted)

# ---------- 3. Open the document and apply the three qualifications ----------
d = Document(SRC)

def find_para(fragment):
    hits = [p for p in d.paragraphs if fragment in p.text]
    assert len(hits) == 1, (fragment, len(hits))
    return hits[0]

def append_text(par, text):
    last = par.runs[-1]
    last.text = last.text + text

def insert_after_sentence(par, sentence_end, text):
    """Insert text immediately after the first occurrence of sentence_end."""
    full = ''.join(r.text for r in par.runs)
    pos = full.index(sentence_end) + len(sentence_end)
    acc = 0
    for r in par.runs:
        if acc + len(r.text) >= pos:
            off = pos - acc
            r.text = r.text[:off] + text + r.text[off:]
            return
        acc += len(r.text)
    raise AssertionError('offset not found')

record = {}

# Q1 - precipitation reference-model margin (para in Sec 3.1.3, claim V7-C286)
p1 = find_para('against 55 for ACCESS-ESM1-5')
s1_before = ("Summed across the three stations, BCC-CSM2-MR achieved the highest "
             "precipitation score in the basin (57 of 78 passes, against 55 for "
             "ACCESS-ESM1-5, CanESM5 and EC-Earth3-Veg), scoring 20/26 at London, "
             "20/26 at Fergus and 17/26 at Harrow.")
assert s1_before in p1.text
q1 = (" Under the Harrow grid-cell substitution reported in Section 3.6, "
      "BCC-CSM2-MR's summed total remains 57 of 78, but the nearest total "
      "rises to 57, and the selection survives only through the ordering rule "
      "applied to the tie.")
append_text(p1, q1)
record['Q1'] = (s1_before, s1_before + q1)

# Q2 - Far Future consensus range (para in Sec 3.2.2, claim V7-C397)
p2 = find_para('of 44 indices per station')
s2_before = ("Inter-model agreement reached near-total convergence across the basin, "
             "with 82%\u201384% of all indices (36\u201337 of 44 indices per station) "
             "demonstrating strong ensemble consensus.")
assert s2_before in p2.text, p2.text[:400]
q2 = (" Under the Harrow grid-cell substitution reported in Section 3.6, the "
      "lower end of the Far-Future range falls to 35 of 44 indices.")
insert_after_sentence(p2, 'demonstrating strong ensemble consensus.', q2)
record['Q2'] = (s2_before, s2_before + q2)

# Q3 - CDD bounded at all three stations (para in Sec 4.1, claim V7-C594)
p3 = find_para('annual CDD change was bounded at all three stations')
s3_before = ("In this study the annual CDD change was bounded at all three stations, "
             "but the distributional test still failed in half of the model-period "
             "cells at Fergus, so the deficiency appears in the absolute length of "
             "dry spells rather than in their historical change.")
assert s3_before in p3.text
q3 = (" The bounded status of the Fergus CDD change is specific to the thesis "
      "cell: on the station cell one grid step to the west, the Fergus annual "
      "CDD change is unbounded (Section 3.6).")
append_text(p3, q3)
record['Q3'] = (s3_before, s3_before + q3)

json.dump(record, open(WS + '/thesis_revision/qualifications.json', 'w'), indent=1, ensure_ascii=False)

# ---------- 4. Build and insert Section 3.6 before '4. Discussion' ----------
anchor = find_para('4. Discussion')
assert anchor.style.name == 'Heading 1'
BODY = 'font-claude-response-body'

def new_para(text, style):
    p = d.add_paragraph(text, style=style)
    anchor._p.addprevious(p._p)
    return p

CAPTION = ("Table 8. Sensitivity of the bounding and arrow post hoc treatments to "
           "grid-cell substitution at Fergus and Harrow, restated at a matched level "
           "of one output per index per method component. For the bounding method, "
           "the outputs are the envelope classification of the observed change and "
           "the pooled Overall Shift label of the index, the label taken under both "
           "the executed pooling and the models-only pooling. For the arrow method, "
           "the output for each of the three printed contrasts is the pair formed by "
           "the sign of the pooled-ensemble median change and the majority direction "
           "of the ten models' median changes. The H1 rows restate the comparison "
           "on the reviewed-breaks homogenization layer.")

new_para('3.6 Robustness of the Post Hoc Treatments to Grid-Cell Selection', 'Heading 2')
for t in methods_paras:
    new_para(t, BODY)
new_para('3.6.1 Results of the Perturbation Experiments', 'Heading 3')
for t in results_paras_a:
    new_para(t, BODY)
new_para(CAPTION, 'Caption')

tbl = d.add_table(rows=len(table_rows), cols=8)
anchor._p.addprevious(tbl._tbl)
tbl.style = 'Normal Table'
tblPr = tbl._tbl.tblPr
# set width + look to mirror Table 6
from docx.oxml.ns import nsdecls
tblW = parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>')
tblLook = parse_xml(f'<w:tblLook {nsdecls("w")} w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>')
for el in list(tblPr):
    if el.tag in (qn('w:tblW'), qn('w:tblLook')):
        tblPr.remove(el)
tblPr.append(tblW); tblPr.append(tblLook)
for ri, rowvals in enumerate(table_rows):
    for ci, val in enumerate(rowvals):
        cell = tbl.cell(ri, ci)
        cell.text = ''
        p = cell.paragraphs[0]
        p.style = d.styles['Normal']
        run = p.add_run(val)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9)
        if ri == 0:
            run.bold = True
        rPr = run._r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rPr.append(rFonts)
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rFonts.set(qn(attr), 'Times New Roman')

new_para('', BODY)
for t in (h1_para, fisher_para, three_para):
    new_para(t, BODY)
new_para('3.6.2 What the Perturbation Establishes about the Two Treatments', 'Heading 3')
for t in discussion_paras:
    new_para(t, BODY)

d.save(OUT)
print('saved', OUT)
