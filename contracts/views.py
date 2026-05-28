import json
import logging
import os
import re
from rest_framework import viewsets, permissions
from .models import Contract, RedlineSuggestion, ContractComparison
from .serializers import ContractSerializer, RedlineSuggestionSerializer, ContractComparisonSerializer
from .forms import QuickUploadForm, WorkbenchConfirmForm
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.files import File
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from datetime import timedelta
from audit.models import AuditLog

from .forms import WorkbenchConfirmForm

logger = logging.getLogger(__name__)


def _regenerate_contract_pdf(contract, highlight_lines=None):
    from ensure_contract_documents import generate_contract_pdf

    filename = f"contract_{contract.id}.pdf"
    out_path = os.path.join(settings.MEDIA_ROOT, 'contracts', filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    generate_contract_pdf(contract, out_path, highlight_lines=highlight_lines or [])
    with open(out_path, 'rb') as f:
        contract.file.save(filename, File(f), save=True)


def _apply_accepted_redline_to_contract(suggestion):
    """Apply accepted redline into contract text and return changed lines for PDF highlighting."""
    contract = suggestion.contract
    text = (contract.ai_extracted_text or '').strip()
    if not text:
        return []

    replacement = _pick_clause_text(
        suggestion.standard_rule,
        suggestion.ai_recommendation,
        suggestion.recommendation,
    )
    if not replacement:
        return []

    lines = text.splitlines()
    changed_lines = []
    line_no, line_text = _find_source_line(text, suggestion.issue, suggestion.recommendation)

    if line_no and 1 <= line_no <= len(lines):
        current_line = lines[line_no - 1].strip()
        if _normalize_text(current_line) != _normalize_text(replacement):
            lines[line_no - 1] = replacement
            changed_lines.append(replacement)
    else:
        # No reliable source line found; append accepted clause as amendment text.
        amendment_line = f"{suggestion.issue}: {replacement}"
        if _normalize_text(amendment_line) not in _normalize_text(text):
            lines.append('')
            lines.append('Accepted Amendment Updates')
            lines.append(amendment_line)
            changed_lines.append(amendment_line)

    if not changed_lines:
        return []

    contract.ai_extracted_text = "\n".join(lines).strip()
    contract.ai_analyzed_at = timezone.now()
    contract.save(update_fields=['ai_extracted_text', 'ai_analyzed_at'])
    return changed_lines


def _extract_json_payload(raw: str):
    text = (raw or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
    return None


def _build_clause_catalog():
    from clauses.models import Clause

    catalog = []
    by_id = {}
    for clause in Clause.objects.all():
        issue = (clause.clause_name or clause.name or clause.clause_category or "Clause")[:255]
        risk = clause.risk_level if clause.risk_level in ('High', 'Medium', 'Low') else (
            clause.risk if clause.risk in ('High', 'Medium', 'Low') else 'Medium'
        )
        item = {
            'id': str(clause.id),
            'issue': issue,
            'standard_rule': _pick_clause_text(clause.standard_rule, clause.standard_rule_value),
            'restricted_terms': _pick_clause_text(clause.restricted_terms, clause.restricted_terms_conditions),
            'deviation_rule': _pick_clause_text(clause.deviation_rule),
            'ai_recommendation': _pick_clause_text(clause.ai_recommendation),
            'risk': risk,
            'clause_obj': clause,
        }
        catalog.append(item)
        by_id[item['id']] = item
    return catalog, by_id


def _run_llm_clause_assessment(contract_text: str, clause_catalog):
    """Use LLM to assess each clause as satisfied/unsatisfied and return normalized JSON records."""
    from contractos.services.llm_service import AzureOpenAIService

    svc = AzureOpenAIService()
    if not svc.is_configured():
        raise RuntimeError('Azure OpenAI is not configured for real-time clause assessment.')

    contract_snippet = (contract_text or "")[:16000]
    clauses_payload = [
        {
            'clause_id': c['id'],
            'issue': c['issue'],
            'standard_rule': c['standard_rule'],
            'restricted_terms': c['restricted_terms'],
            'deviation_rule': c['deviation_rule'],
            'expected_recommendation': c['ai_recommendation'],
            'risk': c['risk'],
        }
        for c in clause_catalog
    ]

    system_prompt = (
        'You are a contract compliance reviewer. '
        'Compare contract text with each clause rule and return ONLY valid JSON.'
    )
    prompt = (
        'Analyze the contract text against each clause. '\
        'Decide satisfied true/false using evidence from the contract passage. '\
        'For every clause, provide a concise reason explaining why the clause is satisfied or unsatisfied. '\
        'If unsatisfied, provide a concrete fix recommendation. '\
        'Return JSON object with this exact shape:\n'
        '{"results":[{"clause_id":"...","issue":"...","satisfied":true|false,'
        '"reason":"...","source_quote":"...","recommendation":"...","risk":"High|Medium|Low"}]}\n\n'
        f'Clauses JSON:\n{json.dumps(clauses_payload, ensure_ascii=True)}\n\n'
        f'Contract Text:\n{contract_snippet}'
    )

    raw = svc.complete(prompt, system_prompt=system_prompt)
    payload = _extract_json_payload(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
        raise RuntimeError('LLM did not return the expected JSON format for clause assessment.')

    normalized = []
    for item in payload.get('results', []):
        if not isinstance(item, dict):
            continue
        clause_id = str(item.get('clause_id', '')).strip()
        if not clause_id:
            continue
        raw_satisfied = item.get('satisfied', False)
        if isinstance(raw_satisfied, str):
            satisfied_flag = raw_satisfied.strip().lower() in {'true', '1', 'yes', 'y'}
        else:
            satisfied_flag = bool(raw_satisfied)
        reason = str(item.get('reason', '')).strip()
        if not reason and satisfied_flag:
            reason = 'Condition satisfied in contract text.'
        elif not reason:
            reason = 'Evidence indicates the clause is absent or altered from the standard rule.'

        normalized.append(
            {
                'clause_id': clause_id,
                'issue': str(item.get('issue', '')).strip(),
                'satisfied': satisfied_flag,
                'reason': reason,
                'source_quote': str(item.get('source_quote', '')).strip(),
                'recommendation': str(item.get('recommendation', '')).strip(),
                'risk': str(item.get('risk', '')).strip(),
            }
        )
    return normalized


def _build_assessment_for_view(contract_text: str, llm_results, clause_by_id):
    """Build satisfied/unsatisfied payload for UI without writing DB rows."""
    satisfied = []
    unsatisfied = []
    seen_clause_ids = set()

    for result in llm_results:
        clause_id = str(result.get('clause_id', '')).strip()
        clause_meta = clause_by_id.get(clause_id)
        if not clause_meta:
            continue
        seen_clause_ids.add(clause_id)

        status = 'Satisfied' if result.get('satisfied') else 'Open'
        recommendation = result.get('recommendation') or clause_meta['ai_recommendation'] or clause_meta['deviation_rule']
        source_line_no, source_line_text = _find_source_line(contract_text, result.get('issue') or clause_meta['issue'], recommendation)
        source_quote = result.get('source_quote', '') or source_line_text or ''
        row = {
            'clause_id': clause_id,
            'issue': result.get('issue') or clause_meta['issue'],
            'risk': result.get('risk') if result.get('risk') in ('High', 'Medium', 'Low') else clause_meta['risk'],
            'reason': result.get('reason', ''),
            'recommendation': recommendation,
            'standard_rule': clause_meta['standard_rule'],
            'restricted_terms': clause_meta['restricted_terms'],
            'deviation_rule': clause_meta['deviation_rule'],
            'ai_recommendation': recommendation,
            'source_quote': source_quote,
            'source_line_no': source_line_no,
            'source_page_no': _find_source_page(source_line_no),
            'status': status,
        }
        if result.get('satisfied'):
            satisfied.append(row)
        else:
            unsatisfied.append(row)

    for clause_id, clause_meta in clause_by_id.items():
        if clause_id in seen_clause_ids:
            continue
        unsatisfied.append(
            {
                'clause_id': clause_id,
                'issue': clause_meta['issue'],
                'risk': clause_meta['risk'],
                'reason': 'Clause missing in LLM response output.',
                'recommendation': 'Clause missing in LLM response. Please review manually.',
                'standard_rule': clause_meta['standard_rule'],
                'restricted_terms': clause_meta['restricted_terms'],
                'deviation_rule': clause_meta['deviation_rule'],
                'ai_recommendation': clause_meta['ai_recommendation'],
                'source_quote': '',
                'status': 'Open',
            }
        )

    if not contract_text:
        return [], []
    return satisfied, unsatisfied


def _cache_assessment_in_session(request, contract_id: str, satisfied, unsatisfied):
    bucket = request.session.get('redline_assessment', {})
    bucket[str(contract_id)] = {
        'satisfied': satisfied,
        'unsatisfied': unsatisfied,
        'at': timezone.now().isoformat(),
    }
    request.session['redline_assessment'] = bucket


def _clear_cached_assessment(request, contract_id: str):
    bucket = request.session.get('redline_assessment', {})
    if str(contract_id) in bucket:
        bucket.pop(str(contract_id), None)
        request.session['redline_assessment'] = bucket


def _get_cached_assessment(request, contract_id: str):
    bucket = request.session.get('redline_assessment', {})
    val = bucket.get(str(contract_id))
    if isinstance(val, dict):
        return val
    return None


def _extract_issue_tokens(issue: str):
    """Extract meaningful tokens from an issue title for text matching."""
    tokens = re.findall(r"[A-Za-z0-9]+", (issue or "").lower())
    return [t for t in tokens if len(t) >= 4]


def _find_source_line(contract_text: str, issue: str, recommendation: str = ""):
    """Return (line_no, line_text) in contract text that best matches a redline issue; else (None, None)."""
    if not contract_text:
        return None, None

    lines = [ln.strip() for ln in contract_text.splitlines() if ln.strip()]
    if not lines:
        return None, None

    issue_tokens = _extract_issue_tokens(issue)
    rec_tokens = _extract_issue_tokens(recommendation)
    tokens = issue_tokens[:4] + rec_tokens[:3]
    if not tokens:
        return None, None

    best_score = 0
    best_line_no = None
    best_line = None

    for idx, line in enumerate(lines, start=1):
        low = line.lower()
        score = sum(1 for tok in tokens if tok in low)
        if score > best_score:
            best_score = score
            best_line_no = idx
            best_line = line

    if best_score == 0:
        return None, None
    return best_line_no, best_line


def _find_source_page(line_no: int, lines_per_page: int = 40):
    if not line_no:
        return None
    return ((line_no - 1) // lines_per_page) + 1


def _attach_source_evidence(redlines, contract):
    """Attach transient source evidence fields to redline objects for template use."""
    contract_text = contract.ai_extracted_text or ""
    for r in redlines:
        ln, txt = _find_source_line(contract_text, r.issue, r.recommendation)
        r.source_line_no = ln
        r.source_page_no = _find_source_page(ln)
        r.source_line_text = txt
        r.source_found = bool(ln and txt)
    return redlines


def _attach_clause_intelligence(redlines):
    """Attach transient clause intelligence fields with fallback for legacy redlines."""
    for r in redlines:
        clause = getattr(r, 'clause', None)
        r.display_standard_rule = _pick_clause_text(
            getattr(r, 'standard_rule', ''),
            getattr(clause, 'standard_rule', '') if clause else '',
            getattr(clause, 'standard_rule_value', '') if clause else '',
        )
        r.display_restricted_terms = _pick_clause_text(
            getattr(r, 'restricted_terms', ''),
            getattr(clause, 'restricted_terms', '') if clause else '',
            getattr(clause, 'restricted_terms_conditions', '') if clause else '',
        )
        r.display_deviation_rule = _pick_clause_text(
            getattr(r, 'deviation_rule', ''),
            getattr(clause, 'deviation_rule', '') if clause else '',
        )
        r.display_ai_recommendation = _pick_clause_text(
            getattr(r, 'ai_recommendation', ''),
            getattr(clause, 'ai_recommendation', '') if clause else '',
            getattr(r, 'recommendation', ''),
        )
    return redlines


def _is_placeholder_text(value: str) -> bool:
    text = (value or "").strip().lower()
    return text in {
        "",
        "no standard rule provided",
        "no restricted terms provided",
        "no deviation rule provided",
        "no ai recommendation provided",
    }


def _pick_clause_text(*candidates):
    for val in candidates:
        if not _is_placeholder_text(str(val or "")):
            return str(val).strip()
    for val in candidates:
        if str(val or "").strip():
            return str(val).strip()
    return ""


# ---------------------------------------------------------------------------
# AI Extraction helper
# ---------------------------------------------------------------------------

def _extract_text_from_file(file_bytes: bytes) -> str:
    """Run Azure Document Intelligence OCR; fall back to empty string on error."""
    try:
        from contractos.services.ocr_service import DocumentIntelligenceService
        svc = DocumentIntelligenceService()
        if svc.is_configured():
            return svc.extract_text(file_bytes)
    except Exception as exc:
        logger.warning("OCR extraction failed: %s", exc)
    return ""


def _extract_metadata_via_llm(file_name: str, hint_name: str, extracted_text: str) -> dict:
    """
    Ask Azure OpenAI to extract contract metadata from the OCR'd text.
    Returns a dict with keys: name, vendor, expiry_date, risk, version, clause_count, status, summary.
    Falls back to sensible defaults on any error.
    """
    today = timezone.now().date().isoformat()
    text_snippet = extracted_text[:6000] if extracted_text else "(no text extracted)"

    system_prompt = (
        "You are an expert contract analyst. Extract structured metadata from legal contracts. "
        "Return ONLY a valid JSON object — no markdown, no explanation."
    )
    prompt = f"""Extract metadata from this contract and return a single JSON object with these exact keys:
- "name": full descriptive contract title (use hint if provided, otherwise infer from text)
- "vendor": the counter-party / vendor company name
- "expiry_date": contract end/expiry date in YYYY-MM-DD format, or null if not found
- "risk": overall risk level — one of "High", "Medium", "Low"
- "version": contract version string like "v1.0", or "v1.0" if not stated
- "clause_count": integer count of distinct numbered clauses
- "status": "Active" if expiry is in the future relative to today ({today}), else "Expired"
- "summary": 2-3 sentence plain-English summary of what this contract covers

Hint name provided by user: "{hint_name or file_name}"
File name: "{file_name}"

Contract text (first 6000 chars):
{text_snippet}"""

    try:
        from contractos.services.llm_service import AzureOpenAIService
        svc = AzureOpenAIService()
        if svc.is_configured():
            raw = svc.complete(prompt, system_prompt=system_prompt)
            # Strip markdown code fences if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
    except Exception as exc:
        logger.warning("LLM metadata extraction failed: %s", exc)

    # Graceful fallback — return empty defaults
    return {
        "name": hint_name or file_name,
        "vendor": "",
        "expiry_date": None,
        "risk": "Medium",
        "version": "v1.0",
        "clause_count": 0,
        "status": "Active",
        "summary": "",
    }


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by('-uploaded')
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]


class RedlineSuggestionViewSet(viewsets.ModelViewSet):
    queryset = RedlineSuggestion.objects.select_related('contract', 'clause').all().order_by('-created_at')
    serializer_class = RedlineSuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]


class ContractComparisonViewSet(viewsets.ModelViewSet):
    queryset = ContractComparison.objects.select_related('contract_left', 'contract_right', 'exported_by').all().order_by('-exported_at')
    serializer_class = ContractComparisonSerializer
    permission_classes = [permissions.IsAuthenticated]

@login_required
def dashboard(request):
    contracts = Contract.objects.all().order_by('-uploaded')
    today = timezone.now().date()

    active_count = contracts.filter(status='Active').count()
    expired_count = contracts.filter(status='Expired').count()
    high_risk_count = contracts.filter(risk='High', status='Active').count()
    expiring_30_count = contracts.filter(status='Active', expiry__lte=today + timedelta(days=30), expiry__gte=today).count()
    expiring_60_count = contracts.filter(status='Active', expiry__lte=today + timedelta(days=60), expiry__gte=today).count()
    expiring_90_count = contracts.filter(status='Active', expiry__lte=today + timedelta(days=90), expiry__gte=today).count()
    expiring_soon_qs = contracts.filter(status='Active', expiry__lte=today + timedelta(days=90), expiry__gte=today).order_by('expiry')
    recent_activities = AuditLog.objects.select_related('user').order_by('-time')[:5]

    # Quick search from dashboard search bar
    q = request.GET.get('q', '').strip()
    search_results = None
    if q:
        search_results = contracts.filter(
            Q(name__icontains=q) | Q(vendor__icontains=q) | Q(id__icontains=q)
        )

    context = {
        'active_nav': 'dashboard',
        'contracts': contracts,
        'active_count': active_count,
        'expired_count': expired_count,
        'high_risk_count': high_risk_count,
        'expiring_30_count': expiring_30_count,
        'expiring_60_count': expiring_60_count,
        'expiring_90_count': expiring_90_count,
        'expiring_soon_contracts': expiring_soon_qs[:6],
        'recent_uploads': contracts[:5],
        'recent_activities': recent_activities,
        'q': q,
        'search_results': search_results,
    }
    return render(request, 'contracts/dashboard.html', context)

@login_required
def contract_list(request):
    qs = Contract.objects.all().order_by('-uploaded')
    q = request.GET.get('q', '').strip()
    risk = request.GET.get('risk', '')
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(vendor__icontains=q) | Q(id__icontains=q))
    if risk:
        qs = qs.filter(risk=risk)
    if status:
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'contracts/contract_list.html', {
        'contracts': page_obj,
        'page_obj': page_obj,
        'active_nav': 'contracts',
        'q': q,
        'filter_risk': risk,
        'filter_status': status,
    })


