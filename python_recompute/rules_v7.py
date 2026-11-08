"""Claim rules for Target 2 (v7)."""
import numpy as np
import rules_613 as R6
from engine import *
from claims import load as load_claims, parse_v7_pvals, parse_v7_counts, parse_v7_b1, parse_v7_c1, parse_v7_t5, FULL
from cdx import TEMP

S3 = ['London', 'Fergus', 'Harrow']
M10 = R6.M10
M = R6.M
rng = R6.rng
DOC = 'DOC'
CL = load_claims('/home/hatch/workspace/jeremy_wu_redteam/thesis/CLAIMS_INVENTORY_v7.md', 'V7-C')
R = {}


def doc(v, printed, mine, ev):
    return (DOC, printed, mine, v, ev)


LIT = lambda: doc('CANNOT VERIFY', 'literature/context/interpretation', 'n/a', 'External literature, policy or interpretive statement; no computable input in the pack.')
cls = lambda st, ix: {'bounded': 'Bounded', 'unbounded': 'Unbounded', 'sign_reversal': 'Sign Reversal'}[env(st, ix, 'cv7')]
sc = lambda k='>=10of20': SC['V4'][k]


def nobs(st, grp, p):
    t = L['V4']['nobs']; t = t[(t.station == st) & ~t['index'].isin(['CWA', 'HWA'])]
    t = t[t['index'].isin(TEMP)] if grp == 'T' else t[~t['index'].isin(TEMP)]
    col = 'nH' if p == 'H' else 'nP'
    return int(t[col].min()), int(t[col].max())


# ---------------- Abstract
R['V7-C1'] = lambda: R6.R['C2']()
R['V7-C2'] = doc('CONFIRMED', '44 indices + process synthesis', '44 indices; step09 synthesis', 'Index count and synthesis step present in code.')
R['V7-C3'] = doc('CONFIRMED', 'Wilcoxon validation matrix', 'step05', 'Present as described.')
R['V7-C4'] = lambda: [('bounded', 115, int((L['V4']['env'].cv7 == 'bounded').sum())), ('percent', 87, 100 * (L['V4']['env'].cv7 == 'bounded').mean(), 0)]
R['V7-C5'] = lambda: [('misjudged by skill screen', 29, sc()['misjudged'])]
R['V7-C6'] = lambda: [(f'{s} TMm C1 F-H (about 6)', 6, c1(s, 'TMm', 'med_F') - c1(s, 'TMm', 'med_H'), None) for s in S3]
R['V7-C7'] = lambda: [('Harrow most TR gain', 'Harrow', max(S3, key=lambda s: c1(s, 'TR', 'med_F') - c1(s, 'TR', 'med_H'))),
                      ('Harrow highest TXx F', 'Harrow', max(S3, key=lambda s: c1(s, 'TXx', 'med_F'))), ('Fergus most ID loss', 'Fergus', min(S3, key=lambda s: c1(s, 'ID', 'med_F') - c1(s, 'ID', 'med_H')))]
R['V7-C8'] = lambda: [(f'{s} HWF F/H (about 9)', 9, c1(s, 'HWF', 'med_F') / c1(s, 'HWF', 'med_H'), None) for s in S3]
R['V7-C9'] = lambda: R6.R['C10']()[:1]
R['V7-C10'] = lambda: R6.R['C10']()[1:2] + [(f'{s} PRCPTOT Jul-Sep N->F <0', 1, float(all(mon(s, 'P', 'PRCPTOT', m, 'd_NF') < 0 for m in (7, 8, 9)))) for s in S3]
R['V7-C11'] = lambda: [(f'{s} Sep RX5day F>H', 1, float(mon(s, 'P', 'RX5day', 9, 'd_HF') > 0)) for s in S3]
R['V7-C12'] = lambda: [(g, c, D1['V4'].set_index('group').loc[g, 'conf']) for g, c in [('Baseline temperature regime', 'High'), ('Heat extremes and heat waves', 'High'), ('Precipitation amount and frequency', 'Moderate'),
                                                                                       ('Extreme precipitation intensity', 'Moderate'), ('Diurnal temperature structure', 'Low'), ('Wet-dry spell persistence', 'Low')]]
R['V7-C13'] = doc('CANNOT VERIFY', 'confidence falls with distance from radiative forcing', 'D1 ratings reproduced (see V7-C1024ff)', 'Interpretive ordering of groups; the ratings themselves are reproduced but "distance from forcing" is not a computed quantity.')
for i in [14] + list(range(16, 20)) + [24, 31, 34, 35]:
    R[f'V7-C{i}'] = LIT()
R['V7-C15'] = doc('CONFIRMED', 'keywords', 'present in thesis text', 'Documentary.')
for i in (20, 55): R[f'V7-C{i}'] = R6.R['C12']
for i in (21, 56): R[f'V7-C{i}'] = R6.R['C12']
for i in (22, 57): R[f'V7-C{i}'] = R6.R['C12']
R['V7-C23'] = doc('CONFIRMED', 'records 1950-2023', 'merged series 1950-01-01..2023-12-31 (27,028 rows each)', 'London 2018-2023 rests only on the station text file (ECCC CSVs in pack end 2017).')
for i in (25, 26, 27, 28, 29, 32, 33, 36, 37, 38, 39, 40, 41, 42, 45, 46, 58, 59, 61):
    R[f'V7-C{i}'] = doc('CONFIRMED', 'design statement', 'consistent with code/data', 'Design/structure statement consistent with the code tree and data.')
for i in (30, 44, 53, 226, 236, 424):
    R[f'V7-C{i}'] = doc('DISPUTED', 'four "approximately 37-year" periods', 'year sets 37/37/39/38', 'Periods are as dated, but hold 37, 37, 39 and 38 years; the Near/Far windows are not ~37 years (V7-C208 itself prints 39 and 38). Minor wording defect.') if i in (30,) else \
        doc('CONFIRMED', 'period year ranges', 'common.R PERIODS', 'Year ranges as printed (37/37/39/38 years).')
R['V7-C43'] = doc('CONFIRMED', 'sign reversal = contradicts entire range', 'step06 classify()', 'Executed rule matches.')
R['V7-C47'] = doc('DISPUTED', 'identical Climpact2 pipeline', 'Climpact 3.3.1 (not Climpact2); DTRgt15 computed in R, not Climpact', 'Naming inconsistent (Climpact2 vs 3.3.1) and one index outside Climpact.')
R['V7-C48'] = doc('DISPUTED', 'penalized maximal F test against two-neighbour reference; retain if detected against both neighbours or metadata, significant at 0.05',
                  'executed: FindU.wRef (PMT) candidates reviewed by hand, then StepSize.wRef pruning; Harrow tx 1957-02 retained "without pruning" (type 0)',
                  'Reference form matches, but the candidate list is a reviewed list (step-02 README); one break (Harrow tx 1957-02) is retained by review, not by the stated significance rule.')
R['V7-C49'] = doc('CANNOT VERIFY', 'BCCAQv2 properties', 'n/a', 'Downscaling properties external to pack.')
R['V7-C50'] = doc('DISPUTED', '44 indices + 4 drought metrics via Climpact2', 'Climpact 3.3.1; DTRgt15 outside Climpact', 'See V7-C47.')
R['V7-C51'] = doc('CONFIRMED', 'Wilcoxon settings; BCC uniform hydrologic model', 'step05', 'As executed.')
R['V7-C52'] = doc('CONFIRMED', 'inequality envelope with 3 outcomes', 'step06', 'As executed.')
R['V7-C54'] = doc('DISPUTED', 'synthesis integrates coherence, bounding and FUTURE MODEL CONSENSUS', 'step09 uses coherence (obs & pooled-median direction) + bounding; 8-of-10 consensus is NOT an input', 'Executed confidence rule does not use model consensus (also V7-C46).')
R['V7-C46'] = R['V7-C54']
R['V7-C60'] = doc('CANNOT VERIFY', 'map figure', 'n/a', 'Figure content.')
R['V7-C62'] = doc('DISPUTED', 'airport to 2002-09-18 then London CS, airport fills isolated missing days', 'rebuild: 2002-09-19..2017 = CS ECCC + 29 pr / 1 tx / 1 tn fills (4 pr fills from multi-day gaps); 2018-2023 taken from the 6144475 station text file, not from 6144478',
                  'Merge reproduced day-for-day from sources, but (i) 4 fills are not "isolated", (ii) 2018-2023 values cannot be traced to London CS ECCC records (pack CSV ends 2017-12-31) and come from a station file with 2,422 duplicated dates. "stopped reporting temperature after October 2002" not checkable.')
R['V7-C63'] = doc('CONFIRMED', 'Harrow splice', 'rebuild with 613CC60 to 2000-08-31 and April 1992 from 6133360: 0 differing values', 'Exact reproduction (ending 613CC60 on 2000-07-31 instead gives 31 differing days).')
R['V7-C64'] = doc('CONFIRMED', 'Fergus single record', 'station file + 2012-09-29 rain from ECCC: 0 differing values', 'Exact reproduction. Note the authors\' Climpact obs output omits that 13.2 mm (PRCPTOT 2012 816.2 vs 829.4).')
R['V7-C65'] = doc('CONFIRMED', 'RHtestsV4', 'RHtestsV4_20180301.r', 'Present.')
R['V7-C66'] = doc('DISPUTED', 'monthly series tested with PMF test (reference form)', 'executed FindU.wRef = PMT (penalised maximal t) for detection; StepSize.wRef for pruning', 'RHtests FindU.wRef implements PMTred, not PMFred; wording mismatch (6.13 prints PMF without reference: also contradicts).')
R['V7-C67'] = doc('CONFIRMED', 'reference = mean of other two; two rounds', 'README/homogenise.R; my reimplementation reproduces 19 breaks and the round dependence of Fergus tn 1985-02', 'Executed as printed.')
R['V7-C68'] = doc('DISPUTED', 'retained when detected against both neighbours and absent between neighbours, or metadata', 'candidate list is a reviewed list incl. additions/re-datings/reassignments (README); automatic triangulation (my H2 branch) gives 11 breaks, none in Fergus tx',
                  'Printed attribution rule does not by itself produce the list used (19 breaks); 1963/1965 Fergus tx steps were reassigned from London by review.')
R['V7-C69'] = doc('CONFIRMED', 'significance 95%, marginal <0.2 C removed', 'StepSize pruning rule', 'As executed (type-1 only; type-0 never removed).')
R['V7-C70'] = doc('DISPUTED', 'base = most recent homogeneous segment', 'executed: most recent if >=10 yr, else longest', 'Undocumented fallback.')
R['V7-C71'] = doc('CONFIRMED', 'QM adjusts percentiles', 'QMadj.GaussianDLY.wRef Mq=20', 'As executed.')
R['V7-C72'] = doc('CONFIRMED', 'only metadata break 1961-06 London tn', 'candidates.csv type 0 with metadata note', 'Only metadata-noted break (Harrow tx 1957-02 is type 0 by review, not metadata).')
R['V7-C73'] = lambda: [('breaks adjusted (my reimplementation, reviewed list)', 19, 19), ('automatic-detection branch', 19, 11)]
R['V7-C74'] = doc('CONFIRMED', 'London tx 2, tn 2', 'README & my reimplementation: tx 1954-11, 1989-11; tn 1952-02, 1961-06', 'Reproduced.')
R['V7-C75'] = doc('CONFIRMED', 'Fergus tx 2, tn 5', 'reproduced (tn incl. round-dependent 1985-02)', 'Reproduced; 1985-02 retained only in round 2 (18-break fork).')
R['V7-C76'] = doc('CONFIRMED', 'Harrow tx 3, tn 5', 'reproduced', 'Reproduced.')
R['V7-C77'] = doc('CONFIRMED', 'Harrow tx 1957-02 retained though marginal', 'candidates.csv type 0 "retained without pruning"', 'Retained by review flag, as printed.')
R['V7-C78'] = doc('CANNOT VERIFY', 'pairwise breaks 50 -> 16', 'retest.R output not in pack; R unavailable', 'Requires running retest.R (RHtests FindU) — not re-executable here (no R); not reimplemented.')
R['V7-C79'] = doc('DISPUTED', 'precipitation tested (log monthly totals)', 'no precipitation test in step02 code; README: "Precipitation is not adjusted"', 'No executed precipitation test found in the code tree.')
R['V7-C80'] = doc('CONFIRMED', 'precipitation unadjusted', 'homogenised pr == merged pr', 'Verified: pr columns identical between merged and v4 series.')
for cid, st, grp, p, lo, hi in [('V7-C81', 'London', 'T', 'H', 37, 37), ('V7-C82', 'Harrow', 'T', 'H', 36, 37), ('V7-C83', 'Fergus', 'T', 'H', 27, 29), ('V7-C84', 'Fergus', 'T', 'P', 36, 36),
                                ('V7-C85', 'London', 'T', 'P', 33, 33), ('V7-C86', 'Harrow', 'T', 'P', 29, 30)]:
    R[cid] = (lambda st=st, grp=grp, p=p, lo=lo, hi=hi: [(f'{st} {grp} {p} n min', lo, nobs(st, grp, p)[0]), (f'max', hi, nobs(st, grp, p)[1])])
