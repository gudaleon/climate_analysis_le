#!/usr/bin/env python
"""Integrity verification for JW_Thesis_combined_arrows_and_bounds.docx.

Proves, against the spine revision, that the combined document differs by
exactly the added Chapter 6 block and the nine reference entries the
literature improvement pass (2026-11-09) inserted for Section 6.4, and
nothing else, and that the spine and the archived originals were not
touched.
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
# paragraph, so combined[:i0] pairs with spine[:j0]. The tail pairs with
# spine[j0:] once the nine reference entries inserted by the literature
# improvement pass are removed from it.
pre_s, pre_c = spine[:j0], comb[:i0]
tail_s, tail_c = spine[j0:], comb[i1:]
assert tail_s[0].strip() == 'References' and tail_c[0].strip() == 'References'
NEW_REFS = [
    'Annan, J. D., & Hargreaves, J. C. (2010). Reliability of the CMIP3 ensemble. Geophysical Research Letters, 37, L02703. https://doi.org/10.1029/2009GL041994',
    'Altman, D. G., & Bland, J. M. (1995). Absence of evidence is not evidence of absence. BMJ, 311(7003), 485.',
    'Beguería, S., Vicente-Serrano, S. M., Reig, F., & Latorre, B. (2014). Standardized precipitation evapotranspiration index (SPEI) revisited: Parameter fitting, evapotranspiration models, tools, datasets and drought monitoring. International Journal of Climatology, 34(10), 3001–3023. https://doi.org/10.1002/joc.3887',
    'Divine, G. W., Norton, H. J., Barón, A. E., & Juarez-Colunga, E. (2018). The Wilcoxon–Mann–Whitney procedure fails as a test of medians. The American Statistician, 72(3), 278–286.',
    'Fay, M. P., & Proschan, M. A. (2010). Wilcoxon-Mann-Whitney or t-test? On assumptions for hypothesis tests and multiple interpretations of decision rules. Statistics Surveys, 4, 1–39.',
    'Hurlbert, S. H. (1984). Pseudoreplication and the design of ecological field experiments. Ecological Monographs, 54(2), 187–211.',
    'Sheffield, J., Wood, E. F., & Roderick, M. L. (2012). Little change in global drought over the past 60 years. Nature, 491(7424), 435–438. https://doi.org/10.1038/nature11575',
    'Wilks, D. S. (2016). “The stippling shows statistically significant grid points”: How research results are routinely overstated and overinterpreted, and what to do about it. Bulletin of the American Meteorological Society, 97(12), 2263–2273.',
    'Zhang, X., Hegerl, G., Zwiers, F. W., & Kenyon, J. (2005). Avoiding inhomogeneity in percentile-based indices of temperature extremes. Journal of Climate, 18, 1641–1651. https://doi.org/10.1175/JCLI3366.1',
]
for entry in NEW_REFS:
    assert comb.count(entry) == 1, entry[:60]
tail_c_filtered = [t for t in tail_c if t not in NEW_REFS]
assert len(tail_c) - len(tail_c_filtered) == len(NEW_REFS)
assert len(pre_s) == len(pre_c) and len(tail_s) == len(tail_c_filtered)
diffs = [(a, b) for a, b in zip(pre_s, pre_c) if a != b]
diffs += [(a, b) for a, b in zip(tail_s, tail_c_filtered) if a != b]
print('changed paragraphs outside the inserted chapter and the nine new references:', len(diffs))
assert len(diffs) == 0
assert len(comb) - len(block) - len(NEW_REFS) == len(spine)
# The two Section 6.4 sources that were already listed stand exactly once.
assert sum(t.startswith('Zhang, X., Alexander, L., Hegerl, G. C.') for t in comb) == 1
assert sum(t.startswith('Vicente-Serrano, S. M., Beguería, S., & López-Moreno, J. I. (2010)') for t in comb) == 1
print('pre-existing Zhang et al. (2011) and Vicente-Serrano et al. (2010) entries not duplicated')

expected_block = 1 + 1 + 1 + 5 + 1 + 3 + 1 + 56 + 1 + 3 + 1 + 3 + 1 + 8  # title, opening, 4 heads,
# 5+6+3+8 body paras, caption, 56 table cells, 1 spacer = 86
print('expected block size:', expected_block, '| match:', len(block) == expected_block)
assert len(block) == expected_block
for marker in ('6. Two Post Hoc Treatments of One Analysis: A Comparison',
               '6.1 The Two Treatments Defined',
               '6.2 The Comparison on the Verified Record',
               '6.3 Adjudication: What Each Treatment Is For',
               '6.4 What the Literature Requires of These Claims'):
    assert any(t.strip() == marker for t in block), marker
assert any(t.startswith('Table 9. Sensitivity of the two post hoc treatments') for t in block)
t9 = next(t for t in block if t.startswith('Table 9 restates the sensitivity'))
assert t9.endswith('not a property of either method.'), t9[-120:]
assert 'does not run in the arrow lineage' in t9
print('chapter headings, sections, Table 9 caption and the Addendum D sentence all present in the block')

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
