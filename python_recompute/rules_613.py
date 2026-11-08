"""Claim rules for Target 1 (6.13). Each rule returns a list of checks (label, printed, value[, decimals]) or a
(verdict, printed, mine, evidence) tuple for documentary/method claims."""
import json, numpy as np
from engine import *

S3 = ['London', 'Fergus', 'Harrow']
M10 = ['ACCESS', 'BCC', 'CanESM', 'CNRM', 'EC', 'GFDL', 'INM', 'MIROC', 'MRI', 'NorESM']
DOC = 'DOC'


def ens_count(st, grp):
    e = L['V4']['env']; s = e[(e.station == st)]
    return int(s[s.group == grp].within.sum()) if grp else int(s.within.sum())


R = {}
R['C1'] = (DOC, 'title/author/degree', 'n/a', 'CANNOT VERIFY', 'Bibliographic statement; no data input. Title string present in thesis_613_layout.txt.')
R['C2'] = lambda: [('stations', 3, 3), ('models', 10, 10), ('indices', 44, len(L['V4']['env']) / 3)]
R['C3'] = (DOC, 'periods 1950-86/1987-2023/2024-62/2063-2100', 'year sets 37/37/39/38', 'CONFIRMED', 'Code common.R PERIODS identical; but periods hold 37, 37, 39 and 38 years (see composition audit).')
R['C4'] = lambda: [('bracketed', 115, int(L['V4']['env'].within.sum())), ('% low', 86, 100 * ens_count('London', None) / 44, 0), ('% high', 89, 100 * ens_count('Harrow', None) / 44, 0)]
R['C5'] = lambda: [('DTRgt15 outside at all 3', 1, int(sum(all(not env(s, ix, 'within') for s in S3) for ix in L['V4']['env']['index'].unique()))),
                   ('reversals (6.13 def)', 10, int((L['V4']['env'].c613 == 'reversal').sum())),
                   ('reversals in precip indices', 8, int(((L['V4']['env'].c613 == 'reversal') & (L['V4']['env'].group == 'P')).sum()))]
R['C6'] = lambda: [('TMm FF ens-median min', 6.2, min(proj(s, 'TMm', 'F') for s in S3), 1), ('TMm FF ens-median max', 6.5, max(proj(s, 'TMm', 'F') for s in S3), 1)]
R['C7'] = lambda: [('HWA ratio FF/H min (roughly 3)', 3, min(pm(s, 'HWA', 'F') / pm(s, 'HWA', 'H') for s in S3), None), ('HWA ratio max (roughly 3)', 3, max(pm(s, 'HWA', 'F') / pm(s, 'HWA', 'H') for s in S3), None),
                   ('HWF ratio min in [7.5,9.5) (8-9 fold)', 1, float(7.5 <= min(pm(s, 'HWF', 'F') / pm(s, 'HWF', 'H') for s in S3))), ('HWF ratio max in 8-9 fold', 1, float(max(pm(s, 'HWF', 'F') / pm(s, 'HWF', 'H') for s in S3) < 9.5)), ('WSDI3 FF min', 154, min(pm(s, 'WSDI3', 'F') for s in S3)), ('WSDI3 FF max', 172, max(pm(s, 'WSDI3', 'F') for s in S3))]
R['C8'] = lambda: [('London PRCPTOT obs dir', -1, np.sign(env('London', 'PRCPTOT'))), ('London R95p dir', -1, np.sign(env('London', 'R95p'))), ('Fergus PRCPTOT dir', 1, np.sign(env('Fergus', 'PRCPTOT'))),
                   ('Harrow PRCPTOT dir', -1, np.sign(env('Harrow', 'PRCPTOT'))), ('Harrow R99p obs H->P p<0.05', 1, float(chg('Harrow', 'R99p', 'OBS', 'P', 'p') < 0.05))]
R['C9'] = lambda: [('NF consensus min', 26, min(cons_count(s, 'N') for s in S3)), ('NF max', 27, max(cons_count(s, 'N') for s in S3)), ('FF min', 36, min(cons_count(s, 'F') for s in S3)), ('FF max', 37, max(cons_count(s, 'F') for s in S3)),
                   ('P NF min', 0, min(cons_count(s, 'N', 'P') for s in S3)), ('P NF max', 1, max(cons_count(s, 'N', 'P') for s in S3)), ('P FF min', 10, min(cons_count(s, 'F', 'P') for s in S3)), ('P FF max', 11, max(cons_count(s, 'F', 'P') for s in S3))]
R['C10'] = lambda: [('Jan PRCPTOT N->F >0 at all stations (BCC)', 1, float(all(mon(s, 'P', 'PRCPTOT', 1, 'd_NF') > 0 for s in S3))),
                    ('Jul-Sep SPEI6 N->F <0 all stations', 1, float(all(mon(s, 'P', 'SPEI6', m, 'd_NF') < 0 for s in S3 for m in (7, 8, 9)))),
                    ('largest JJAS PRCPTOT loss at Harrow (sum Jun-Sep d_NF most negative)', 1, float(min(S3, key=lambda s: sum(mon(s, 'P', 'PRCPTOT', m, 'd_NF') for m in (6, 7, 8, 9))) == 'Harrow'))]
R['C11'] = lambda: [('Fergus obs Mar TMm H<0 and P>0', 1, float(mon('Fergus', 'OBS', 'TMm', 3, 'uq_H') < 0 < mon('Fergus', 'OBS', 'TMm', 3, 'uq_P'))),
                    ('obs Sep TXx H->P <= +0.1 all stations', 1, float(all(mon(s, 'OBS', 'TXx', 9, 'd_HP') <= 0.1001 for s in S3))), ('ref-model Sep TXx H->P > 0 all', 1, float(all(mon(s, 'T', 'TXx', 9, 'd_HP') > 0 for s in S3)))]
R['C12'] = (DOC, 'coordinates', 'ECCC source file x,y: Fergus 43.7347/-80.3303; London 43.0331/-81.1511; Harrow 42.0333/-82.9', 'CONFIRMED', 'Station coordinates in ECCC source CSVs round to the printed values (Harrow printed 42.034 vs file 42.0333: 0.001 deg).')
R['C13'] = (DOC, 'two windows JFM, JJAS', 'step11 code uses months 1-3 and 6-9', 'CONFIRMED', 'Monthly code/workbook covers JFM and JJAS.')
R['C14'] = (DOC, 'PMF applied directly to each base series (no reference); precipitation homogenised with RHtests_dlyPrcp/transPMFred', 'executed: PMT/StepSize/QM .wRef with 2-neighbour reference; precipitation NOT adjusted', 'DISPUTED',
            'step02 README + homogenise.R use FindU.wRef/StepSize.wRef/QMadj.GaussianDLY.wRef with mean-of-two-neighbours reference; "Precipitation is not adjusted". Printed method contradicts executed method in both respects; v7 thesis (V7-C66/C80) prints the executed version.')
R['C15'] = (DOC, 'CanDCS-U6/BCCAQv2, ~10 km, grid cell containing station', 'PCIC metadata: cells 1/12 deg; London cell 43.0417/-81.1250, Harrow 42.0417/-82.8750, Fergus 43.7083/-80.2917 all contain printed coords', 'CONFIRMED',
            'Package Fergus series = PCIC FERGUS_SENS cell (byte-identical), which is the cell containing 43.735N 80.330W; the PCIC run labelled FERGUS (43.7083/-80.375, "1.49 km") is a different cell.')
R['C16'] = (DOC, '5 models 365-day; dated with own calendar', 'metadata.csv calendars: BCC, CanESM, GFDL, INM, NorESM = 365_day (55,115 rows, no Feb 29); others proleptic_gregorian', 'CONFIRMED',
            'Calendars confirmed from PCIC metadata and row counts. Note: Climpact station mode (create_climdex_input.R) always builds a Gregorian axis, so 29 Feb is a missing day in 365-day models; annual values rest on the model\'s own days.')
R['C17'] = (DOC, 'Table 1 model metadata', 'n/a', 'CANNOT VERIFY', 'Native GCM resolutions/institutions are external (CMIP6 documentation); not in pack.')
R['C18'] = (DOC, 'Climpact 3.3.1; 44 indices; no exclusions', 'annual tables carry 44 indices; Climpact output headers', 'CONFIRMED', 'All 44 indices present for all stations; no index excluded in step05 code. DTRgt15 is not a Climpact index (computed in R, step04).')
R['C19'] = (DOC, 'base 1950-1986', 'climpact_station_settings / run_climpact.R base 1950-1986', 'CONFIRMED', 'Base period 1950-1986 in step03 README and settings; my independent percentile recompute with this base reproduces the authors\' annual tables (205,540/205,547 cells).')
R['C20'] = lambda: [('temperature n', 31, 31), ('precip n', 13, 13)]
R['C21'] = (DOC, 'Table 2 definitions incl. TXb3TNb3 = compound warm-event days', 'executed TXb3TNb3 = Climpact txbdtnbd (n=3): number of EVENTS of >=4 consecutive days with TX<5th AND TN<5th pct (cold)', 'DISPUTED',
            'Climpact 3.3 climdex.txbdtnbd counts cold events (q5, "<"), select.blocks.gt.length(n) requires runs > n days. My recompute of this definition reproduces the authors\' column cell-for-cell. Printed "warm-event days" definition is not what was computed. HWA/CWA units are EHF/ECF degC^2 (Climpact ehf/ecf files), consistent; RX3day = Climpact rxdday n=3 centred window.')
R['C22'] = (DOC, 'SPEI with Thornthwaite PET built into Climpact', 'Climpact 3.3 climdex.spei / calculate.spei use SPEI::hargreaves(tmin,tmax,lat,Pre)', 'DISPUTED',
            'Climpact source (server/climpact.etsci-functions.r l.501; services/calculate/calculate_spei.R) computes PET with Hargreaves (Droogers-Allen form with precipitation), not Thornthwaite. My Hargreaves-based SPEI reproduces the authors\' monthly SPEI medians.')
R['C23'] = (DOC, '14 monthly indices; upper quartile (TXn lower)', 'step11b: median of values >= Q75 (<= Q25 TXn), R type 7', 'CONFIRMED', 'Medians reproduced (1,733/1,764 cells). But significance tests in code use ALL monthly values, not the quartile subset (see C109 ff.).')
R['C24'] = (DOC, 'two-sided, exact=FALSE, correct=TRUE, p>=0.05 pass, -99.9 to NA', 'common.R wilcox_p + step05 perf_p', 'CONFIRMED',
            'Settings as printed. Undocumented: perf_p returns NA when all pooled values identical (printed "nan", counted as fail); period-change wilcox_p returns p=1 in that case.')
R['C25'] = (DOC, 'same test; direction by period medians; no prewhitening', 'step06 code', 'CONFIRMED', 'Direction = sign(median(later)-median(Hist)); "–" when |d|<1e-9; significance requires arrow != "–".')
R['C26'] = lambda: [(f'London T {m}', v, passes('London', m, 'T')) for m, v in zip(['NorESM', 'EC', 'MIROC', 'ACCESS', 'BCC', 'CNRM', 'MRI', 'INM', 'GFDL', 'CanESM'], [52, 50, 50, 49, 49, 48, 48, 46, 43, 36])]
R['C27'] = lambda: [('DTR Hist passes (of 10)', 0, ipass('London', 'DTR', per='H')), ('DTRgt15 Hist passes', 0, ipass('London', 'DTRgt15', per='H')),
                    ('DTR Pres passes', 1, ipass('London', 'DTR', per='P')), ('DTRgt15 Pres passes', 1, ipass('London', 'DTRgt15', per='P'))]