@login_required
def upload_contract(request):
    """Step 1: upload file → OCR + LLM extraction → redirect to workbench."""
    error = None
    if request.method == 'POST':
        form = QuickUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            hint_name = form.cleaned_data.get('contract_hint', '') or ''

            file_bytes = uploaded_file.read()

            # Store file in media so we can reference it later
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os
            save_path = os.path.join('contracts', uploaded_file.name)
            saved_path = default_storage.save(save_path, ContentFile(file_bytes))

            # --- AI pipeline ---
            extracted_text = _extract_text_from_file(file_bytes)
            metadata = _extract_metadata_via_llm(uploaded_file.name, hint_name, extracted_text)

            # Stash everything in session for the workbench step
            request.session['wb_file_path'] = saved_path
            request.session['wb_file_name'] = uploaded_file.name
            request.session['wb_metadata'] = metadata
            request.session['wb_extracted_text'] = extracted_text[:3000]  # preview only

            return redirect('contract_workbench')
    else:
        form = QuickUploadForm()

    return render(request, 'contracts/upload_contract.html', {
        'form': form,
        'error': error,
        'active_nav': 'contracts',
    })


@login_required
def contract_workbench(request, pk=None):
    """Step 2: review / edit AI-extracted metadata, then save."""
    if pk:
        contract = get_object_or_404(Contract, pk=pk)
        file_name = ''
        document_url = ''
        summary = ''
        extracted_text = ''
        if contract.file:
            current_file_ref = str(contract.file.name)
            file_name = current_file_ref.split('/')[-1]
            document_url = contract.file.url
            if request.method == 'GET':
                needs_refresh = (
                    contract.ai_analyzed_at is None
                    or contract.ai_source_file != current_file_ref
                )

                if needs_refresh:
                    try:
                        file_bytes = contract.file.read()
                        extracted_full_text = _extract_text_from_file(file_bytes)
                        metadata = _extract_metadata_via_llm(file_name, contract.name, extracted_full_text)
                        summary = metadata.get('summary', '')
                        extracted_text = (extracted_full_text or '')[:3000]

                        contract.ai_summary = summary
                        contract.ai_extracted_text = extracted_text
                        contract.ai_source_file = current_file_ref
                        contract.ai_analyzed_at = timezone.now()
                        contract.save(update_fields=['ai_summary', 'ai_extracted_text', 'ai_source_file', 'ai_analyzed_at'])
                    except Exception as exc:
                        logger.warning('Failed to build workbench preview for %s: %s', contract.id, exc)
                        summary = contract.ai_summary or ''
                        extracted_text = contract.ai_extracted_text or ''
                else:
                    summary = contract.ai_summary or ''
                    extracted_text = contract.ai_extracted_text or ''

        if request.method == 'POST':
            form = WorkbenchConfirmForm(request.POST, instance=contract)
            if form.is_valid():
                form.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='Workbench Update',
                    target=contract.name,
                    ip=request.META.get('REMOTE_ADDR', ''),
                )
                messages.success(request, f'Contract "{contract.name}" updated from workbench.')
                return redirect('contract_detail', pk=contract.id)
        else:
            form = WorkbenchConfirmForm(instance=contract)

        return render(request, 'contracts/workbench.html', {
            'form': form,
            'file_name': file_name,
            'summary': summary,
            'extracted_text': extracted_text,
            'document_url': document_url,
            'active_nav': 'contracts',
        })

    metadata = request.session.get('wb_metadata')
    file_path = request.session.get('wb_file_path')
    file_name = request.session.get('wb_file_name', '')
    extracted_text = request.session.get('wb_extracted_text', '')
    document_url = ''

    try:
        from django.core.files.storage import default_storage
        if file_path:
            document_url = default_storage.url(file_path)
    except Exception:
        document_url = ''

    if not metadata or not file_path:
        messages.error(request, 'No pending upload found. Please upload a document first.')
        return redirect('upload_contract')

    if request.method == 'POST':
        form = WorkbenchConfirmForm(request.POST)
        if form.is_valid():
            # Auto-generate next contract ID
            used_nums = []
            for c in Contract.objects.filter(id__startswith='C-'):
                try:
                    used_nums.append(int(c.id.split('-')[1]))
                except (IndexError, ValueError):
                    pass
            next_num = max(used_nums) + 1 if used_nums else 1
            contract_id = f'C-{next_num:03d}'

            contract = form.save(commit=False)
            contract.id = contract_id
            contract.file = file_path
            contract.ai_summary = metadata.get('summary', '')
            contract.ai_extracted_text = extracted_text
            contract.ai_source_file = file_path
            contract.ai_analyzed_at = timezone.now()
            contract.created_by = request.user
            contract.save()

            AuditLog.objects.create(
                user=request.user,
                action='Upload',
                target=contract.name,
                ip=request.META.get('REMOTE_ADDR', ''),
            )

            # Clear session workbench data
            for key in ('wb_file_path', 'wb_file_name', 'wb_metadata', 'wb_extracted_text'):
                request.session.pop(key, None)

            messages.success(request, f'Contract "{contract.name}" saved as {contract_id}.')
            return redirect('contract_detail', pk=contract.id)
    else:
        # Pre-fill form from AI extraction
        expiry = metadata.get('expiry_date') or ''
        initial = {
            'name': metadata.get('name', file_name),
            'vendor': metadata.get('vendor', ''),
            'expiry': expiry,
            'risk': metadata.get('risk', 'Medium'),
            'version': metadata.get('version', 'v1.0'),
            'status': metadata.get('status', 'Active'),
            'clauses': metadata.get('clause_count', 0),
        }
        form = WorkbenchConfirmForm(initial=initial)

    return render(request, 'contracts/workbench.html', {
        'form': form,
        'file_name': file_name,
        'summary': metadata.get('summary', ''),
        'extracted_text': extracted_text,
        'document_url': document_url,
        'active_nav': 'contracts',
    })

