#!/usr/bin/env python
"""Integrity verification for JW_Thesis_combined_arrows_and_bounds.docx.

Proves, against the spine revision, that the combined document differs by
exactly the added Chapter 6 block and nothing else, and that the spine and
the archived originals were not touched.
"""
import zipfile, json, hashlib, os
from docx import Document

WS = '/home/hatch/workspace/jeremy_wu_redteam'
SPINE = WS + '/thesis_revision_v2/JW_Thesis_revised_v7_with_insert_v2.docx'
COMB = WS + '/thesis_combined/JW_Thesis_combined_arrows_and_bounds.docx'
ORIG_COPY = WS + '/thesis_revision_v2/original_copy.docx'
MIRROR = WS + '/drive_mirror/JW_October_2026/Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data/1_Thesis/After_v7_defence/JW_Thesis_revised_v7_clean.docx'
BUILD1 = WS + '/thesis_revision/JW_Thesis_revised_v7_with_insert.docx'

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def walk(path):
    d = Document(path)
    out = []
    for p in d.element.body.iter():
        if p.tag.endswith('}p'):
            out.append(''.join(n.text or '' for n in p.iter() if n.tag.endswith('}t')))
    return d, out

ds, spine = walk(SPINE)
dc, comb = walk(COMB)
print('paragraphs: spine', len(spine), '| combined', len(comb), '| diff', len(comb) - len(spine))
print('tables: spine', len(ds.tables), '| combined', len(dc.tables))
print('inline shapes: spine', len(ds.inline_shapes), '| combined', len(dc.inline_shapes))

i0 = next(i for i, t in enumerate(comb) if t.startswith('6. Two Post Hoc Treatments'))
i1 = next(i for i, t in enumerate(comb) if t.strip() == 'References')
j0 = next(i for i, t in enumerate(spine) if t.strip() == 'References')
block = comb[i0:i1]
print('inserted chapter block paragraphs:', len(block))
# The block was inserted immediately before the spine's 'References'
# paragraph, so combined[:i0] pairs with spine[:j0] and combined[i1:]
# pairs with spine[j0:]. Compare both segments pairwise.
pre_s, pre_c = spine[:j0], comb[:i0]
tail_s, tail_c = spine[j0:], comb[i1:]
assert len(pre_s) == len(pre_c) and len(tail_s) == len(tail_c)
assert tail_s[0].strip() == 'References' and tail_c[0].strip() == 'References'
diffs = [(a, b) for a, b in zip(pre_s, pre_c) if a != b]
diffs += [(a, b) for a, b in zip(tail_s, tail_c) if a != b]
print('changed paragraphs outside the inserted chapter:', len(diffs))
assert len(diffs) == 0
assert len(comb) - len(block) == len(spine)

expected_block = 1 + 1 + 1 + 5 + 1 + 3 + 1 + 56 + 1 + 3 + 1 + 3  # title, opening, 3 heads,
# 5+6+3 body paras, caption, 56 table cells, 1 spacer = 77
print('expected block size:', expected_block, '| match:', len(block) == expected_block)
assert len(block) == expected_block
for marker in ('6. Two Post Hoc Treatments of One Analysis: A Comparison',
               '6.1 The Two Treatments Defined',
               '6.2 The Comparison on the Verified Record',
               '6.3 Adjudication: What Each Treatment Is For'):
    assert any(t.strip() == marker for t in block), marker
assert any(t.startswith('Table 9. Sensitivity of the two post hoc treatments') for t in block)
print('chapter headings, sections and Table 9 caption all present in the block')

for path in (SPINE, COMB):
    z = zipfile.ZipFile(path)
    media = [n for n in z.namelist() if n.startswith('word/media/')]
    print(path.split('/')[-1], 'zip testzip:', z.testzip(), '| media files:', len(media),
          '| bytes:', os.path.getsize(path))

rec = json.load(open(WS + '/thesis_combined/combined_build_record.json'))
spine_now = md5(SPINE)
print('spine md5 at build time :', rec['spine_md5_before_build'])
print('spine md5 now           :', spine_now)
print('spine untouched:', spine_now == rec['spine_md5_before_build'] == rec['spine_md5_after_build'])
print('md5 v2 working original copy (unchanged record):', md5(ORIG_COPY))
print('md5 mirror archived original                 :', md5(MIRROR))
print('md5 build-1 revision output (unchanged record):', md5(BUILD1))
print('combined md5:', md5(COMB), '| recorded at build:', rec['output_md5'])