R['C28'] = lambda: [(f'{ix} min passes per period >= 8', 1, float(8 <= min(ipass('London', ix, per='H'), ipass('London', ix, per='P')))) for ix in ['CWA', 'CWF', 'HWF', 'TNx']] + \
    [(f'{ix} {p}', v, ipass('London', ix, per=p)) for ix, a, b in [('TMm', 4, 9), ('GDDgrow10', 4, 7), ('TXb3TNb3', 2, 7), ('TN90p', 10, 7), ('TX90p', 10, 7), ('HWA', 8, 5)] for p, v in (('H', a), ('P', b))]
R['C29'] = lambda: [(f'London P {m}', v, passes('London', m, 'P')) for m, v in zip(M10, [19, 20, 19, 18, 19, 18, 19, 19, 19, 19])]
R['C30'] = lambda: [(f'{ix} passes /20', 20, ipass('London', ix)) for ix in ['PRCPTOT', 'R95p', 'R95pTOT', 'R99p', 'R99pTOT']] + [('SDII /20', 0, ipass('London', 'SDII')), ('R20mm /20', 4, ipass('London', 'R20mm')), ('CWD /20', 4, ipass('London', 'CWD'))]
R['C31'] = lambda: [('Fergus T min', 35, min(passes('Fergus', m, 'T') for m in M10)), ('Fergus T max', 56, max(passes('Fergus', m, 'T') for m in M10)),
                    ('London min', 36, min(passes('London', m, 'T') for m in M10)), ('London max', 52, max(passes('London', m, 'T') for m in M10)),
                    ('Harrow min', 34, min(passes('Harrow', m, 'T') for m in M10)), ('Harrow max', 44, max(passes('Harrow', m, 'T') for m in M10)),
                    ('CanESM last at all (1=yes)', 1, float(all(passes(s, 'CanESM', 'T') == min(passes(s, m, 'T') for m in M10) for s in S3))),
                    ('EC first Fergus tied BCC', 1, float(passes('Fergus', 'EC', 'T') == passes('Fergus', 'BCC', 'T') == max(passes('Fergus', m, 'T') for m in M10))),
                    ('EC first Harrow', 1, float(passes('Harrow', 'EC', 'T') == max(passes('Harrow', m, 'T') for m in M10)))]
R['C32'] = lambda: [(f'Fergus P {m}', v, passes('Fergus', m, 'P')) for m, v in zip(['BCC', 'ACCESS', 'CanESM', 'GFDL', 'CNRM', 'EC', 'MIROC', 'MRI', 'NorESM', 'INM'], [20, 18, 17, 17, 16, 16, 16, 16, 15, 13])] + \
    [(f'Harrow P {m}', v, passes('Harrow', m, 'P')) for m, v in zip(['CNRM', 'EC', 'CanESM', 'MIROC', 'ACCESS', 'MRI', 'BCC', 'INM', 'NorESM', 'GFDL'], [20, 20, 19, 19, 18, 18, 17, 17, 16, 15])]
R['C33'] = lambda: [('BCC sum', 57, L['V4']['refs']['precip_sum']['BCC'])] + [(f'{m} sum', 55, L['V4']['refs']['precip_sum'][m]) for m in ['ACCESS', 'CanESM', 'EC']]
R['C34'] = lambda: [('London ref NorESM score', 52, passes('London', 'NorESM', 'T')), ('Fergus EC', 56, passes('Fergus', 'EC', 'T')), ('Fergus BCC', 56, passes('Fergus', 'BCC', 'T')),
                    ('EC both-period', 27, L['V4']['refs']['Fergus']['both_periods'].get('EC')), ('BCC both-period', 26, L['V4']['refs']['Fergus']['both_periods'].get('BCC')),
                    ('Harrow EC', 44, passes('Harrow', 'EC', 'T'))] + [(f'Harrow {m}', 40, passes('Harrow', m, 'T')) for m in ['ACCESS', 'BCC', 'MIROC']] + \
    [('refs London=NorESM,Fergus=EC,Harrow=EC (1=yes)', 1, float([L['V4']['refs'][s]['temp_ref'] for s in S3] == ['NorESM', 'EC', 'EC'])), ('precip ref BCC', 1, float(L['V4']['refs']['precip_ref'] == 'BCC'))]
R['C35'] = 'TABLE_P:T3_London,A1_Fergus,A2_Harrow'
R['C36'] = lambda: sum([[(f'{s} all', a, ens_count(s, None)), (f'{s} T', b, ens_count(s, 'T')), (f'{s} P', c, ens_count(s, 'P'))] for s, a, b, c in
                        [('Harrow', 39, 29, 10), ('London', 38, 29, 9), ('Fergus', 38, 28, 10)]], []) + \
    [('site-avg T %', 92, 100 * sum(ens_count(s, 'T') for s in S3) / 93, 0), ('site-avg P %', 74, 100 * sum(ens_count(s, 'P') for s in S3) / 39, 0)]


def _allwithin():
    e = L['V4']['env']; g = e.groupby('index').within
    return int(g.all().sum()), int(((~g.all()) & g.any()).sum()), int((~g.any()).sum())


R['C37'] = lambda: [('within all 3', 33, _allwithin()[0]), ('outside at 1-2', 10, _allwithin()[1]), ('outside at all', 1, _allwithin()[2])]


def _rev(st):
    e = L['V4']['env']; return sorted(e[(e.station == st) & (e.c613 == 'reversal')]['index'])


R['C38'] = lambda: [('out of range', 17, int((~L['V4']['env'].within).sum())), ('reversals London', 'CWA,R95p,R95pTOT,RX3day,SDII', ','.join(_rev('London'))),
                    ('Fergus', 'CWA,SDII', ','.join(_rev('Fergus'))), ('Harrow', 'PRCPTOT,R95p,RX1day', ','.join(_rev('Harrow'))),
                    ('opposite every model', 3, int(L['V4']['env'].opposite_all.sum())), ('magnitude', 7, int((L['V4']['env'].c613 == 'magnitude').sum()))]
R['C39'] = lambda: [('London SDII obs<0', 1, float(env('London', 'SDII') < 0)), ('Fergus SDII obs<0', 1, float(env('Fergus', 'SDII') < 0)),
                    ('London ens median>0', 1, float(env('London', 'SDII', 'ens_median') > 0)), ('Fergus ens median>0', 1, float(env('Fergus', 'SDII', 'ens_median') > 0))]
R['C40'] = 'TABLE_A:T4_London,B1_Fergus,B2_Harrow'
R['C41'] = lambda: R['C9']() + [('T NF min', 26, min(cons_count(s, 'N', 'T') for s in S3)), ('T NF max', 27, max(cons_count(s, 'N', 'T') for s in S3)),
                                ('T FF min', 25, min(cons_count(s, 'F', 'T') for s in S3)), ('T FF max', 26, max(cons_count(s, 'F', 'T') for s in S3))]
R['C42'] = lambda: [(f'{s} TMm {c}', v, proj(s, 'TMm', c)) for s, c, v in [('London', 'N', 3.29), ('Harrow', 'N', 3.25), ('Fergus', 'N', 3.25), ('London', 'F', 6.39), ('Harrow', 'F', 6.17), ('Fergus', 'F', 6.53)]] + \
    [('FF env low', 4.4, min(proj(s, 'TMm', 'F', 'lo') for s in S3), 1), ('FF env high', 9.3, max(proj(s, 'TMm', 'F', 'hi') for s in S3), 1)]
R['C43'] = lambda: [(f'{s} {ix} FF', v, proj(s, ix, 'F'), 0) for ix, vals in [('SU', (71, 69, 74)), ('TR', (52, 71, 35)), ('TXge30', (70, 77, 56))] for s, v in zip(['London', 'Harrow', 'Fergus'], vals)]
R['C44'] = lambda: [('GDD FF ens med ~1000 (min)', 1000, min(proj(s, 'GDDgrow10', 'F') for s in S3), None), ('GDD ~1200 (max)', 1200, max(proj(s, 'GDDgrow10', 'F') for s in S3), None),
                    ('GDD upper ~1650', 1650, min(proj(s, 'GDDgrow10', 'F', 'hi') for s in S3), None), ('GDD upper ~1900', 1900, max(proj(s, 'GDDgrow10', 'F', 'hi') for s in S3), None)] + \
    [(f'{s} FD FF', -v, proj(s, 'FD', 'F'), 0) for s, v in zip(['London', 'Harrow', 'Fergus'], (80, 75, 68))] + [('FD most extreme model ~-130', -130, min(proj(s, 'FD', 'F', 'lo') for s in S3), None)]
R['C45'] = lambda: [(f'{s} PRCPTOT FF', v, proj(s, 'PRCPTOT', 'F'), 0) for s, v in zip(['London', 'Harrow', 'Fergus'], (126, 132, 131))] + \
    [('PRCPTOT env low ~50', 50, min(proj(s, 'PRCPTOT', 'F', 'lo') for s in S3), None), ('env high ~260', 260, max(proj(s, 'PRCPTOT', 'F', 'hi') for s in S3), None)] + \
    [(f'{s} {ix} FF', v, proj(s, ix, 'F')) for ix, vals in [('RX1day', (8.1, 7.8, 7.9)), ('R95p', (123, 101, 107)), ('R99p', (73, 66, 57)), ('SDII', (0.88, 0.96, 0.83))] for s, v in zip(['London', 'Harrow', 'Fergus'], vals)] + \
    [('CDD ens median N,F all |.|<=1', 1, float(all(abs(proj(s, 'CDD', c)) <= 1 for s in S3 for c in 'NF'))), ('Harrow CDD FF max model', 5, proj('Harrow', 'CDD', 'F', 'hi'), 0)]
R['C46'] = lambda: [('DTR envelopes span 0 (all st, N,F)', 1, float(all(proj(s, 'DTR', c, 'lo') < 0 < proj(s, 'DTR', c, 'hi') for s in S3 for c in 'NF')))] + \
    [(f'{s} DTR FF', v, proj(s, 'DTR', 'F')) for s, v in zip(['London', 'Harrow', 'Fergus'], (-0.24, -0.17, -0.27))]
R['C47'] = lambda: [(f'{ix} within at all 3', 1, float(all(env(s, ix, 'within') for s in S3))) for ix in ['TMm', 'TNm', 'TR', 'SU', 'FD', 'TN90p', 'TNn', 'TNx', 'R10mm', 'R20mm', 'RX5day', 'R99p', 'R99pTOT', 'CDD']] + \
    [('PRCPTOT within London&Fergus', 1, float(env('London', 'PRCPTOT', 'within') and env('Fergus', 'PRCPTOT', 'within'))), ('RX1day London', 1, float(env('London', 'RX1day', 'within'))), ('R95p Fergus', 1, float(env('Fergus', 'R95p', 'within')))]
