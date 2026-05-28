"""
Seed redline suggestions for all contracts using the clause repository.
Run: python seed_redlines_from_clauses.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractos.settings')
django.setup()

from contracts.models import Contract, RedlineSuggestion
from clauses.models import Clause

def seed_redlines():
    clauses = list(Clause.objects.all()[:8])
    if not clauses:
        print("❌ No clauses found in repository. Add clauses first.")
        return

    print(f"Found {len(clauses)} clauses to use as redline sources.\n")

    for contract in Contract.objects.all():
        existing = RedlineSuggestion.objects.filter(contract=contract).count()
        if existing > 0:
            print(f"⏭  Skipping {contract.name} ({contract.id}) — already has {existing} redlines")
            continue

        count = 0
        for clause in clauses:
            issue = clause.clause_name or clause.name or clause.clause_category
            issue = issue[:255]
            recommendation = (
                clause.ai_recommendation or clause.deviation_rule or
                f"Review {clause.clause_category} clause against standard terms."
            )
            risk = clause.risk_level if clause.risk_level in ('High', 'Medium', 'Low') else (
                clause.risk if clause.risk in ('High', 'Medium', 'Low') else 'Medium'
            )
            RedlineSuggestion.objects.create(
                contract=contract,
                clause=clause,
                issue=issue,
                recommendation=recommendation,
                risk=risk,
                status='Open',
                standard_rule=clause.standard_rule_value or clause.standard_rule or '',
                restricted_terms=clause.restricted_terms_conditions or clause.restricted_terms or '',
                deviation_rule=clause.deviation_rule or '',
                ai_recommendation=clause.ai_recommendation or '',
            )
            count += 1

        # Update contract redlines count
        contract.redlines = RedlineSuggestion.objects.filter(contract=contract).count()
        contract.save(update_fields=['redlines'])
        print(f"✓ {contract.name} ({contract.id}) — created {count} redline suggestions")

    print("\n✅ Done seeding redline suggestions from clause repository.")

if __name__ == '__main__':
    seed_redlines()
