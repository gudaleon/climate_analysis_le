"""Addendum C: extract every number the report needs from the saved tables pickles, the Stage 3 matched
file and the claim outputs, and write a compact text summary to out_addC/extract_summary.txt."""
import pickle, numpy as np, pandas as pd
pd.set_option('display.width', 250)
OUT = []
def w(s=''): OUT.append(str(s))

# ---------- Stage 3 matched summaries, all stations and layers ----------
s3 = pd.read_csv('out_addC/stage3_matched.csv')
w('=== STAGE 3 MATCHED SUMMARIES ===')
for (lay, st), g in s3.groupby(['layer', 'station']):
    env = g[g.output == 'env']; c1 = g[g.output == 'c1']; c1m = g[g.output == 'c1m']
    arr = g[g.output.isin(['arr_P', 'arr_N', 'arr_F'])]
    bnd_idx = sorted(set(g[g.output.isin(['env', 'c1']) & (g.changed)].index))
    bnd_rows = g[g.output.isin(['env', 'c1']) & (g.changed)]
    arr_rows = arr[arr.changed]
    sign_moves = arr_rows[arr_rows.apply(lambda r: r['T'].split('|')[0] != r['other'].split('|')[0], axis=1)]
    w(f"{lay} {st}: env {int(env.changed.sum())}/44, c1 {int(c1.changed.sum())}/44, c1m {int(c1m.changed.sum())}/44, "
      f"bounding {len(bnd_rows)}/88 over {bnd_rows['index'].nunique()} indices; arrows {len(arr_rows)}/132 over {arr_rows['index'].nunique()} indices; "
      f"ensemble-sign movements {len(sign_moves)}: " + ', '.join(f"{r['index']} {r['output']} {r['T']}->{r['other']}" for r in sign_moves.to_dict('records')))
    w(f"   env changes: " + '; '.join(f"{r['index']}: {r['T']} -> {r['other']}" for r in env[env.changed].to_dict('records')))
    w(f"   c1 changes: " + '; '.join(f"{r['index']}: {r['T']} -> {r['other']}" for r in c1[c1.changed].to_dict('records')))
    w(f"   c1m changes: " + '; '.join(f"{r['index']}: {r['T']} -> {r['other']}" for r in c1m[c1m.changed].to_dict('records')))
    w(f"   arrow changes: " + '; '.join(f"{r['index']} {r['output']}: {r['T']} -> {r['other']}" for r in arr_rows.to_dict('records')))