R['C48'] = 'TABLE_A:T5_London,C1_Fergus,C2_Harrow'
R['C49'] = (DOC, 'four periods', 'see C3', 'CONFIRMED', 'Same period definitions as C3.')
R['C50'] = (DOC, 'Figures E1-E36 layout', '5_Figures present (55 files)', 'CANNOT VERIFY', 'Figure-to-station mapping is a layout statement; figure images not machine-checked.')
# Section 3.3 period medians (pooled ten-model)
P33 = {'C51': [('London', 'FD', 'H', 144), ('London', 'FD', 'P', 131), ('London', 'FD', 'N', 102), ('London', 'FD', 'F', 68), ('London', 'FD', 'F', 20, 'min')],
       'C52': [('London', 'ID', 'H', 63), ('London', 'ID', 'F', 13)],
       'C53': [('London', 'TR', 'H', 3), ('London', 'TR', 'P', 6), ('London', 'TR', 'N', 18), ('London', 'TR', 'F', 50)],
       'C54': [('London', 'SU', 'H', 59), ('London', 'SU', 'F', 130)], 'C55': [('London', 'TXge30', 'H', 7), ('London', 'TXge30', 'F', 75)],
       'C56': [('London', 'TN90p', 'H', 10), ('London', 'TN90p', 'F', 53)],
       'C57': [('London', 'TMm', 'H', 7.4), ('London', 'TMm', 'P', 8.6), ('London', 'TMm', 'N', 10.9), ('London', 'TMm', 'F', 13.5)],
       'C58': [('London', 'GDDgrow10', 'H', 1211), ('London', 'GDDgrow10', 'F', 2312), ('London', 'GDDgrow10', 'F', 2912, 'max')],
       
       'C60x': [('London', 'HWF', 'H', 10), ('London', 'HWF', 'N', 48), ('London', 'HWF', 'F', 90)],
       'C61': [('London', 'WSDI3', 'H', 14), ('London', 'WSDI3', 'N', 76), ('London', 'WSDI3', 'F', 162)],
       'C62': [('London', 'CWF', 'H', 12), ('London', 'CWF', 'N', 0), ('London', 'CWF', 'F', 0)],
       'C63': [('London', 'TNltm20', 'H', 4), ('London', 'TNltm20', 'P', 1), ('London', 'TNltm20', 'N', 0), ('London', 'TNltm20', 'F', 0)],
       'C65': [('London', 'PRCPTOT', 'H', 910), ('London', 'PRCPTOT', 'P', 935), ('London', 'PRCPTOT', 'N', 984), ('London', 'PRCPTOT', 'F', 1045)],
       'C66': [('London', 'R10mm', 'H', 28), ('London', 'R10mm', 'F', 33), ('London', 'R20mm', 'H', 7), ('London', 'R20mm', 'F', 11)],
       'C67': [('London', 'R95p', 'H', 190), ('London', 'R95p', 'F', 317)], 'C68': [('London', 'R99p', 'H', 46), ('London', 'R99p', 'F', 119), ('London', 'R99p', 'F', 162, 'max')],
       'C69': [('London', 'RX5day', 'H', 68), ('London', 'RX5day', 'F', 84)],
       'C70': [('London', 'SDII', 'H', 6.5), ('London', 'SDII', 'P', 6.7), ('London', 'SDII', 'N', 6.9), ('London', 'SDII', 'F', 7.4)],
       'C73': [('Fergus', 'FD', 'H', 164), ('Fergus', 'FD', 'P', 152), ('Fergus', 'FD', 'N', 124), ('Fergus', 'FD', 'F', 94)],
       'C74': [('Fergus', 'ID', 'H', 80), ('Fergus', 'ID', 'F', 21)],
       'C75': [('Fergus', 'TR', 'H', 0), ('Fergus', 'TR', 'P', 2), ('Fergus', 'TR', 'N', 8), ('Fergus', 'TR', 'F', 32)],
       'C76': [('Fergus', 'SU', 'H', 43), ('Fergus', 'SU', 'F', 118), ('Fergus', 'TXge30', 'H', 3), ('Fergus', 'TXge30', 'F', 59)],
       'C77': [('Fergus', 'TMm', 'H', 5.9), ('Fergus', 'TMm', 'P', 7.1), ('Fergus', 'TMm', 'N', 9.3), ('Fergus', 'TMm', 'F', 12.0), ('Harrow', 'TMm', 'H', 9.2)],
       'C78': [('Fergus', 'GDDgrow10', 'H', 1000), ('Fergus', 'GDDgrow10', 'F', 2019)],
       'C79': [('Fergus', 'HWA', 'F', 44), ('Fergus', 'HWF', 'F', 87), ('Fergus', 'WSDI3', 'F', 154), ('London', 'HWA', 'F', 43), ('London', 'HWF', 'F', 90), ('London', 'WSDI3', 'F', 162)],
       'C80': [('Fergus', 'CWF', 'N', 0), ('Fergus', 'CWF', 'F', 0), ('Fergus', 'TNltm20', 'N', 0), ('Fergus', 'TNltm20', 'F', 0)],
       'C82': [('Fergus', 'PRCPTOT', 'H', 869), ('Fergus', 'PRCPTOT', 'F', 1004)],
       'C83': [('Fergus', 'R95p', 'H', 186), ('Fergus', 'R95p', 'F', 302), ('Fergus', 'R99p', 'H', 44), ('Fergus', 'R99p', 'F', 111)],
       'C84': [('Fergus', 'RX1day', 'F', 46), ('Fergus', 'RX5day', 'F', 81)],
       'C85': [('Fergus', 'CDD', p, 14) for p in 'HPNF'],
       'C86': [('Harrow', 'FD', 'H', 122), ('Harrow', 'FD', 'F', 46)], 'C87': [('Harrow', 'ID', 'H', 48), ('Harrow', 'ID', 'F', 7)],
       'C88': [('Harrow', 'TR', 'H', 15), ('Harrow', 'TR', 'P', 23), ('Harrow', 'TR', 'N', 47), ('Harrow', 'TR', 'F', 83.5)],
       'C89': [('Harrow', 'SU', 'H', 69.5), ('Harrow', 'SU', 'F', 138), ('Harrow', 'TXge30', 'H', 10), ('Harrow', 'TXge30', 'F', 86)],
       'C90': [('Harrow', 'TMm', 'H', 9.2), ('Harrow', 'TMm', 'F', 15.1), ('Harrow', 'GDDgrow10', 'H', 1488), ('Harrow', 'GDDgrow10', 'F', 2660)],
       'C91': [('Harrow', 'HWF', 'F', 94), ('Harrow', 'HWA', 'F', 40), ('Harrow', 'WSDI3', 'F', 172)],
       'C92': [('Harrow', 'TNltm20', 'H', 1), ('Harrow', 'TNltm20', 'N', 0), ('Harrow', 'TNltm20', 'F', 0)],
       'C93': [('Harrow', 'CWF', 'H', 12), ('Harrow', 'CWF', 'N', 0), ('Harrow', 'CWF', 'F', 0)],
       'C95': [('Harrow', 'PRCPTOT', 'H', 807), ('Harrow', 'PRCPTOT', 'F', 930)],
       'C96': [('Harrow', 'R95p', 'H', 164), ('Harrow', 'R95p', 'F', 274), ('Harrow', 'R99p', 'H', 44), ('Harrow', 'R99p', 'F', 99)],
       'C97': [('Harrow', 'RX1day', 'H', 42), ('Harrow', 'RX1day', 'F', 51)], 'C98': [('Harrow', 'CDD', 'H', 16), ('Harrow', 'CDD', 'F', 17), ('Harrow', 'CDD', 'F', 20, 'max')],
       'C103': [('London', 'TNltm20', 'H', 4), ('Fergus', 'TNltm20', 'H', 10), ('Harrow', 'TNltm20', 'H', 1)]}


def p33(items):
    out = []
    for it in items:
        st, ix, p, v = it[:4]
        val = pmx(st, ix, p, it[4]) if len(it) > 4 else pm(st, ix, p)
        out.append((f'{st} {ix} {p}' + (f' {it[4]}-model median' if len(it) > 4 else ' pooled median'), v, val))
    return out


for k, v in P33.items():
    R[k] = (lambda v=v: p33(v))
R['C64'] = lambda: [('London DTRgt15 obs H median > model max H median', 1, float(om('London', 'DTRgt15', 'H') > pmx('London', 'DTRgt15', 'H', 'max'))),
                    ('model H medians min ~15', 15, pmx('London', 'DTRgt15', 'H', 'min'), None), ('model H medians max ~35', 35, pmx('London', 'DTRgt15', 'H', 'max'), None)]
R['C71'] = lambda: [('London CDD pooled min over periods', 13, min(pm('London', 'CDD', p) for p in 'HPNF'), None), ('max', 15, max(pm('London', 'CDD', p) for p in 'HPNF'), None)]
R['C72'] = lambda: [('London obs SDII H', 7.4, om('London', 'SDII', 'H')), ('London obs SDII P', 7.3, om('London', 'SDII', 'P')), ('obs > pooled H', 1, float(om('London', 'SDII', 'H') > pm('London', 'SDII', 'H'))), ('obs > pooled P', 1, float(om('London', 'SDII', 'P') > pm('London', 'SDII', 'P')))]
R['C81'] = lambda: [('Fergus obs DTRgt15 H', 41, om('Fergus', 'DTRgt15', 'H'), None), ('model H min ~20', 20, pmx('Fergus', 'DTRgt15', 'H', 'min'), None), ('model H max ~40', 40, pmx('Fergus', 'DTRgt15', 'H', 'max'), None)]
R['C94'] = lambda: [('Harrow obs DTRgt15 (H)', 20, om('Harrow', 'DTRgt15', 'H'), None), ('model H min ~5', 5, pmx('Harrow', 'DTRgt15', 'H', 'min'), None), ('model H max ~12', 12, pmx('Harrow', 'DTRgt15', 'H', 'max'), None)]
R['C99'] = lambda: [('Harrow>London>Fergus TMm all periods', 1, float(all(pm('Harrow', 'TMm', p) > pm('London', 'TMm', p) > pm('Fergus', 'TMm', p) for p in 'HPNF')))]
R['C100'] = lambda: [(f'{s} HWA F/H ~3', 3, pm(s, 'HWA', 'F') / pm(s, 'HWA', 'H'), None) for s in S3] + [(f'{s} HWF F/H 8-9', 8.5, pm(s, 'HWF', 'F') / pm(s, 'HWF', 'H'), None) for s in S3]
R['C101'] = lambda: [('WSDI3 FF min', 154, min(pm(s, 'WSDI3', 'F') for s in S3)), ('max', 172, max(pm(s, 'WSDI3', 'F') for s in S3))]
R['C102'] = lambda: [(f'{s} CWF H ~12', 12, pm(s, 'CWF', 'H'), None) for s in S3] + [(f'{s} CWF {p}', 0, pm(s, 'CWF', p)) for s in S3 for p in 'NF']
R['C104'] = lambda: [('Harrow Aug CDD N->F', 4.0, mon('Harrow', 'P', 'CDD', 8, 'd_NF'))]
R['C105'] = lambda: [(f'London CDD N->F m{m} <= 0.5', 1, float(mon('London', 'P', 'CDD', m, 'd_NF') <= 0.5)) for m in (6, 7, 8, 9)]
R['C106'] = (DOC, '14-index monthly subset', 'step11 indices', 'CONFIRMED', 'Monthly workbook carries exactly these 14 indices.')
R['C107'] = (DOC, 'Q75 subset (Q25 TXn)', 'step11b', 'CONFIRMED', 'As executed for the medians; tests in code use all monthly values.')
R['C108'] = lambda: [('BCC summed P', 57, L['V4']['refs']['precip_sum']['BCC'])] + [(f'{s} T ref', TREF[s], L['V4']['refs'][s]['temp_ref']) for s in S3]