@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    redlines = RedlineSuggestion.objects.select_related('clause').filter(contract=contract).order_by('-created_at')
    redlines = _attach_source_evidence(redlines, contract)
    redlines = _attach_clause_intelligence(redlines)
    cached_assessment = _get_cached_assessment(request, contract.id)
    if cached_assessment:
        satisfied_conditions = cached_assessment.get('satisfied', [])
        unsatisfied_conditions = cached_assessment.get('unsatisfied', [])

        redline_by_id = {str(r.pk): r for r in redlines}
        redline_by_clause = {
            str(r.clause_id): r for r in redlines if getattr(r, 'clause_id', None)
        }
        for row in satisfied_conditions + unsatisfied_conditions:
            row_redline = None
            rid = str(row.get('redline_id', '') or '')
            cid = str(row.get('clause_id', '') or '')
            if rid and rid in redline_by_id:
                row_redline = redline_by_id[rid]
            elif cid and cid in redline_by_clause:
                row_redline = redline_by_clause[cid]
                row['redline_id'] = row_redline.pk

            if row_redline:
                row['status'] = row_redline.status
                row['source_line_no'] = getattr(row_redline, 'source_line_no', None)
                row['source_page_no'] = getattr(row_redline, 'source_page_no', None)
                if not row.get('source_quote'):
                    row['source_quote'] = getattr(row_redline, 'source_line_text', '')
    else:
        # Build live assessment when cache is absent (e.g., after command-line rebuilds/new sessions).
        satisfied_conditions = []
        unsatisfied_conditions = []
        try:
            clause_catalog, clause_by_id = _build_clause_catalog()
            contract_text = (contract.ai_extracted_text or '').strip()
            if contract_text and clause_catalog:
                llm_results = _run_llm_clause_assessment(contract_text, clause_catalog)
                satisfied_conditions, unsatisfied_conditions = _build_assessment_for_view(
                    contract_text, llm_results, clause_by_id
                )
                _cache_assessment_in_session(request, contract.id, satisfied_conditions, unsatisfied_conditions)
        except Exception as exc:
            logger.warning('Live assessment fallback failed for %s: %s', contract.id, exc)

        # Last-resort fallback from DB rows if live assessment could not run.
        if not satisfied_conditions and not unsatisfied_conditions:
            unsatisfied_conditions = [
                {
                    'clause_id': str(getattr(r.clause, 'id', '')) if getattr(r, 'clause', None) else '',
                    'issue': r.issue,
                    'risk': r.risk,
                    'reason': '',
                    'recommendation': r.recommendation,
                    'standard_rule': getattr(r, 'display_standard_rule', ''),
                    'restricted_terms': getattr(r, 'display_restricted_terms', ''),
                    'deviation_rule': getattr(r, 'display_deviation_rule', ''),
                    'ai_recommendation': getattr(r, 'display_ai_recommendation', ''),
                    'source_quote': getattr(r, 'source_line_text', ''),
                    'source_line_no': getattr(r, 'source_line_no', None),
                    'source_page_no': getattr(r, 'source_page_no', None),
                    'status': r.status,
                    'redline_id': r.pk,
                }
                for r in redlines
            ]
    audit_logs = AuditLog.objects.filter(target__icontains=contract.name).order_by('-time')[:10]
    contract_versions = Contract.objects.filter(
        name=contract.name,
        vendor=contract.vendor,
    ).order_by('-uploaded')

    return render(request, 'contracts/contract_detail.html', {
        'contract': contract,
        'redlines': redlines,
        'satisfied_conditions': satisfied_conditions,
        'unsatisfied_conditions': unsatisfied_conditions,
        'audit_logs': audit_logs,
        'contract_versions': contract_versions,
        'active_nav': 'contracts',
    })


