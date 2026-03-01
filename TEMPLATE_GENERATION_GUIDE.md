# Template-Based Contract Generation System

**Implementation Date:** January 30, 2026  
**Scope:** Template loading, data injection, draft generation  
**Files Modified:** `contracts/services.py`

---

## Overview

The template generation system handles the complete workflow for contract-based drafts:

1. **Load Template** - Retrieve the active template for a contract type
2. **Build Context** - Combine contract metadata + submitted form data
3. **Validate Variables** - Ensure all required template variables are available
4. **Render Template** - Generate HTML from Django template syntax
5. **Save Draft** - Store versioned draft document

---

## Architecture

### Two Service Classes

#### **TemplateService**
Handles template loading, context building, variable validation, and rendering.

**Public Methods:**
- `get_template_for_contract_type(contract_type_code)` - Load active template
- `build_template_context(contract, contract_data_dict)` - Build context
- `validate_template_variables(template_content, contract_data_dict)` - Validate vars
- `render_template(template_instance, context_dict)` - Render HTML

#### **ContractDraftService**
Handles draft generation, version management, and draft retrieval.

**Public Methods:**
- `generate_draft(contract, submitted_data, user, is_regeneration)` - Generate draft
- `regenerate_draft_from_latest_data(contract, user)` - Regenerate from existing data
- `get_draft_download_url(draft)` - Get download URL
- `list_drafts_for_contract(contract, limit)` - List all drafts

---

## Usage Examples

### Example 1: Generate Draft After Form Submission

```python
from contracts.services import ContractDraftService

# In view after form submission
contract_data_dict = {
    'vendor_name': 'Acme Corp',
    'service_description': 'IT Support Services',
    'annual_target': 100000.00,
    'contract_value': 50000.00,
}

draft = ContractDraftService.generate_draft(
    contract=contract,
    submitted_data=contract_data_dict,
    user=request.user,
    is_regeneration=False
)

if draft:
    messages.success(request, f'Draft v{draft.version} generated successfully')
else:
    messages.error(request, 'Failed to generate draft')
```

### Example 2: Regenerate Draft When Template Changes

```python
from contracts.services import ContractDraftService

# Regenerate using latest submitted data
draft = ContractDraftService.regenerate_draft_from_latest_data(
    contract=contract,
    user=request.user
)

if draft:
    messages.success(request, f'Draft regenerated as v{draft.version}')
```

### Example 3: Get Latest Draft URL

```python
from contracts.services import ContractDraftService

latest_draft = ContractDraftService.list_drafts_for_contract(
    contract=contract,
    limit=1
).first()

if latest_draft:
    download_url = ContractDraftService.get_draft_download_url(latest_draft)
```

### Example 4: Validate Template Before Generation

```python
from contracts.services import TemplateService

is_valid, missing_vars, available_vars = TemplateService.validate_template_variables(
    template_content=template.content,
    contract_data_dict=submitted_data
)

if not is_valid:
    print(f"Missing variables: {missing_vars}")
```

---

## Template System

### Template Format

Templates use Django template syntax with `{{ variable }}` placeholders:

```html
<h1>{{ contract_type }} - {{ contract_title }}</h1>

<p><strong>Vendor:</strong> {{ vendor_name }}</p>
<p><strong>Service:</strong> {{ service_description }}</p>
<p><strong>Annual Target:</strong> ${{ annual_target }}</p>
<p><strong>Contract Value:</strong> ${{ contract_value }}</p>

<p><strong>Period:</strong> {{ start_date }} to {{ end_date }}</p>
<p><strong>Generated:</strong> {{ generated_date }}</p>

<p>Contract Details:</p>
<p>{{ contract.description }}</p>
```

### Available Variables

**System Variables (always available):**
- `contract` - Contract instance
- `contract_id` - Contract ID
- `contract_title` - Contract title
- `contract_type` - Contract type display name
- `party_a` - First party
- `party_b` - Second party
- `contract_value` - Total contract value
- `annual_target` - Annual target (sales agreements)
- `start_date` - Contract start date
- `end_date` - Contract end date
- `created_at` - Contract creation timestamp
- `owner` - Contract owner user object
- `today` - Current date
- `generated_date` - Template generation timestamp

**Form-Submitted Data:**
- All values from `ContractField` definitions
- Examples: `vendor_name`, `service_description`, custom fields

### Creating Templates in Admin

1. Go to Admin → Contract Templates
2. Select contract type (must be template-based)
3. Enter template name (e.g., "Standard GTA v1")
4. Enter content using Django template syntax
5. Save and mark as "Active"

### Template Versioning

- Multiple templates can exist per contract type
- Only one can be "active" at a time
- Old versions preserved in database
- Drafts remember which template version was used

---

## Error Handling

### ValueError: Contract Type Not Template-Based

```python
# Raised when:
# - Contract type does not have is_template_based=True
# - Attempting to generate draft for Vendor/Purchase agreement

# Solution:
# Ensure contract.contract_type is one of:
# - GENERAL_TRADE
# - MODERN_TRADE
# - DISTRIBUTOR
```

### ValueError: No Template Found

```python
# Raised when:
# - Contract type has no active template
# - All templates are inactive

# Solution:
# 1. Go to Admin → Contract Templates
# 2. Create new template for contract type
# 3. Mark as "Active"
```

### Template Rendering Exception