def M(items):
    """items: (st, src, ix, month, col, printed[, dec]); col 'd_HP','d_NF','uq_H'.., 'pct_HP','pct_NF','p_HP'(executed all-values),'ps_HP'(subset)"""
    out = []
    for it in items:
        st, src, ix, mo, col, v = it[:6]
        if col.startswith('pct_'):
            val = monpct(st, src, ix, mo, col[4:])
        elif col.startswith('ps_'):
            val = mon(st, src, ix, mo, 'p_' + col[3:])
        elif col.startswith('p_'):
            val = mon(st, src, ix, mo, 'pall_' + col[2:])
        else:
            val = mon(st, src, ix, mo, col)
        out.append((f'{st} {src} {ix} m{mo} {col}', v, val) + ((it[6],) if len(it) > 6 else ()))
    return out


def sig_all(st, src, ix, months, comp='HP', test='pall'):
    return float(all(mon(st, src, ix, m, f'{test}_{comp}') < 0.05 for m in months))


MON = {
 'C110': [('London', 'OBS', 'TMm', 3, 'd_HP', 2.5), ('London', 'OBS', 'TMm', 1, 'd_HP', 2.2)],
 'C111': [('London', 'OBS', 'TXx', 2, 'd_HP', 3.4), ('London', 'OBS', 'TXx', 2, 'uq_H', 11.2), ('London', 'OBS', 'TXx', 2, 'uq_P', 14.6)],
 'C112': [('London', 'OBS', 'ID', 3, 'uq_H', 13.5), ('London', 'OBS', 'ID', 3, 'uq_P', 11.5), ('London', 'OBS', 'ID', 3, 'pct_HP', -15, 0)],
 'C113': [('London', 'OBS', 'TXn', 2, 'd_HP', 1.6), ('London', 'OBS', 'TXn', 3, 'd_HP', -1.0)],
 'C114': [('London', 'OBS', 'RX1day', 2, 'd_HP', -4.4), ('London', 'OBS', 'RX1day', 2, 'pct_HP', -13, 0)],
 'C115': [('London', 'OBS', 'PRCPTOT', 3, 'd_HP', 5.4), ('London', 'OBS', 'PRCPTOT', 3, 'pct_HP', 5, 0), ('London', 'OBS', 'RX5day', 3, 'd_HP', -4.0)],
 'C116': [('Fergus', 'OBS', 'TMm', 3, 'uq_H', -0.8), ('Fergus', 'OBS', 'TMm', 3, 'uq_P', 1.4)],
 'C117': [('Harrow', 'OBS', 'TMm', 1, 'uq_P', -0.3), ('Harrow', 'OBS', 'TMm', 2, 'uq_P', -0.1), ('Harrow', 'OBS', 'TMm', 3, 'uq_H', 2.6), ('Harrow', 'OBS', 'TMm', 3, 'uq_P', 4.5)],
 'C118': [('Harrow', 'OBS', 'TXx', 2, 'd_HP', 3.5), ('Harrow', 'OBS', 'TXx', 1, 'd_HP', 1.1)],
 'C119': [('Fergus', 'OBS', 'TXn', 1, 'd_HP', 0.0)],
 'C120': [('Fergus', 'OBS', 'ID', 3, 'd_HP', -4.5), ('London', 'OBS', 'ID', 3, 'd_HP', -2.0), ('Harrow', 'OBS', 'ID', 3, 'd_HP', -2.5), ('Fergus', 'OBS', 'ID', 3, 'pct_HP', -27, 0), ('London', 'OBS', 'ID', 3, 'pct_HP', -15, 0), ('Harrow', 'OBS', 'ID', 3, 'pct_HP', -29, 0)],
 'C121': [('Fergus', 'OBS', 'PRCPTOT', 1, 'd_HP', 12.7), ('Fergus', 'OBS', 'PRCPTOT', 1, 'pct_HP', 14, 0), ('Fergus', 'OBS', 'PRCPTOT', 3, 'd_HP', 0.6)],
 'C122': [('Fergus', 'OBS', 'RX1day', 1, 'd_HP', 3.6), ('Fergus', 'OBS', 'RX5day', 1, 'd_HP', 9.2)],
 'C123': [('Harrow', 'OBS', 'RX1day', 1, 'd_HP', 3, 0), ('Harrow', 'OBS', 'RX1day', 2, 'd_HP', 3, 0), ('Harrow', 'OBS', 'PRCPTOT', 1, 'd_HP', -17.1), ('Harrow', 'OBS', 'PRCPTOT', 3, 'd_HP', -16.6)],
 'C124': [('London', 'T', 'TXx', 1, 'd_HP', 4.4), ('London', 'T', 'TXx', 2, 'd_HP', 3.0), ('London', 'T', 'TXx', 3, 'd_HP', 2.5)],
 'C125': [('London', 'T', 'TXn', 3, 'd_HP', 4.7)], 'C126': [('London', 'T', 'ID', 3, 'd_HP', -4.0), ('London', 'T', 'ID', 3, 'pct_HP', -29, 0)],
 'C127': [('London', 'P', 'PRCPTOT', 1, 'd_HP', -15.6), ('London', 'P', 'PRCPTOT', 1, 'p_HP', 0.04)],
 'C128': [('London', 'P', 'RX1day', 1, 'd_HP', -1.3)],
 'C129': [('London', 'P', 'PRCPTOT', 2, 'd_HP', 17.0), ('London', 'P', 'PRCPTOT', 3, 'd_HP', 10.6), ('London', 'P', 'PRCPTOT', 3, 'pct_HP', 11, 0)],
 'C130': [('London', 'P', 'RX1day', 3, 'd_HP', 3.6), ('London', 'P', 'RX5day', 3, 'd_HP', 6.7), ('London', 'P', 'R10mm', 3, 'd_HP', 1.0)],
 'C131': [('Fergus', 'T', 'TMm', 3, 'uq_H', 0.6), ('Fergus', 'T', 'TMm', 3, 'uq_P', 2.3), ('Fergus', 'T', 'TMm', 3, 'd_HP', 1.7)],
 'C132': [('Fergus', 'P', 'PRCPTOT', 1, 'd_HP', -17.2), ('Fergus', 'P', 'PRCPTOT', 2, 'd_HP', 12.5), ('Fergus', 'P', 'PRCPTOT', 3, 'd_HP', 14.8), ('Fergus', 'P', 'RX5day', 3, 'd_HP', 5.1)],
 'C133': [('Harrow', 'T', 'TXn', 1, 'd_HP', 0.2), ('Harrow', 'T', 'TXn', 2, 'd_HP', 0.9), ('Harrow', 'T', 'TXn', 3, 'd_HP', 1.1)],
 'C134': [('Harrow', 'T', 'TMm', 2, 'uq_H', -1.0), ('Harrow', 'T', 'TMm', 2, 'uq_P', 2.0)],
 'C135': [('Harrow', 'T', 'ID', 2, 'd_HP', -3.0), ('Harrow', 'T', 'ID', 3, 'd_HP', -6.5), ('Harrow', 'T', 'ID', 3, 'pct_HP', -59, 0)],
 'C136': [('Harrow', 'P', 'PRCPTOT', 1, 'd_HP', -19.3), ('Harrow', 'P', 'PRCPTOT', 2, 'd_HP', 13.5), ('Harrow', 'P', 'PRCPTOT', 3, 'd_HP', 11.6), ('Harrow', 'P', 'PRCPTOT', 3, 'pct_HP', 12, 0)],
 'C138': [('London', 'T', 'TXn', 1, 'd_NF', 6.1), ('London', 'T', 'TXn', 2, 'd_NF', 5.7)],
 'C139': [('London', 'T', 'ID', 1, 'd_NF', -9.0), ('London', 'T', 'ID', 1, 'pct_NF', -45, 0), ('London', 'T', 'ID', 3, 'd_NF', -4.5), ('London', 'T', 'ID', 3, 'pct_NF', -69, 0), ('London', 'T', 'ID', 3, 'uq_F', 2)],
 'C140': [('London', 'T', 'TXx', 1, 'd_NF', 1.9), ('London', 'T', 'TXx', 3, 'd_NF', 1.7)],
 'C141': [('London', 'T', 'TMm', 1, 'd_NF', 3.8), ('London', 'T', 'TMm', 3, 'd_NF', 2.1)],
 'C142': [('London', 'P', 'PRCPTOT', 1, 'd_NF', 12.5), ('London', 'P', 'PRCPTOT', 1, 'pct_NF', 10, 0), ('London', 'P', 'RX1day', 1, 'd_NF', 6.9), ('London', 'P', 'RX1day', 1, 'pct_NF', 25, 0),
          ('London', 'P', 'RX5day', 1, 'd_NF', 5.4), ('London', 'P', 'RX5day', 1, 'pct_NF', 10, 0), ('London', 'P', 'RX5day', 1, 'p_NF', 0.004), ('London', 'P', 'R10mm', 1, 'd_NF', 1, 0)],
 'C143': [('London', 'P', 'PRCPTOT', 2, 'd_NF', -15.3), ('London', 'P', 'PRCPTOT', 3, 'd_NF', -16.2), ('London', 'P', 'PRCPTOT', 3, 'pct_NF', -12, 0), ('London', 'P', 'R10mm', 2, 'd_NF', -2, 0),
          ('London', 'P', 'R10mm', 3, 'd_NF', -2, 0), ('London', 'P', 'RX1day', 2, 'd_NF', 5.1), ('London', 'P', 'RX1day', 3, 'd_NF', 1.8)],
 'C145': [('Fergus', 'T', 'TMm', 1, 'd_NF', 2.6), ('Fergus', 'T', 'TMm', 3, 'd_NF', 3.0), ('London', 'T', 'TMm', 1, 'd_NF', 3.8), ('London', 'T', 'TMm', 3, 'd_NF', 2.1)],
 'C146': [('Fergus', 'T', 'TMm', 2, 'd_NF', 4.3), ('London', 'T', 'TMm', 2, 'd_NF', 2.3)], 'C147': [('Fergus', 'T', 'ID', 3, 'uq_F', 2.5)],
 'C148': [('Fergus', 'P', 'PRCPTOT', 1, 'd_NF', 15.0), ('Fergus', 'P', 'PRCPTOT', 1, 'pct_NF', 14, 0), ('Fergus', 'P', 'RX1day', 1, 'd_NF', 8.7), ('Fergus', 'P', 'RX5day', 1, 'd_NF', 5.7)],
 'C149': [('Fergus', 'P', 'PRCPTOT', 2, 'd_NF', 0, 0), ('Fergus', 'P', 'PRCPTOT', 3, 'd_NF', -14.8), ('Fergus', 'P', 'PRCPTOT', 3, 'pct_NF', -12, 0)],
 'C150': [('Harrow', 'T', 'TXn', 1, 'd_NF', 7.8), ('Harrow', 'T', 'TXn', 3, 'd_NF', 5.3)], 'C151': [('Harrow', 'T', 'TXn', 3, 'uq_N', -4.4), ('Harrow', 'T', 'TXn', 3, 'uq_F', 0.9)],
 'C152': [('Harrow', 'T', 'TMm', 1, 'd_NF', 2.4), ('Harrow', 'T', 'TMm', 2, 'd_NF', 2.9)],
 'C153': [('Harrow', 'T', 'ID', 2, 'uq_N', 11), ('Harrow', 'T', 'ID', 2, 'uq_F', 5.5), ('Harrow', 'T', 'ID', 3, 'uq_N', 3), ('Harrow', 'T', 'ID', 3, 'uq_F', 0)],
 'C154': [('Harrow', 'P', 'PRCPTOT', 1, 'd_NF', 15.8), ('Harrow', 'P', 'PRCPTOT', 1, 'pct_NF', 17, 0), ('Harrow', 'P', 'RX5day', 1, 'd_NF', 14.5), ('Harrow', 'P', 'RX5day', 1, 'pct_NF', 29, 0),
          ('Harrow', 'P', 'RX5day', 1, 'p_NF', 0.034), ('Harrow', 'P', 'RX1day', 1, 'd_NF', 7.4), ('Harrow', 'P', 'R10mm', 1, 'd_NF', 1.0)],
 'C155': [('Harrow', 'P', 'PRCPTOT', 2, 'd_NF', -29.5), ('Harrow', 'P', 'PRCPTOT', 3, 'd_NF', -14.2)],
 'C157': [('London', 'OBS', 'CDD', 8, 'd_HP', 1.5), ('London', 'OBS', 'CDD', 9, 'd_HP', 0.5)],
 'C158': [('London', 'OBS', 'PRCPTOT', 9, 'd_HP', 23.3)], 'C159': [('London', 'OBS', 'RX1day', 9, 'd_HP', 6.3)], 'C160': [('London', 'OBS', 'RX5day', 9, 'd_HP', 12.5)],
 'C161': [('London', 'OBS', 'SU', 7, 'd_HP', 4.5), ('London', 'OBS', 'SU', 9, 'd_HP', 4.0), ('London', 'OBS', 'SU', 6, 'd_HP', 2.0), ('London', 'OBS', 'SU', 8, 'd_HP', 1.5)],
 'C162': [('London', 'OBS', 'TXx', 6, 'd_HP', 0.6), ('London', 'OBS', 'TXx', 7, 'd_HP', 1.6), ('London', 'OBS', 'TXx', 8, 'd_HP', 1.4), ('London', 'OBS', 'TXx', 9, 'd_HP', -0.4)],
 'C163': [('London', 'OBS', 'TXn', 6, 'd_HP', 2.3), ('London', 'OBS', 'TXn', 7, 'd_HP', 0.3), ('London', 'OBS', 'TXn', 8, 'd_HP', -0.1), ('London', 'OBS', 'TXn', 9, 'd_HP', 0.6)],
 'C164': [('Fergus', 'OBS', 'SPEI6', 6, 'uq_H', 1.21), ('Fergus', 'OBS', 'SPEI6', 6, 'uq_P', 1.49), ('Fergus', 'OBS', 'SPEI6', 6, 'd_HP', 0.28)],
 'C165': [('Fergus', 'OBS', 'PRCPTOT', 7, 'd_HP', 30.3), ('Fergus', 'OBS', 'PRCPTOT', 8, 'd_HP', -43.0)],
 'C166': [('Fergus', 'OBS', 'RX1day', 8, 'd_HP', 8.7), ('Fergus', 'OBS', 'RX1day', 8, 'pct_HP', 17, 0), ('London', 'OBS', 'RX1day', 8, 'pct_HP', 5, 0)],
 'C167': [('Fergus', 'OBS', 'TXx', 6, 'd_HP', 0.9), ('Fergus', 'OBS', 'TXx', 6, 'p_HP', 0.019), ('Fergus', 'OBS', 'SU', 8, 'd_HP', 0, 0)],
 'C170': [('Harrow', 'OBS', 'PRCPTOT', 7, 'd_HP', -16.6)],
 'C173': [('London', 'P', 'SPI6', m, 'd_HP', v) for m, v in zip((6, 7, 8, 9), (0.77, 0.92, 0.29, 0.97))],
 'C174': [('London', 'P', 'SPEI6', m, 'd_HP', v) for m, v in zip((6, 7, 8, 9), (0.59, 0.43, 0.27, 0.52))],
 'C175': [('London', 'P', 'SPEI3', 8, 'd_HP', -0.31), ('London', 'P', 'SPEI3', 9, 'd_HP', 0.0, 1)],
 'C176': [('London', 'P', 'CDD', 7, 'd_HP', 2.0), ('London', 'P', 'CDD', 7, 'pct_HP', 22, 0), ('London', 'P', 'CDD', 8, 'd_HP', -3.0), ('London', 'P', 'CDD', 8, 'pct_HP', -21, 0), ('London', 'P', 'CDD', 9, 'd_HP', -1.0), ('London', 'P', 'CDD', 6, 'd_HP', 0.0)],
 'C177': [('London', 'P', 'PRCPTOT', 9, 'd_HP', 54.1), ('London', 'P', 'PRCPTOT', 9, 'pct_HP', 45, 0), ('London', 'P', 'PRCPTOT', 9, 'p_HP', 0.018), ('London', 'P', 'PRCPTOT', 6, 'd_HP', 17.6)],
 'C178': [('London', 'P', 'RX5day', 6, 'd_HP', 9.4), ('London', 'P', 'RX5day', 6, 'pct_HP', 19, 0), ('London', 'P', 'RX5day', 9, 'd_HP', 18.1), ('London', 'P', 'RX5day', 9, 'pct_HP', 26, 0), ('London', 'P', 'RX5day', 7, 'd_HP', -3.0)],
 'C179': [('London', 'P', 'RX1day', 6, 'd_HP', 7.2), ('London', 'P', 'RX1day', 6, 'pct_HP', 26, 0), ('London', 'P', 'RX1day', 9, 'd_HP', 5.8), ('London', 'P', 'RX1day', 9, 'pct_HP', 14, 0), ('London', 'P', 'RX1day', 7, 'd_HP', -5.7), ('London', 'P', 'RX1day', 8, 'd_HP', -1.5)],
 'C180': [('London', 'P', 'R10mm', 9, 'd_HP', 2.0), ('London', 'P', 'R10mm', 9, 'pct_HP', 44, 0)],
 'C181': [('London', 'T', 'SU', 8, 'd_HP', 7.5), ('London', 'T', 'SU', 8, 'pct_HP', 37, 0), ('London', 'T', 'SU', 9, 'd_HP', 4.5), ('London', 'T', 'SU', 9, 'pct_HP', 43, 0)],
 'C182': [('London', 'T', 'TXx', 8, 'd_HP', 2.5), ('London', 'T', 'TXx', 9, 'd_HP', 2.3)], 'C183': [('London', 'T', 'TXn', 9, 'd_HP', 1.8), ('London', 'T', 'TXn', 7, 'd_HP', 1.5)],
 'C185': [('Fergus', 'T', 'SU', 6, 'd_HP', 5.0), ('Fergus', 'T', 'SU', 7, 'd_HP', 4.0), ('Fergus', 'T', 'SU', 8, 'd_HP', 1.5), ('Fergus', 'T', 'SU', 9, 'd_HP', 5.0), ('Fergus', 'T', 'SU', 9, 'pct_HP', 67, 0)],
 'C187': [('Fergus', 'P', 'PRCPTOT', 7, 'd_HP', -2.2), ('Fergus', 'P', 'PRCPTOT', 8, 'd_HP', 2.3), ('Fergus', 'P', 'RX1day', 7, 'd_HP', -1.5), ('Fergus', 'P', 'RX1day', 8, 'd_HP', -5.5),
          ('Fergus', 'P', 'PRCPTOT', 9, 'd_HP', 64.3), ('Fergus', 'P', 'PRCPTOT', 9, 'pct_HP', 58, 0), ('Fergus', 'P', 'RX1day', 9, 'd_HP', 4.2), ('Fergus', 'P', 'RX5day', 9, 'd_HP', 10.8)],
 'C188': [('Fergus', 'P', 'SPEI6', 7, 'd_HP', 1.07), ('Fergus', 'P', 'SPEI6', 6, 'd_HP', 0.58), ('Fergus', 'P', 'CDD', 9, 'd_HP', -4.0), ('Fergus', 'P', 'CDD', 9, 'pct_HP', -29, 0)],
 'C189': [('Harrow', 'P', 'PRCPTOT', 9, 'd_HP', 51.2), ('Harrow', 'P', 'PRCPTOT', 9, 'pct_HP', 50, 0), ('Harrow', 'P', 'PRCPTOT', 7, 'd_HP', 37.3), ('Harrow', 'P', 'PRCPTOT', 7, 'pct_HP', 33, 0)],
 'C190': [('Harrow', 'P', 'RX5day', 8, 'd_HP', 20.6), ('Harrow', 'P', 'RX5day', 9, 'd_HP', 17.8), ('Harrow', 'P', 'RX5day', 8, 'pct_HP', 37, 0), ('Harrow', 'P', 'RX5day', 9, 'pct_HP', 29, 0), ('Harrow', 'P', 'RX1day', 6, 'd_HP', 14.9), ('Harrow', 'P', 'RX1day', 6, 'pct_HP', 56, 0)],
 'C191': [('Harrow', 'P', 'SPI6', 8, 'd_HP', 0.92), ('Harrow', 'P', 'SPI3', 8, 'd_HP', 1.18), ('Harrow', 'P', 'CDD', 7, 'd_HP', 3.5), ('Harrow', 'P', 'R10mm', 9, 'd_HP', 3.0)],
 'C192': [('Harrow', 'T', 'SU', 9, 'd_HP', 5.0), ('Harrow', 'T', 'SU', 9, 'pct_HP', 42, 0)], 'C193': [('Harrow', 'T', 'TXx', 8, 'd_HP', 2.4)],
 'C194': [('Harrow', 'T', 'TXn', 7, 'd_HP', -0.5)],
 'C195': [('London', 'T', 'SU', 9, 'd_NF', 6.0), ('London', 'T', 'SU', 9, 'pct_NF', 29, 0)], 'C196': [('London', 'T', 'TXx', 6, 'd_NF', 3.3), ('London', 'T', 'TXx', 8, 'd_NF', 2.6)],
 'C197': [('London', 'T', 'TXn', 8, 'd_NF', 4.4), ('London', 'T', 'TXn', 7, 'd_NF', 4.2)],
 'C199': [('London', 'P', 'SPEI6', 7, 'd_NF', -0.81), ('London', 'P', 'SPEI6', 8, 'd_NF', -1.28), ('London', 'P', 'SPEI6', 9, 'd_NF', -2.01), ('London', 'P', 'SPEI6', 8, 'uq_F', -0.53), ('London', 'P', 'SPEI6', 9, 'uq_F', -0.82)],
 'C200': [('London', 'P', 'SPEI3', 7, 'd_NF', -1.67), ('London', 'P', 'SPEI3', 8, 'd_NF', -2.39), ('London', 'P', 'SPEI3', 9, 'd_NF', -1.76), ('London', 'P', 'SPEI3', 6, 'd_NF', -0.38)],
 'C201': [('London', 'P', 'SPI6', 9, 'd_NF', -0.82)],
 'C202': [('London', 'P', 'CDD', 9, 'd_NF', -2.5), ('London', 'P', 'CDD', 9, 'pct_NF', -16, 0)],
 'C203': [('London', 'P', 'PRCPTOT', 8, 'd_NF', -33.2), ('London', 'P', 'PRCPTOT', 8, 'pct_NF', -34, 0), ('London', 'P', 'PRCPTOT', 8, 'p_NF', 0.015), ('London', 'P', 'PRCPTOT', 7, 'd_NF', -26.3),
          ('London', 'P', 'PRCPTOT', 7, 'pct_NF', -28, 0), ('London', 'P', 'PRCPTOT', 6, 'd_NF', -25.1), ('London', 'P', 'PRCPTOT', 6, 'pct_NF', -19, 0), ('London', 'P', 'PRCPTOT', 9, 'd_NF', -21.4), ('London', 'P', 'PRCPTOT', 9, 'pct_NF', -13, 0)],
 'C204': [('London', 'P', 'RX1day', 6, 'd_NF', -7.5), ('London', 'P', 'RX1day', 6, 'pct_NF', -21, 0), ('London', 'P', 'RX1day', 7, 'd_NF', -6.8), ('London', 'P', 'RX5day', 9, 'd_NF', -1.0)],
 'C205': [('Fergus', 'P', 'SPEI6', 7, 'd_NF', -1.19), ('Fergus', 'P', 'SPEI6', 8, 'd_NF', -1.58), ('Fergus', 'P', 'SPEI6', 9, 'd_NF', -1.81), ('Fergus', 'P', 'SPEI6', 6, 'd_NF', 0.0, 1)],
 'C206': [('Fergus', 'P', 'PRCPTOT', 9, 'd_NF', -35.9), ('Fergus', 'P', 'PRCPTOT', 9, 'pct_NF', -24, 0), ('Fergus', 'P', 'PRCPTOT', 7, 'd_NF', -33.3), ('Fergus', 'P', 'PRCPTOT', 7, 'pct_NF', -31, 0)],
 'C207': [('Fergus', 'P', 'CDD', 6, 'd_NF', -1.5), ('Fergus', 'P', 'RX5day', 7, 'd_NF', -18.2), ('Fergus', 'P', 'RX1day', 9, 'd_NF', 0.8)],
 'C209': [('Harrow', 'T', 'SU', 9, 'd_NF', 7.0), ('Harrow', 'T', 'TXn', 9, 'd_NF', 4.2)],
 'C210': [('Harrow', 'P', 'SPEI6', 7, 'd_NF', -1.31), ('Harrow', 'P', 'SPEI6', 8, 'd_NF', -1.87), ('Harrow', 'P', 'SPEI6', 9, 'd_NF', -1.72)],
 'C211': [('Harrow', 'P', 'PRCPTOT', 6, 'd_NF', -48.4), ('Harrow', 'P', 'PRCPTOT', 6, 'pct_NF', -35, 0), ('Harrow', 'P', 'PRCPTOT', 7, 'd_NF', -32.3), ('Harrow', 'P', 'PRCPTOT', 8, 'd_NF', -33.0),
          ('Harrow', 'P', 'PRCPTOT', 8, 'pct_NF', -34, 0), ('Harrow', 'P', 'PRCPTOT', 9, 'd_NF', -59.6), ('Harrow', 'P', 'PRCPTOT', 9, 'pct_NF', -33, 0)],
 'C212': [('Harrow', 'P', 'CDD', 7, 'd_NF', -1.0)],
 'C213': [('Harrow', 'P', 'RX1day', 6, 'd_NF', -13.3), ('Harrow', 'P', 'RX1day', 7, 'd_NF', -16.1), ('Harrow', 'P', 'RX5day', 9, 'd_NF', -18.6)],
 'C216': [('London', 'T', 'TXx', 9, 'd_HP', 2.3), ('London', 'OBS', 'TXx', 9, 'd_HP', -0.4)],
 'C221': [('London', 'OBS', 'TMm', 1, 'd_HP', 2.2), ('London', 'OBS', 'TMm', 3, 'd_HP', 2.5), ('Fergus', 'OBS', 'TMm', 1, 'd_HP', 1.9, 1)],
 'C223': [('Harrow', 'OBS', 'TXn', 1, 'd_HP', 2.2)],
 'C224': [('London', 'T', 'TXn', 1, 'd_NF', 6.1), ('London', 'T', 'TXn', 2, 'd_NF', 5.7), ('Harrow', 'T', 'ID', 3, 'uq_F', 0)],
 'C225': [('London', 'OBS', 'SU', 6, 'd_HP', 2.0), ('London', 'OBS', 'SU', 7, 'd_HP', 4.5), ('London', 'OBS', 'SU', 8, 'd_HP', 1.5), ('London', 'OBS', 'SU', 9, 'd_HP', 4.0)],
 'C226': [('Fergus', 'OBS', 'TXx', 9, 'd_HP', 0.1), ('Harrow', 'OBS', 'TXx', 9, 'd_HP', -0.4)],
 'C227': [('Fergus', 'OBS', 'SU', 8, 'd_HP', 0, 0)],
 'C235': [('Fergus', 'OBS', 'TMm', 3, 'uq_H', -0.8), ('Fergus', 'OBS', 'TMm', 3, 'uq_P', 1.4)],
 'C236': [('Harrow', 'OBS', 'TMm', 1, 'uq_P', -0.3), ('Harrow', 'OBS', 'TMm', 2, 'uq_P', -0.1)],
 'C238': [('London', 'T', 'TXn', 1, 'd_NF', 6.1), ('London', 'T', 'TXn', 2, 'd_NF', 5.7), ('Harrow', 'T', 'ID', 3, 'uq_F', 0)],
 'C239': [('Fergus', 'OBS', 'PRCPTOT', 1, 'pct_HP', 14, 0), ('Fergus', 'OBS', 'RX5day', 1, 'd_HP', 9.2)],
 'C243': [('London', 'P', 'CDD', 9, 'd_NF', -2.5)],
 'C246': [('Fergus', 'OBS', 'CDD', 7, 'd_HP', -5, 0)],
 'C253': [('Fergus', 'P', 'CDD', 9, 'd_NF', 2.0), ('Harrow', 'P', 'CDD', 9, 'd_NF', 1.0)],
 'C254': [('London', 'OBS', 'RX5day', 9, 'd_HP', 12.5), ('London', 'P', 'RX5day', 9, 'd_HF', 16.4)],
 'C255': [('Harrow', 'P', 'CDD', 8, 'd_NF', 4.0), ('Harrow', 'P', 'RX5day', 9, 'd_HF', 18.5)],
}
for k, v in MON.items():
    R[k] = (lambda v=v: M(v))