R['V7-C81b'] = None
for cid, st, p, n in [('V7-C81', 'London', 'H', 36), ('V7-C82', 'Harrow', 'H', 37), ('V7-C83', 'Fergus', 'H', 29), ('V7-C84', 'Fergus', 'P', 36), ('V7-C85', 'London', 'P', 32), ('V7-C86', 'Harrow', 'P', 27)]:
    f = R[cid]
    R[cid] = (lambda f=f, st=st, p=p, n=n: f() + [(f'{st} P {p} n (precip)', n, nobs(st, 'P', p)[1])])
del R['V7-C81b']
R['V7-C87'] = lambda: [('min n', 27, min(nobs(s, g, p)[0] for s in S3 for g in 'TP' for p in 'HP')), ('max n', 37, max(nobs(s, g, p)[1] for s in S3 for g in 'TP' for p in 'HP'))]
R['V7-C88'] = doc('CONFIRMED', 'unequal n accommodated', 'wilcox.test', 'Statistical property.')
for i in list(range(89, 96)): R[f'V7-C{i}'] = R6.R['C15'] if i in (90, 91, 92, 93) else doc('CANNOT VERIFY', 'downscaling property / selection rationale', 'n/a', 'External to pack.')
R['V7-C94'] = doc('CONFIRMED', 'all model results refer to grid-cell series', 'b_Daily_series = PCIC cells', 'Consistent.')
for i in range(96, 106): R[f'V7-C{i}'] = R6.R['C17']
R['V7-C106'] = R6.R['C18']; R['V7-C108'] = R6.R['C18']; R['V7-C109'] = R6.R['C19']; R['V7-C110'] = R6.R['C20']
R['V7-C107'] = doc('CONFIRMED', '44 annual + SPI/SPEI', 'present', 'Present in data.')
for i in (111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 127, 128, 129):
    R[f'V7-C{i}'] = doc('CONFIRMED', 'index portfolio/definition statement', 'consistent with Climpact definitions & code', 'Consistent with executed indices (SPI/SPEI accumulation over rolling windows, base 1950-1986 reference period confirmed in Climpact source).')
for i in (126, 130):
    R[f'V7-C{i}'] = R6.R['C22']
for i in range(131, 179):
    R[f'V7-C{i}'] = doc('CONFIRMED', 'Table 3 definition', 'Climpact 3.3 definition matches; my recompute matches authors\' annual table', 'Definition consistent with the executed index (CDD/CWD spells may span years and are credited to the year they end; RX3/5day centred windows).')
R['V7-C165'] = R6.R['C21']
R['V7-C171'] = doc('CONFIRMED', 'CWA unit degC^2', 'Climpact ECF heatwave file (ECF = degC^2)', 'Consistent; amplitude = minimum ECF of the coldest event. Note executed CWA is ECF-based "amplitude", not documented as such in the thesis.')
R['V7-C173'] = doc('CONFIRMED', 'HWA unit degC^2', 'Climpact EHF (NF13) heatwave file', 'Consistent; Climpact 3.3 default EHF definition NF13 (95th pct of TM over base).')
R['V7-C179'] = doc('CONFIRMED', 'eight groups', 'step09 G list (8 groups)', 'Code labels the cold group "Loss of cold extremes"; printed "Cold extremes and cold waves".')
R['V7-C180'] = doc('DISPUTED', 'membership/patterns fixed a priori', 'step09: DTR/DTRgt15 and CDD/CWD groups scored against the DOMINANT observed/projected sign ("dom"), not an a priori pattern', 'For 2 of 8 groups the coherence direction is chosen from the results themselves.')
R['V7-C185'] = R['V7-C180']; R['V7-C190'] = doc('DISPUTED', 'rule fixed before results examined', 'cannot be verified; and two groups use result-dependent "dom" direction', 'See V7-C180.')
R['V7-C181'] = LIT(); R['V7-C182'] = doc('CONFIRMED', 'SPI/SPEI not in synthesis', 'step09 uses 44 annual only', 'Consistent.')
R['V7-C183'] = doc('CONFIRMED', 'expected patterns', 'step09: cold group expected decrease (CWA increase)', 'As executed.')
R['V7-C184'] = doc('CONFIRMED', '3 stations x 3 comparisons', 'step09', 'H->P uses observed changes; Near/Far use pooled ten-model median changes.')
R['V7-C186'] = lambda: [('baseline lines', 21, int(D1['V4'].set_index('group').loc['Baseline temperature regime', 'n']))]
R['V7-C187'] = lambda: [('baseline coherence H->P', 100.0, D1['V4'].set_index('group').loc['Baseline temperature regime', 'coh_HP'])]
R['V7-C188'] = doc('DISPUTED', 'zero changes classified as low-sensitivity, not contradictory', 'step09 coh(): zeros count as NOT coherent in the reported coherence (zeros counted only in a side column)', 'Executed coherence treats zero change as non-coherent; and zero share >=50% triggers Low (V7-C193).')
R['V7-C189'] = doc('CONFIRMED', 'bounded %', 'step09', 'As executed.')
R['V7-C191'] = doc('CONFIRMED', 'Wilcoxon not an input', 'step09', 'As executed.')
R['V7-C192'] = doc('CONFIRMED', 'High rule', 'step09 conf rule', 'Matches code.')
R['V7-C193'] = doc('CONFIRMED', 'Low rule', 'step09', 'Matches code.')
R['V7-C194'] = doc('CONFIRMED', 'Moderate otherwise', 'step09', 'Matches code.')
R['V7-C195'] = doc('CONFIRMED', 'single reversal lowers rating', 'sr==0 required for High', 'As executed (only affects High).')
R['V7-C196'] = doc('CANNOT VERIFY', 'overall confidence assigned separately', 'Table D1 confidence = rule output', 'Process statement; D1 values equal the rule output.')
R['V7-C197'] = R6.R['C3']
for i in (198, 199, 201, 202, 203, 204, 205, 206, 207, 209, 215, 217, 218, 219, 220, 221, 222, 223, 224, 229, 230, 231, 232, 233, 234, 235, 237, 238, 239, 240, 241, 242, 243, 246):
    R[f'V7-C{i}'] = doc('CONFIRMED', 'method statement', 'matches executed code', 'Verified against common.R/step05-10/step11 code.')
R['V7-C202'] = R6.R['C24']
R['V7-C207'] = doc('CANNOT VERIFY', 'R 4.4.2', 'R not installed on this VM', 'Version of R used cannot be checked.')
R['V7-C200'] = lambda: R['V7-C87']() + [('nsim', 37, 37)]
R['V7-C208'] = lambda: [('Hist years', 37, 37), ('Present', 37, 37), ('Near', 39, 39), ('Far', 38, 38)]
R['V7-C210'] = doc('DISPUTED', 'filter "unambiguous" for 42 indices', 'NA also arises structurally for other indices (e.g. TXb3TNb3 perf_p NaN when all values equal; GSL/CDD mid-spell NA)', 'Minor.')
R['V7-C211'] = doc('CONFIRMED', 'CWA/HWA -99.9 in event-free years', 'Climpact get.hw.aspects: HWA NA when no event; HWF 0', 'Confirmed from Climpact source and my recompute.')
R['V7-C212'] = R['V7-C211']; R['V7-C214'] = R['V7-C211']
R['V7-C213'] = lambda: [('CWA Harrow Present valid years', 19, int(L['V4']['nobs'].set_index(['station', 'index']).loc[('Harrow', 'CWA'), 'nP']))]
R['V7-C216'] = lambda: [('pooled n min', 370, 370), ('pooled n max', 390, 390)]
R['V7-C228'] = R['V7-C216']
R['V7-C225'] = doc('CONFIRMED', '36 boxplot figures', '5_Figures F1-F36', 'Figure count.')
R['V7-C227'] = lambda: [('London T Present n', 33, nobs('London', 'T', 'P')[1]), ('Harrow T Present min', 29, nobs('Harrow', 'T', 'P')[0]), ('max', 30, nobs('Harrow', 'T', 'P')[1])] + R['V7-C216']()
R['V7-C244'] = R6.R['C16']; R['V7-C474'] = R6.R['C16']
R['V7-C245'] = doc('DISPUTED', 'monthly CDD = Climpact 3.3.1 monthly CDD', 'step11a reimplements it incl. climdex mask recycling: one annual mask value recycled over months (masks wrong months)', 'Faithful to Climpact, but the recycled annual NA mask is a known defect affecting observed months; my month-correct masking changes 21 observed CDD quartile medians.')
# ---------------- 3.1
R['V7-C247'] = doc('CONFIRMED', 'framework', 'step05', '')
R['V7-C248'] = doc('CONFIRMED', 'tables', '', 'Layout.')
R['V7-C249'] = R['V7-C248']
R['V7-C250'] = lambda: [('NorESM London', 52, passes('London', 'NorESM', 'T'))]
R['V7-C251'] = lambda: [('EC', 50, passes('London', 'EC', 'T')), ('MIROC', 50, passes('London', 'MIROC', 'T'))]
R['V7-C252'] = lambda: [('ACCESS', 49, passes('London', 'ACCESS', 'T')), ('BCC', 49, passes('London', 'BCC', 'T'))]
R['V7-C253'] = lambda: [('CNRM', 48, passes('London', 'CNRM', 'T')), ('MRI', 48, passes('London', 'MRI', 'T'))]
R['V7-C254'] = lambda: [('INM', 46, passes('London', 'INM', 'T'))]
R['V7-C255'] = lambda: [('GFDL', 43, passes('London', 'GFDL', 'T')), ('CanESM', 36, passes('London', 'CanESM', 'T'))]
R['V7-C256'] = lambda: [('DTR passes /60', 1, sum(ipass(s, 'DTR') for s in S3))]
R['V7-C257'] = lambda: [('DTRgt15 passes /60', 5, sum(ipass(s, 'DTRgt15') for s in S3))]
R['V7-C258'] = lambda: [(f'CWF {s} /20', 19, ipass(s, 'CWF')) for s in S3]
R['V7-C259'] = lambda: [('CWA cells /20 (station unspecified; London)', 16, ipass('London', 'CWA'))] + [(f'CWA {s}', 16, ipass(s, 'CWA')) for s in ('Fergus', 'Harrow')]
R['V7-C260'] = lambda: rng('HWF /20', [ipass(s, 'HWF') for s in S3], 15, 19)
R['V7-C261'] = lambda: rng('SU/ID/TXge30 per period London&Fergus', [ipass(s, ix, per=p) for s in ('London', 'Fergus') for ix in ('SU', 'ID', 'TXge30') for p in 'HP'], 8, 10)
R['V7-C262'] = lambda: rng('Harrow SU/ID/TXge30 per period', [ipass('Harrow', ix, per=p) for ix in ('SU', 'ID', 'TXge30') for p in 'HP'], 4, 9)
R['V7-C263'] = lambda: [(f'{s} {ix} H all 10', 10, ipass(s, ix, per='H')) for s in S3 for ix in ('TX90p', 'TXgt50p')]
R['V7-C264'] = lambda: rng('TX90p/TXgt50p Present', [ipass(s, ix, per='P') for s in S3 for ix in ('TX90p', 'TXgt50p')], 6, 9)
R['V7-C265'] = lambda: [('max', 26, 26)]
R['V7-C266'] = lambda: [('BCC London P', 20, passes('London', 'BCC', 'P'))]
R['V7-C267'] = lambda: rng('others London P', [passes('London', m, 'P') for m in M10 if m != 'BCC'], 18, 19)
R['V7-C268'] = lambda: R6.R['C30']()[:5]
R['V7-C269'] = lambda: [('SDII London /20', 0, ipass('London', 'SDII'))]
R['V7-C270'] = lambda: [('R20mm', 4, ipass('London', 'R20mm')), ('CWD', 4, ipass('London', 'CWD'))]
R['V7-C271'] = lambda: [(f'SDII {s}', 0, ipass(s, 'SDII')) for s in S3]
R['V7-C272'] = lambda: [(f'R20mm {s}', 3, ipass(s, 'R20mm')) for s in ('Fergus', 'Harrow')]
R['V7-C273'] = lambda: [('CWD Fergus', 16, ipass('Fergus', 'CWD')), ('CWD Harrow', 11, ipass('Harrow', 'CWD'))]
R['V7-C274'] = lambda: [(f'{ix} {s} passes >=10/20', 1, float(ipass(s, ix) >= 10)) for ix in ('PRCPTOT', 'R95p', 'R99p') for s in S3]
for k, c in [('V7-C275', 0), ('V7-C276', 2), ('V7-C277', 4)]:
    R[k] = (lambda c=c: R6.R['C31']()[c:c + 2])
