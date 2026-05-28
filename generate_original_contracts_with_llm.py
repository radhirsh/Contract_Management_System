"""Generate original contract documents using Azure OpenAI and attach PDFs.

Usage:
    python generate_original_contracts_with_llm.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contractos.settings")
django.setup()

from django.conf import settings
from django.core.files import File

from contracts.models import Contract
from ensure_contract_documents import (
    _generate_contract_text_with_llm,
    build_contract_document_text,
    generate_contract_pdf,
)


def generate_original_contracts_with_llm():
    media_root = settings.MEDIA_ROOT
    generated = 0
    fallback = 0

    for contract in Contract.objects.all().order_by("id"):
        llm_text = _generate_contract_text_with_llm(contract)
        if llm_text:
            contract.ai_extracted_text = llm_text
            contract.save(update_fields=["ai_extracted_text"])
            generated += 1
        else:
            # Keep existing text if LLM is not available.
            contract.ai_extracted_text = build_contract_document_text(contract)
            contract.save(update_fields=["ai_extracted_text"])
            fallback += 1

        filename = f"contract_{contract.id}.pdf"
        out_path = os.path.join(media_root, "contracts", filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        generate_contract_pdf(contract, out_path)
        with open(out_path, "rb") as f:
            contract.file.save(filename, File(f), save=True)

        print(f"✓ Updated contract document: {contract.id} - {contract.name}")

    print("\nSummary")
    print(f"LLM-generated originals: {generated}")
    print(f"Fallback content used: {fallback}")


if __name__ == "__main__":
    generate_original_contracts_with_llm()