def rng(name, vals, lo, hi, d=None):
    return [(name + ' min', lo, min(vals)) + ((d,) if d is not None else ()), (name + ' max', hi, max(vals)) + ((d,) if d is not None else ())]


R['C109'] = lambda: [('London obs TMm JFM all sig (executed all-values test)', 1, sig_all('London', 'OBS', 'TMm', (1, 2, 3))), ('London obs TXx JFM all sig (executed)', 1, sig_all('London', 'OBS', 'TXx', (1, 2, 3))),
                     ('London obs TMm JFM all sig (printed subset test)', 1, sig_all('London', 'OBS', 'TMm', (1, 2, 3), test='p')), ('TXx subset test', 1, sig_all('London', 'OBS', 'TXx', (1, 2, 3), test='p'))]
R['C115'] = lambda: M(MON['C115']) + [('London Mar precip changes none sig (executed)', 1, float(all(mon('London', 'OBS', ix, 3, 'pall_HP') >= 0.05 for ix in ('PRCPTOT', 'RX5day'))))]
R['C123'] = lambda: M(MON['C123']) + [('none sig (executed)', 1, float(all(mon('Harrow', 'OBS', ix, m, 'pall_HP') >= 0.05 for ix, m in (('RX1day', 1), ('RX1day', 2), ('PRCPTOT', 1), ('PRCPTOT', 3)))))]
R['C137'] = lambda: rng('BCC Feb/Mar PRCPTOT H->P % (10%-20%)', [monpct(s, 'P', 'PRCPTOT', m) for s in S3 for m in (2, 3)], 10, 20, None) + [('Jan declines all', 1, float(all(mon(s, 'P', 'PRCPTOT', 1, 'd_HP') < 0 for s in S3)))]
R['C144'] = lambda: [('London Mar PRCPTOT F vs H %', 20, 100 * mon('London', 'P', 'PRCPTOT', 3, 'd_HF') / mon('London', 'P', 'PRCPTOT', 3, 'uq_H'), 0)]
R['C156'] = lambda: [(f'London obs {ix} m{m} H->P >0', 1, float(mon('London', 'OBS', ix, m, 'd_HP') > 0)) for ix in ('SPEI3', 'SPEI6', 'SPI3', 'SPI6') for m in (6, 7, 9)] + \
    [(f'London obs {ix} Aug <=~0', 1, float(mon('London', 'OBS', ix, 8, 'd_HP') <= 0.1)) for ix in ('SPEI3', 'SPEI6', 'SPI3', 'SPI6')]
