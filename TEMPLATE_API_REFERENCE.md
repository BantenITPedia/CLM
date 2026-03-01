# Template Generation System - Quick API Reference

**Location:** `contracts/services.py`  
**Classes:** `TemplateService`, `ContractDraftService`

---

## TemplateService

### `get_template_for_contract_type(contract_type_code)`

Load the active template for a contract type.

**Parameters:**
- `contract_type_code` (str): Type code like 'GENERAL_TRADE', 'MODERN_TRADE', 'DISTRIBUTOR'

**Returns:**
- `ContractTemplate` instance

**Raises:**
- `ValueError`: If type not found, not active, or not template-based

**Example:**
```python
from contracts.services import TemplateService

template = TemplateService.get_template_for_contract_type('GENERAL_TRADE')
```

---

### `build_template_context(contract, contract_data_dict)`

Build context dictionary for template rendering.

**Parameters:**
- `contract` (Contract): Contract instance
- `contract_data_dict` (dict): Form field values

**Returns:**
- `dict`: Complete context with system + form variables

**Example:**
```python
context = TemplateService.build_template_context(
    contract,
    {'vendor_name': 'Acme', 'annual_target': 100000}
)
```

---

### `validate_template_variables(template_content, contract_data_dict)`

Validate all template variables are available.

**Parameters:**
- `template_content` (str): Template HTML with `{{ variables }}`
- `contract_data_dict` (dict): Available data

**Returns:**
- `tuple`: (is_valid, missing_vars, available_vars)

**Example:**
```python
is_valid, missing, available = TemplateService.validate_template_variables(
    template.content,
    data_dict
)

if not is_valid:
    print(f"Missing: {missing}")
```

---

### `render_template(template_instance, context_dict)`

Render template with context.

**Parameters:**
- `template_instance` (ContractTemplate): Template to render
- `context_dict` (dict): Context variables

**Returns:**
- `str`: Rendered HTML

**Raises:**
- `Exception`: If rendering fails

**Example:**
```python
html = TemplateService.render_template(template, context)
```

---

## ContractDraftService

### `generate_draft(contract, submitted_data, user=None, is_regeneration=False)`

Generate a new draft document.

**Parameters:**
- `contract` (Contract): Contract instance (must be template-based)
- `submitted_data` (dict): Form field values
- `user` (User, optional): User triggering generation
- `is_regeneration` (bool): Whether this is template update

**Returns:**
- `ContractDraft` instance, or `None` if generation failed

**Raises:**
- `ValueError`: If contract not template-based

**Example:**
```python
from contracts.services import ContractDraftService

draft = ContractDraftService.generate_draft(
    contract=contract,
    submitted_data={'vendor_name': 'Acme'},
    user=request.user,
    is_regeneration=False
)

if draft:
    print(f"Draft v{draft.version} created")
```

---

### `regenerate_draft_from_latest_data(contract, user=None)`

Regenerate draft using existing submitted data.

**Parameters:**
- `contract` (Contract): Contract instance
- `user` (User, optional): User triggering regeneration

**Returns:**
- `ContractDraft` instance, or `None` if no data submitted

**Example:**
```python
draft = ContractDraftService.regenerate_draft_from_latest_data(
    contract=contract,
    user=request.user
)
```

---

### `get_draft_download_url(draft)`

Get download URL for draft.

**Parameters:**
- `draft` (ContractDraft): Draft instance

**Returns:**
- `str`: URL to download, or `None`

**Example:**
```python
url = ContractDraftService.get_draft_download_url(draft)
if url:
    print(f"Download: {url}")
```

---

### `list_drafts_for_contract(contract, limit=None)`

Get all drafts for a contract.

**Parameters:**
- `contract` (Contract): Contract instance
- `limit` (int, optional): Max results

**Returns:**
- `QuerySet`: ContractDraft instances ordered by version desc

**Example:**
```python
# All drafts
all_drafts = ContractDraftService.list_drafts_for_contract(contract)

# Last 5 drafts
recent = ContractDraftService.list_drafts_for_contract(contract, limit=5)

# Most recent only
latest = ContractDraftService.list_drafts_for_contract(
    contract, 
    limit=1
).first()
```

---

## Constants

### Contract Type Codes

```python
'GENERAL_TRADE'      # General Trade Agreement (template-based)
'MODERN_TRADE'       # Modern Trade Agreement (template-based)
'DISTRIBUTOR'        # Distributor Agreement (template-based)
'VENDOR'             # Vendor Agreement (non-template)
'PURCHASE'           # Purchase Agreement (non-template)
```

### Template Variables

**Always Available:**
```
contract           # Contract instance
contract_id        # Contract ID
contract_title     # Contract title
contract_type      # Contract type (display name)
party_a            # First party
party_b            # Second party
contract_value     # Contract value (decimal)
annual_target      # Annual target (decimal)
start_date         # Start date
end_date           # End date
created_at         # Creation timestamp
owner              # Owner User instance
today              # Current date
generated_date     # Template generation timestamp
```

