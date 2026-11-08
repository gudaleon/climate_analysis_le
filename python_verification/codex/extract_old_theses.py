from independent_pass1 import *
from zipfile import ZipFile
from lxml import etree
import difflib,re
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
branches=[('613_old',next((P1/'1_Thesis/Before_6.13_old_data').glob('*.docx'))),('613_new',next((P1/'1_Thesis/After_6.13_new_data').glob('*clean.docx'))),('v7_old',next((P2/'1_Thesis/Before_submitted_9_28_old_data').glob('*.docx'))),('v7_intermediate',next((P2/'1_Thesis/Intermediate_v6').glob('*.docx'))),('v7_new',next((P2/'1_Thesis/After_v7_defence').glob('*clean.docx')))]
texts={}
for label,p in branches:
 with ZipFile(p) as z:doc=etree.fromstring(z.read('word/document.xml'))
 t=[''.join(e.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns)) for e in doc.xpath('//w:p',namespaces=ns)];texts[label]=t;(OUT/f'text_{label}.txt').write_text('\n'.join(t))
for old,new in [('613_old','613_new'),('v7_old','v7_new'),('v7_intermediate','v7_new')]:
 diff='\n'.join(difflib.unified_diff(texts[old],texts[new],fromfile=old,tofile=new));(OUT/f'text_diff_{old}_{new}.txt').write_text(diff)
print({k:len(v) for k,v in texts.items()})