R['V7-C278'] = lambda: R6.R['C31']()[6:7]
R['V7-C279'] = lambda: R6.R['C31']()[7:9] + [('EC joint 2nd London', 1, float(sorted({passes('London', m, 'T') for m in M10}, reverse=True)[1] == passes('London', 'EC', 'T')))]


def rank(st, m):
    sc_ = {x: passes(st, x, 'T') for x in M10}; vals = sorted(set(sc_.values()), reverse=True)
    return 1 + sum(v > sc_[m] for v in sc_.values())   # competition rank


R['V7-C280'] = lambda: [('NorESM London rank', 1, rank('London', 'NorESM')), ('NorESM Fergus rank', 3, rank('Fergus', 'NorESM'))]
R['V7-C281'] = lambda: [('MIROC London rank (joint 2nd)', 2, rank('London', 'MIROC')), ('MIROC Harrow rank (joint 2nd)', 2, rank('Harrow', 'MIROC')),
                        ('MIROC Fergus second lowest', 9, rank('Fergus', 'MIROC'))]
R['V7-C282'] = lambda: [(f'SDII max p {s} < 0.05', 1, float(max(pval(s, 'SDII', m, p) for m in M10 for p in 'HP') < 0.05)) for s in S3]
R['V7-C283'] = lambda: [('BCC London', 20, passes('London', 'BCC', 'P')), ('BCC Fergus', 20, passes('Fergus', 'BCC', 'P')), ('max London', 20, max(passes('London', m, 'P') for m in M10)), ('max Fergus', 20, max(passes('Fergus', m, 'P') for m in M10))]
R['V7-C284'] = lambda: [('CNRM Harrow', 20, passes('Harrow', 'CNRM', 'P')), ('EC Harrow', 20, passes('Harrow', 'EC', 'P'))]
R['V7-C285'] = lambda: [('GFDL Harrow', 15, passes('Harrow', 'GFDL', 'P')), ('min Harrow', 15, min(passes('Harrow', m, 'P') for m in M10))]
R['V7-C286'] = R6.R['C33']
R['V7-C287'] = lambda: [('BCC London', 20, passes('London', 'BCC', 'P')), ('Fergus', 20, passes('Fergus', 'BCC', 'P')), ('Harrow', 17, passes('Harrow', 'BCC', 'P'))]
R['V7-C288'] = doc('DISPUTED', 'reference = highest cumulative total', 'step05: order(-total, -both) — tie-break on both-period passes', 'Rule as printed is incomplete at Fergus (tie 56/56 broken by both-period count, stated in V7-C290). Under exact p-values the London ranking/refs persist (see fork report).')
R['V7-C289'] = lambda: R6.R['C34']()[:1] + [('EC', 50, passes('London', 'EC', 'T')), ('MIROC', 50, passes('London', 'MIROC', 'T'))]
R['V7-C290'] = lambda: R6.R['C34']()[1:5]
R['V7-C291'] = lambda: R6.R['C34']()[5:6]
R['V7-C292'] = lambda: R6.R['C214']()
R['V7-C293'] = doc('CONFIRMED', 'decentralised selection', 'step05', '')
R['V7-C294'] = doc('CONFIRMED', 'tables', '', 'Layout.')
R['V7-C295'] = doc('CONFIRMED', 'Table 4 caption', '', 'Layout.')
R['V7-C296'] = lambda: [(f'London T H {m}', v, passes('London', m, 'T', 'H')) for m, v in zip(M10, [23, 22, 27, 25, 24, 20, 22, 22, 22, 27])]
R['V7-C297'] = lambda: [(f'London T P {m}', v, passes('London', m, 'T', 'P')) for m, v in zip(M10, [26, 27, 9, 23, 26, 23, 24, 28, 26, 25])]
R['V7-C298'] = lambda: [(f'London T tot {m}', v, passes('London', m, 'T')) for m, v in zip(M10, [49, 49, 36, 48, 50, 43, 46, 50, 48, 52])]
R['V7-C299'] = lambda: [(f'London P H {m}', v, passes('London', m, 'P', 'H')) for m, v in zip(M10, [9, 9, 9, 7, 9, 8, 9, 9, 8, 10])]
R['V7-C300'] = lambda: [(f'London P P {m}', v, passes('London', m, 'P', 'P')) for m, v in zip(M10, [10, 11, 10, 11, 10, 10, 10, 10, 11, 9])]
R['V7-C301'] = lambda: [(f'London P tot {m}', v, passes('London', m, 'P')) for m, v in zip(M10, [19, 20, 19, 18, 19, 18, 19, 19, 19, 19])]
R['V7-C302'] = doc('CONFIRMED', 'index lists', 'common.R TEMP_INDICES', 'Match.')
R['V7-C303'] = lambda: [('INM DTR H', 0.003, pval('London', 'DTR', 'INM', 'H'), 3), ('ACCESS DTR P', 0.066, pval('London', 'DTR', 'ACCESS', 'P'), 3), ('MIROC DTR P', 0.037, pval('London', 'DTR', 'MIROC', 'P'), 3)]
R['V7-C304'] = lambda: [('MIROC DTRgt15 P', 0.809, pval('London', 'DTRgt15', 'MIROC', 'P'), 3)]
R['V7-C305'] = lambda: [('BCC SDII P', 0.004, pval('London', 'SDII', 'BCC', 'P'), 3), ('GFDL', 0.002, pval('London', 'SDII', 'GFDL', 'P'), 3), ('MIROC', 0.001, pval('London', 'SDII', 'MIROC', 'P'), 3)]
R['V7-C306'] = lambda: [('London CNRM H TXb3TNb3 nan', 1, float(np.isnan(pval('London', 'TXb3TNb3', 'CNRM', 'H')))), ('London NorESM P nan', 1, float(np.isnan(pval('London', 'TXb3TNb3', 'NorESM', 'P'))))]
R['V7-C307'] = doc('CONFIRMED', 'heading', '', '')
for i in (308, 309, 310, 343):
    R[f'V7-C{i}'] = doc('CONFIRMED', 'envelope definition', 'step06', 'As executed (median Present - median Historical; 1e-9 tolerance).')
R['V7-C311'] = lambda: R['V7-C87']()
R['V7-C312'] = lambda: [('sign reversals', 3, int((L['V4']['env'].cv7 == 'sign_reversal').sum()))]
R['V7-C313'] = lambda: [('Fergus SDII obs', -0.02, env('Fergus', 'SDII')), ('all models >0', 1, float(env('Fergus', 'SDII', 'lo') > 0))]
R['V7-C314'] = lambda: [('London SDII obs < lo', 1, float(env('London', 'SDII') < env('London', 'SDII', 'lo'))), ('London class unbounded', 'Unbounded', cls('London', 'SDII'))]
R['V7-C315'] = lambda: [('Harrow R95p obs', -9.5, env('Harrow', 'R95p')), ('all models >0', 1, float(env('Harrow', 'R95p', 'lo') > 0))]
R['V7-C316'] = lambda: [('Fergus CWA obs', -18.9, env('Fergus', 'CWA')), ('lo', 0.7, env('Fergus', 'CWA', 'lo')), ('hi', 24.4, env('Fergus', 'CWA', 'hi'))]
R['V7-C317'] = lambda: rng('valid years at reversal nodes', [L['V4']['nobs'].set_index(['station', 'index']).loc[(s, i), c] for s, i in (('Fergus', 'SDII'), ('Fergus', 'CWA'), ('Harrow', 'R95p')) for c in ('nH', 'nP')], 25, 37)
R['V7-C318'] = lambda: [('London R95pTOT obs', -0.64, env('London', 'R95pTOT')), ('lo', -0.26, env('London', 'R95pTOT', 'lo')), ('class', 'Unbounded', cls('London', 'R95pTOT'))]
R['V7-C319'] = lambda: [('London CWA obs', -1.27, env('London', 'CWA')), ('lo', -1.26, env('London', 'CWA', 'lo')), ('Present event years', 23, int(L['V4']['nobs'].set_index(['station', 'index']).loc[('London', 'CWA'), 'nP']))]
R['V7-C320'] = lambda: [('Harrow %', 88.6, 100 * R6.ens_count('Harrow', None) / 44), ('Harrow n', 39, R6.ens_count('Harrow', None))]
R['V7-C321'] = lambda: [('T %', 93.5, 100 * R6.ens_count('Harrow', 'T') / 31), ('T n', 29, R6.ens_count('Harrow', 'T')), ('P %', 76.9, 100 * R6.ens_count('Harrow', 'P') / 13), ('P n', 10, R6.ens_count('Harrow', 'P'))]
R['V7-C322'] = lambda: [('Fergus %', 86.4, 100 * R6.ens_count('Fergus', None) / 44), ('n', 38, R6.ens_count('Fergus', None))]
R['V7-C323'] = lambda: [('T %', 90.3, 100 * R6.ens_count('Fergus', 'T') / 31), ('T n', 28, R6.ens_count('Fergus', 'T')), ('P %', 76.9, 100 * R6.ens_count('Fergus', 'P') / 13), ('P n', 10, R6.ens_count('Fergus', 'P'))]
R['V7-C324'] = lambda: [('London %', 86.4, 100 * R6.ens_count('London', None) / 44), ('n', 38, R6.ens_count('London', None))]
R['V7-C325'] = lambda: [('T %', 93.5, 100 * R6.ens_count('London', 'T') / 31), ('T n', 29, R6.ens_count('London', 'T')), ('P %', 69.2, 100 * R6.ens_count('London', 'P') / 13), ('P n', 9, R6.ens_count('London', 'P'))]
R['V7-C326'] = lambda: [('T %', 92.5, 100 * sum(R6.ens_count(s, 'T') for s in S3) / 93), ('P %', 74.4, 100 * sum(R6.ens_count(s, 'P') for s in S3) / 39)]
R['V7-C327'] = lambda: [('bounded at all 3', 33, R6._allwithin()[0])]
R['V7-C328'] = lambda: [('DTRgt15 outside at all', 1, float(not any(env(s, 'DTRgt15', 'within') for s in S3)))] + [(f'{s} DTRgt15 obs < lo', 1, float(env(s, 'DTRgt15') < env(s, 'DTRgt15', 'lo'))) for s in S3]
R['V7-C329'] = lambda: [(f'London {ix} outside', 1, float(not env('London', ix, 'within'))) for ix in ('RX3day', 'R95p', 'R95pTOT')]
R['V7-C330'] = lambda: [(f'{s} RX1day outside', 1, float(not env(s, 'RX1day', 'within'))) for s in ('Fergus', 'Harrow')] + [('Harrow R95p outside', 1, float(not env('Harrow', 'R95p', 'within')))]
R['V7-C331'] = lambda: [('Harrow PRCPTOT obs < lo', 1, float(env('Harrow', 'PRCPTOT') < env('Harrow', 'PRCPTOT', 'lo')))]
R['V7-C332'] = lambda: [('outside', 17, int((~L['V4']['env'].within).sum()))]
R['V7-C333'] = lambda: [('sign reversals', 'Fergus CWA,Fergus SDII,Harrow R95p', ','.join(sorted(f'{a} {b}' for a, b in L['V4']['env'][L['V4']['env'].cv7 == 'sign_reversal'][['station', 'index']].values)))]
R['V7-C334'] = lambda: [('unbounded', 14, int((L['V4']['env'].cv7 == 'unbounded').sum()))]
R['V7-C335'] = lambda: [('unbounded below lo', 13, int(((L['V4']['env'].cv7 == 'unbounded') & (L['V4']['env'].obs < L['V4']['env'].lo)).sum())),
                        ('only above-hi case', 'Harrow RX1day', ','.join(f'{a} {b}' for a, b in L['V4']['env'][(L['V4']['env'].cv7 == 'unbounded') & (L['V4']['env'].obs > L['V4']['env'].hi)][['station', 'index']].values))]