for LAY in ['AUTHORS_v4', 'H1_reviewed']:
    t = pickle.load(open(f'out_addC/tables_{LAY}.pkl', 'rb'))
    w(f"\n=== LAYER {LAY} ===")
    aT, aP = t['agg']['T'], t['agg']['P']
    w(f"AGG bounded: T {aT['bounded']} P {aP['bounded']} | per station T {aT['per_station']} P {aP['per_station']}")
    w(f"AGG bounded at all 3 stations (per index): T {aT['bounded_all3']} P {aP['bounded_all3']}")
    w(f"AGG London env by group: T temp {aT['london_T']} precip {aT['london_P']} | P temp {aP['london_T']} precip {aP['london_P']}")
    w(f"AGG c613 counts: T {aT['c613']} | P {aP['c613']}")
    w(f"AGG cv7 counts: T {aT['cv7']} | P {aP['cv7']}")
    w(f"SKILL >=10of20: T {aT['skill']} | P {aP['skill']}")
    w(f"REFS: T {aT['refs']} | P {aP['refs']}")
    w(f"CONS strong London: " + '; '.join(f"{k}: T {aT['cons'][k]} P {aP['cons'][k]}" for k in aT['cons'] if k.startswith('London')))
    w("D1 process records:")
    dT = {r['group']: r for r in aT['d1']}; dP = {r['group']: r for r in aP['d1']}
    for gname in dT:
        w(f"   {gname}: T coh_HP {dT[gname]['coh_HP']} coh_N {dT[gname]['coh_N']} coh_F {dT[gname]['coh_F']} bounded {dT[gname]['bounded']} sign_rev {dT[gname]['sign_rev']} conf {dT[gname]['conf']}"
          f" || P coh_HP {dP[gname]['coh_HP']} coh_N {dP[gname]['coh_N']} coh_F {dP[gname]['coh_F']} bounded {dP[gname]['bounded']} sign_rev {dP[gname]['sign_rev']} conf {dP[gname]['conf']}")
    w("TEST1 (London): rows are models; T branch then P branch")
    w("T:\n" + t['t1T'].to_string())
    w("P:\n" + t['t1P'].to_string())
    w(f"Test1 London column sums: T all_tot {int(t['t1T'].all_tot.sum())} (T {int(t['t1T'].T_tot.sum())}, P {int(t['t1T'].P_tot.sum())}) | P all_tot {int(t['t1P'].all_tot.sum())} (T {int(t['t1P'].T_tot.sum())}, P {int(t['t1P'].P_tot.sum())})")
    w(f"basinP London column (precip-group passes per model): T {t['bT']['London'].to_dict()} | P {t['bP']['London'].to_dict()}")
    w(f"basinP Fergus/Harrow London-perturbed restatement: Fergus T {int(t['bT']['Fergus'].sum())} P {int(t['bP']['Fergus'].sum())}; Harrow T {int(t['bT']['Harrow'].sum())} P {int(t['bP']['Harrow'].sum())}")
    # envelope, London, all 44
    eT, eP = t['eT'], t['eP']
    def margin(r):
        if r.obs < r.lo: return r.lo - r.obs, 'below lo'
        if r.obs > r.hi: return r.obs - r.hi, 'above hi'
        return min(r.obs - r.lo, r.hi - r.obs), 'inside'
    w("ENVELOPE London (44): index | T class613/classv7 obs lo hi margin | P class613/classv7 obs lo hi margin")
    for ix in eT.index:
        rT, rP = eT.loc[ix], eP.loc[ix]
        mT, sT = margin(rT); mP, sP = margin(rP)
        flag = '  <<<' if (rT.cv7 != rP.cv7 or rT.c613 != rP.c613) else ''
        w(f"  {ix}: T [{rT.c613}/{rT.cv7}] obs {rT.obs:.6f} lo {rT.lo:.6f} hi {rT.hi:.6f} m {mT:.6f} ({sT}) | "
          f"P [{rP.c613}/{rP.cv7}] obs {rP.obs:.6f} lo {rP.lo:.6f} hi {rP.hi:.6f} m {mP:.6f} ({sP}){flag}")
    for nm, e in (('T', eT), ('P', eP)):
        near = []
        for ix in e.index:
            m, s = margin(e.loc[ix])
            if m <= 1.0: near.append(f"{ix} {m:.4f} ({s}, class {e.loc[ix].cv7})")
        w(f"NEAR-EDGE {nm} (margin <= 1.0): " + '; '.join(near))
    # C1 labels London
    c1T, c1P = t['c1T'], t['c1P']
    lab_cols = [c for c in c1T.columns if 'label' in c.lower()]
    w(f"C1 columns with 'label': {lab_cols}; all columns: {list(c1T.columns)}")
    for c in lab_cols:
        ch = [(ix, c1T.loc[ix, c], c1P.loc[ix, c]) for ix in c1T.index if c1T.loc[ix, c] != c1P.loc[ix, c]]
        w(f"C1 {c} changes at London ({len(ch)}): " + '; '.join(f"{ix}: {a} -> {b}" for ix, a, b in ch))
    # arrows at London
    arr = t['arr']
    def glyph_dir(g): return 'n/a' if g == 'n/a' else g[0]
    def glyph_star(g): return g.endswith('*')
    ch = arr[arr['T'] != arr['P']]
    dch = ch[[glyph_dir(a) != glyph_dir(b) for a, b in zip(ch['T'], ch['P'])]]
    sch = ch[[glyph_dir(a) == glyph_dir(b) and glyph_star(a) != glyph_star(b) for a, b in zip(ch['T'], ch['P'])]]
    w(f"ARROWS London: cells {len(arr)}, changed {len(ch)} (direction {len(dch)}, shading-only {len(sch)})")
    w(f"  changed by source: ENS {int((ch.source == 'ENS').sum())}, OBS {int((ch.source == 'OBS').sum())}, models {int((~ch.source.isin(['ENS', 'OBS'])).sum())}")
    w("  ENS changes: " + '; '.join(f"{r['index']} {r['comp']}: {r['T']} -> {r['P']}" for r in ch[ch.source == 'ENS'].to_dict("records")))
    w("  OBS changes: " + '; '.join(f"{r['index']} {r['comp']}: {r['T']} -> {r['P']}" for r in ch[ch.source == 'OBS'].to_dict("records")))
    # consensus at London
    cT, cP = t['cT'], t['cP']
    w("CONS London (up/down/strong) changes:")
    for k in cT.index:
        a, b = cT.loc[k], cP.loc[k]
        if a.up != b.up or a.down != b.down or a.strong != b.strong:
            w(f"   {k}: T up {a.up} down {a.down} strong {a.strong} | P up {b.up} down {b.down} strong {b.strong}")
    # annual cells and pooled medians
    cdv = t['cd']
    w(f"ANNUAL CELLS: model-index series {len(cdv)}, with any differing annual value {int((cdv.n_diff > 0).sum())}, total differing annual values {int(cdv.n_diff.sum())}, nan mismatches {int(cdv.nan_mismatch.sum())}")
    pm = t['pm']
    w("POOLED PERIOD MEDIANS London (T vs P by period H/P/N/F):")
    w(pm.round(4).to_string())

