import os
import django
import hashlib
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractos.settings')
django.setup()

# Allow 'testserver' for Django Test Client
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from contracts.models import Contract, RedlineSuggestion

def run_test():
    User = get_user_model()
    user = User.objects.first()
    if not user:
        print('Error: No users found')
        return
    
    client = Client()
    client.force_login(user)
    
    contract = Contract.objects.first()
    if not contract:
        print('Error: No contracts found')
        return
        
    redline = RedlineSuggestion.objects.filter(contract=contract, status='Open').first()
    if not redline:
        print(f'Error: No Open redlines found for contract {contract.id}')
        return

    detail_url = reverse('contract_detail', kwargs={'pk': contract.id})
    client.get(detail_url)
    
    text_before = contract.ai_extracted_text or ''
    hash_before = hashlib.md5(text_before.encode()).hexdigest()
    file_before = contract.file.name if contract.file else 'None'
    
    print(f'Contract: {contract.id}')
    print(f'Redline ID: {redline.id}')
    print(f'Initial Status: {redline.status}')
    print(f'Initial Hash: {hash_before}')
    print(f'Initial File: {file_before}')
    
    update_url = reverse('redline_update_status', kwargs={'pk': redline.id})
    # Setting HTTP_HOST to 'localhost' or 'testserver' is usually handled by Client, 
    # but we added it to ALLOWED_HOSTS above.
    response = client.post(update_url, {'status': 'Accepted', 'next': detail_url}, follow=True)
    
    contract.refresh_from_db()
    redline.refresh_from_db()
    
    text_after = contract.ai_extracted_text or ''
    hash_after = hashlib.md5(text_after.encode()).hexdigest()
    file_exists = bool(contract.file and os.path.exists(contract.file.path)) if contract.file else False
    
    print(f'Accepted Status: {redline.status}')
    print(f'AI Text Changed: {hash_before != hash_after}')
    print(f'File Exists After: {file_exists}')
    print(f'Final Hash: {hash_after}')

if __name__ == '__main__':
    run_test()
