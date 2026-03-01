from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
import re
from contracts import permissions

register = template.Library()

# Field name mapping for user-friendly display
FIELD_LABEL_MAP = {
    'businessform': 'Business Form',
    'cvcodenumber': 'CV Code Number',
    'partybladdress': 'Party B Address',
    'partyblrepresentativename': 'Representative Name',
    'partyblrepresentativetitle': 'Representative Title',
    'deliveryaddress': 'Delivery Address',
    'shippingaddress': 'Shipping Address',
    'paymentterms': 'Payment Terms',
    'contractvalue': 'Contract Value',
    'startdate': 'Start Date',
    'enddate': 'End Date',
    'renewalperiod': 'Renewal Period',
}


@register.filter(name='abs')
def abs_filter(value):
    """Return the absolute value of the argument"""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value


@register.filter(name='replace')
def replace_filter(value, args):
    """Replace occurrences of old with new. Usage: {{ value|replace:"old,new" }}"""
    try:
        old, new = args.split(',')
        return str(value).replace(old, new)
    except (ValueError, AttributeError):
        return value


@register.filter(name='friendly_field_name')
def friendly_field_name(value):
    """Convert technical field names to user-friendly labels"""
    if not value:
        return value
    
    # Check if we have a predefined mapping
    value_lower = str(value).lower()
    if value_lower in FIELD_LABEL_MAP:
        return FIELD_LABEL_MAP[value_lower]
    
    # Smart conversion: add spaces before capital letters and clean up
    import re
    # Replace underscores with spaces
    result = str(value).replace('_', ' ')
    # Insert space before capital letters (camelCase detection)
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    # Capitalize each word
    result = ' '.join(word.capitalize() for word in result.split())
    
    return result


@register.filter(name='format_number')
def format_number(value, field_name=''):
    """Format numeric values with thousand separators, leave non-numeric as-is.
    
    Does NOT format code/ID fields like cvcode_number, code_number, etc.
    """
    if value is None:
        return value

    text = str(value).strip()
    if not text:
        return value

    # Skip formatting for code/ID fields
    if any(skip in field_name.lower() for skip in ['code', 'id', 'number', 'period', 'date', 'address']):
        return value

    # Remove existing commas for detection
    normalized = text.replace(',', '')
    if not re.fullmatch(r'-?\d+(\.\d+)?', normalized):
        return value

    if '.' in normalized:
        integer_part, decimal_part = normalized.split('.', 1)
        return f"{intcomma(int(integer_part))}.{decimal_part}"

    return intcomma(int(normalized))


@register.simple_tag(name='has_contract_permission')
def has_contract_permission(user, contract, permission):
    return permissions.has_contract_permission(user, contract, permission)