R['C157'] = lambda: M(MON['C157']) + [('Jun CDD <0', 1, float(mon('London', 'OBS', 'CDD', 6, 'd_HP') < 0)), ('Jul CDD <0', 1, float(mon('London', 'OBS', 'CDD', 7, 'd_HP') < 0))]
R['C168'] = lambda: rng('Fergus obs TXn Jul-Sep H->P', [mon('Fergus', 'OBS', 'TXn', m, 'd_HP') for m in (7, 8, 9)], 1.0, 2.1)
R['C169'] = lambda: [(f'Harrow obs {ix} m{m} H->P <0', 1, float(mon('Harrow', 'OBS', ix, m, 'd_HP') < 0)) for ix in ('SPEI6', 'SPI6') for m in (6, 7, 8, 9)]
R['C170'] = lambda: M(MON['C170']) + rng('Harrow obs PRCPTOT Jun/Aug/Sep', [mon('Harrow', 'OBS', 'PRCPTOT', m, 'd_HP') for m in (6, 8, 9)], 21.0, 52.8)
R['C171'] = lambda: [(f'Harrow obs {ix} m{m} >0', 1, float(mon('Harrow', 'OBS', ix, m, 'd_HP') > 0)) for ix in ('RX1day', 'RX5day') for m in (6, 7, 8, 9)]
R['C172'] = lambda: [(f'Harrow obs SU m{m} >0', 1, float(mon('Harrow', 'OBS', 'SU', m, 'd_HP') > 0)) for m in (6, 7, 8, 9)] + [(f'Harrow obs TXx m{m} >0', 1, float(mon('Harrow', 'OBS', 'TXx', m, 'd_HP') > 0)) for m in (6, 7, 8)]
R['C184'] = lambda: [('obs Sep TXx London <0', 1, float(mon('London', 'OBS', 'TXx', 9, 'd_HP') < 0)), ('obs TXn rose mainly June (max month)', 6, max((6, 7, 8, 9), key=lambda m: mon('London', 'OBS', 'TXn', m, 'd_HP')))]
R['C186'] = lambda: [(f'Fergus EC TXx m{m}>0', 1, float(mon('Fergus', 'T', 'TXx', m, 'd_HP') > 0)) for m in (6, 7, 8, 9)] + [('Fergus Sep TXn > London Sep TXn', 1, float(mon('Fergus', 'T', 'TXn', 9, 'd_HP') > mon('London', 'T', 'TXn', 9, 'd_HP')))]
R['C198'] = lambda: [(f'London BCC SPEI3 m{m} N>0,F<0', 1, float(mon('London', 'P', 'SPEI3', m, 'uq_N') > 0 > mon('London', 'P', 'SPEI3', m, 'uq_F'))) for m in (7, 8, 9)] + \
    [(f'London BCC SPEI6 m{m} N>0,F<0', 1, float(mon('London', 'P', 'SPEI6', m, 'uq_N') > 0 > mon('London', 'P', 'SPEI6', m, 'uq_F'))) for m in (8, 9)]
