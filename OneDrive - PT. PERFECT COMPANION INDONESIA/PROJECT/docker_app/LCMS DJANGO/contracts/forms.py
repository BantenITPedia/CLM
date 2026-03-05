from django import forms
from django.contrib.auth.models import User
from .models import (
    Contract, ContractParticipant, ContractSignature,
    ContractDocument, FinalApprovedDocument, Comment, ContractType, ContractStatus,
    ContractTypeDefinition,
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_code = self.initial.get('contract_type') or getattr(self.instance, 'contract_type', None)
        self.fields['contract_type'].choices = _build_contract_type_choices(include_code=current_code)

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
    def __init__(self, *args, user=None, contract=None, **kwargs):
        super().__init__(*args, **kwargs)

        target_contract = contract or getattr(self, 'instance', None)
        if not target_contract or not getattr(target_contract, 'pk', None) or not user:
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

    class Meta:
        model = Contract
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


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

    def __init__(self, *args, **kwargs):
        field_definitions = kwargs.pop('field_definitions', [])
        super().__init__(*args, **kwargs)

        for field in field_definitions:
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