```python
# Raised when:
# - Template syntax is invalid
# - Missing context variable causes error
# - Context value type incompatible with template

# Solution:
# 1. Review template for syntax errors
# 2. Ensure all required variables in context
# 3. Check variable types (dates, decimals, strings)
```

---

## Integration with Existing Views

### Where to Use

**contract_data_input() view:**
```python
# After form submission
draft = ContractDraftService.generate_draft(
    contract=contract,
    submitted_data=clean_data,
    user=request.user,
    is_regeneration=False
)

if draft:
    messages.success(request, 'Data saved and draft generated')
else:
    messages.warning(request, 'Data saved, but draft generation failed')
```

**regenerate_contract_draft() view:**
```python
# When template is updated
draft = ContractDraftService.regenerate_draft_from_latest_data(
    contract=contract,
    user=request.user
)

if draft:
    messages.success(request, f'Draft v{draft.version} regenerated')
```

**contract_detail() view:**
```python
# Display drafts
drafts = ContractDraftService.list_drafts_for_contract(
    contract=contract,
    limit=10
)

context['drafts'] = drafts
```

---

## Data Flow

```
User fills form (contract_data_input view)
    ↓
Form validates (ContractDataForm)
    ↓
ContractData record created (versioned)
    ↓
ContractDraftService.generate_draft() called
    ├─ TemplateService.get_template_for_contract_type()
    ├─ TemplateService.build_template_context()
    ├─ TemplateService.validate_template_variables()
    ├─ TemplateService.render_template()
    └─ Draft saved to ContractDraft model
    ↓
AuditLog entry created (DRAFT_GENERATED)
    ↓
Draft email sent to participants
    ↓
User downloads draft from contract detail page
```

---

## Testing the Implementation

### Test 1: Template Loading

```python
from contracts.services import TemplateService
from contracts.models import ContractTypeDefinition, ContractTemplate

# Setup: Create template
type_def = ContractTypeDefinition.objects.create(
    code='GENERAL_TRADE',
    name='General Trade Agreement',
    is_template_based=True,
    active=True
)

ContractTemplate.objects.create(
    contract_type=type_def,
    name='v1',
    content='<p>{{ vendor_name }}</p>',
    active=True
)

# Test
template = TemplateService.get_template_for_contract_type('GENERAL_TRADE')
assert template is not None
assert 'vendor_name' in template.content
```

### Test 2: Context Building

```python
from contracts.services import TemplateService
from contracts.models import Contract

contract = Contract.objects.create(
    title='Test Contract',
    contract_type='GENERAL_TRADE',
    party_a='Our Company',
    party_b='Vendor Inc',
    contract_value=50000.00,
)

data = {'vendor_name': 'Vendor Inc', 'service_description': 'Services'}

context = TemplateService.build_template_context(contract, data)

assert context['contract_title'] == 'Test Contract'
assert context['vendor_name'] == 'Vendor Inc'
assert 'today' in context
```

### Test 3: Draft Generation

```python
from contracts.services import ContractDraftService
from contracts.models import ContractDraft

draft = ContractDraftService.generate_draft(
    contract=contract,
    submitted_data={'vendor_name': 'Acme'},
    user=request.user,
)

assert draft is not None
assert draft.version == 1
assert draft.file.read().decode() != ''
```

### Test 4: Template Validation

```python
from contracts.services import TemplateService

template_content = '<p>{{ vendor_name }}, {{ missing_var }}</p>'
data = {'vendor_name': 'Acme'}

is_valid, missing, available = TemplateService.validate_template_variables(
    template_content,
    data
)

assert not is_valid
assert 'missing_var' in missing
```

---

## Performance Considerations

### Template Caching
- Templates are cached in database (no file I/O)
- Use `.select_related('contract_type')` for efficiency

### Draft Storage
- Drafts stored as HTML files in media directory
- Each draft is a complete, standalone HTML file
- Versioning prevents overwriting

### Query Optimization
```python
# Efficient: Load template with type definition
template = ContractTemplate.objects.select_related(
    'contract_type'
).filter(active=True).first()

# Efficient: List drafts
drafts = ContractDraft.objects.filter(
    contract=contract
).order_by('-version')[:10]
```

---

## Future Enhancements

### Potential Additions (Not In MVP)
- DOCX template support (python-docx)
- PDF generation from HTML drafts
- Template preview before draft generation
- Template validation UI in admin
- Variable extraction from template (admin help)
- S3 integration for draft storage
- Draft comparison (version diff)

### Not Implementing Now
- Rich text editor for templates (use Django template syntax)
- Template builder UI (admins write templates)
- Internationalization (English only)

---

## Troubleshooting

### "No active template found"
**Cause:** Template not created or not marked active  
**Solution:** Create template in Admin → Contract Templates

### "Contract type does not use templates"
**Cause:** Attempting to generate draft for non-template contract  
**Solution:** Use document upload for Vendor/Purchase agreements

### Template variables not rendering
**Cause:** Variable name mismatch or typo  
**Solution:** Ensure variable names match field_key from ContractField

### Draft file empty or corrupted
**Cause:** Template rendering error or file save issue  
**Solution:** Check template syntax in admin, verify context variables

---

**Implementation Complete**

The template generation system is ready for integration with:
- Form submission views
- Draft regeneration views
- Admin interfaces
- Email notification system

All services are stateless and can be called independently.
