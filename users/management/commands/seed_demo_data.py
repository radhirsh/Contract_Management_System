from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from clauses.models import Clause
from contracts.models import Contract, RedlineSuggestion, ContractComparison
from sharepoint.models import SharePointConfig, SharePointSyncLog


USERS = [
    {"name": "Priya Sharma", "email": "priya.sharma@org.com", "role": "Contract Manager", "status": "Active"},
    {"name": "Ravi Kumar", "email": "ravi.kumar@org.com", "role": "Legal Reviewer", "status": "Active"},
    {"name": "Anjali Rao", "email": "anjali.rao@org.com", "role": "Admin", "status": "Active"},
    {"name": "Kiran Mehta", "email": "kiran.mehta@org.com", "role": "Viewer", "status": "Inactive"},
]

CONTRACTS = [
    {"id": "C-001", "name": "Master Services Agreement - Accenture", "vendor": "Accenture", "expiry": "2025-06-15", "redlines": 3, "version": "v2.1", "risk": "High", "status": "Active", "uploaded": "2024-01-10", "clauses": 28},
    {"id": "C-002", "name": "Software License Agreement - Oracle", "vendor": "Oracle Corp", "expiry": "2025-07-20", "redlines": 1, "version": "v1.0", "risk": "Medium", "status": "Active", "uploaded": "2024-02-14", "clauses": 15},
    {"id": "C-003", "name": "Consulting Agreement - Deloitte", "vendor": "Deloitte", "expiry": "2024-12-31", "redlines": 0, "version": "v3.0", "risk": "Low", "status": "Expired", "uploaded": "2022-12-01", "clauses": 20},
    {"id": "C-004", "name": "NDA - TechPartners Inc", "vendor": "TechPartners", "expiry": "2025-08-30", "redlines": 2, "version": "v1.2", "risk": "Medium", "status": "Active", "uploaded": "2024-03-05", "clauses": 8},
    {"id": "C-005", "name": "Cloud Services Agreement - AWS", "vendor": "Amazon Web Services", "expiry": "2025-05-28", "redlines": 5, "version": "v1.0", "risk": "High", "status": "Active", "uploaded": "2024-04-18", "clauses": 40},
    {"id": "C-006", "name": "Support Contract - Microsoft", "vendor": "Microsoft", "expiry": "2025-06-10", "redlines": 0, "version": "v2.0", "risk": "Low", "status": "Active", "uploaded": "2023-06-01", "clauses": 12},
    {"id": "C-007", "name": "Vendor Agreement - Infosys", "vendor": "Infosys Ltd", "expiry": "2024-11-15", "redlines": 4, "version": "v1.5", "risk": "High", "status": "Expired", "uploaded": "2023-11-01", "clauses": 32},
    {"id": "C-008", "name": "SaaS Agreement - Salesforce", "vendor": "Salesforce", "expiry": "2025-09-01", "redlines": 1, "version": "v1.0", "risk": "Low", "status": "Active", "uploaded": "2024-05-12", "clauses": 18},
]

CLAUSES = [
    {"id": "CL-001", "name": "Liability Clause", "category": "Liability", "risk": "High", "version": "v2.0", "status": "Approved"},
    {"id": "CL-002", "name": "Payment Terms", "category": "Finance", "risk": "Medium", "version": "v1.3", "status": "Approved"},
    {"id": "CL-003", "name": "Indemnification", "category": "Legal", "risk": "High", "version": "v1.0", "status": "Pending"},
    {"id": "CL-004", "name": "Termination Clause", "category": "Operational", "risk": "Medium", "version": "v1.1", "status": "Approved"},
    {"id": "CL-005", "name": "Confidentiality", "category": "Legal", "risk": "Low", "version": "v3.0", "status": "Approved"},
]

AUDIT_LOGS = [
    {"user": "priya.sharma@org.com", "action": "Uploaded Contract", "target": "SaaS Agreement - Salesforce", "time": "2025-05-15 09:12", "ip": "192.168.1.101"},
    {"user": "ravi.kumar@org.com", "action": "Accepted Redline", "target": "MSA - Accenture Cl. 7.2", "time": "2025-05-15 08:47", "ip": "192.168.1.102"},
    {"user": None, "action": "Sent Expiry Alert", "target": "AWS Cloud Services", "time": "2025-05-15 08:00", "ip": "Internal"},
    {"user": "anjali.rao@org.com", "action": "Exported Report", "target": "Oracle vs NDA Comparison", "time": "2025-05-14 17:35", "ip": "192.168.1.103"},
    {"user": None, "action": "SharePoint Sync", "target": "All Contracts", "time": "2025-05-14 12:10", "ip": "Internal"},
]

ACTIVITIES = [
    {"user": "priya.sharma@org.com", "action": "Contract uploaded", "target": "SaaS Agreement - Salesforce", "time": "2025-05-16 09:58", "ip": "192.168.1.101"},
    {"user": "ravi.kumar@org.com", "action": "Redline accepted", "target": "Master Services Agreement - Accenture", "time": "2025-05-16 09:35", "ip": "192.168.1.102"},
    {"user": None, "action": "Expiry alert sent", "target": "Cloud Services Agreement - AWS", "time": "2025-05-16 08:40", "ip": "Internal"},
    {"user": "anjali.rao@org.com", "action": "Comparison exported", "target": "Software License - Oracle vs NDA", "time": "2025-05-16 07:15", "ip": "192.168.1.103"},
    {"user": None, "action": "SharePoint sync", "target": "All Contracts", "time": "2025-05-16 06:20", "ip": "Internal"},
]

