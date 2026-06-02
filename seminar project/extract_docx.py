import zipfile
import xml.etree.ElementTree as ET

z = zipfile.ZipFile(r'c:\Study\260330 AgentDAG\세미나 프로젝트 연구 계획서.docx')
tree = ET.fromstring(z.read('word/document.xml'))
text = [''.join(t.text for t in p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text) for p in tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')]
with open('doc_content.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join([t for t in text if t.strip()]))
