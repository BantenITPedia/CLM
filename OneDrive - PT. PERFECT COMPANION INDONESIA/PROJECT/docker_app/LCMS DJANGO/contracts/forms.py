from django import forms
from django.contrib.auth.models import User
from .models import (
    Contract, ContractParticipant, ContractSignature,
    ContractDocument, FinalApprovedDocument, Comment, ContractType, ContractStatus,
    ContractTypeDefinition, CompanyProfile,
    ParticipantRole
)


def _build_contract_type_choices(include_blank=False, include_inactive=False, include_code=None):
    queryset = ContractTypeDefinition.objects.all()
    if not include_inactive:
        queryset = queryset.filter(active=True)

    choices = list(queryset.order_by('name').values_list('code', 'name'))
    if not choices:
        choices = list(ContractType.choices)

    if include_code:
        existing_codes = {code for code, _ in choices}
        if include_code not in existing_codes:
            fallback_label = dict(ContractType.choices).get(include_code, include_code.replace('_', ' ').title())
            choices.append((include_code, fallback_label))

    if include_blank:
        return [('', 'All Types')] + choices
    return choices


class ContractForm(forms.ModelForm):
    issuing_company = forms.ModelChoiceField(
        queryset=CompanyProfile.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Issuing Company'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_code = self.initial.get('contract_type') or getattr(self.instance, 'contract_type', None)
        self.fields['contract_type'].choices = _build_contract_type_choices(include_code=current_code)
        self.fields['issuing_company'].queryset = CompanyProfile.objects.all().order_by('name')
        self.fields['issuing_company'].empty_label = 'Select issuing company (required for Vendor)'

        if not self.is_bound and getattr(self.instance, 'pk', None):
            existing_company = None
            if getattr(self.instance, 'issuing_company_code', None):
                existing_company = CompanyProfile.objects.filter(
                    short_name__iexact=self.instance.issuing_company_code
                ).first()
            if not existing_company and getattr(self.instance, 'issuing_company_name', None):
                existing_company = CompanyProfile.objects.filter(
                    name__iexact=self.instance.issuing_company_name
                ).first()
            if existing_company:
                self.fields['issuing_company'].initial = existing_company

    def clean(self):
        cleaned_data = super().clean()
        contract_type = cleaned_data.get('contract_type')
        issuing_company = cleaned_data.get('issuing_company')

        if contract_type == ContractType.VENDOR and not issuing_company:
            self.add_error('issuing_company', 'Issuing company is required for Vendor Agreement (04).')

        return cleaned_data

    def save(self, commit=True):
        contract = super().save(commit=False)

        selected_company = self.cleaned_data.get('issuing_company')
        if selected_company:
            contract.party_a = selected_company.name
            contract.issuing_company_name = selected_company.name

            short_name = (selected_company.short_name or '').strip().upper().replace(' ', '')
            if not short_name:
                words = [w for w in selected_company.name.split() if w and w[0].isalnum()]
                short_name = ''.join(word[0].upper() for word in words)[:8]

            contract.issuing_company_code = short_name or 'PCI'
        else:
            contract.issuing_company_name = None
            contract.issuing_company_code = None

        if commit:
            contract.save()
            self.save_m2m()

        return contract

    class Meta:
        model = Contract
        fields = [
            'title', 'contract_type', 'party_b',
            'contract_value', 'start_date', 'end_date', 'duration_days', 'notes'
        ]
        labels = {
            'contract_value': 'Target Value (IDR)',
            'party_b': 'Legal Entity Name (PT / CV / Others)',
            'duration_days': 'Duration (days)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_type': forms.Select(attrs={'class': 'form-control'}),
            'party_b': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5,000,000,000', 'id': 'id_contract_value'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 30', 'help_text': 'Specify duration in days. If provided with start date, end date will be calculated.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContractStatusUpdateForm(forms.ModelForm):
    contract_number_override = forms.CharField(
        required=False,
        max_length=64,
        label='Contract Number Override (Optional)',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank to auto-generate',
            }
        ),
        help_text='Legal can set this manually when approving. Leave empty for automatic numbering.',
    )

    def __init__(self, *args, user=None, contract=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.target_contract = contract or getattr(self, 'instance', None)
        self.show_contract_number_override = False

        target_contract = self.target_contract
        if not target_contract or not getattr(target_contract, 'pk', None) or not user:
            self.fields.pop('contract_number_override', None)
            return

        from .permissions import get_allowed_next_statuses

        allowed_statuses = get_allowed_next_statuses(user, target_contract)
        self.fields['status'].choices = [
            (value, label)
            for value, label in ContractStatus.choices
            if value in allowed_statuses
        ]

        if not self.fields['status'].choices:
            self.fields['status'].required = False

        can_override_contract_number = (
            not target_contract.contract_number
            and ContractStatus.APPROVED in allowed_statuses
        )

        if can_override_contract_number:
            self.show_contract_number_override = True
        else:
            self.fields.pop('contract_number_override', None)

    def clean_contract_number_override(self):
        value = (self.cleaned_data.get('contract_number_override') or '').strip()
        if not value:
            return ''
        return value.upper()

    def clean(self):
        cleaned_data = super().clean()
        override_number = (cleaned_data.get('contract_number_override') or '').strip()
        selected_status = cleaned_data.get('status')

        if not override_number:
            return cleaned_data

        if selected_status != ContractStatus.APPROVED:
            self.add_error(
                'contract_number_override',
                'Manual contract number can only be set when status is Approved.'
            )
            return cleaned_data

        if self.instance and self.instance.contract_number:
            self.add_error(
                'contract_number_override',
                'Contract number is already assigned and cannot be overridden from this action.'
            )
            return cleaned_data

        duplicate = Contract.objects.filter(contract_number__iexact=override_number)
        if self.instance and self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            self.add_error(
                'contract_number_override',
                'This contract number is already used by another contract.'
            )

        return cleaned_data

    class Meta:
        model = Contract
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class ContractNumberOverrideForm(forms.Form):
    contract_number = forms.CharField(
        required=False,
        max_length=64,
        label='Contract Number (Optional)',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank to auto-generate',
            }
        ),
        help_text='Legal may fill manually or leave empty to auto-generate based on sequence.',
    )

    def __init__(self, *args, contract=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.contract = contract

    def clean_contract_number(self):
        value = (self.cleaned_data.get('contract_number') or '').strip().upper()
        if not value:
            return ''

        duplicate = Contract.objects.filter(contract_number__iexact=value)
        if self.contract and getattr(self.contract, 'pk', None):
            duplicate = duplicate.exclude(pk=self.contract.pk)
        if duplicate.exists():
            raise forms.ValidationError('This contract number is already used by another contract.')

        return value


class ContractTypeSelectForm(forms.Form):
    contract_type = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_code = self.initial.get('contract_type')
        self.fields['contract_type'].choices = _build_contract_type_choices(include_code=current_code)


class ContractParticipantForm(forms.ModelForm):
    class Meta:
        model = ContractParticipant
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class ContractDocumentForm(forms.ModelForm):
    class Meta:
        model = ContractDocument
        fields = ['title', 'document', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class FinalApprovedDocumentForm(forms.ModelForm):
    class Meta:
        model = FinalApprovedDocument
        fields = ['document', 'notes']
        widgets = {
            'document': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes about the final signed document...'}),
        }
        labels = {
            'document': 'Upload Final Signed Contract',
            'notes': 'Notes',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'is_internal']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment...'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContractFilterForm(forms.Form):
    contract_type = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(ContractStatus.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    owner = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='All Owners'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search contracts...'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_code = None
        if self.is_bound:
            selected_code = self.data.get(self.add_prefix('contract_type'))
        else:
            selected_code = self.initial.get('contract_type')

        self.fields['contract_type'].choices = _build_contract_type_choices(
            include_blank=True,
            include_inactive=True,
            include_code=selected_code,
        )


class ContractDataForm(forms.Form):
    """Dynamic form built from ContractField definitions"""

    LEGACY_MANUAL_NUMBER_KEYS = {'no_contract', 'contract_number'}
    TEMPLATE_FIXED_KEYS = {'product_types', 'incentive_percentage'}
    SKIPPED_FIELD_KEYS = LEGACY_MANUAL_NUMBER_KEYS | TEMPLATE_FIXED_KEYS

    def __init__(self, *args, **kwargs):
        field_definitions = kwargs.pop('field_definitions', [])
        super().__init__(*args, **kwargs)

        for field in field_definitions:
            if (field.field_key or '').strip().lower() in self.SKIPPED_FIELD_KEYS:
                continue

            common_attrs = {'class': 'form-control', 'placeholder': field.label}

            if field.field_type == 'text':
                self.fields[field.field_key] = forms.CharField(
                    label=field.label,
                    required=field.required,
                    widget=forms.TextInput(attrs=common_attrs)
                )
            elif field.field_type == 'number':
                self.fields[field.field_key] = forms.DecimalField(
                    label=field.label,
                    required=field.required,
                    widget=forms.NumberInput(attrs=common_attrs)
                )
            elif field.field_type == 'date':
                self.fields[field.field_key] = forms.DateField(
                    label=field.label,
                    required=field.required,
                    widget=forms.DateInput(attrs={**common_attrs, 'type': 'date'})
                )
            elif field.field_type == 'select':
                options = field.options or []
                choices = [(opt, opt) for opt in options]
                self.fields[field.field_key] = forms.ChoiceField(
                    label=field.label,
                    required=field.required,
                    choices=choices,
                    widget=forms.Select(attrs=common_attrs)
                )
            elif field.field_type == 'file':
                self.fields[field.field_key] = forms.FileField(
                    label=field.label,
                    required=field.required,
                    widget=forms.FileInput(attrs={'class': 'form-control'})
                )


# Wizard Forms for Contract Creation

class BusinessEntityTypeForm(forms.Form):
    """Step 1: Select business entity type"""
    from .models import BusinessEntityType
    
    business_entity_type = forms.ChoiceField(
        label='Jenis Badan Usaha',
        choices=BusinessEntityType.choices,
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text='Pilih jenis badan usaha Anda'
    )


class BusinessEntityDocumentForm(forms.Form):
    """Step 2: Upload required documents based on entity type"""
    
    def __init__(self, *args, entity_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Define required documents based on entity type
        if entity_type in ['PT', 'CV']:
            self.fields['akta_pendirian'] = forms.FileField(
                label='Akta Pendirian',
                required=True,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload Akta Pendirian perusahaan'
            )
            self.fields['npwp'] = forms.FileField(
                label='NPWP',
                required=True,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload NPWP perusahaan'
            )
            self.fields['nib'] = forms.FileField(
                label='NIB (Nomor Induk Berusaha)',
                required=True,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload NIB'
            )
            self.fields['ktp_penanggung_jawab'] = forms.FileField(
                label='KTP Penanggung Jawab',
                required=True,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload KTP Penanggung Jawab'
            )
            self.fields['perizinan_lainnya'] = forms.FileField(
                label='Perizinan Lainnya',
                required=False,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload perizinan lainnya (opsional)'
            )
        elif entity_type == 'PERORANGAN':
            self.fields['ktp'] = forms.FileField(
                label='KTP',
                required=True,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload KTP'
            )
            self.fields['npwp'] = forms.FileField(
                label='NPWP',
                required=True,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
                help_text='Upload NPWP'
            )

