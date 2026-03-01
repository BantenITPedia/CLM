import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
import django
django.setup()

from contracts.templatetags.contract_filters import format_number

print("TESTING FORMAT_NUMBER FILTER WITH FIELD NAMES:")
print("=" * 60)

test_cases = [
    ('22500000000', 'sales_target_q1', '22,500,000,000'),  # Should format
    ('90000000000', 'total_purchase_target', '90,000,000,000'),  # Should format
    ('102930', 'cvcode_number', '102930'),  # Should NOT format (has 'code')
    ('1234567', 'contract_id', '1234567'),  # Should NOT format (has 'id')
    ('120000', 'annual_salary', '120,000'),  # Should format (monetary)
    ('Jakarta', 'delivery_address', 'Jakarta'),  # Should NOT format (has 'address')
    ('2026-03-01', 'start_date', '2026-03-01'),  # Should NOT format (has 'date')
]

for value, field_name, expected in test_cases:
    result = format_number(value, field_name)
    status = '✓' if result == expected else '✗'
    print(f"{status} {field_name:25} {value:15} -> {result:20} (expected: {expected})")

print("=" * 60)