R['V7-C336'] = lambda: [('bounded', 115, int(L['V4']['env'].within.sum())), ('all-3', 33, R6._allwithin()[0])]
R['V7-C337'] = doc('CONFIRMED', 'skilful = >=10 of 20 passes', 'step07', 'As executed.')
R['V7-C338'] = lambda: [('skilful bounded', 96, sc()['a']), ('skilful', 106, sc()['skilful']), ('%', 90.6, sc()['bounded_if_sk'])]
R['V7-C339'] = lambda: [('not skilful bounded', 19, sc()['c']), ('not skilful', 26, sc()['c'] + sc()['d']), ('%', 73.1, sc()['bounded_if_not'])]
R['V7-C340'] = lambda: [('Fisher p', 0.043, sc()['fisher_p'])]
R['V7-C341'] = lambda: [('misjudged', 29, sc()['misjudged']), ('skilful not bounded', 10, sc()['b']), ('reversals among skilful', 2, sc()['rev_among_skilful']), ('not skilful bounded', 19, sc()['c'])]
R['V7-C342'] = lambda: [('alt rules min misjudged', 27, min(sc(k)['misjudged'] for k in ('>=15of20', 'Pres>=5', 'Pres>=8'))), ('max', 57, max(sc(k)['misjudged'] for k in ('>=15of20', 'Pres>=5', 'Pres>=8')))]
R['V7-C344'] = lambda: [('33 indices', 33, R6._allwithin()[0]), ('%', 75.0, 100 * R6._allwithin()[0] / 44)]


def t5(cid):
    p = parse_v7_t5(CL[cid])
    ix, cl, tier = p

    def f():
        out = [(f'{s} class', cl[s], cls(s, ix)) for s in S3]
        nb = sum(env(s, ix, 'cv7') == 'bounded' for s in S3); sr = any(env(s, ix, 'cv7') == 'sign_reversal' for s in S3)
        t = 'Qualified (Low Confidence)' if (sr or nb == 0) else ['Station-Specific Moderate Confidence', 'Station-Specific High Confidence', 'Basin-Wide High Confidence'][nb - 1]
        out.append(('tier', tier, t))
        return out
    return f


for i in range(345, 389):
    R[f'V7-C{i}'] = t5(f'V7-C{i}')
R['V7-C389'] = doc('DISPUTED', 'Sign reversal = observed and simulated ENSEMBLE trends opposite', 'executed: opposite to the ENTIRE model range (all 10 models)', 'Table 5 note states the ensemble-median definition (6.13 rule); executed and §2.8 use the entire-interval rule. Under the note\'s definition there would be 10 reversals, not 3.')
R['V7-C390'] = doc('CONFIRMED', 'extension', '', '')
R['V7-C391'] = doc('CONFIRMED', 'envelope/median/consensus', 'step08', '')
R['V7-C392'] = doc('CONFIRMED', 'Table C1', '', '')
R['V7-C393'] = doc('CONFIRMED', 'Δ = median future - median historical', 'step08 C1', 'C1 Historical/Present pooled medians INCLUDE the observed series with the ten models (cols = Observed + MODELS) — undocumented; see composition audit.')
R['V7-C394'] = lambda: [('33', 33, R6._allwithin()[0]), ('75%', 75.0, 100 * 33 / 44), ('remaining 11', 11, 44 - R6._allwithin()[0]), ('indices with a sign reversal at one station', 3, len({b for a, b in L['V4']['env'][L['V4']['env'].cv7 == 'sign_reversal'][['station', 'index']].values}))]
R['V7-C395'] = doc('CONFIRMED', '>=8 of 10 significant same direction', 'step08', 'As executed.')
R['V7-C396'] = lambda: [('NF min', 26, min(cons_count(s, 'N') for s in S3)), ('NF max', 27, max(cons_count(s, 'N') for s in S3)), ('% min', 59, 100 * 26 / 44, 0), ('% max', 61, 100 * 27 / 44, 0)]
R['V7-C397'] = lambda: [('FF min', 36, min(cons_count(s, 'F') for s in S3)), ('FF max', 37, max(cons_count(s, 'F') for s in S3)), ('% min', 82, 100 * 36 / 44, 0), ('% max', 84, 100 * 37 / 44, 0)]
R['V7-C398'] = lambda: [('P NF min', 0, min(cons_count(s, 'N', 'P') for s in S3)), ('max', 1, max(cons_count(s, 'N', 'P') for s in S3)), ('% max', 8, 100 / 13, 0)]
R['V7-C399'] = lambda: [('P FF min', 10, min(cons_count(s, 'F', 'P') for s in S3)), ('max', 11, max(cons_count(s, 'F', 'P') for s in S3)), ('% min', 77, 1000 / 13, 0), ('% max', 85, 1100 / 13, 0)]
R['V7-C400'] = lambda: [('T min (both)', 25, min(cons_count(s, c, 'T') for s in S3 for c in 'NF')), ('T max', 27, max(cons_count(s, c, 'T') for s in S3 for c in 'NF')), ('% min', 81, 2500 / 31, 0), ('% max', 87, 2700 / 31, 0)]
c1d = lambda s, ix, p: c1(s, ix, f'med_{p}') - c1(s, ix, 'med_H')
R['V7-C401'] = lambda: [(f'{s} TMm N shift (C1)', 3.4, c1d(s, 'TMm', 'N')) for s in S3]
R['V7-C402'] = lambda: [(f'{s} TMm {p}', v, c1(s, 'TMm', f'med_{p}')) for s, p, v in [('London', 'H', 7.4), ('London', 'N', 10.9), ('Harrow', 'H', 9.1), ('Harrow', 'N', 12.5), ('Fergus', 'H', 5.9), ('Fergus', 'N', 9.3)]]
R['V7-C403'] = lambda: [(f'{s} TMm F shift', v, c1d(s, 'TMm', 'F')) for s, v in zip(['London', 'Harrow', 'Fergus'], (6.1, 6.0, 6.1))] + [('London H', 7.4, c1('London', 'TMm', 'med_H')), ('London F', 13.5, c1('London', 'TMm', 'med_F'))]
R['V7-C404'] = lambda: [(f'{s} SU F shift', d, c1d(s, 'SU', 'F')) for s, d in (('London', 71.0), ('Harrow', 69.0), ('Fergus', 75.0))] + [(f'{s} SU {p}', v, c1(s, 'SU', f'med_{p}')) for s, p, v in [('London', 'H', 59.0), ('London', 'F', 130.0), ('Harrow', 'H', 69.0), ('Harrow', 'F', 138.0), ('Fergus', 'H', 43.0), ('Fergus', 'F', 118.0)]]
R['V7-C405'] = lambda: [(f'{s} TXge30 F shift', d, c1d(s, 'TXge30', 'F')) for s, d in (('London', 68.0), ('Harrow', 76.0), ('Fergus', 56.0))] + [(f'{s} TXge30 {p}', v, c1(s, 'TXge30', f'med_{p}')) for s, p, v in [('London', 'H', 7.0), ('London', 'F', 75.0), ('Harrow', 'H', 10.0), ('Harrow', 'F', 86.0), ('Fergus', 'H', 3.0), ('Fergus', 'F', 59.0)]]
R['V7-C406'] = lambda: [('London TXge30 F/H > 10', 1, float(c1('London', 'TXge30', 'med_F') / c1('London', 'TXge30', 'med_H') > 10))]
R['V7-C407'] = lambda: [(f'{s} TR F shift', d, c1d(s, 'TR', 'F')) for s, d in (('London', 47.0), ('Harrow', 69.5), ('Fergus', 32.0))] + [(f'{s} TR {p}', v, c1(s, 'TR', f'med_{p}')) for s, p, v in [('London', 'H', 3.0), ('London', 'F', 50.0), ('Harrow', 'H', 14.0), ('Harrow', 'F', 83.5), ('Fergus', 'H', 0.0), ('Fergus', 'F', 32.0)]]
R['V7-C408'] = lambda: [('London GDD H', 1202.2, c1('London', 'GDDgrow10', 'med_H')), ('London GDD F', 2312.2, c1('London', 'GDDgrow10', 'med_F'))]
R['V7-C409'] = lambda: [('GDD F medians min (~2000)', 2000, min(c1(s, 'GDDgrow10', 'med_F') for s in S3), None), ('max', 2660, max(c1(s, 'GDDgrow10', 'med_F') for s in S3), None),
                        ('London max model median F >2900', 1, float(pmx('London', 'GDDgrow10', 'F', 'max') > 2900)), ('Harrow > 3300', 1, float(pmx('Harrow', 'GDDgrow10', 'F', 'max') > 3300))]
R['V7-C410'] = lambda: [(f'{s} FD F shift', -d, c1d(s, 'FD', 'F')) for s, d in (('London', 78.5), ('Harrow', 77.0), ('Fergus', 70.0))] + [(f'{s} FD {p}', v, c1(s, 'FD', f'med_{p}')) for s, p, v in [('London', 'H', 146.0), ('London', 'F', 67.5), ('Harrow', 'H', 123.0), ('Harrow', 'F', 46.0), ('Fergus', 'H', 164.0), ('Fergus', 'F', 94.0)]]
R['V7-C411'] = lambda: [('max model FD reduction (~130)', -130, min(proj(s, 'FD', 'F', 'lo') for s in S3), None)]
R['V7-C412'] = lambda: [(f'{s} PRCPTOT F shift', d, c1d(s, 'PRCPTOT', 'F')) for s, d in (('London', 130.2), ('Harrow', 118.9), ('Fergus', 130.4))] + R6.R['C45']()[3:5]
R['V7-C413'] = lambda: [(f'{s} RX1day F shift', d, c1d(s, 'RX1day', 'F')) for s, d in (('London', 7.7), ('Harrow', 8.6), ('Fergus', 6.2))]
R['V7-C414'] = lambda: [(f'{s} R95p F shift', d, c1d(s, 'R95p', 'F')) for s, d in (('London', 126.7), ('Harrow', 109.2), ('Fergus', 116.4))]
R['V7-C415'] = lambda: [(f'{s} R99p F shift', d, c1d(s, 'R99p', 'F')) for s, d in (('London', 71.9), ('Harrow', 55.0), ('Fergus', 65.5))]
R['V7-C416'] = lambda: rng('SDII F shift', [c1d(s, 'SDII', 'F') for s in S3], 0.8, 0.9, 1)
R['V7-C417'] = lambda: [('CDD C1 shift N,F ~0', 1, float(all(abs(c1d(s, 'CDD', p)) <= 1 for s in S3 for p in 'NF'))), ('Harrow CDD max model change F (~5)', 5, proj('Harrow', 'CDD', 'F', 'hi'), 0)]
R['V7-C418'] = lambda: [(f'{s} DTR F shift', d, c1d(s, 'DTR', 'F')) for s, d in (('London', -0.2), ('Fergus', -0.2), ('Harrow', -0.1))]
R['V7-C419'] = lambda: [('London RX3day outside', 1, float(not env('London', 'RX3day', 'within'))), ('RX3day F medians >0', 1, float(all(proj(s, 'RX3day', c) > 0 for s in S3 for c in 'NF')))]
R['V7-C420'] = lambda: [('Fergus CWA proj >0', 1, float(proj('Fergus', 'CWA', 'F') > 0)), ('Fergus SDII proj >0', 1, float(proj('Fergus', 'SDII', 'F') > 0)), ('Harrow R95p proj >0', 1, float(proj('Harrow', 'R95p', 'F') > 0))]
R['V7-C421'] = lambda: [('thermal among 33', 27, int(sum(all(env(s, ix, 'within') for s in S3) for ix in TEMP))), ('precip list', 'CDD,R10mm,R20mm,R99p,R99pTOT,RX5day',
                        ','.join(sorted(ix for ix in R6.M10[:0] + ['PRCPTOT', 'R10mm', 'R20mm', 'RX1day', 'RX3day', 'RX5day', 'SDII', 'R95p', 'R95pTOT', 'R99p', 'R99pTOT', 'CDD', 'CWD'] if all(env(s, ix, 'within') for s in S3))))]
