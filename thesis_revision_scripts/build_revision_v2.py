#!/usr/bin/env python
"""Build JW_Thesis_revised_v7_with_insert_v2.docx from original_copy.docx
(a fresh copy of the archived v7 clean thesis in the Drive mirror).

- Inserts METHODS_CONTRAST_INSERT_v2 (three-station form) as new
  Section 3.6 before the '4. Discussion' heading.
- Applies the five per-branch qualifications of the re-derived set.
- Insert text is parsed from reports/METHODS_CONTRAST_INSERT_v2.md so no
  manual transcription occurs. Spelling conversions to the thesis's
  demonstrated conventions (American -ize spelling; '%' for 'per cent')
  are applied through an explicit, asserted replacement list.
"""
import re, json
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

WS = '/home/hatch/workspace/jeremy_wu_redteam'
SRC = WS + '/thesis_revision_v2/original_copy.docx'
OUT = WS + '/thesis_revision_v2/JW_Thesis_revised_v7_with_insert_v2.docx'
INSERT_MD = WS + '/reports/METHODS_CONTRAST_INSERT_v2.md'

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
assert len(paras) == 11, len(paras)         # 4 methods + 5 results + 2 discussion
assert table_rows is not None and len(table_rows) == 7 and len(table_rows[0]) == 8

def by_start(prefix):
    return next(p for p in paras if p.startswith(prefix))

methods_paras = [by_start('The model series used in this study'),
                 by_start('At Fergus, the experiment arose'),
                 by_start('At London, as at Harrow'),
                 by_start('That absorption is most of the story')]
results_paras_a = [by_start('The bounding classification is moved'),
                   by_start('The arrow presentation moves in far more places')]
h1_para = by_start('The H1 rows restate')
fisher_para = by_start("The bounding framework's own threshold statistic")
statements_para = by_start('Five printed statements beyond the p-value')
discussion_paras = [by_start('The conclusion these experiments support'),
                    by_start('The scope of these conclusions is the scope')]

# ---------- 2. Spelling / style conversions (asserted, listed for the change note) ----------
CONVERSIONS = [
    ('their homogenisation', 'their homogenization'),
    ('reviewed-breaks homogenisation layer', 'reviewed-breaks homogenization layer'),
    ('a different homogenisation decision', 'a different homogenization decision'),
    ('between about 51 and 60 per cent of days', 'between about 51% and 60% of days'),
    ('by about 1 to 7.5 per cent of the ten-model spread', 'by about 1% to 7.5% of the ten-model spread'),
]
converted = []
def convert(p):
    for old, new in CONVERSIONS:
        if old in p:
            assert p.count(old) == 1, (old, p.count(old))
            p = p.replace(old, new)
            converted.append((old, new))
    return p

methods_paras    = [convert(p) for p in methods_paras]
results_paras_a  = [convert(p) for p in results_paras_a]
h1_para          = convert(h1_para)
fisher_para      = convert(fisher_para)
statements_para  = convert(statements_para)
discussion_paras = [convert(p) for p in discussion_paras]
all_insert_paras = methods_paras + results_paras_a + [h1_para, fisher_para, statements_para] + discussion_paras
for old, new in CONVERSIONS:
    assert (old, new) in converted, f'conversion not applied: {old}'
joined = ' '.join(all_insert_paras)
for pat in [r'per cent', r'homogenisation', r'behaviour', r'summaris\w+', r'labelled', r'characteris\w+', r'organis\w+']:
    assert not re.search(pat, joined), (pat, re.search(pat, joined).group(0))
print('conversions applied:', converted)

# ---------- 3. Open the document and apply the five qualifications ----------
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
q1 = (" Under the grid-cell substitutions reported in Section 3.6, that margin "
      "of two passes does not survive at any station: with Fergus on its station "
      "cell or London on its perturbed cell, the summed total is 56 of 78 and "
      "the margin is one pass, and with Harrow on its perturbed cell the total "
      "remains 57 of 78 but the nearest total rises to 57, so the selection "
      "survives only through the ordering rule applied to the tie.")
append_text(p1, q1)
record['Q1'] = (s1_before, s1_before + q1)

