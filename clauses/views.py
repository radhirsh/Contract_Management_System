import json
import re
from rest_framework import viewsets, permissions
from .models import Clause
from .serializers import ClauseSerializer
from .forms import ClauseForm, UploadClauseFileForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from audit.models import AuditLog
from contractos.services.llm_service import AzureOpenAIService
from contractos.services.ocr_service import DocumentIntelligenceService


class ClauseViewSet(viewsets.ModelViewSet):
    queryset = Clause.objects.all()
    serializer_class = ClauseSerializer
    permission_classes = [permissions.IsAuthenticated]


def _next_clause_id() -> str:
    max_seq = 0
    for clause_id in Clause.objects.values_list('id', flat=True):
        if not clause_id:
            continue
        match = re.search(r'(\d+)$', str(clause_id))
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return f'CL-{max_seq + 1:04d}'


def _extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    di_service = DocumentIntelligenceService()
    if di_service.is_configured():
        try:
            return di_service.extract_text(file_bytes)
        except Exception:
            pass

    lower_name = filename.lower()
    if lower_name.endswith('.txt'):
        return file_bytes.decode('utf-8', errors='ignore')

    if lower_name.endswith('.docx'):
        try:
            from docx import Document
            from io import BytesIO

            doc = Document(BytesIO(file_bytes))
            lines = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            return '\n'.join(lines)
        except Exception:
            return ''

    return ''


def _infer_with_llm(text: str) -> dict:
    llm = AzureOpenAIService()
    if not llm.is_configured() or not text.strip():
        return {}

    schema = {
        'name': 'string',
        'category': 'Legal|Finance|Liability|Operational',
        'risk_level': 'High|Medium|Low',
        'mandatory': 'Yes|No',
        'standard_rule': 'string',
        'restricted_terms': 'string',
        'deviation_rule': 'string',
        'ai_recommendation': 'string',
        'escalation_required': 'Yes|No',
        'clause_category': 'string',
    }

    prompt = (
        'Extract clause metadata from this clause text. Return JSON only with keys exactly as follows: '
        f'{list(schema.keys())}. '\
        'If unknown, provide conservative defaults.\n\n'
        f'Clause text:\n{text[:6000]}'
    )

    try:
        raw = llm.complete(prompt=prompt, system_prompt='You extract legal clause metadata in strict JSON.')
        cleaned = raw.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _infer_clause_fields(filename: str, text: str) -> dict:
    lower_text = text.lower()

    keyword_category = {
        'Liability': ['liability', 'indemnity', 'damages', 'warranty'],
        'Finance': ['payment', 'invoice', 'fee', 'price', 'tax'],
        'Operational': ['service level', 'sla', 'support', 'uptime', 'delivery'],
        'Legal': ['confidential', 'governing law', 'compliance', 'privacy', 'termination'],
    }

    inferred_category = 'Legal'
    for category_name, words in keyword_category.items():
        if any(word in lower_text for word in words):
            inferred_category = category_name
            break

    inferred_risk = 'Medium'
    if any(k in lower_text for k in ['unlimited liability', 'penalty', 'breach', 'indemnify']):
        inferred_risk = 'High'
    elif any(k in lower_text for k in ['best effort', 'reasonable', 'subject to']):
        inferred_risk = 'Low'

    inferred_mandatory = any(k in lower_text for k in ['must', 'shall', 'required'])

    first_line = next((line.strip() for line in text.splitlines() if line.strip()), '')
    default_name = first_line[:120] if first_line else filename.rsplit('.', 1)[0].replace('_', ' ').strip()
    if not default_name:
        default_name = 'Uploaded Clause'

    llm_data = _infer_with_llm(text)

    category = llm_data.get('category', inferred_category)
    if category not in ['Legal', 'Finance', 'Liability', 'Operational']:
        category = inferred_category

    risk_level = llm_data.get('risk_level', inferred_risk)
    if risk_level not in ['High', 'Medium', 'Low']:
        risk_level = inferred_risk

    mandatory_text = str(llm_data.get('mandatory', 'Yes' if inferred_mandatory else 'No')).lower()
    escalation_text = str(llm_data.get('escalation_required', 'Yes' if risk_level == 'High' else 'No')).lower()

    standard_rule = (llm_data.get('standard_rule') or text[:600] or 'No standard rule provided').strip()
    restricted_terms = (llm_data.get('restricted_terms') or 'No restricted terms provided').strip()
    deviation_rule = (llm_data.get('deviation_rule') or 'No deviation rule provided').strip()
    ai_recommendation = (llm_data.get('ai_recommendation') or 'No AI recommendation provided').strip()

    clause_category = llm_data.get('clause_category') or 'Confidentiality'
    valid_clause_categories = {choice for choice, _ in Clause._meta.get_field('clause_category').choices}
    if clause_category not in valid_clause_categories:
        clause_category = 'Confidentiality'

    clause_name = (llm_data.get('name') or default_name).strip()

    return {
        'name': clause_name,
        'clause_name': clause_name,
        'category': category,
        'clause_category': clause_category,
        'risk': risk_level,
        'risk_level': risk_level,
        'mandatory': mandatory_text == 'yes',
        'standard_rule': standard_rule,
        'standard_rule_value': standard_rule,
        'restricted_terms': restricted_terms,
        'restricted_terms_conditions': restricted_terms,
        'deviation_rule': deviation_rule,
        'ai_recommendation': ai_recommendation,
        'escalation_required': escalation_text == 'yes',
    }