@login_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        form = WorkbenchConfirmForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action='Edit',
                target=contract.name,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'Contract "{contract.name}" updated.')
            return redirect('contract_detail', pk=contract.id)
    else:
        form = WorkbenchConfirmForm(instance=contract)

    return render(request, 'contracts/contract_edit.html', {
        'form': form,
        'contract': contract,
        'active_nav': 'contracts',
    })


@login_required
@require_POST
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    contract_name = contract.name
    contract_id = contract.id

    contract.delete()

    AuditLog.objects.create(
        user=request.user,
        action='Delete',
        target=f'{contract_name} ({contract_id})',
        ip=request.META.get('REMOTE_ADDR', ''),
    )
    messages.success(request, f'Contract "{contract_name}" ({contract_id}) deleted successfully.')
    return redirect('contract_list')


@login_required
def redline_recommendations(request):
    qs = RedlineSuggestion.objects.select_related('contract', 'clause').all().order_by('-created_at')
    contract_filter = request.GET.get('contract', '')
    if contract_filter:
        qs = qs.filter(contract__id=contract_filter)
    suggestions = list(qs)
    for s in suggestions:
        _attach_source_evidence([s], s.contract)
        _attach_clause_intelligence([s])
    contracts_for_filter = Contract.objects.all().order_by('name')
    return render(
        request,
        'contracts/redline_recommendations.html',
        {
            'suggestions': suggestions,
            'contracts_for_filter': contracts_for_filter,
            'contract_filter': contract_filter,
            'active_nav': 'redline',
        },
    )