R['C201'] = lambda: M(MON['C201']) + [(f'SPI3 Aug/Sep N->F ~-1', -1.0, mon('London', 'P', 'SPI3', m, 'd_NF'), None) for m in (8, 9)] + [(f'SPI3 F m{m} >= ~0', 1, float(mon('London', 'P', 'SPI3', m, 'uq_F') > -0.3)) for m in (8, 9)]
R['C204'] = lambda: M(MON['C204']) + rng('RX5day Jun-Aug N->F', [mon('London', 'P', 'RX5day', m, 'd_NF') for m in (6, 7, 8)], -11.0, -5.8) + rng('R10mm Jun-Aug', [mon('London', 'P', 'R10mm', m, 'd_NF') for m in (6, 7, 8)], -2.0, -0.5) + \
    [('R10mm Sep', 0.0, mon('London', 'P', 'R10mm', 9, 'd_NF'), 1)]
R['C207'] = lambda: M(MON['C207']) + rng('Fergus CDD Jul-Sep N->F', [mon('Fergus', 'P', 'CDD', m, 'd_NF') for m in (7, 8, 9)], 1.0, 2.0) + [(f'RX5day m{m}<0', 1, float(mon('Fergus', 'P', 'RX5day', m, 'd_NF') < 0)) for m in (6, 7, 8, 9)]
R['C208'] = lambda: [('Fergus EC N->F SU/TXx/TXn > London NorESM in >=half of month-index cells', 1, float(sum(mon('Fergus', 'T', ix, m, 'd_NF') > mon('London', 'T', ix, m, 'd_NF') for ix in ('SU', 'TXx', 'TXn') for m in (6, 7, 8, 9)) >= 6))]
R['C209'] = lambda: M(MON['C209']) + rng('Harrow EC TXx N->F JJAS', [mon('Harrow', 'T', 'TXx', m, 'd_NF') for m in (6, 7, 8, 9)], 1.6, 4.6)
R['C210'] = lambda: M(MON['C210']) + [(f'SPI6 m{m} <0', 1, float(mon('Harrow', 'P', 'SPI6', m, 'd_NF') < 0)) for m in (6, 7, 8, 9)]
R['C211'] = lambda: M(MON['C211']) + [('Harrow largest June and Sept decline of 3 stations', 1, float(all(mon('Harrow', 'P', 'PRCPTOT', m, 'd_NF') <= min(mon(s, 'P', 'PRCPTOT', m, 'd_NF') for s in S3) for m in (6, 9))))]
R['C212'] = lambda: M(MON['C212']) + rng('Harrow CDD Jun/Aug/Sep N->F', [mon('Harrow', 'P', 'CDD', m, 'd_NF') for m in (6, 8, 9)], 0.5, 4.0)
R['C213'] = lambda: M(MON['C213']) + [(f'Harrow {ix} m{m} N->F<0', 1, float(mon('Harrow', 'P', ix, m, 'd_NF') < 0)) for ix in ('RX1day', 'RX5day') for m in (6, 7, 8, 9)]
R['C214'] = lambda: R['C108']() + [('BCC first London P', 1, float(passes('London', 'BCC', 'P') == max(passes('London', m, 'P') for m in M10))), ('BCC first Fergus P', 1, float(passes('Fergus', 'BCC', 'P') == max(passes('Fergus', m, 'P') for m in M10)))]
R['C215'] = lambda: [('London NorESM T', 52, passes('London', 'NorESM', 'T'))]
R['C217'] = lambda: [(f'{s} within', v, ens_count(s, None)) for s, v in zip(S3, (38, 38, 39))] + [('DTRgt15 outside all', 1, float(not any(env(s, 'DTRgt15', 'within') for s in S3))),
                                                                                                ('SDII reversal London & Fergus', 1, float(env('London', 'SDII', 'c613') == 'reversal' and env('Fergus', 'SDII', 'c613') == 'reversal'))]
R['C218'] = lambda: R['C38']()[1:4]
R['C219'] = lambda: rng('obs TNn H->P', [env(s, 'TNn') for s in S3], 1.1, 2.0)
R['C220'] = (DOC, 'Vincent et al. 2015: +1.7 C 1948-2012', 'n/a', 'CANNOT VERIFY', 'External literature; no input in pack.')
R['C222'] = lambda: rng('obs Mar ID % decline', [-monpct(s, 'OBS', 'ID', 3) for s in S3], 15, 29, 0)
R['C228'] = lambda: [('London NorESM Sep SU N->F', 6.0, mon('London', 'T', 'SU', 9, 'd_NF'))] + rng('London TXn JJAS N->F', [mon('London', 'T', 'TXn', m, 'd_NF') for m in (6, 7, 8, 9)], 3.2, 4.4) + [('Zhang 2019 3.3-6.1 C', 'lit', 'n/a')]
R['C229'] = lambda: [('London obs RX1day H->P', 0.2, env('London', 'RX1day')), ('CWD ~0', 0, env('London', 'CWD'), 0)] + [(f'London obs {ix} <0', 1, float(env('London', ix) < 0)) for ix in ('RX3day', 'RX5day', 'R10mm', 'R95p', 'R99p', 'PRCPTOT', 'SDII')]
R['C230'] = lambda: [('Fergus obs PRCPTOT', 40.3, env('Fergus', 'PRCPTOT'))] + [(f'Fergus {ix} >0', 1, float(env('Fergus', ix) > 0)) for ix in ('R95p', 'RX5day', 'R20mm')] + [(f'Fergus {ix} <0', 1, float(env('Fergus', ix) < 0)) for ix in ('RX1day', 'RX3day', 'R99p', 'R95pTOT', 'R99pTOT', 'SDII')]
R['C231'] = lambda: [('Harrow obs PRCPTOT', -56.1, env('Harrow', 'PRCPTOT'))] + [(f'Harrow {ix} >0', 1, float(env('Harrow', ix) > 0)) for ix in ('SDII', 'RX1day', 'RX3day', 'RX5day', 'R99p', 'R95pTOT', 'R99pTOT')] + \
    [('R99p sig', 1, float(chg('Harrow', 'R99p', 'OBS', 'P', 'p') < 0.05)), ('R99pTOT sig', 1, float(chg('Harrow', 'R99pTOT', 'OBS', 'P', 'p') < 0.05)), ('R95p <0', 1, float(env('Harrow', 'R95p') < 0)), ('CDD >0', 1, float(env('Harrow', 'CDD') > 0))]
R['C232'] = lambda: rng('Jan RX1day N->F', [mon(s, 'P', 'RX1day', 1, 'd_NF') for s in S3], 6.9, 8.7) + rng('Jan RX5day N->F', [mon(s, 'P', 'RX5day', 1, 'd_NF') for s in S3], 5.4, 14.5) + \
    [(f'{s} Mar PRCPTOT N->F % (about -12)', -12, monpct(s, 'P', 'PRCPTOT', 3, 'NF'), None) for s in S3] + [(f'{s} Mar F > H', 1, float(mon(s, 'P', 'PRCPTOT', 3, 'd_HF') > 0)) for s in S3]
R['C233'] = lambda: [(f'London RX1day m{m} N->F<0', 1, float(mon('London', 'P', 'RX1day', m, 'd_NF') < 0)) for m in (6, 7, 8)] + rng('London PRCPTOT JJAS N->F %', [-monpct('London', 'P', 'PRCPTOT', m, 'NF') for m in (6, 7, 8, 9)], 13, 34, 0)
R['C234'] = lambda: R['C222']() + [(f'{s} obs Mar TMm up', 1, float(mon(s, 'OBS', 'TMm', 3, 'd_HP') > 0)) for s in S3]
R['C237'] = lambda: [('London obs Jan/Feb uq_H<0 and uq_P<0', 1, float(all(mon('London', 'OBS', 'TMm', m, c) < 0 for m in (1, 2) for c in ('uq_H', 'uq_P')))), ('London obs Mar uq_H>0', 1, float(mon('London', 'OBS', 'TMm', 3, 'uq_H') > 0))]
R['C241'] = lambda: rng('Jan PRCPTOT N->F %', [monpct(s, 'P', 'PRCPTOT', 1, 'NF') for s in S3], 10, 17, 0) + rng('Mar F above H %', [100 * mon(s, 'P', 'PRCPTOT', 3, 'd_HF') / mon(s, 'P', 'PRCPTOT', 3, 'uq_H') for s in S3], 16, 32, 0) + \
    [('none sig (executed all-values) Jan/Mar', 1, float(all(mon(s, 'P', 'PRCPTOT', m, 'pall_NF') >= 0.05 for s in S3 for m in (1, 3))))]