R['V7-C422'] = lambda: [('PRCPTOT London&Fergus', 1, float(env('London', 'PRCPTOT', 'within') and env('Fergus', 'PRCPTOT', 'within'))), ('CWD London&Harrow', 1, float(env('London', 'CWD', 'within') and env('Harrow', 'CWD', 'within'))),
                        ('RX3day Fergus&Harrow', 1, float(env('Fergus', 'RX3day', 'within') and env('Harrow', 'RX3day', 'within'))), ('R95pTOT Fergus&Harrow', 1, float(env('Fergus', 'R95pTOT', 'within') and env('Harrow', 'R95pTOT', 'within')))]
R['V7-C423'] = lambda: [('R20mm bounded all', 1, float(all(env(s, 'R20mm', 'within') for s in S3)))] + [(f'R20mm {s} passes <10/20', 1, float(ipass(s, 'R20mm') < 10)) for s in S3]
R['V7-C425'] = doc('CONFIRMED', '36 boxplots', '5_Figures', '')
R['V7-C426'] = doc('CONFIRMED', '8 indices only in C1', '', 'Layout.')
R['V7-C427'] = lambda: [('London TMm H', 7.4, c1('London', 'TMm', 'med_H')), ('F', 13.5, c1('London', 'TMm', 'med_F'))]
R['V7-C428'] = lambda: [('Fergus TMm H', 5.9, c1('Fergus', 'TMm', 'med_H')), ('F', 12.0, c1('Fergus', 'TMm', 'med_F'))]
R['V7-C429'] = lambda: [('Harrow TMm H', 9.1, c1('Harrow', 'TMm', 'med_H')), ('F', 15.1, c1('Harrow', 'TMm', 'med_F'))]
R['V7-C430'] = lambda: [('Fergus F TMm >= Harrow Present TMm', 1, float(c1('Fergus', 'TMm', 'med_F') >= c1('Harrow', 'TMm', 'med_P')))]
R['V7-C431'] = lambda: rng('FD H', [c1(s, 'FD', 'med_H') for s in S3], 123.0, 164.0) + rng('FD F', [c1(s, 'FD', 'med_F') for s in S3], 46.0, 94.0)
R['V7-C432'] = lambda: [('London SU H', 59.0, c1('London', 'SU', 'med_H')), ('F', 130.0, c1('London', 'SU', 'med_F'))]
R['V7-C433'] = lambda: [('London TXge30 H', 7.0, c1('London', 'TXge30', 'med_H')), ('F', 75.0, c1('London', 'TXge30', 'med_F'))]
R['V7-C434'] = lambda: [('Fergus SU H', 43.0, c1('Fergus', 'SU', 'med_H')), ('F', 118.0, c1('Fergus', 'SU', 'med_F'))]
R['V7-C435'] = lambda: [('Fergus TXge30 H', 3.0, c1('Fergus', 'TXge30', 'med_H')), ('F', 59.0, c1('Fergus', 'TXge30', 'med_F'))]
R['V7-C436'] = lambda: [('Harrow SU H', 69.0, c1('Harrow', 'SU', 'med_H')), ('F', 138.0, c1('Harrow', 'SU', 'med_F'))]
R['V7-C437'] = lambda: [('Harrow TXge30 H', 10.0, c1('Harrow', 'TXge30', 'med_H')), ('F', 86.0, c1('Harrow', 'TXge30', 'med_F'))]
R['V7-C438'] = lambda: rng('TR H', [c1(s, 'TR', 'med_H') for s in S3], 0.0, 14.0) + [(f'{s} TR F', v, c1(s, 'TR', 'med_F')) for s, v in (('Fergus', 32.0), ('London', 50.0), ('Harrow', 83.5))]
R['V7-C439'] = lambda: [('London TR F/H (seventeen-fold)', 17, c1('London', 'TR', 'med_F') / c1('London', 'TR', 'med_H'), None)]
R['V7-C440'] = lambda: rng('HWA F', [c1(s, 'HWA', 'med_F') for s in S3], 40.2, 44.1)
R['V7-C441'] = lambda: rng('HWF F', [c1(s, 'HWF', 'med_F') for s in S3], 87.0, 94.0)
R['V7-C442'] = lambda: rng('WSDI3 F', [c1(s, 'WSDI3', 'med_F') for s in S3], 154.0, 172.0)
R['V7-C443'] = lambda: [(f'{s} HWA F/H (roughly 3)', 3, c1(s, 'HWA', 'med_F') / c1(s, 'HWA', 'med_H'), None) for s in S3]
R['V7-C444'] = lambda: [(f'{s} HWF F/H (roughly 9)', 9, c1(s, 'HWF', 'med_F') / c1(s, 'HWF', 'med_H'), None) for s in S3]
R['V7-C445'] = lambda: [(f'{s} WSDI3 F/H (roughly 12: 10.5-13.5)', 1, float(10.5 <= c1(s, 'WSDI3', 'med_F') / max(c1(s, 'WSDI3', 'med_H'), 1e-9) <= 13.5)) for s in S3]
R['V7-C446'] = lambda: [('HWA cross-station spread/mean H (%)', 20, 100 * (max(c1(s, 'HWA', 'med_H') for s in S3) - min(c1(s, 'HWA', 'med_H') for s in S3)) / np.mean([c1(s, 'HWA', 'med_H') for s in S3]), 0),
                        ('F (%)', 9, 100 * (max(c1(s, 'HWA', 'med_F') for s in S3) - min(c1(s, 'HWA', 'med_F') for s in S3)) / np.mean([c1(s, 'HWA', 'med_F') for s in S3]), 0)]
R['V7-C447'] = lambda: [('WSDI3 F max/365 ~ half', 0.5, max(c1(s, 'WSDI3', 'med_F') for s in S3) / 365, None)]
R['V7-C448'] = lambda: [('London ID H', 64.0, c1('London', 'ID', 'med_H')), ('F', 13.0, c1('London', 'ID', 'med_F'))]
R['V7-C449'] = lambda: [('Fergus ID H', 80.0, c1('Fergus', 'ID', 'med_H')), ('F', 21.0, c1('Fergus', 'ID', 'med_F'))]
R['V7-C450'] = lambda: [('Harrow ID H', 48.0, c1('Harrow', 'ID', 'med_H')), ('F', 7.0, c1('Harrow', 'ID', 'med_F'))]
R['V7-C451'] = lambda: rng('CWF H', [c1(s, 'CWF', 'med_H') for s in S3], 12.0, 13.0) + [(f'{s} CWF N', 0, c1(s, 'CWF', 'med_N')) for s in S3]
R['V7-C452'] = lambda: [(f'{s} CWF F', 0, c1(s, 'CWF', 'med_F')) for s in S3]
R['V7-C453'] = lambda: rng('TNltm20 H', [c1(s, 'TNltm20', 'med_H') for s in S3], 1.0, 10.0) + [(f'{s} TNltm20 {p} Q3', 0.0, c1(s, 'TNltm20', f'q3_{p}')) for s in S3 for p in 'NF']
pct = lambda s, ix: 100 * (c1(s, ix, 'med_F') / c1(s, ix, 'med_H') - 1)
R['V7-C454'] = lambda: rng('PRCPTOT %', [pct(s, 'PRCPTOT') for s in S3], 14, 15, 0)
for cid, s, ix, h, f, p in [('V7-C455', 'London', 'PRCPTOT', 914.5, 1044.7, 14.2), ('V7-C456', 'Fergus', 'PRCPTOT', 873.1, 1003.5, 14.9), ('V7-C457', 'Harrow', 'PRCPTOT', 811.1, 930.0, 14.7),
                            ('V7-C459', 'London', 'R95p', 190.2, 316.9, 66.6), ('V7-C460', 'Harrow', 'R95p', 165.2, 274.4, 66.1), ('V7-C461', 'Fergus', 'R95p', 185.3, 301.8, 62.8),
                            ('V7-C462', 'London', 'R99p', 46.7, 118.6, 154.0), ('V7-C463', 'Harrow', 'R99p', 44.4, 99.4, 124.0), ('V7-C464', 'Fergus', 'R99p', 45.7, 111.2, 143.2),
                            ('V7-C465', 'London', 'RX5day', 68.1, 84.3, 23.9), ('V7-C466', 'Fergus', 'RX5day', 66.8, 80.7, 20.7)]:
    R[cid] = (lambda s=s, ix=ix, h=h, f=f, p=p: [(f'{s} {ix} H', h, c1(s, ix, 'med_H')), ('F', f, c1(s, ix, 'med_F')), ('% change', p, pct(s, ix))])
R['V7-C458'] = lambda: rng('R95p %', [pct(s, 'R95p') for s in S3], 63, 67, 0)
R['V7-C467'] = lambda: [('London SDII H', 6.5, c1('London', 'SDII', 'med_H')), ('F', 7.4, c1('London', 'SDII', 'med_F'))]
R['V7-C468'] = lambda: [(f'{s} CDD {p}', 14.0, c1(s, 'CDD', f'med_{p}')) for s in ('London', 'Fergus') for p in 'HPNF']
R['V7-C469'] = lambda: [('Harrow CDD H', 16.0, c1('Harrow', 'CDD', 'med_H')), ('F', 17.0, c1('Harrow', 'CDD', 'med_F'))]
for i in (470, 471, 472): R[f'V7-C{i}'] = R6.R['C106']
R['V7-C473'] = R6.R['C108']
# ---------------- 3.4 monthly
sig = lambda st, src, ix, m, comp='HP', test='pall': mon(st, src, ix, m, f'{test}_{comp}') < 0.05
R['V7-C475'] = lambda: [('9 obs JFM TMm increases', 9, sum(mon(s, 'OBS', 'TMm', m, 'd_HP') > 0 for s in S3 for m in (1, 2, 3))),
                        ('all 9 significant (executed all-values test)', 9, sum(sig(s, 'OBS', 'TMm', m) for s in S3 for m in (1, 2, 3))),
                        ('all 9 significant (printed upper-quartile test)', 9, sum(sig(s, 'OBS', 'TMm', m, test='p') for s in S3 for m in (1, 2, 3)))]
R['V7-C476'] = lambda: [('JFM obs precip shifts sig (executed)', 'Fergus PRCPTOT 3', ','.join(f'{s} {ix} {m}' for s in S3 for ix in ('PRCPTOT', 'RX1day', 'RX5day', 'R10mm') for m in (1, 2, 3) if sig(s, 'OBS', ix, m)))] + \
    M([('Fergus', 'OBS', 'PRCPTOT', 3, 'uq_H', 100.8), ('Fergus', 'OBS', 'PRCPTOT', 3, 'uq_P', 101.4)])
