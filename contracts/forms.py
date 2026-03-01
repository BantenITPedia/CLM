from django import forms
from django.contrib.auth.models import User
from .models import (
    Contract, ContractParticipant, ContractSignature,
    ContractDocument, FinalApprovedDocument, Comment, ContractType, ContractStatus,
    ParticipantRole
)


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'title', 'contract_type', 'party_b',
            'contract_value', 'start_date', 'end_date', 'renewal_reminder_days',
            'auto_renew', 'renewal_period_months', 'document', 'notes'
        ]
        labels = {
            'contract_value': 'Target Value (IDR)',
            'party_b': 'Legal Entity Name (PT / CV / Others)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_type': forms.Select(attrs={'class': 'form-control'}),
            'party_b': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5000000000', 'inputmode': 'numeric'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'renewal_reminder_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'renewal_period_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContractStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class ContractTypeSelectForm(forms.Form):
    contract_type = forms.ChoiceField(
        choices=list(ContractType.choices),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


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
        choices=[('', 'All Types')] + list(ContractType.choices),
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