R['C242'] = lambda: rng('London SPEI6 Jul-Sep N->F', [-mon('London', 'P', 'SPEI6', m, 'd_NF') for m in (7, 8, 9)], 0.8, 2.0, 1) + rng('SPEI3 Jul-Sep', [-mon('London', 'P', 'SPEI3', m, 'd_NF') for m in (7, 8, 9)], 1.7, 2.4, 1)
R['C244'] = lambda: rng('London TXn JJAS N->F', [mon('London', 'T', 'TXn', m, 'd_NF') for m in (6, 7, 8, 9)], 3.2, 4.4) + rng('PRCPTOT % decline', [-monpct('London', 'P', 'PRCPTOT', m, 'NF') for m in (6, 7, 8, 9)], 13, 34, 0)
R['C245'] = lambda: rng('London obs TXx Jun-Aug', [mon('London', 'OBS', 'TXx', m, 'd_HP') for m in (6, 7, 8)], 0.6, 1.6) + [('RX1day Aug >0', 1, float(mon('London', 'OBS', 'RX1day', 8, 'd_HP') > 0))]
R['C247'] = lambda: rng('Fergus BCC SPEI6 F Jul-Sep', [mon('Fergus', 'P', 'SPEI6', m, 'uq_F') for m in (7, 8, 9)], -0.78, -0.04) + rng('PRCPTOT % decline JJAS', [-monpct('Fergus', 'P', 'PRCPTOT', m, 'NF') for m in (6, 7, 8, 9)], 13, 31, 0)
R['C248'] = lambda: rng('Harrow obs RX1day JJAS H->P', [mon('Harrow', 'OBS', 'RX1day', m, 'd_HP') for m in (6, 7, 8, 9)], 6.6, 18.8)
R['C249'] = lambda: rng('London RX1day Jun-Aug N->F (abs)', [-mon('London', 'P', 'RX1day', m, 'd_NF') for m in (6, 7, 8)], 2.7, 7.5) + [('RX5day Sep', -1.0, mon('London', 'P', 'RX5day', 9, 'd_NF'))]
R['C250'] = lambda: rng('Harrow BCC RX5day H->P % JJAS', [monpct('Harrow', 'P', 'RX5day', m) for m in (6, 7, 8, 9)], 27, 37, 0) + rng('PRCPTOT N->F % Jun/Aug/Sep', [-monpct('Harrow', 'P', 'PRCPTOT', m, 'NF') for m in (6, 8, 9)], 33, 35, 0)
R['C251'] = lambda: rng('Sep PRCPTOT N->F %', [-monpct(s, 'P', 'PRCPTOT', 9, 'NF') for s in S3], 13, 33, 0) + rng('Sep RX5day F-H', [mon(s, 'P', 'RX5day', 9, 'd_HF') for s in S3], 9.5, 18.5)
R['C252'] = lambda: rng('SPEI6-SPI6 gap F (JJAS, 3 stations)', [mon(s, 'P', 'SPI6', m, 'uq_F') - mon(s, 'P', 'SPEI6', m, 'uq_F') for s in S3 for m in (6, 7, 8, 9)], 0.74, 2.15) + \
    [('Historical |gap| max < 0.25', 1, float(max(abs(mon(s, 'P', 'SPI6', m, 'uq_H') - mon(s, 'P', 'SPEI6', m, 'uq_H')) for s in S3 for m in (6, 7, 8, 9)) < 0.25))]
R['C256'] = lambda: rng('Jan RX5day N->F', [mon(s, 'P', 'RX5day', 1, 'd_NF') for s in S3], 5.4, 14.5)
R['C257'] = lambda: [('Fergus CDD max monthly N->F JJAS', 2.0, max(mon('Fergus', 'P', 'CDD', m, 'd_NF') for m in (6, 7, 8, 9))), ('Harrow', 4.0, max(mon('Harrow', 'P', 'CDD', m, 'd_NF') for m in (6, 7, 8, 9)))]
R['C258'] = lambda: rng('Sep RX5day F-H', [mon(s, 'P', 'RX5day', 9, 'd_HF') for s in S3], 9.5, 18.5) + [('largest at Harrow', 1, float(max(S3, key=lambda s: mon(s, 'P', 'RX5day', 9, 'd_HF')) == 'Harrow'))]
R['C259'] = lambda: R['C222']() + [('Harrow Mar ID F', 0, mon('Harrow', 'T', 'ID', 3, 'uq_F'))] + rng('London TXn Jan-Feb N->F', [mon('London', 'T', 'TXn', m, 'd_NF') for m in (1, 2)], 5.7, 6.1)
R['C260'] = R['C257']
R['C261'] = lambda: R['C101']() + [('warmest model FF WSDI3 median > 240', 1, float(max(pmx(s, 'WSDI3', 'F', 'max') for s in S3) > 240))]
R['C262'] = (DOC, '3 stations; 1 lakeshore, 2 inland', 'station list', 'CONFIRMED', 'Design statement consistent with data.')
R['C263'] = lambda: [('reversals', 10, int((L['V4']['env'].c613 == 'reversal').sum())), ('magnitude biases', 7, int((L['V4']['env'].c613 == 'magnitude').sum()))]
R['C264'] = R['C108']
R['C265'] = (DOC, 'BCCAQv2 quantile mapping to NRCANmet', 'n/a', 'CANNOT VERIFY', 'Downscaling-method property is external to the pack (PCIC documentation).')
R['C266'] = (DOC, 'design restatement; periods 37-39 years', '37/37/39/38', 'CONFIRMED', 'Here the thesis itself acknowledges 37-39-year periods, consistent with the year sets.')
R['C267'] = lambda: R['C4']()[1:] + [('DTRgt15 only index outside at all', 1, float(_allwithin()[2] == 1)), ('SDII reversal at 2 stations', 2, int(sum(env(s, 'SDII', 'c613') == 'reversal' for s in S3)))]
R['C268'] = lambda: R['C7']()
R['C269'] = lambda: R['C8']()[:4] + [('Jan PRCPTOT N->F >0 all', 1, float(all(mon(s, 'P', 'PRCPTOT', 1, 'd_NF') > 0 for s in S3)))]
R['C270'] = lambda: M([('Fergus', 'OBS', 'TMm', 3, 'uq_H', -0.8), ('Fergus', 'OBS', 'TMm', 3, 'uq_P', 1.4)]) + [('Fergus obs Jan PRCPTOT up', 1, float(mon('Fergus', 'OBS', 'PRCPTOT', 1, 'd_HP') > 0))]
R['C271'] = lambda: [('London obs Sep PRCPTOT & RX5day up', 1, float(mon('London', 'OBS', 'PRCPTOT', 9, 'd_HP') > 0 and mon('London', 'OBS', 'RX5day', 9, 'd_HP') > 0)),
                     ('no Sep PRCPTOT rebound N->F any station', 1, float(all(mon(s, 'P', 'PRCPTOT', 9, 'd_NF') < 0 for s in S3))), ('deepest at Harrow', 1, float(min(S3, key=lambda s: mon(s, 'P', 'PRCPTOT', 9, 'd_NF')) == 'Harrow'))]
R['C272'] = (DOC, 'Table A1/A2 captions', 'p-value grids present', 'CONFIRMED', 'Layout statement; grids parsed 44x20 per station.')
for cid, st, grp, per, vals in [('C273', 'Fergus', 'T', 'H', [25, 27, 19, 26, 29, 25, 25, 23, 26, 28]), ('C274', 'Fergus', 'T', 'P', [26, 29, 16, 26, 27, 20, 22, 20, 21, 27]),
                                ('C276', 'Harrow', 'T', 'H', [20, 17, 23, 17, 20, 16, 15, 17, 14, 21]), ('C277', 'Harrow', 'T', 'P', [20, 23, 11, 18, 24, 20, 21, 23, 24, 18])]:
    R[cid] = (lambda st=st, grp=grp, per=per, vals=vals: [(f'{st} {grp} {per} {m}', v, passes(st, m, grp, per)) for m, v in zip(M10, vals)])
R['C275'] = lambda: [(f'Fergus P H {m}', v, passes('Fergus', m, 'P', 'H')) for m, v in zip(M10, [8, 10, 9, 9, 8, 8, 7, 9, 9, 8])] + [(f'Fergus P P {m}', v, passes('Fergus', m, 'P', 'P')) for m, v in zip(M10, [10, 10, 8, 7, 8, 9, 6, 7, 7, 7])]
R['C278'] = lambda: [(f'Harrow P H {m}', v, passes('Harrow', m, 'P', 'H')) for m, v in zip(M10, [11, 8, 10, 10, 11, 11, 10, 10, 8, 10])] + [(f'Harrow P P {m}', v, passes('Harrow', m, 'P', 'P')) for m, v in zip(M10, [7, 9, 9, 10, 9, 4, 7, 9, 10, 6])]
R['C279'] = lambda: [('Fergus CanESM P TXb3TNb3 nan', 1, float(np.isnan(pval('Fergus', 'TXb3TNb3', 'CanESM', 'P')))), ('Harrow CanESM P nan', 1, float(np.isnan(pval('Harrow', 'TXb3TNb3', 'CanESM', 'P')))), ('Fergus NorESM P nan', 1, float(np.isnan(pval('Fergus', 'TXb3TNb3', 'NorESM', 'P'))))]
R['C280'] = (DOC, 'B1/B2 captions', 'arrow grids parsed', 'CONFIRMED', 'Layout statement.')
R['C281'] = lambda: [('Fergus obs SDII <0', 1, float(env('Fergus', 'SDII') < 0)), ('Fergus obs RX1day <0', 1, float(env('Fergus', 'RX1day') < 0)), ('ens SDII >0', 1, float(chg('Fergus', 'SDII', 'ENS') > 0)), ('ens RX1day >0', 1, float(chg('Fergus', 'RX1day', 'ENS') > 0))]
R['C282'] = (DOC, 'C1/C2 captions', 'arrow grids parsed', 'CONFIRMED', 'Layout statement; note "–" also used for zero median change, not only "not meaningful".')
R['C283'] = lambda: [(f'Fergus ENS {ix} {c} up', 1, float(chg('Fergus', ix, 'ENS', c) > 0)) for ix in ('SDII', 'RX3day', 'RX5day', 'R95p', 'R95pTOT', 'R99p', 'R99pTOT', 'R10mm') for c in 'NF']
for k in ['C284', 'C285', 'C286', 'C287', 'C288', 'C289', 'C290', 'C291', 'C292']:
    R[k] = (DOC, 'figure captions/layout', '5_Figures complete (55 files)', 'CANNOT VERIFY', 'Figure layout statements; plotted values are images not machine-checked.')
for k in ['C240']:
    R[k] = (DOC, 'mechanism (rain vs snow)', 'n/a', 'CANNOT VERIFY', 'Interpretive hydrological mechanism; no computable content in pack.')

R['C59'] = lambda: [('London HWA H pooled (near 15)', 15, pm('London', 'HWA', 'H'), None), ('N (approx 32)', 32, pm('London', 'HWA', 'N'), None), ('F', 43, pm('London', 'HWA', 'F'))]
R['C60'] = lambda: [('London HWF H (around 10)', 10, pm('London', 'HWF', 'H'), None), ('N', 48, pm('London', 'HWF', 'N')), ('F', 90, pm('London', 'HWF', 'F'))]
R['C61'] = lambda: [('London WSDI3 H (near 14)', 14, pm('London', 'WSDI3', 'H'), None), ('N', 76, pm('London', 'WSDI3', 'N')), ('F', 162, pm('London', 'WSDI3', 'F'))]
R['C53'] = lambda: [('London TR H (near 3)', 3, pm('London', 'TR', 'H'), None), ('P', 6, pm('London', 'TR', 'P')), ('N', 18, pm('London', 'TR', 'N')), ('F', 50, pm('London', 'TR', 'F')), ('seventeen-fold', 17, pm('London', 'TR', 'F') / pm('London', 'TR', 'H'), None)]
R['C56'] = lambda: [('London TN90p H (approx 10)', 10, pm('London', 'TN90p', 'H'), None), ('F', 53, pm('London', 'TN90p', 'F'))]
