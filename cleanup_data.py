#!/usr/bin/env python
"""
Script to clean out all test data from the system for fresh trial use
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
django.setup()

from contracts.models import Contract, ContractParticipant, ContractData, AuditLog, BusinessEntityDocument

def cleanup_data():
    print("\n" + "="*60)
    print("CLEANING DATABASE - REMOVING ALL TEST DATA")
    print("="*60 + "\n")
    
    # Count before deletion
    contracts_count = Contract.objects.count()
    participants_count = ContractParticipant.objects.count()
    contract_data_count = ContractData.objects.count()
    docs_count = BusinessEntityDocument.objects.count()
    audit_count = AuditLog.objects.count()
    
    print(f"Data before cleanup:")
    print(f"  • Contracts: {contracts_count}")
    print(f"  • Participants: {participants_count}")
    print(f"  • Contract Data: {contract_data_count}")
    print(f"  • Documents: {docs_count}")
    print(f"  • Audit Logs: {audit_count}")
    
    # Delete all contracts (cascade will handle participants, data, etc)
    print(f"\n🗑️  Deleting all contracts...")
    Contract.objects.all().delete()
    
    # Delete business entity documents
    print(f"🗑️  Deleting business entity documents...")
    BusinessEntityDocument.objects.all().delete()
    
    # Delete audit logs
    print(f"🗑️  Deleting audit logs...")
    AuditLog.objects.all().delete()
    
    # Verify deletion
    print(f"\n✓ Data after cleanup:")
    print(f"  • Contracts: {Contract.objects.count()}")
    print(f"  • Participants: {ContractParticipant.objects.count()}")
    print(f"  • Contract Data: {ContractData.objects.count()}")
    print(f"  • Documents: {BusinessEntityDocument.objects.count()}")
    print(f"  • Audit Logs: {AuditLog.objects.count()}")
    
    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETE - System is ready for fresh trial use!")
    print("="*60)
    print("\nWhat's preserved:")
    print("  ✓ All user accounts and permissions")
    print("  ✓ Admin configurations")
    print("  ✓ Database schema")
    print("\nWhat was deleted:")
    print(f"  ✗ {contracts_count} contracts")
    print(f"  ✗ {participants_count} participants")
    print(f"  ✗ {contract_data_count} contract data records")
    print(f"  ✗ {docs_count} documents")
    print(f"  ✗ {audit_count} audit logs")
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    cleanup_data()