@login_required
def clause_list(request):
    clauses = Clause.objects.all().order_by('id')
    return render(request, 'clauses/clause_list.html', {'clauses': clauses, 'active_nav': 'clauses'})


@login_required
def clause_add(request):
    error = None
    if request.method == 'POST':
        form = ClauseForm(request.POST, request.FILES)
        if form.is_valid():
            clause = form.save()
            AuditLog.objects.create(
                user=request.user,
                action='Clause Added',
                target=clause.name,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'Clause "{clause.name}" added successfully.')
            return redirect('clause_list_web')
        else:
            error = 'Please fix the errors below.'
    else:
        form = ClauseForm()
    return render(request, 'clauses/clause_form.html', {
        'form': form,
        'error': error,
        'is_edit': False,
        'active_nav': 'clauses',
    })


@login_required
def clause_edit(request, pk):
    clause = get_object_or_404(Clause, pk=pk)
    error = None
    if request.method == 'POST':
        form = ClauseForm(request.POST, request.FILES, instance=clause, is_edit=True)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action='Clause Updated',
                target=clause.name,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'Clause "{clause.name}" updated.')
            return redirect('clause_list_web')
        else:
            error = 'Please fix the errors below.'
    else:
        form = ClauseForm(instance=clause, is_edit=True)
    return render(request, 'clauses/clause_form.html', {
        'form': form,
        'clause': clause,
        'error': error,
        'is_edit': True,
        'active_nav': 'clauses',
    })


@login_required
def clause_detail(request, pk):
    clause = get_object_or_404(Clause, pk=pk)
    return render(request, 'clauses/clause_detail.html', {
        'clause': clause,
        'active_nav': 'clauses',
    })


@login_required
def clause_action(request, pk):
    """Approve or Reject a clause via POST."""
    clause = get_object_or_404(Clause, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'approve':
            clause.status = 'Approved'
            clause.save(update_fields=['status'])
            AuditLog.objects.create(
                user=request.user,
                action='Clause Approved',
                target=clause.name,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, f'Clause "{clause.name}" approved.')
        elif action == 'reject':
            clause.status = 'Pending'
            clause.save(update_fields=['status'])
            AuditLog.objects.create(
                user=request.user,
                action='Clause Rejected',
                target=clause.name,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.warning(request, f'Clause "{clause.name}" set back to Pending.')
    return redirect('clause_list_web')


@login_required
def clause_upload(request):
    error = None

    if request.method == 'POST':
        form = UploadClauseFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']

            try:
                file_bytes = uploaded_file.read()
                uploaded_file.seek(0)
                extracted_text = _extract_text_from_upload(uploaded_file.name, file_bytes)
                inferred_data = _infer_clause_fields(uploaded_file.name, extracted_text)

                clause = Clause.objects.create(
                    id=_next_clause_id(),
                    version='v1.0',
                    status='Pending',
                    document=uploaded_file,
                    **inferred_data,
                )

                AuditLog.objects.create(
                    user=request.user,
                    action='Clause Uploaded',
                    target=clause.name,
                    ip=request.META.get('REMOTE_ADDR', ''),
                )

                messages.success(request, f'Clause "{clause.name}" uploaded and extracted successfully.')
                return redirect('clause_list_web')
            except Exception as exc:
                error = f'Could not process this file: {exc}'
        else:
            error = 'Please select a valid file and try again.'
    else:
        form = UploadClauseFileForm()

    return render(request, 'clauses/clause_upload.html', {
        'form': form,
        'error': error,
        'active_nav': 'clauses',
    })