REDLINE_SUGGESTIONS = [
    {
        "contract_id": "C-001",
        "clause_id": "CL-001",
        "issue": "Liability cap missing",
        "recommendation": "Insert liability cap at 12-month fees and carve out fraud/willful misconduct.",
        "risk": "High",
        "status": "Open",
    },
    {
        "contract_id": "C-005",
        "clause_id": "CL-003",
        "issue": "Indemnification scope too broad",
        "recommendation": "Limit indemnity to third-party IP claims and add mutual indemnity language.",
        "risk": "High",
        "status": "Accepted",
    },
    {
        "contract_id": "C-002",
        "clause_id": "CL-002",
        "issue": "Payment terms conflict",
        "recommendation": "Align invoice cycle to Net-45 and include late payment dispute workflow.",
        "risk": "Medium",
        "status": "Open",
    },
]

COMPARISONS = [
    {
        "title": "Oracle License vs NDA Baseline",
        "left": "C-002",
        "right": "C-004",
        "external_document": "Oracle_License_External_v1.docx",
        "summary": "Detected 8 material differences in indemnity, liability, and SLA penalties.",
    },
    {
        "title": "AWS Cloud Terms vs MSA",
        "left": "C-005",
        "right": "C-001",
        "external_document": "AWS_External_Schedule.pdf",
        "summary": "Found 5 high-risk deltas around termination rights and data residency obligations.",
    },
]

SYNC_LOGS = [
    {"status": "Success", "message": "Auto sync completed for 8 contracts."},
    {"status": "Warning", "message": "Metadata mismatch detected for C-004. Retry queued."},
    {"status": "Success", "message": "Permission map updated for legal reviewers."},
    {"status": "Failed", "message": "Upload failed for attachment in C-007 due to transient network error."},
]


class Command(BaseCommand):
    help = "Seed demo data converted from JSX mock arrays."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing app demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        demo_password = "Demo@12345"

        if options["reset"]:
            AuditLog.objects.all().delete()
            ContractComparison.objects.all().delete()
            RedlineSuggestion.objects.all().delete()
            SharePointSyncLog.objects.all().delete()
            SharePointConfig.objects.all().delete()
            Contract.objects.all().delete()
            Clause.objects.all().delete()
            User.objects.filter(email__iendswith='@org.com').delete()
            self.stdout.write(self.style.WARNING("Existing demo data removed."))

        user_map = {}
        for item in USERS:
            user, created = User.objects.get_or_create(
                email=item["email"],
                defaults={
                    "username": item["email"],
                    "name": item["name"],
                    "role": item["role"],
                    "status": item["status"],
                },
            )
            user.name = item["name"]
            user.username = item["email"]
            user.role = item["role"]
            user.status = item["status"]
            user.set_password(demo_password)
            user.save()
            user_map[item["email"]] = user
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user {item['email']}"))

        for item in CONTRACTS:
            created_by = user_map.get("anjali.rao@org.com")
            contract, _ = Contract.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "vendor": item["vendor"],
                    "expiry": date.fromisoformat(item["expiry"]),
                    "redlines": item["redlines"],
                    "version": item["version"],
                    "risk": item["risk"],
                    "status": item["status"],
                    "clauses": item["clauses"],
                    "created_by": created_by,
                },
            )
            Contract.objects.filter(id=contract.id).update(uploaded=date.fromisoformat(item["uploaded"]))

        for item in CLAUSES:
            Clause.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "category": item["category"],
                    "risk": item["risk"],
                    "version": item["version"],
                    "status": item["status"],
                },
            )

        sharepoint_config, _ = SharePointConfig.objects.update_or_create(
            url="https://contoso.sharepoint.com/sites/contracts",
            defaults={
                "folder": "Shared Documents/ContractOS",
                "auto_sync": True,
                "meta_sync": True,
                "last_sync": timezone.now(),
            },
        )

        for row in SYNC_LOGS:
            SharePointSyncLog.objects.get_or_create(
                config=sharepoint_config,
                status=row["status"],
                message=row["message"],
            )

        for row in REDLINE_SUGGESTIONS:
            contract = Contract.objects.filter(id=row["contract_id"]).first()
            clause = Clause.objects.filter(id=row["clause_id"]).first()
            if not contract:
                continue
            RedlineSuggestion.objects.update_or_create(
                contract=contract,
                issue=row["issue"],
                defaults={
                    "clause": clause,
                    "recommendation": row["recommendation"],
                    "risk": row["risk"],
                    "status": row["status"],
                },
            )

        for row in COMPARISONS:
            ContractComparison.objects.update_or_create(
                title=row["title"],
                defaults={
                    "contract_left": Contract.objects.filter(id=row["left"]).first(),
                    "contract_right": Contract.objects.filter(id=row["right"]).first(),
                    "external_document": row["external_document"],
                    "summary": row["summary"],
                    "exported_by": user_map.get("anjali.rao@org.com"),
                },
            )

        self._seed_logs(AUDIT_LOGS, user_map)
        self._seed_logs(ACTIVITIES, user_map)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write(self.style.SUCCESS("Demo user password for seeded accounts: Demo@12345"))

    def _seed_logs(self, rows, user_map):
        for row in rows:
            user = user_map.get(row["user"]) if row.get("user") else None
            dt = timezone.make_aware(datetime.strptime(row["time"], "%Y-%m-%d %H:%M"))
            log, _ = AuditLog.objects.get_or_create(
                action=row["action"],
                target=row["target"],
                ip=row["ip"],
                defaults={"user": user},
            )
            if log.user_id != (user.id if user else None):
                log.user = user
                log.save(update_fields=["user"])
            AuditLog.objects.filter(pk=log.pk).update(time=dt)