# Q2 - Far Future consensus range (para in Sec 3.2.2, claim V7-C397)
p2 = find_para('of 44 indices per station')
s2_before = ("Inter-model agreement reached near-total convergence across the basin, "
             "with 82%\u201384% of all indices (36\u201337 of 44 indices per station) "
             "demonstrating strong ensemble consensus.")
assert s2_before in p2.text, p2.text[:400]
q2 = (" Under the Harrow grid-cell substitution reported in Section 3.6, the "
      "lower end of the Far-Future range falls to 35 of 44 indices; the range "
      "is unchanged under the Fergus and London substitutions.")
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
      "CDD change is unbounded (Section 3.6); the statement stands under the "
      "Harrow and London substitutions.")
append_text(p3, q3)
record['Q3'] = (s3_before, s3_before + q3)

# Q4 - London temperature reference-model selection (para in Sec 3.1.4, claim V7-C289)
p4 = find_para('highest cumulative pass total')
s4_before = ("For temperature extremes, the reference model at each station was "
             "the model with the highest cumulative pass total: NorESM2-LM at "
             "London (52/62 passes, ahead of EC-Earth3-Veg and MIROC-ES2L at 50) "
             "and EC-Earth3-Veg at Fergus (56/62, level with BCC-CSM2-MR and "
             "retained because it passed in both periods for more indices, 27 "
             "against 26) and at Harrow (44/62).")
assert s4_before in p4.text, p4.text[:600]
q4 = (" The London selection is specific to the thesis cell: under the London "
      "grid-cell substitution reported in Section 3.6, EC-Earth3-Veg scores 52 "
      "of 62 at London and NorESM2-LM 50, so the perturbed branch selects "
      "EC-Earth3-Veg as London's temperature reference model, and the monthly "
      "temperature analysis at London is then computed on that model rather "
      "than on NorESM2-LM.")
insert_after_sentence(p4, 'and at Harrow (44/62).', q4)
record['Q4'] = (s4_before, s4_before + q4)

# Q5 - Harrow most often bounded (para in Sec 4.1, claim V7-C589)
p5 = find_para('most often bounded by the ensemble')
s5_before = ("Harrow illustrates the distinction at station scale: its temperature "
             "skill was the lowest of the three stations, yet its observed changes "
             "were the most often bounded by the ensemble (88.6%).")
assert s5_before in p5.text, p5.text[:600]
q5 = (" That standing holds on the thesis cells alone: under the grid-cell "
      "substitutions reported in Section 3.6, Fergus and Harrow tie at 39 of 44 "
      "cases when Fergus is on its station cell, the three stations tie at 38 "
      "of 44 when Harrow is on its perturbed cell, on which Harrow's own share "
      "is 86.4%, and London and Harrow tie at 39 of 44 when London is on its "
      "perturbed cell.")
insert_after_sentence(p5, 'most often bounded by the ensemble (88.6%).', q5)
record['Q5'] = (s5_before, s5_before + q5)

json.dump(record, open(WS + '/thesis_revision_v2/qualifications_v2.json', 'w'), indent=1, ensure_ascii=False)

# ---------- 4. Build and insert Section 3.6 before '4. Discussion' ----------
anchor = find_para('4. Discussion')
assert anchor.style.name == 'Heading 1'
BODY = 'font-claude-response-body'

def new_para(text, style):
    p = d.add_paragraph(text, style=style)
    anchor._p.addprevious(p._p)
    return p

CAPTION = ("Table 8. Sensitivity of the bounding and arrow post hoc treatments to "
           "grid-cell substitution at Fergus, Harrow and London, restated at a matched level "
           "of one output per index per method component. For the bounding method, "
           "the outputs are the envelope classification of the observed change and "
           "the pooled Overall Shift label of the index, the label taken under both "
           "the executed pooling and the models-only pooling. For the arrow method, "
           "the output for each of the three printed contrasts is the pair formed by "
           "the sign of the pooled-ensemble median change and the majority direction "
           "of the ten models' median changes. The H1 rows restate the comparison "
           "on the reviewed-breaks homogenization layer; at London every count is "
           "identical on the two layers.")

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
for t in (h1_para, fisher_para, statements_para):
    new_para(t, BODY)
new_para('3.6.2 What the Perturbation Establishes about the Two Treatments', 'Heading 3')
for t in discussion_paras:
    new_para(t, BODY)

d.save(OUT)
print('saved', OUT)
