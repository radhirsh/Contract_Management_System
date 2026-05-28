import os
from typing import List


class DocumentIntelligenceService:
    def __init__(self) -> None:
        self.endpoint = os.getenv("AZURE_DI_ENDPOINT", "")
        self.key = os.getenv("AZURE_DI_KEY", "")
        self.model = os.getenv("AZURE_DI_MODEL", "prebuilt-layout")

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.key)

    def extract_text(self, file_bytes: bytes) -> str:
        if not self.is_configured():
            raise RuntimeError("Azure Document Intelligence is not configured.")

        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.ai.documentintelligence import DocumentIntelligenceClient
        except ImportError as exc:
            raise RuntimeError("azure-ai-documentintelligence package is not installed.") from exc

        client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
        )

        poller = client.begin_analyze_document(self.model, body=file_bytes)
        result = poller.result()

        lines: List[str] = []
        for page in getattr(result, "pages", []) or []:
            for line in getattr(page, "lines", []) or []:
                if getattr(line, "content", None):
                    lines.append(line.content)
        return "\n".join(lines)
