from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from audit.models import AuditLog
from contracts.models import Contract
from contractos.services.llm_service import AzureOpenAIService
from contractos.services.ocr_service import DocumentIntelligenceService


@shared_task
def ingest_contract_document(contract_id: str, file_bytes: bytes) -> dict:
    ocr = DocumentIntelligenceService()
    if not ocr.is_configured():
        return {"status": "skipped", "reason": "document intelligence not configured"}

    extracted_text = ocr.extract_text(file_bytes)
    return {"status": "ok", "contract_id": contract_id, "text_length": len(extracted_text)}


@shared_task
def run_llm_redline_analysis(contract_id: str, prompt: str) -> dict:
    llm = AzureOpenAIService()
    if not llm.is_configured():
        return {"status": "skipped", "reason": "azure openai not configured"}

    result = llm.complete(prompt, system_prompt="You are a legal contract analysis assistant.")
    return {"status": "ok", "contract_id": contract_id, "response": result}


@shared_task
def create_expiry_alerts() -> dict:
    today = timezone.now().date()
    windows = [30, 60, 90]
    created = 0

    for days in windows:
        target_date = today + timedelta(days=days)
        contracts = Contract.objects.filter(status="Active", expiry=target_date)
        for contract in contracts:
            AuditLog.objects.create(
                user=None,
                action=f"Expiry Alert {days}d",
                target=contract.name,
                ip="Internal",
            )
            created += 1

    return {"status": "ok", "alerts_created": created}
