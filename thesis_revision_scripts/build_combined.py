#!/usr/bin/env python
"""Build JW_Thesis_combined_arrows_and_bounds.docx from the spine revision
thesis_revision_v2/JW_Thesis_revised_v7_with_insert_v2.docx (never modified).

- Adds exactly one element: Chapter 6, "Two Post Hoc Treatments of One
  Analysis: A Comparison", inserted immediately before the 'References'
  Heading 1, i.e. after the document's final chapter (5. Conclusion).
- Chapter text is parsed from thesis_combined/chapter_text.md so no manual
  transcription occurs. The chapter carries the stability table as Table 9,
  the document's next table number (Table 8 is the Section 3.6 table).
- Records the spine's md5 before the build in combined_build_record.json
  so verify_combined.py can prove the spine was not touched.
"""
import re, json, hashlib, shutil, os
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

WS = '/home/hatch/workspace/jeremy_wu_redteam'
SPINE = WS + '/thesis_revision_v2/JW_Thesis_revised_v7_with_insert_v2.docx'
OUT = WS + '/thesis_combined/JW_Thesis_combined_arrows_and_bounds.docx'
CHAPTER_MD = WS + '/thesis_combined/chapter_text.md'

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

spine_md5_before = md5(SPINE)

# ---------- 1. Parse the chapter text out of the markdown ----------
md = open(CHAPTER_MD, encoding='utf-8').read()
blocks = [b.strip() for b in re.split(r'\n\s*\n', md) if b.strip()]

chapter_title, section_heads, paras, caption, table_rows = None, [], [], None, None
for b in blocks:
    if b.startswith('## '):
        section_heads.append(b[3:].strip())
    elif b.startswith('# '):
        chapter_title = b[2:].strip()
    elif b.startswith('CAPTION: '):
        caption = b[len('CAPTION: '):].strip()
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

assert chapter_title == '6. Two Post Hoc Treatments of One Analysis: A Comparison', chapter_title
assert section_heads == ['6.1 The Two Treatments Defined',
                         '6.2 The Comparison on the Verified Record',
                         '6.3 Adjudication: What Each Treatment Is For'], section_heads
assert len(paras) == 15, len(paras)      # 1 opening + 5 (6.1) + 6 (6.2) + 3 (6.3)
assert caption is not None and caption.startswith('Table 9.'), caption[:40]
assert table_rows is not None and len(table_rows) == 7 and len(table_rows[0]) == 8

def by_start(prefix):
    return next(p for p in paras if p.startswith(prefix))

opening      = by_start('This thesis is presented in two versions')
s61_paras    = [by_start('Both treatments stand on the same first pass'),
                by_start('(Correction: the printed description of the homogenization'),
                by_start('Method A, the arrow treatment'),
                by_start('Method B, the bounding treatment'),
                by_start('The two treatments do not produce comparable counts')]
s62_before   = [by_start('On the thesis cells the two treatments agree'),
                by_start('Under each grid-cell substitution the shared within-range count'),
                by_start('Table 9 restates the sensitivity')]
s62_after    = [by_start("The bounding treatment's own threshold statistic"),
                by_start('What distinguishes the treatments is the kind of output'),
                by_start('One further finding about the arrow layer')]
s63_paras    = [by_start('On this record, and at no greater strength'),
                by_start('The comparison cannot adjudicate more'),
                by_start('For a decision-maker, the division of labour')]
assert len(s61_paras) == 5 and len(s62_before) == 3 and len(s62_after) == 3 and len(s63_paras) == 3

# Spelling/style conventions demonstrated by the thesis (as asserted in the v2 build)
joined = ' '.join(paras + [caption])
for pat in [r'per cent', r'homogenisation', r'behaviour', r'summaris\w+', r'labelled', r'characteris\w+', r'organis\w+']:
    assert not re.search(pat, joined), (pat, re.search(pat, joined).group(0))
print('chapter parsed: title +', len(section_heads), 'sections,', len(paras), 'body paragraphs, table',
      len(table_rows), 'x', len(table_rows[0]))

# ---------- 2. Open a copy of the spine and insert Chapter 6 ----------
shutil.copyfile(SPINE, OUT)
d = Document(OUT)

anchors = [p for p in d.paragraphs if p.style.name == 'Heading 1' and p.text.strip() == 'References']
assert len(anchors) == 1, len(anchors)
anchor = anchors[0]
BODY = 'font-claude-response-body'

def new_para(text, style):
    p = d.add_paragraph(text, style=style)
    anchor._p.addprevious(p._p)
    return p

new_para(chapter_title, 'Heading 1')
new_para(opening, BODY)
new_para(section_heads[0], 'Heading 2')
for t in s61_paras:
    new_para(t, BODY)
new_para(section_heads[1], 'Heading 2')
for t in s62_before:
    new_para(t, BODY)
new_para(caption, 'Caption')

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
for t in s62_after:
    new_para(t, BODY)
new_para(section_heads[2], 'Heading 2')
for t in s63_paras:
    new_para(t, BODY)

d.save(OUT)

record = {
    'spine': SPINE,
    'spine_md5_before_build': spine_md5_before,
    'spine_md5_after_build': md5(SPINE),
    'output': OUT,
    'output_md5': md5(OUT),
    'output_bytes': os.path.getsize(OUT),
    'chapter': chapter_title,
    'sections': section_heads,
    'body_paragraphs': len(paras),
    'table_caption': caption,
    'table_rows': len(table_rows),
    'table_cols': len(table_rows[0]),
}
json.dump(record, open(WS + '/thesis_combined/combined_build_record.json', 'w'), indent=1, ensure_ascii=False)
print('saved', OUT)
print('spine untouched by build:', spine_md5_before == record['spine_md5_after_build'])