**From Form Submission:**
```
<all_field_key_values_from_ContractField>
Examples: vendor_name, service_description, etc.
```

---

## Error Handling

### Common Errors and Solutions

**ValueError: Contract type not found**
```python
# Cause: Invalid contract type code
# Solution: Use valid code from list above

# Check available types
from contracts.models import ContractType
print(ContractType.choices)
```

**ValueError: does not use templates**
```python
# Cause: Trying to generate draft for non-template contract
# Solution: Check contract.is_template_based

if contract.is_template_based:
    draft = ContractDraftService.generate_draft(...)
```

**ValueError: No active template found**
```python
# Cause: No template exists or all inactive
# Solution: Create/activate template in admin

# Admin: Contract Templates → Add Template
#   - Select contract type
#   - Enter template content
#   - Check "Active"
#   - Save
```

**Template rendering error**
```python
# Cause: Invalid Django template syntax
# Solution: Check template content

# Valid:
{{ variable }}
{% if condition %}...{% endif %}
{{ variable|default:"fallback" }}

# Invalid:
{{variable}}  # No spaces
{{ missing_variable }}  # Variable not in context
```

---

## Integration Examples

### In View - After Form Submission

```python
@login_required
def contract_data_input(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        form = ContractDataForm(request.POST, request.FILES, ...)
        
        if form.is_valid():
            # Save form data
            contract_data = ContractData.objects.create(
                contract=contract,
                data=clean_data,
                submitted_by=request.user
            )
            
            # Generate draft
            from contracts.services import ContractDraftService
            draft = ContractDraftService.generate_draft(
                contract=contract,
                submitted_data=clean_data,
                user=request.user
            )
            
            if draft:
                messages.success(request, 'Draft generated!')
            
            return redirect('contract_detail', pk=contract.pk)
    
    return render(request, 'contract_data_form.html', {...})
```

### In Template - Display Drafts

```html
{% if drafts %}
<div class="drafts">
    <h3>Contract Drafts</h3>
    <ul>
    {% for draft in drafts %}
        <li>
            v{{ draft.version }}
            - {{ draft.generated_at|date:"M d, Y H:i" }}
            <a href="{{ draft.file.url }}" class="btn btn-sm btn-primary">
                Download
            </a>
        </li>
    {% endfor %}
    </ul>
</div>
{% endif %}
```

### In Task - Regenerate on Template Update

```python
@shared_task
def regenerate_drafts_for_template(template_id):
    """Regenerate all drafts for updated template"""
    from contracts.models import ContractTemplate
    from contracts.services import ContractDraftService
    
    template = ContractTemplate.objects.get(id=template_id)
    
    # Get contracts using this template
    contracts = Contract.objects.filter(
        contract_type__templates=template,
        status__in=['ACTIVE', 'PENDING_SIGNATURE']
    )
    
    for contract in contracts:
        draft = ContractDraftService.regenerate_draft_from_latest_data(
            contract=contract
        )
        
        if draft:
            print(f"Regenerated draft v{draft.version} for {contract.title}")
```

---

## Performance Tips

### Efficient Queries

```python
# Load template with relationship
from contracts.models import ContractTemplate
template = ContractTemplate.objects.select_related(
    'contract_type'
).get(pk=template_id)

# Load contracts with templates
from contracts.models import Contract
contracts = Contract.objects.prefetch_related(
    'drafts'
).filter(...)

# List drafts efficiently
drafts = ContractDraftService.list_drafts_for_contract(
    contract,
    limit=10  # Limit results
)
```

### Caching Template Lookup

```python
from django.core.cache import cache

def get_cached_template(contract_type):
    cache_key = f"template_{contract_type}"
    template = cache.get(cache_key)
    
    if not template:
        from contracts.services import TemplateService
        template = TemplateService.get_template_for_contract_type(contract_type)
        cache.set(cache_key, template, 3600)  # Cache 1 hour
    
    return template
```

---

## Complete Workflow Example

```python
from contracts.models import Contract, ContractData
from contracts.services import TemplateService, ContractDraftService

# 1. Get contract
contract = Contract.objects.get(pk=123)

# 2. Get form data from user submission
form_data = {
    'vendor_name': 'Acme Corp',
    'service_description': 'IT Services',
    'annual_target': 100000.00,
}

# 3. Save form data
contract_data = ContractData.objects.create(
    contract=contract,
    data=form_data,
    submitted_by=request.user
)

# 4. Generate draft
draft = ContractDraftService.generate_draft(
    contract=contract,
    submitted_data=form_data,
    user=request.user
)

# 5. Use draft
if draft:
    url = ContractDraftService.get_draft_download_url(draft)
    print(f"Download: {url}")
```

---

**Quick Reference Complete**

For detailed documentation, see `TEMPLATE_GENERATION_GUIDE.md`