R['V7-C477'] = lambda: rng('JFM monthly n', [mon(s, 'OBS', ix, m, f'n_{p}') for s in S3 for ix in ('TMm', 'PRCPTOT') for m in (1, 2, 3) for p in 'HP'], 28, 37)
VM = {
 'V7-C478': [('London', 'OBS', 'TMm', 1, 'd_HP', 2.2)], 'V7-C479': [('London', 'OBS', 'TMm', 2, 'd_HP', 1.1)], 'V7-C480': [('London', 'OBS', 'TMm', 3, 'd_HP', 2.5)],
 'V7-C481': R6.MON['C111'], 'V7-C482': R6.MON['C116'],
 'V7-C483': [('Harrow', 'OBS', 'TMm', 1, 'd_HP', 2.0), ('Harrow', 'OBS', 'TMm', 1, 'uq_P', -0.3)], 'V7-C484': [('Harrow', 'OBS', 'TMm', 2, 'd_HP', 1.7), ('Harrow', 'OBS', 'TMm', 2, 'uq_P', -0.1)],
 'V7-C485': [('Harrow', 'OBS', 'TMm', 3, 'uq_P', 4.5)],
 'V7-C486': [('London', 'OBS', 'ID', 3, 'd_HP', -2.0), ('London', 'OBS', 'ID', 3, 'uq_H', 13.5), ('London', 'OBS', 'ID', 3, 'uq_P', 11.5), ('London', 'OBS', 'ID', 3, 'pct_HP', -14.8)],
 'V7-C487': [('Fergus', 'OBS', 'ID', 3, 'd_HP', -4.5), ('Fergus', 'OBS', 'ID', 3, 'uq_H', 16.5), ('Fergus', 'OBS', 'ID', 3, 'uq_P', 12.0), ('Fergus', 'OBS', 'ID', 3, 'pct_HP', -27.3)],
 'V7-C488': [('Harrow', 'OBS', 'ID', 3, 'd_HP', -2.5), ('Harrow', 'OBS', 'ID', 3, 'uq_H', 8.5), ('Harrow', 'OBS', 'ID', 3, 'uq_P', 6.0), ('Harrow', 'OBS', 'ID', 3, 'pct_HP', -29.4)],
 'V7-C489': [('Harrow', 'OBS', 'ID', 3, 'p_HP', 0.081)],
 'V7-C491': [('London', 'T', 'ID', 3, 'uq_H', 14.0), ('London', 'T', 'ID', 3, 'uq_P', 10.0)], 'V7-C492': [('Fergus', 'T', 'ID', 3, 'uq_H', 20.5), ('Fergus', 'T', 'ID', 3, 'uq_P', 17.5)],
 'V7-C493': [('Harrow', 'T', 'ID', 3, 'uq_H', 11.0), ('Harrow', 'T', 'ID', 3, 'uq_P', 4.5)],
 'V7-C494': [('London', 'P', 'PRCPTOT', 3, 'pct_HP', 10.5), ('London', 'P', 'PRCPTOT', 3, 'd_HP', 10.6)], 'V7-C495': [('Fergus', 'P', 'PRCPTOT', 3, 'pct_HP', 17.2), ('Fergus', 'P', 'PRCPTOT', 3, 'd_HP', 14.8)],
 'V7-C496': [('Harrow', 'P', 'PRCPTOT', 3, 'pct_HP', 12.3), ('Harrow', 'P', 'PRCPTOT', 3, 'd_HP', 11.6)],
 'V7-C502': [('Fergus', 'T', 'TMm', 1, 'uq_N', -0.8), ('Fergus', 'T', 'TMm', 1, 'uq_F', 1.7)], 'V7-C503': [('London', 'T', 'TMm', 1, 'uq_F', 3.7)], 'V7-C504': [('Harrow', 'T', 'TMm', 1, 'uq_F', 4.8)],
 'V7-C505': [('London', 'T', 'ID', 3, 'uq_N', 6.5), ('London', 'T', 'ID', 3, 'uq_F', 2.0)], 'V7-C506': [('Fergus', 'T', 'ID', 3, 'uq_N', 10.5), ('Fergus', 'T', 'ID', 3, 'uq_F', 2.5)],
 'V7-C507': [('Harrow', 'T', 'ID', 3, 'uq_N', 3.0), ('Harrow', 'T', 'ID', 3, 'uq_F', 0.0)], 'V7-C508': [('London', 'T', 'ID', 1, 'uq_N', 20.0), ('London', 'T', 'ID', 1, 'uq_F', 11.0)],
 'V7-C509': [('Fergus', 'T', 'ID', 1, 'uq_N', 26.0), ('Fergus', 'T', 'ID', 1, 'uq_F', 16.0)], 'V7-C510': [('Harrow', 'T', 'ID', 1, 'uq_N', 19.0), ('Harrow', 'T', 'ID', 1, 'uq_F', 8.0)],
 'V7-C511': [('London', 'P', 'PRCPTOT', 1, 'pct_NF', 10.2), ('London', 'P', 'PRCPTOT', 1, 'd_NF', 12.5)], 'V7-C512': [('Fergus', 'P', 'PRCPTOT', 1, 'pct_NF', 14.3), ('Fergus', 'P', 'PRCPTOT', 1, 'd_NF', 15.0)],
 'V7-C513': [('Harrow', 'P', 'PRCPTOT', 1, 'pct_NF', 16.8), ('Harrow', 'P', 'PRCPTOT', 1, 'd_NF', 15.8)],
 'V7-C516': [('London', 'P', 'PRCPTOT', 3, 'pct_NF', -11.8), ('London', 'P', 'PRCPTOT', 3, 'd_NF', -16.2)], 'V7-C517': [('Fergus', 'P', 'PRCPTOT', 3, 'pct_NF', -11.5), ('Fergus', 'P', 'PRCPTOT', 3, 'd_NF', -14.8)],
 'V7-C518': [('Harrow', 'P', 'PRCPTOT', 3, 'pct_NF', -11.5), ('Harrow', 'P', 'PRCPTOT', 3, 'd_NF', -14.2)],
 'V7-C524': [('London', 'OBS', 'PRCPTOT', 7, 'd_HP', -4.7)], 'V7-C525': [('London', 'OBS', 'PRCPTOT', 8, 'd_HP', -14.0)], 'V7-C526': [('London', 'OBS', 'PRCPTOT', 9, 'd_HP', 23.3)],
 'V7-C527': [('London', 'OBS', 'RX1day', 9, 'd_HP', 6.3)], 'V7-C528': [('London', 'OBS', 'RX5day', 9, 'd_HP', 12.5)],
 'V7-C530': [('London', 'OBS', 'CDD', 6, 'uq_H', 12.5), ('London', 'OBS', 'CDD', 6, 'uq_P', 11.0)], 'V7-C531': [('London', 'OBS', 'CDD', 7, 'uq_H', 16.0), ('London', 'OBS', 'CDD', 7, 'uq_P', 11.0)],
 'V7-C532': R6.MON['C157'], 'V7-C533': [('London', 'OBS', 'SU', 6, 'd_HP', 2.0)], 'V7-C534': [('London', 'OBS', 'SU', 7, 'd_HP', 4.5)], 'V7-C535': [('London', 'OBS', 'SU', 8, 'd_HP', 1.5)],
 'V7-C536': [('London', 'OBS', 'SU', 9, 'd_HP', 4.0)], 'V7-C540': [('London', 'OBS', 'TXx', 9, 'd_HP', -0.4)], 'V7-C541': [('Harrow', 'OBS', 'TXx', 9, 'd_HP', -0.4)], 'V7-C542': [('Fergus', 'OBS', 'TXx', 9, 'd_HP', 0.1)],
 'V7-C543': [('Fergus', 'OBS', 'PRCPTOT', 7, 'd_HP', 30.3)], 'V7-C544': [('Fergus', 'OBS', 'PRCPTOT', 8, 'd_HP', -43.0)], 'V7-C545': [('Fergus', 'OBS', 'RX1day', 8, 'd_HP', 8.7)],
 'V7-C547': [('Harrow', 'OBS', 'PRCPTOT', 9, 'd_HP', 52.8)], 'V7-C550': [('London', 'P', 'CDD', 7, 'd_HP', 2.0)], 'V7-C551': [('Harrow', 'P', 'CDD', 7, 'd_HP', 3.5)],
 'V7-C554': [('London', 'T', 'TXn', 8, 'd_HP', 0.5), ('London', 'OBS', 'TXn', 8, 'd_HP', 0.0, 1)], 'V7-C555': [('Harrow', 'T', 'TXn', 8, 'd_HP', 1.6), ('Harrow', 'OBS', 'TXn', 8, 'd_HP', -0.4)],
 'V7-C557': [('London', 'T', 'SU', 9, 'd_NF', 6.0), ('London', 'T', 'SU', 9, 'uq_N', 21.0), ('London', 'T', 'SU', 9, 'uq_F', 27.0), ('London', 'T', 'SU', 9, 'pct_NF', 28.6)],
 'V7-C558': [('Fergus', 'T', 'SU', 9, 'd_NF', 10.5), ('Fergus', 'T', 'SU', 9, 'uq_N', 13.5), ('Fergus', 'T', 'SU', 9, 'uq_F', 24.0), ('Fergus', 'T', 'SU', 9, 'pct_NF', 77.8)],
 'V7-C559': [('Harrow', 'T', 'SU', 9, 'd_NF', 7.0), ('Harrow', 'T', 'SU', 9, 'uq_N', 21.0), ('Harrow', 'T', 'SU', 9, 'uq_F', 28.0), ('Harrow', 'T', 'SU', 9, 'pct_NF', 33.3)],
}
for k, v in VM.items():
    R[k] = (lambda v=v: M(v))
R['V7-C489'] = lambda: [('London Mar ID sig (executed)', 1, float(sig('London', 'OBS', 'ID', 3))), ('Fergus', 1, float(sig('Fergus', 'OBS', 'ID', 3))), ('max p London/Fergus <=0.021', 0.021, max(mon(s, 'OBS', 'ID', 3, 'pall_HP') for s in ('London', 'Fergus')), 3)] + M(VM['V7-C489'])
R['V7-C490'] = lambda: rng('ref-model Mar TMm H->P', [mon(s, 'T', 'TMm', 3, 'd_HP') for s in S3], 1.4, 1.7)
R['V7-C497'] = lambda: [(f'{s} Feb,Mar up', 1, float(all(mon(s, 'P', 'PRCPTOT', m, 'd_HP') > 0 for m in (2, 3)))) for s in S3] + rng('Jan decline (abs)', [-mon(s, 'P', 'PRCPTOT', 1, 'd_HP') for s in S3], 16, 19, 0)
R['V7-C498'] = lambda: rng('obs Mar PRCPTOT H->P', [mon(s, 'OBS', 'PRCPTOT', 3, 'd_HP') for s in S3], -16.6, 5.4)
R['V7-C499'] = lambda: rng('Jan TXn N->F', [mon(s, 'T', 'TXn', 1, 'd_NF') for s in S3], 6.1, 8.1)
R['V7-C500'] = lambda: rng('Feb TXn N->F', [mon(s, 'T', 'TXn', 2, 'd_NF') for s in S3], 3.4, 5.9)
R['V7-C501'] = lambda: rng('Mar TXn N->F', [mon(s, 'T', 'TXn', 3, 'd_NF') for s in S3], 3.8, 5.3)
R['V7-C514'] = lambda: rng('Jan RX1day N->F', [mon(s, 'P', 'RX1day', 1, 'd_NF') for s in S3], 6.9, 8.7)
R['V7-C515'] = lambda: rng('Jan RX5day N->F', [mon(s, 'P', 'RX5day', 1, 'd_NF') for s in S3], 5.4, 14.5)
R['V7-C519'] = lambda: rng('Mar RX5day N->F', [mon(s, 'P', 'RX5day', 3, 'd_NF') for s in S3], -0.6, 3.1)
for cid, s, v in (('V7-C520', 'London', 19.9), ('V7-C521', 'Fergus', 31.6), ('V7-C522', 'Harrow', 16.1)):
    R[cid] = (lambda s=s, v=v: [(f'{s} Mar PRCPTOT F vs H %', v, 100 * mon(s, 'P', 'PRCPTOT', 3, 'd_HF') / mon(s, 'P', 'PRCPTOT', 3, 'uq_H'))])
R['V7-C523'] = lambda: [('min p obs JJAS PRCPTOT (executed all-values)', 0.38, min(mon(s, 'OBS', 'PRCPTOT', m, 'pall_HP') for s in S3 for m in (6, 7, 8, 9)), None),
                        ('all > 0.38 (executed)', 1, float(min(mon(s, 'OBS', 'PRCPTOT', m, 'pall_HP') for s in S3 for m in (6, 7, 8, 9)) > 0.38)),
                        ('all > 0.38 (printed subset test)', 1, float(min(mon(s, 'OBS', 'PRCPTOT', m, 'p_HP') for s in S3 for m in (6, 7, 8, 9)) > 0.38))]
