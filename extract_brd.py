import docx
import os

doc_path = '../Contract_Management_System_BRD.docx'
if not os.path.exists(doc_path):
    print(f'File {doc_path} not found.')
else:
    doc = docx.Document(doc_path)
    print('### SECTION HEADINGS ###')
    for para in doc.paragraphs:
        if para.style.name.startswith('Heading') or (para.text.isupper() and len(para.text) > 3):
            print(para.text.strip())
    
    print('\n### CONTENT SUMMARY ###')
    # Print the first 100 non-empty paragraphs to get an overview
    count = 0
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            print(text)
            count += 1
        if count > 200:
            break
