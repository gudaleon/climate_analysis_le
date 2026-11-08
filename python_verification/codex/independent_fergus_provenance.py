from independent_pass1 import *
rows=[]
for sh,mo in MODELS.items():
 sens=read(PC/'txt'/f'FERGUS_SENS_{mo}.txt')
 for tag,root in [('613',P1),('v7',P2)]:
  pack=read(root/'2_Data/2_Models/b_Daily_series'/f'Fergus_{sh}.txt');eq=sens.shape==pack.shape and np.allclose(sens,pack,equal_nan=True);rows.append(dict(target=tag,model=sh,equal_fergus_sensitivity_cell=bool(eq),different_cells=int(sum((~np.isclose(sens,pack,equal_nan=True)).ravel()))))
pd.DataFrame(rows).to_csv(OUT/'fergus_sensitivity_provenance.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
