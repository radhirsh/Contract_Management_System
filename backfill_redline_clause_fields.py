from contracts.models import RedlineSuggestion
from clauses.models import Clause

def backfill_redline_clause_fields():
    count = 0
    for suggestion in RedlineSuggestion.objects.all():
        # Try to match a clause by issue name
        clause_match = Clause.objects.filter(name__icontains=suggestion.issue).first()
        if not clause_match:
            clause_match = Clause.objects.filter(clause_name__icontains=suggestion.issue).first()
        if clause_match:
            suggestion.clause = clause_match
            suggestion.standard_rule = clause_match.standard_rule or clause_match.standard_rule_value or ''
            suggestion.restricted_terms = clause_match.restricted_terms or clause_match.restricted_terms_conditions or ''
            suggestion.deviation_rule = clause_match.deviation_rule or ''
            suggestion.ai_recommendation = clause_match.ai_recommendation or ''
            suggestion.save()
            count += 1
    print(f"Backfilled {count} redline suggestions with clause fields.")

if __name__ == "__main__":
    backfill_redline_clause_fields()