# ---------- spread / stability ----------
sp = pd.read_csv('out_addC/london_cell_vs_spread.csv')
w("\n=== STABILITY (london_cell_vs_spread) ===")
w(f"columns: {list(sp.columns)}")
num = sp.select_dtypes('number')
w(sp.describe().round(4).to_string())
w("rows with largest max ratio:")
ratiocols = [c for c in sp.columns if 'ratio' in c.lower()]
if ratiocols:
    sp['maxratio'] = sp[ratiocols].max(axis=1)
    w(sp.nlargest(8, 'maxratio')[['index'] + ratiocols].round(4).to_string())

# ---------- claims ----------
ch = pd.read_csv('out_addC/claim_check_changes_sec.csv')
w("\n=== CLAIMS ===")
w(f"changed-check rows total: {len(ch)}; distinct claims: 613 {ch[ch.target == '613'].claim.nunique()}, v7 {ch[ch.target == 'v7'].claim.nunique()}")
flip = ch[ch.printed_matches_T != ch.printed_matches_P]
w(f"rows whose printed-precision match status flips T->P: {len(flip)}; distinct claims: 613 {flip[flip.target == '613'].claim.nunique()}, v7 {flip[flip.target == 'v7'].claim.nunique()}")
w("flips by adc section:")
w(flip.groupby(['target', 'adc']).size().to_string())
adc_flip = flip[flip.adc.notna()]
for (tg, c), g in adc_flip.groupby(['target', 'claim'], sort=False):
    w(f"## {c} [{g.adc.iloc[0]} | {g.sec.iloc[0]}] {str(g.text.iloc[0])[:300]}")
    for r in g.to_dict('records'):
        w(f"   {r['check']}: printed {r['printed']} | T {r['T']} | P {r['P']} | T-match {r['printed_matches_T']} P-match {r['printed_matches_P']}")
cp = pickle.load(open('out_addC/claim_parts.pkl', 'rb'))
w(f"\nclaim_parts type: {type(cp)}; keys/len: {list(cp.keys()) if isinstance(cp, dict) else len(cp)}")
open('out_addC/extract_summary.txt', 'w').write('\n'.join(OUT))
print('\n'.join(OUT[:60]))
print('... total lines:', len(OUT))