@login_required
def redline_update_status(request, pk):
    """Accept or Reject a redline suggestion with optional reviewer comment."""
    suggestion = get_object_or_404(RedlineSuggestion, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status', '')
        comment = request.POST.get('reviewer_comment', '').strip()
        if new_status in ('Accepted', 'Rejected', 'Open'):
            suggestion.status = new_status
            if comment:
                suggestion.reviewer_comment = comment
            suggestion.save()

            if new_status == 'Accepted':
                changed_lines = _apply_accepted_redline_to_contract(suggestion)
                try:
                    _regenerate_contract_pdf(suggestion.contract, highlight_lines=changed_lines)
                except Exception as exc:
                    logger.warning('Failed to regenerate contract PDF after acceptance: %s', exc)

            _clear_cached_assessment(request, suggestion.contract.id)
            AuditLog.objects.create(
                user=request.user,
                action=f'Redline {new_status}',
                target=f'{suggestion.contract.name} — {suggestion.issue[:60]}',
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'Suggestion marked as {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
    return redirect(request.POST.get('next', 'redline_recommendations'))


@login_required
def contract_view_document(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not contract.file:
        messages.error(request, 'No generated contract document found to view.')
        return redirect('contract_detail', pk=pk)

    try:
        _regenerate_contract_pdf(contract)
    except Exception as exc:
        logger.warning('Failed to regenerate contract PDF for view: %s', exc)

    contract.file.open('rb')
    filename = os.path.basename(contract.file.name) or f'contract_{contract.id}.pdf'
    response = FileResponse(contract.file, as_attachment=False, filename=filename)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def contract_download(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not contract.file:
        messages.error(request, 'No generated contract document found to download.')
        return redirect('contract_detail', pk=pk)

    if contract.ai_extracted_text and not os.path.exists(contract.file.path):
        try:
            _regenerate_contract_pdf(contract)
        except Exception as exc:
            logger.warning('Failed to regenerate contract PDF for download: %s', exc)

    contract.file.open('rb')
    filename = os.path.basename(contract.file.name) or f'contract_{contract.id}.pdf'
    response = FileResponse(contract.file, as_attachment=True, filename=filename)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def _normalize_text(text):
    """Utility to normalize text for comparison (lowercase, remove extra spaces, strip)."""
    return re.sub(r'\s+', ' ', (text or '').lower()).strip()

def _persist_llm_assessment(contract, llm_results, clause_by_id):
    """Persist only unsatisfied LLM results as redline suggestions and return tab payloads."""
    satisfied = []
    unsatisfied = []

    seen_clause_ids = set()
    for result in llm_results:
        clause_id = str(result.get('clause_id', '')).strip()
        clause_meta = clause_by_id.get(clause_id)
        if not clause_meta:
            continue
        seen_clause_ids.add(clause_id)

        satisfied_flag = bool(result.get('satisfied', False))
        issue = result.get('issue') or clause_meta['issue']
        risk = result.get('risk') if result.get('risk') in ('High', 'Medium', 'Low') else clause_meta['risk']
        recommendation = result.get('recommendation') or clause_meta['ai_recommendation'] or clause_meta['deviation_rule']
        source_quote = result.get('source_quote', '')

        row = {
            'clause_id': clause_id,
            'issue': issue,
            'risk': risk,
            'reason': result.get('reason', ''),
            'recommendation': recommendation,
            'standard_rule': clause_meta['standard_rule'],
            'restricted_terms': clause_meta['restricted_terms'],
            'deviation_rule': clause_meta['deviation_rule'],
            'ai_recommendation': recommendation,
            'source_quote': source_quote,
            'status': 'Satisfied' if satisfied_flag else 'Open',
        }

        if satisfied_flag:
            satisfied.append(row)
            continue

        created = RedlineSuggestion.objects.create(
            contract=contract,
            clause=clause_meta['clause_obj'],
            issue=str(issue)[:255],
            recommendation=recommendation or 'Clause is not satisfied in contract text.',
            risk=risk,
            status='Open',
            standard_rule=clause_meta['standard_rule'],
            restricted_terms=clause_meta['restricted_terms'],
            deviation_rule=clause_meta['deviation_rule'],
            ai_recommendation=recommendation or clause_meta['ai_recommendation'],
        )
        row['redline_id'] = created.pk
        unsatisfied.append(row)

    # Any clause omitted by model is treated as unsatisfied to avoid silent misses.
    for clause_id, clause_meta in clause_by_id.items():
        if clause_id in seen_clause_ids:
            continue
        created = RedlineSuggestion.objects.create(
            contract=contract,
            clause=clause_meta['clause_obj'],
            issue=str(clause_meta['issue'])[:255],
            recommendation='LLM response did not include this clause. Please review manually.',
            risk=clause_meta['risk'],
            status='Open',
            standard_rule=clause_meta['standard_rule'],
            restricted_terms=clause_meta['restricted_terms'],
            deviation_rule=clause_meta['deviation_rule'],
            ai_recommendation=clause_meta['ai_recommendation'],
        )
        unsatisfied.append(
            {
                'clause_id': clause_id,
                'issue': clause_meta['issue'],
                'risk': clause_meta['risk'],
                'reason': 'Clause missing in LLM response output.',
                'recommendation': 'LLM response did not include this clause. Please review manually.',
                'standard_rule': clause_meta['standard_rule'],
                'restricted_terms': clause_meta['restricted_terms'],
                'deviation_rule': clause_meta['deviation_rule'],
                'ai_recommendation': clause_meta['ai_recommendation'],
                'source_quote': '',
                'status': 'Open',
                'redline_id': created.pk,
            }
        )

    return satisfied, unsatisfied




@login_required
def redline_run_ai(request, pk):
    """Trigger real-time LLM redline analysis and persist unsatisfied conditions only."""
    contract = get_object_or_404(Contract, pk=pk)
    if request.method != 'POST':
        return redirect('contract_detail', pk=pk)

    # Clear existing redlines before re-running
    RedlineSuggestion.objects.filter(contract=contract).delete()

    satisfied = []
    unsatisfied = []
    try:
        contract_text = (contract.ai_extracted_text or '').strip()
        if not contract_text and contract.file:
            try:
                file_bytes = contract.file.read()
                contract_text = (_extract_text_from_file(file_bytes) or '').strip()
                if contract_text:
                    contract.ai_extracted_text = contract_text
                    contract.ai_analyzed_at = timezone.now()
                    contract.save(update_fields=['ai_extracted_text', 'ai_analyzed_at'])
            except Exception as ocr_exc:
                logger.warning('Contract OCR refresh failed for %s: %s', contract.id, ocr_exc)

        if not contract_text:
            raise RuntimeError('No contract text available for analysis. Upload or re-process the contract document first.')

        clause_catalog, clause_by_id = _build_clause_catalog()
        if not clause_catalog:
            raise RuntimeError('No clause repository entries found to assess.')

        llm_results = _run_llm_clause_assessment(contract_text, clause_catalog)
        satisfied, unsatisfied = _persist_llm_assessment(contract, llm_results, clause_by_id)
        _cache_assessment_in_session(request, contract.id, satisfied, unsatisfied)
        created_count = len(unsatisfied)
    except Exception as exc:
        logger.warning('Redline analysis failed: %s', exc)
        RedlineSuggestion.objects.create(
            contract=contract,
            issue='Redline analysis failed',
            recommendation=f'Error: {str(exc)[:200]}',
            risk='Medium',
            status='Open',
        )
        _cache_assessment_in_session(request, contract.id, [], [])
        created_count = 1

    # Update redlines count on contract
    contract.redlines = RedlineSuggestion.objects.filter(contract=contract).count()
    contract.save(update_fields=['redlines'])

    AuditLog.objects.create(
        user=request.user,
        action='Redline Analysis',
        target=contract.name,
        ip=request.META.get('REMOTE_ADDR', ''),
    )
    if created_count == 0:
        messages.success(request, 'Redline analysis complete — all conditions are satisfied.')
    else:
        messages.success(request, f'Redline analysis complete — {created_count} unsatisfied condition(s) found in real-time analysis.')
    return redirect('contract_detail', pk=pk)

@login_required
def contract_comparisons(request):
    comparisons = ContractComparison.objects.select_related('contract_left', 'contract_right', 'exported_by').all().order_by('-exported_at')
    return render(
        request,
        'contracts/contract_comparisons.html',
        {'comparisons': comparisons, 'active_nav': 'comparison'},
    )


@login_required
def comparison_create(request):
    """Create a new AI-powered comparison between two contracts."""
    contracts_qs = Contract.objects.all().order_by('name')
    error = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        left_id = request.POST.get('contract_left', '')
        right_id = request.POST.get('contract_right', '')
        external_file = request.FILES.get('external_file')

        if not title:
            error = 'Please provide a title for this comparison.'
        elif not left_id:
            error = 'Please select Contract A.'
        elif not right_id and not external_file:
            error = 'Please select Contract B or upload an external document.'
        else:
            contract_left = get_object_or_404(Contract, pk=left_id)
            contract_right = None
            right_text = ''
            ext_doc_name = ''

            if right_id:
                contract_right = get_object_or_404(Contract, pk=right_id)

            # Extract texts
            def _get_text(contract_obj):
                try:
                    if contract_obj and contract_obj.file:
                        from contractos.services.ocr_service import DocumentIntelligenceService
                        svc = DocumentIntelligenceService()
                        if svc.is_configured():
                            return svc.extract_text(contract_obj.file.read())
                except Exception as exc:
                    logger.warning('OCR in comparison failed: %s', exc)
                return f'Contract: {contract_obj.name if contract_obj else ""}'

            left_text = _get_text(contract_left)

            if external_file:
                ext_file_bytes = external_file.read()
                ext_doc_name = external_file.name
                try:
                    from contractos.services.ocr_service import DocumentIntelligenceService
                    svc = DocumentIntelligenceService()
                    if svc.is_configured():
                        right_text = svc.extract_text(ext_file_bytes)
                    else:
                        right_text = f'External document: {ext_doc_name}'
                except Exception as exc:
                    logger.warning('OCR for external doc failed: %s', exc)
                    right_text = f'External document: {ext_doc_name}'
                # Save external file
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                import os
                saved = default_storage.save(os.path.join('comparisons', external_file.name), ContentFile(ext_file_bytes))
                ext_doc_name = saved
            else:
                right_text = _get_text(contract_right)

            # AI comparison
            system_prompt = (
                'You are an expert contract analyst. Compare two contracts clause by clause. '
                'Return ONLY valid JSON — no markdown, no explanation.'
            )
            left_name = contract_left.name
            right_name = contract_right.name if contract_right else ext_doc_name or 'External Document'
            prompt = f"""Compare these two contracts and identify key differences.
Return a JSON object with:
- "summary": 3-4 sentence plain-English overview of the main differences
- "clauses": array of objects, each with: "topic" (string), "left" (brief description from Contract A), "right" (brief description from Contract B), "deviation" ("High"/"Medium"/"Low"/"None"), "notes" (short observation)
Limit to 10 most important clause comparisons.

Contract A ({left_name}):
{left_text[:3000]}

Contract B ({right_name}):
{right_text[:3000]}"""

            summary_text = ''
            detail_json = '[]'
            try:
                from contractos.services.llm_service import AzureOpenAIService
                svc = AzureOpenAIService()
                if svc.is_configured():
                    raw = svc.complete(prompt, system_prompt=system_prompt)
                    raw = raw.strip()
                    if raw.startswith('```'):
                        raw = raw.split('```')[1]
                        if raw.startswith('json'):
                            raw = raw[4:]
                    parsed = json.loads(raw.strip())
                    summary_text = parsed.get('summary', '')
                    detail_json = json.dumps(parsed.get('clauses', []))
                else:
                    summary_text = 'Azure OpenAI not configured — comparison summary unavailable.'
            except Exception as exc:
                logger.warning('LLM comparison failed: %s', exc)
                summary_text = f'AI comparison failed: {exc}'

            comparison = ContractComparison.objects.create(
                title=title,
                contract_left=contract_left,
                contract_right=contract_right,
                external_document=ext_doc_name,
                summary=summary_text,
                comparison_detail=detail_json,
                exported_by=request.user,
            )
            AuditLog.objects.create(
                user=request.user,
                action='Comparison Created',
                target=title,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'Comparison "{title}" created.')
            return redirect('comparison_detail', pk=comparison.pk)

    return render(request, 'contracts/comparison_create.html', {
        'contracts': contracts_qs,
        'error': error,
        'active_nav': 'comparison',
    })


@login_required
def comparison_detail(request, pk):
    comparison = get_object_or_404(ContractComparison, pk=pk)
    clauses = []
    try:
        clauses = json.loads(comparison.comparison_detail or '[]')
    except (json.JSONDecodeError, TypeError):
        pass
    return render(request, 'contracts/comparison_detail.html', {
        'comparison': comparison,
        'clauses': clauses,
        'active_nav': 'comparison',
    })


@login_required
def comparison_export(request, pk):
    """Export comparison as downloadable text."""
    import csv
    from django.http import HttpResponse
    comparison = get_object_or_404(ContractComparison, pk=pk)
    clauses = []
    try:
        clauses = json.loads(comparison.comparison_detail or '[]')
    except (json.JSONDecodeError, TypeError):
        pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="comparison_{comparison.pk}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Comparison Report', comparison.title])
    writer.writerow(['Summary', comparison.summary])
    writer.writerow([])
    writer.writerow(['Topic', 'Contract A', 'Contract B', 'Deviation', 'Notes'])
    for clause in clauses:
        writer.writerow([
            clause.get('topic', ''),
            clause.get('left', ''),
            clause.get('right', ''),
            clause.get('deviation', ''),
            clause.get('notes', ''),
        ])
    return response
