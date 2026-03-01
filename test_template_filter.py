import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_clm.settings')
import django
django.setup()

from django.template import Template, Context

template_str = """{% load contract_filters %}
Test 1: {{ '22500000000'|format_number }}
Test 2: {{ '90000000000'|format_number }}
Test 3: {{ '102930'|format_number }}
Test 4: {{ 'Jakarta'|format_number }}
"""

t = Template(template_str)
c = Context({})
result = t.render(c)
print("TEMPLATE RENDER TEST RESULTS:")
print("=" * 50)
print(result)
print("=" * 50)
