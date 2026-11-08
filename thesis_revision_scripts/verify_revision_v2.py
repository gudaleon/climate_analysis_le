#!/usr/bin/env python
"""Integrity verification for JW_Thesis_revised_v7_with_insert_v2.docx."""
import zipfile, json, hashlib
from docx import Document

WS = '/home/hatch/workspace/jeremy_wu_redteam'
ORIG = WS + '/thesis_revision_v2/original_copy.docx'
REV  = WS + '/thesis_revision_v2/JW_Thesis_revised_v7_with_insert_v2.docx'
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

do, orig = walk(ORIG)
dr, rev = walk(REV)
print('paragraphs: original', len(orig), '| revised', len(rev), '| diff', len(rev) - len(orig))
print('tables: original', len(do.tables), '| revised', len(dr.tables))
print('inline shapes: original', len(do.inline_shapes), '| revised', len(dr.inline_shapes))

i0 = next(i for i, t in enumerate(rev) if t.startswith('3.6 Robustness'))
i1 = next(i for i, t in enumerate(rev) if t.strip() == '4. Discussion')
block = rev[i0:i1]
print('inserted block paragraphs:', len(block))
# The block was inserted immediately before the original's '4. Discussion'
# paragraph, so the revised prefix [0:i0] pairs with orig[0:i0] and the
# revised tail [i1:] pairs with orig[i0:]. Compare both segments pairwise.
pre_o, pre_r = orig[:i0], rev[:i0]
tail_o, tail_r = orig[i0:], rev[i1:]
assert len(pre_o) == len(pre_r) and len(tail_o) == len(tail_r)
assert tail_o[0].strip() == '4. Discussion' and tail_r[0].strip() == '4. Discussion'
diffs = [(a, b) for a, b in zip(pre_o, pre_r) if a != b]
diffs += [(a, b) for a, b in zip(tail_o, tail_r) if a != b]
print('changed paragraphs outside the inserted block:', len(diffs))
assert len(rev) - len(block) - len(diffs) == len(orig) - len(diffs)

rec = json.load(open(WS + '/thesis_revision_v2/qualifications_v2.json'))
for k, (before, after) in rec.items():
    ok = any(before in a and after in b for a, b in diffs)
    print(k, 'before/after pair found in a changed paragraph:', ok)

for path in (ORIG, REV):
    z = zipfile.ZipFile(path)
    media = [n for n in z.namelist() if n.startswith('word/media/')]
    print(path.split('/')[-1], 'zip testzip:', z.testzip(), '| media files:', len(media),
          '| bytes:', __import__('os').path.getsize(path))
print('md5 mirror original :', md5(MIRROR))
print('md5 working copy    :', md5(ORIG))
print('md5 build-1 output (untouched record):', md5(BUILD1))