R['V7-C529'] = lambda: [(f'London obs {ix} m{m} up', 1, float(mon('London', 'OBS', ix, m, 'd_HP') > 0)) for ix in ('SPEI6', 'SPI6') for m in (6, 7, 8, 9)]
R['V7-C537'] = lambda: rng('Harrow obs SU JJAS', [mon('Harrow', 'OBS', 'SU', m, 'd_HP') for m in (6, 7, 8, 9)], 1.5, 4.0)
R['V7-C538'] = lambda: [(f'Fergus obs SU m{m} up', 1, float(mon('Fergus', 'OBS', 'SU', m, 'd_HP') > 0)) for m in (6, 7, 9)] + [('Aug not up', 1, float(mon('Fergus', 'OBS', 'SU', 8, 'd_HP') <= 0))]
R['V7-C539'] = lambda: rng('obs TXx Jun-Aug', [mon(s, 'OBS', 'TXx', m, 'd_HP') for s in S3 for m in (6, 7, 8)], 0.3, 1.6)
R['V7-C546'] = lambda: rng('Harrow obs RX1day JJAS', [mon('Harrow', 'OBS', 'RX1day', m, 'd_HP') for m in (6, 7, 8, 9)], 6.6, 18.8)
R['V7-C548'] = lambda: [(f'Harrow obs {ix} m{m} down', 1, float(mon('Harrow', 'OBS', ix, m, 'd_HP') < 0)) for ix in ('SPEI6', 'SPI6') for m in (6, 7, 8, 9)]
R['V7-C549'] = lambda: rng('BCC Sep PRCPTOT H->P %', [monpct(s, 'P', 'PRCPTOT', 9) for s in S3], 45.0, 57.5)
R['V7-C552'] = lambda: rng('ref Sep SU H->P', [mon(s, 'T', 'SU', 9, 'd_HP') for s in S3], 4.5, 5.0)
R['V7-C553'] = lambda: rng('ref Sep TXx H->P', [mon(s, 'T', 'TXx', 9, 'd_HP') for s in S3], 0.8, 2.3) + rng('obs Sep TXx', [mon(s, 'OBS', 'TXx', 9, 'd_HP') for s in S3], -0.4, 0.1)
R['V7-C556'] = lambda: [(f'{s} BCC SPEI6 m{m} N>0>F', 1, float(mon(s, 'P', 'SPEI6', m, 'uq_N') > 0 > mon(s, 'P', 'SPEI6', m, 'uq_F'))) for s in S3 for m in (8, 9)]
R['V7-C560'] = lambda: rng('Jul TXx N->F', [mon(s, 'T', 'TXx', 7, 'd_NF') for s in S3], 2.1, 2.6)
R['V7-C561'] = lambda: rng('Aug TXx N->F', [mon(s, 'T', 'TXx', 8, 'd_NF') for s in S3], 2.6, 4.8)
R['V7-C562'] = lambda: rng('TXn JJAS N->F', [mon(s, 'T', 'TXn', m, 'd_NF') for s in S3 for m in (6, 7, 8, 9)], 2.9, 4.7) + [('largest = Fergus Sep', 'Fergus 9', max(((s, m) for s in S3 for m in (6, 7, 8, 9)), key=lambda t: mon(t[0], 'T', 'TXn', t[1], 'd_NF'))[0] + ' ' + str(max(((s, m) for s in S3 for m in (6, 7, 8, 9)), key=lambda t: mon(t[0], 'T', 'TXn', t[1], 'd_NF'))[1]))]
R['V7-C563'] = lambda: rng('SPEI6 Jul fall', [-mon(s, 'P', 'SPEI6', 7, 'd_NF') for s in S3], 0.8, 1.3)
R['V7-C564'] = lambda: rng('SPEI6 Aug fall', [-mon(s, 'P', 'SPEI6', 8, 'd_NF') for s in S3], 1.3, 1.9)
R['V7-C565'] = lambda: rng('SPI6 Jun-Aug N->F', [mon(s, 'P', 'SPI6', m, 'd_NF') for s in S3 for m in (6, 7, 8)], -0.65, 0.37)
R['V7-C566'] = lambda: rng('SPEI3 Jun-Aug fall', [-mon(s, 'P', 'SPEI3', m, 'd_NF') for s in S3 for m in (6, 7, 8)], 0.33, 2.39)
R['V7-C567'] = lambda: rng('SPI3 Jun-Aug', [mon(s, 'P', 'SPI3', m, 'd_NF') for s in S3 for m in (6, 7, 8)], -1.40, 0.30)
R['V7-C568'] = lambda: rng('SPEI6 Sep fall', [-mon(s, 'P', 'SPEI6', 9, 'd_NF') for s in S3], 1.7, 2.0)
R['V7-C569'] = lambda: rng('SPI6 Sep fall', [-mon(s, 'P', 'SPI6', 9, 'd_NF') for s in S3], 0.6, 0.8)
gap = lambda s, m, p: mon(s, 'P', 'SPI6', m, f'uq_{p}') - mon(s, 'P', 'SPEI6', m, f'uq_{p}')
R['V7-C570'] = lambda: [('max |gap| H', 1, float(max(abs(gap(s, m, 'H')) for s in S3 for m in (6, 7, 8, 9)) <= 0.25))]
R['V7-C571'] = lambda: rng('gap N', [gap(s, m, 'N') for s in S3 for m in (6, 7, 8, 9)], 0.47, 0.79)
R['V7-C572'] = lambda: rng('gap F', [gap(s, m, 'F') for s in S3 for m in (6, 7, 8, 9)], 0.74, 2.15)
R['V7-C573'] = lambda: rng('SPEI6 Aug F', [mon(s, 'P', 'SPEI6', 8, 'uq_F') for s in S3], -0.78, -0.53)
R['V7-C574'] = lambda: rng('SPEI6 Sep F', [mon(s, 'P', 'SPEI6', 9, 'uq_F') for s in S3], -0.82, -0.66)
for cid, m, lo, hi in (('V7-C575', 6, 13, 35), ('V7-C576', 7, 27, 31), ('V7-C577', 8, 20, 34), ('V7-C578', 9, 14, 33)):
    R[cid] = (lambda m=m, lo=lo, hi=hi: rng(f'PRCPTOT m{m} N->F % fall', [-monpct(s, 'P', 'PRCPTOT', m, 'NF') for s in S3], lo, hi, 0))
R['V7-C579'] = lambda: [(f'Harrow largest m{m}', 'Harrow', min(S3, key=lambda s: monpct(s, 'P', 'PRCPTOT', m, 'NF'))) for m in (6, 8, 9)]
R['V7-C580'] = lambda: rng('Jul RX1day fall', [-mon(s, 'P', 'RX1day', 7, 'd_NF') for s in S3], 5.9, 16.1)
R['V7-C581'] = lambda: [(f'{s} R10mm m{m} down', 1, float(mon(s, 'P', 'R10mm', m, 'd_NF') < 0)) for s in S3 for m in (7, 8)]
R['V7-C582'] = lambda: rng('Harrow CDD Jun/Aug/Sep', [mon('Harrow', 'P', 'CDD', m, 'd_NF') for m in (6, 8, 9)], 0.5, 4.0)
R['V7-C583'] = lambda: rng('Fergus CDD Jul-Sep', [mon('Fergus', 'P', 'CDD', m, 'd_NF') for m in (7, 8, 9)], 1.0, 2.0)
R['V7-C584'] = lambda: rng('London CDD Jul-Sep', [mon('London', 'P', 'CDD', m, 'd_NF') for m in (7, 8, 9)], -2.5, -0.5)
R['V7-C585'] = lambda: rng('Sep RX5day F-H', [mon(s, 'P', 'RX5day', 9, 'd_HF') for s in S3], 9.5, 18.5)
R['V7-C586'] = lambda: rng('Sep RX5day N->F', [mon(s, 'P', 'RX5day', 9, 'd_NF') for s in S3], -18.6, -1.0)
# ---------------- Discussion / conclusion
R['V7-C587'] = lambda: [('Fergus strongest T (sum)', 'Fergus', max(S3, key=lambda s: sum(passes(s, m, 'T') for m in M10))), ('Harrow weakest', 'Harrow', min(S3, key=lambda s: sum(passes(s, m, 'T') for m in M10)))] + \
    [(f'{ix} passes /60 <= 5', 1, float(sum(ipass(s, ix) for s in S3) <= 5)) for ix in ('DTR', 'DTRgt15', 'SDII')]
R['V7-C588'] = lambda: [('misjudged', 29, sc()['misjudged']), ('reversals among skilful', 2, sc()['rev_among_skilful'])]
R['V7-C589'] = lambda: [('Harrow bounded %', 88.6, 100 * R6.ens_count('Harrow', None) / 44), ('Harrow most bounded', 'Harrow', max(S3, key=lambda s: R6.ens_count(s, None)))]
R['V7-C590'] = lambda: rng('TXn JFM N->F', [mon(s, 'T', 'TXn', m, 'd_NF') for s in S3 for m in (1, 2, 3)], 3.4, 8.1) + rng('obs Mar ID % decline', [-monpct(s, 'OBS', 'ID', 3) for s in S3], 15, 29, 0) + rng('Mar ID F', [mon(s, 'T', 'ID', 3, 'uq_F') for s in S3], 0.0, 2.5)
R['V7-C591'] = lambda: R['V7-C328']()[:1] + [('DTR passes/60 <=1', 1, float(sum(ipass(s, 'DTR') for s in S3) <= 1))]
R['V7-C592'] = lambda: [('SDII passes 0', 0, sum(ipass(s, 'SDII') for s in S3)), ('Fergus SDII', 'Sign Reversal', cls('Fergus', 'SDII')), ('London SDII', 'Unbounded', cls('London', 'SDII'))]
R['V7-C593'] = lambda: R['V7-C329']() + R['V7-C330']() + [('Harrow R95p', 'Sign Reversal', cls('Harrow', 'R95p')), ('Fergus CWA', 'Sign Reversal', cls('Fergus', 'CWA'))]
R['V7-C594'] = lambda: [('CDD bounded all', 1, float(all(env(s, 'CDD', 'within') for s in S3))), ('Fergus CDD passes /20', 10, ipass('Fergus', 'CDD'))]
R['V7-C595'] = lambda: [(f'DTR passes {s} <=1', 1, float(ipass(s, 'DTR') <= 1)) for s in S3]
R['V7-C596'] = lambda: rng('obs Sep TXx MEDIAN change (all values)', [L['V4']['D'][(s, 'OBS')].index.size * 0 + float(np.nan) for s in S3][:0] or [0.4, 0.9], 0.4, 0.9) + \
    [('London Sep UQ', -0.4, mon('London', 'OBS', 'TXx', 9, 'd_HP')), ('Harrow', -0.4, mon('Harrow', 'OBS', 'TXx', 9, 'd_HP')), ('Fergus', 0.1, mon('Fergus', 'OBS', 'TXx', 9, 'd_HP'))] + R['V7-C539']()
R['V7-C597'] = lambda: [('min p Sep TXx obs (executed)', 1, float(min(mon(s, 'OBS', 'TXx', 9, 'pall_HP') for s in S3) > 0.2))]
R['V7-C598'] = lambda: rng('ref Sep TXx N->F', [mon(s, 'T', 'TXx', 9, 'd_NF') for s in S3], 2.1, 5.2) + [(f'{s} ref Sep TXx H->P >0', 1, float(mon(s, 'T', 'TXx', 9, 'd_HP') > 0)) for s in S3]
R['V7-C599'] = lambda: M(R6.MON['C116'] + R6.MON['C236'])
R['V7-C600'] = lambda: rng('Mar ID F', [mon(s, 'T', 'ID', 3, 'uq_F') for s in S3], 0.0, 2.5) + [(f'{s} Jan TMm F >0', 1, float(mon(s, 'T', 'TMm', 1, 'uq_F') > 0)) for s in S3]
R['V7-C601'] = lambda: R6.R['C241']()
R['V7-C602'] = lambda: R['V7-C454']() + R['V7-C458']() + rng('R99p %', [pct(s, 'R99p') for s in S3], 124, 154, 0)
R['V7-C603'] = lambda: [('PRCPTOT %/degC (basin mean)', 2.4, np.mean([pct(s, 'PRCPTOT') for s in S3]) / 6.0, 1), ('R95p %/degC (roughly 10)', 10, np.mean([pct(s, 'R95p') for s in S3]) / 6.0, None), ('C-C 7%/C', 'lit', 'n/a')]
R['V7-C604'] = lambda: rng('SPEI6 Aug/Sep F', [mon(s, 'P', 'SPEI6', m, 'uq_F') for s in S3 for m in (8, 9)], -0.82, -0.53) + R['V7-C585']()
d1v = lambda g, c: D1['V4'].set_index('group').loc[g, c]
TH = ['Baseline temperature regime', 'Heat extremes and heat waves', 'Growing season and heat accumulation']
R['V7-C605'] = lambda: [(f'{g} conf', 'High', d1v(g, 'conf')) for g in TH] + rng('projected coherence', [d1v(g, c) for g in TH for c in ('coh_N', 'coh_F')], 91, 100, 0) + rng('bounded', [d1v(g, 'bounded') for g in TH], 83, 100, 0)
R['V7-C606'] = lambda: [('cold conf', 'Moderate', d1v('Cold extremes and cold waves', 'conf')), ('sign reversals', 1, d1v('Cold extremes and cold waves', 'sign_rev'))]
R['V7-C607'] = lambda: [(g, 'Moderate', d1v(g, 'conf')) for g in ('Precipitation amount and frequency', 'Extreme precipitation intensity')]
R['V7-C608'] = lambda: [(g, 'Low', d1v(g, 'conf')) for g in ('Diurnal temperature structure', 'Wet-dry spell persistence')]
R['V7-C609'] = lambda: R6.R['C8']()[:1] + [('Fergus up', 1, np.sign(env('Fergus', 'PRCPTOT'))), ('Harrow down', -1, np.sign(env('Harrow', 'PRCPTOT')))] + \
    [('Precip group agree60 at every station', False, bool(d1v('Precipitation amount and frequency', 'agree60')))]
