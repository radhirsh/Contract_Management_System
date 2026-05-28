import os
import django
from django.conf import settings
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractos.settings')
django.setup()

from contracts.models import Contract
from ensure_contract_documents import generate_contract_pdf

def regenerate_all_contract_pdfs():
    """Regenerate all contract PDFs to include redline suggestions"""
    media_root = settings.MEDIA_ROOT
    count = 0
    
    for contract in Contract.objects.all():
        filename = f"contract_{contract.id}.pdf"
        out_path = os.path.join(media_root, "contracts", filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        # Generate new PDF
        generate_contract_pdf(contract, out_path)
        
        # Save to model
        with open(out_path, "rb") as f:
            contract.file.save(filename, File(f), save=True)
        
        print(f"✓ Regenerated: {contract.name} ({contract.id})")
        count += 1
    
    print(f"\n✓ Successfully regenerated {count} contract PDFs with redline suggestions")

if __name__ == "__main__":
    regenerate_all_contract_pdfs()
