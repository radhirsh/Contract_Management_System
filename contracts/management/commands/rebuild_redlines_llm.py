from django.core.management.base import BaseCommand
from django.utils import timezone

from contracts.models import Contract, RedlineSuggestion
from contracts.views import (
    _build_clause_catalog,
    _extract_text_from_file,
    _persist_llm_assessment,
    _run_llm_clause_assessment,
)


class Command(BaseCommand):
    help = "Rebuild all contract redlines using real-time LLM JSON assessment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-existing",
            action="store_true",
            help="Keep existing redline rows and append new unsatisfied records.",
        )

    def handle(self, *args, **options):
        keep_existing = bool(options.get("keep_existing"))
        contracts = Contract.objects.all().order_by("id")

        if not contracts.exists():
            self.stdout.write(self.style.WARNING("No contracts found."))
            return

        clause_catalog, clause_by_id = _build_clause_catalog()
        if not clause_catalog:
            self.stdout.write(self.style.ERROR("No clauses found in repository."))
            return

        total_contracts = 0
        total_unsatisfied = 0
        total_satisfied = 0
        failed = 0

        for contract in contracts:
            total_contracts += 1
            try:
                if not keep_existing:
                    RedlineSuggestion.objects.filter(contract=contract).delete()

                contract_text = (contract.ai_extracted_text or "").strip()
                if not contract_text and contract.file:
                    try:
                        file_bytes = contract.file.read()
                        contract_text = (_extract_text_from_file(file_bytes) or "").strip()
                    except Exception:
                        contract_text = ""

                if contract_text:
                    contract.ai_extracted_text = contract_text
                    contract.ai_analyzed_at = timezone.now()
                    contract.save(update_fields=["ai_extracted_text", "ai_analyzed_at"])
                else:
                    raise RuntimeError("No contract text found")

                llm_results = _run_llm_clause_assessment(contract_text, clause_catalog)
                satisfied, unsatisfied = _persist_llm_assessment(contract, llm_results, clause_by_id)

                contract.redlines = RedlineSuggestion.objects.filter(contract=contract).count()
                contract.save(update_fields=["redlines"])

                total_satisfied += len(satisfied)
                total_unsatisfied += len(unsatisfied)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{contract.id}: satisfied={len(satisfied)} unsatisfied={len(unsatisfied)} saved={contract.redlines}"
                    )
                )
            except Exception as exc:
                failed += 1
                self.stdout.write(self.style.ERROR(f"{contract.id}: FAILED - {exc}"))

        summary = (
            f"Processed={total_contracts}, Failed={failed}, "
            f"Satisfied={total_satisfied}, Unsatisfied={total_unsatisfied}"
        )
        if failed:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