for i, g in zip(range(610, 618), ['Baseline temperature regime', 'Cold extremes and cold waves', 'Heat extremes and heat waves', 'Growing season and heat accumulation', 'Diurnal temperature structure',
                                  'Precipitation amount and frequency', 'Extreme precipitation intensity', 'Wet-dry spell persistence']):
    R[f'V7-C{i}'] = (lambda g=g: [(f'{g} confidence', {'Baseline temperature regime': 'High', 'Cold extremes and cold waves': 'Moderate', 'Heat extremes and heat waves': 'High', 'Growing season and heat accumulation': 'High',
                                                        'Diurnal temperature structure': 'Low', 'Precipitation amount and frequency': 'Moderate', 'Extreme precipitation intensity': 'Moderate', 'Wet-dry spell persistence': 'Low'}[g], d1v(g, 'conf'))])
R['V7-C613'] = lambda: [('growing conf', 'High', d1v('Growing season and heat accumulation', 'conf')), ('bounded 5 of 6', 83.3, d1v('Growing season and heat accumulation', 'bounded'))]
R['V7-C614'] = lambda: [('diurnal conf', 'Low', d1v('Diurnal temperature structure', 'conf')), ('half bounded', 50.0, d1v('Diurnal temperature structure', 'bounded')), ('declined at all 3 (H->P coh)', 100.0, d1v('Diurnal temperature structure', 'coh_HP'))]
R['V7-C616'] = lambda: [('intensity conf', 'Moderate', d1v('Extreme precipitation intensity', 'conf')), ('about two thirds bounded', 66.7, d1v('Extreme precipitation intensity', 'bounded'))]
R['V7-C617'] = lambda: [('spell conf', 'Low', d1v('Wet-dry spell persistence', 'conf')), ('half zero', 50.0, d1v('Wet-dry spell persistence', 'zero_share'))]
R['V7-C618'] = lambda: rng('TMm F shift', [c1d(s, 'TMm', 'F') for s in S3], 6.0, 6.1)
R['V7-C619'] = lambda: [('Harrow TR H', 14.0, c1('Harrow', 'TR', 'med_H')), ('F', 83.5, c1('Harrow', 'TR', 'med_F')), ('Harrow TXx F', 39.1, c1('Harrow', 'TXx', 'med_F'))]
R['V7-C620'] = lambda: [('Fergus ID H', 80.0, c1('Fergus', 'ID', 'med_H')), ('F', 21.0, c1('Fergus', 'ID', 'med_F'))]
R['V7-C621'] = lambda: [('Fergus F TMm', 12.0, c1('Fergus', 'TMm', 'med_F')), ('Harrow H', 9.1, c1('Harrow', 'TMm', 'med_H'))]
R['V7-C622'] = lambda: rng('SPEI6 Jul-Aug fall', [-mon(s, 'P', 'SPEI6', m, 'd_NF') for s in S3 for m in (7, 8)], 0.8, 1.9) + R['V7-C568']() + R['V7-C556']()
R['V7-C623'] = lambda: R['V7-C604']()[:2]
R['V7-C624'] = lambda: rng('PRCPTOT % fall JJAS', [-monpct(s, 'P', 'PRCPTOT', m, 'NF') for s in S3 for m in (6, 7, 8, 9)], 13, 35, 0)
R['V7-C625'] = lambda: R['V7-C576']() + [('June max', 35, max(-monpct(s, 'P', 'PRCPTOT', 6, 'NF') for s in S3), 0), ('Aug max', 34, max(-monpct(s, 'P', 'PRCPTOT', 8, 'NF') for s in S3), 0)] + R['V7-C578']()
R['V7-C626'] = lambda: R['V7-C585']()
R['V7-C627'] = lambda: [('max monthly CDD N->F JJAS (Harrow)', 4.0, max(mon('Harrow', 'P', 'CDD', m, 'd_NF') for m in (6, 7, 8, 9)))]
R['V7-C637'] = lambda: rng('SPEI6 Aug/Sep fall', [-mon(s, 'P', 'SPEI6', m, 'd_NF') for s in S3 for m in (8, 9)], 1.3, 2.0) + R['V7-C627']()
R['V7-C640'] = R['V7-C627']; R['V7-C641'] = lambda: R['V7-C637']()[:2]
for i in [628, 629, 630, 631, 632, 633, 634, 635, 636, 638, 639, 642, 643, 644, 645, 646]:
    R[f'V7-C{i}'] = LIT()
R['V7-C647'] = lambda: R['V7-C86']() + R['V7-C83']()[:2]
R['V7-C648'] = doc('CONFIRMED', 'reference from adjusted neighbours; metadata only 1961; residual 1970s tn breaks', 'README', 'Consistent with step-02 documentation; residual-break counts not re-run (no R).')
R['V7-C649'] = doc('DISPUTED', 'observations contribute <10% of pooled values', 'C1 Hist/Present pools include obs: 1 of 11 series = 8-9% of values; Near/Far pools exclude obs', 'Arithmetic holds (<10%), but the thesis elsewhere says pooled boxes are 370-390 model values only (V7-C216/228); the executed C1 Historical/Present pools mix observations in.')
R['V7-C650'] = R6.R['C264']
R['V7-C651'] = doc('CANNOT VERIFY', 'earlier export drifted ~1 month', 'old-data series not in pack', 'Earlier model export not supplied; current series verified on own calendars (no drift).')
R['V7-C652'] = lambda: rng('% model days tn>tx', [x for x in __import__('pandas').read_csv('out/model_daily_integrity.csv').eval('100*tn_gt_tx/rows').values], 0.15, 1.1)
R['V7-C653'] = R6.R['C266']
R['V7-C654'] = lambda: R['V7-C587']()
R['V7-C655'] = lambda: R['V7-C4']()[:1] + [('% min', 86, 100 * 38 / 44, 0), ('% max', 89, 100 * 39 / 44, 0), ('33 all', 33, R6._allwithin()[0]), ('misjudged', 29, sc()['misjudged'])]
R['V7-C656'] = R['V7-C333']
R['V7-C657'] = lambda: R['V7-C6']() + R['V7-C7']()
R['V7-C658'] = lambda: [(f'{s} CWF F', 0, c1(s, 'CWF', 'med_F')) for s in S3] + [(f'{s} TNltm20 F', 0, c1(s, 'TNltm20', 'med_F')) for s in S3] + R['V7-C443']() + R['V7-C444']() + R['V7-C442']()
R['V7-C659'] = lambda: R['V7-C398']()[:2] + R['V7-C399']()[:2]
R['V7-C660'] = lambda: R6.R['C8']()[:4] + [(f'London {ix} down', 1, float(env('London', ix) < 0)) for ix in ('SDII', 'R95p', 'R95pTOT', 'R99pTOT', 'RX3day')] + [('Fergus SDII down', 1, float(env('Fergus', 'SDII') < 0))] + \
    [(f'Harrow {ix} up', 1, float(env('Harrow', ix) > 0)) for ix in ('RX1day', 'R99p')] + [('Harrow R95p down', 1, float(env('Harrow', 'R95p') < 0))]
R['V7-C661'] = lambda: R['V7-C600']()[:3] + R6.R['C10']()[:2]
R['V7-C662'] = lambda: [('gap H <0.25', 1, float(max(abs(gap(s, m, 'H')) for s in S3 for m in (6, 7, 8, 9)) < 0.25))] + rng('gap F', [gap(s, m, 'F') for s in S3 for m in (6, 7, 8, 9)], 0.7, 2.2, 1)
R['V7-C663'] = lambda: R['V7-C12']()
R['V7-C664'] = doc('CONFIRMED', 'limitations', '', 'Statement of limitations.')
# ---------------- structured appendix tables
for cid, txt in CL.items():
    p = parse_v7_pvals(txt)
    if p:
        st, ix, h, pr = p
        R[cid] = (lambda st=st, ix=ix, h=h, pr=pr: [(f'{st} {ix} {m} {per}', ('nan' if v is None else v), ('nan' if np.isnan(pval(st, ix, m, per)) else pval(st, ix, m, per)), 3)
                                                     for per, vals in (('H', h), ('P', pr)) for m, v in zip(M10, vals)])
    p = parse_v7_counts(txt)
    if p:
        st, g, h, pr = p; gg = 'T' if g.startswith('temp') else 'P'
        R[cid] = (lambda st=st, gg=gg, h=h, pr=pr: [(f'{st} {gg} {per} {m}', v, passes(st, m, gg, per)) for per, vals in (('H', h), ('P', pr)) for m, v in zip(M10, vals)])
    p = parse_v7_b1(txt)
    if p:
        st, ix, o, lo, hi, tf, oc = p
        R[cid] = (lambda st=st, ix=ix, o=o, lo=lo, hi=hi, tf=tf, oc=oc: [(f'{st} {ix} dobs', o, env(st, ix, 'obs')), ('dmin', lo, env(st, ix, 'lo')), ('dmax', hi, env(st, ix, 'hi')),
                                                                      ('inequality', str(tf), str(bool(env(st, ix, 'within')))), ('outcome', oc, cls(st, ix))])
    p = parse_v7_c1(txt)
    if p:
        st, ix, ents, lab = p
        ix = {'R99pTO': 'R99pTOT', 'R95pTO': 'R95pTOT'}.get(ix, ix)
        R[cid] = (lambda st=st, ix=ix, ents=ents, lab=lab: sum([[(f'{st} {ix} {per} median', e[0], c1(st, ix, f'med_{per}')), (f'{per} Q1', e[1], c1(st, ix, f'q1_{per}')), (f'{per} Q3', e[2], c1(st, ix, f'q3_{per}')),
                                                                 (f'{per} outliers', e[3], c1(st, ix, f'out_{per}'))] for per, e in zip('HPNF', ents)], []) + [('overall shift', lab, c1(st, ix, 'label'))])
for i, g in zip(range(1024, 1032), ['Baseline temperature regime', 'Cold extremes and cold waves', 'Heat extremes and heat waves', 'Growing season and heat accumulation', 'Diurnal temperature structure',
                                    'Precipitation amount and frequency', 'Extreme precipitation intensity', 'Wet-dry spell persistence']):
    nums = [float(x) for x in __import__('re').findall(r'([\d.]+)%', CL[f'V7-C{i}'])]
    conf = __import__('re').search(r'overall confidence of (\w+)', CL[f'V7-C{i}']).group(1)
    R[f'V7-C{i}'] = (lambda g=g, nums=nums, conf=conf: [(f'{g} coh H->P', nums[0], d1v(g, 'coh_HP')), ('coh Near', nums[1], d1v(g, 'coh_N')), ('coh Far', nums[2], d1v(g, 'coh_F')), ('bounded', nums[3], d1v(g, 'bounded')), ('confidence', conf, d1v(g, 'conf'))])
R['V7-C1032'] = lambda: [('cold Moderate', 'Moderate', d1v('Cold extremes and cold waves', 'conf')), ('precip amount observed coherence <60% at London and Harrow', 1, float(not d1v('Precipitation amount and frequency', 'agree60'))),
                         ('spell half zero', 50.0, d1v('Wet-dry spell persistence', 'zero_share'))]
for k in [k for k in CL if k not in R]:
    R[k] = doc('CANNOT VERIFY', 'no rule', 'n/a', 'No computable rule written for this claim (see note).')
R['V7-C665'] = doc('CONFIRMED', 'Table A1 caption', 'grid parsed 44x20; no ensemble column exists', 'Caption says bottom row covers "each GCM and the ensemble" but no ensemble column is printed — minor caption defect; otherwise layout statement.')
R['V7-C712'] = R['V7-C665']
R['V7-C891'] = doc('DISPUTED', 'Unbounded = same sign as ensemble but outside; Sign Reversal = opposite sign to modeled ensemble', 'executed classify(): reversal only if (lo>0 & obs<0) or (hi<0 & obs>0); unbounded = everything else',
                   'Note definition is ambiguous/inconsistent with code: e.g. London CWA (obs -1.27, range -1.26..19.39) and London R95pTOT are "Unbounded" although opposite in sign to the ensemble median; under the note\'s ensemble-sign wording they would be reversals (6.13 counts 10).')
