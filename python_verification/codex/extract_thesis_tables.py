from independent_pass1 import *
from zipfile import ZipFile
from lxml import etree
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
for tag,root,fn in [('613',P1,'JW_Thesis_6.13_new_data_clean.docx'),('v7',P2,'JW_Thesis_revised_v7_clean.docx')]:
 p=next((root/'1_Thesis').rglob(fn))
 with ZipFile(p) as z:doc=etree.fromstring(z.read('word/document.xml'))
 rows=[];tables=[]
 for ti,tab in enumerate(doc.xpath('//w:tbl',namespaces=ns)):
  out=[]
  for ri,row in enumerate(tab.xpath('./w:tr',namespaces=ns)):
   cells=[]
   for ci,cell in enumerate(row.xpath('./w:tc',namespaces=ns)):
    txt=''.join(cell.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns));fill=cell.xpath('./w:tcPr/w:shd/@w:fill',namespaces=ns);sym=cell.xpath('.//w:sym/@w:char',namespaces=ns);cells.append(txt);rows.append(dict(table=ti,row=ri,column=ci,text=txt,fill=';'.join(fill),symbol=';'.join(sym)))
   out.append(cells)
  tables.append(dict(table=ti,rows=len(out),first_rows=out[:3]))
 pd.DataFrame(rows).to_csv(OUT/f'thesis_tables_{tag}.csv',index=False);(OUT/f'thesis_tables_{tag}_map.json').write_text(json.dumps(tables,indent=2,ensure_ascii=False));print(tag,'tables',len(tables),'cells',len(rows))
