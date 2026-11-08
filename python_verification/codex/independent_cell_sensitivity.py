from independent_pass1 import *
rows=[]
for short,model in MODELS.items():
 d=read(PC/'txt'/f'FERGUS_SENS_{model}.txt');r=indices(d);r['station']='Fergus_sensitivity_cell';r['model']=short;rows.append(r)
a=pd.concat(rows,ignore_index=True);a.to_csv(OUT/'fergus_cell_sensitivity_pass1.csv',index=False);print('annual rows',len(a))
