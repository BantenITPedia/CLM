from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from django.template import Template, Context
from django.core.files.base import ContentFile
from django.utils.text import slugify
from .models import (
    Contract, ContractParticipant, ContractSignature,
    ContractDocument, FinalApprovedDocument, Comment, AuditLog, ContractStatus,
    ContractField, ContractData, ContractTemplate, ContractDraft,
    ContractTypeDefinition, ContractDataFile, ContractType
)
from .forms import (
    ContractForm, ContractStatusUpdateForm, ContractParticipantForm,
    ContractDocumentForm, CommentForm, ContractFilterForm,
    ContractDataForm, ContractTypeSelectForm
)
from .services import EmailService
from .permissions import (
    can_view_contract,
    can_edit_contract,
    can_delete_contract,
    can_update_contract_status,
    can_manage_participants,
    can_add_document,
    can_add_comment,
    can_edit_contract_data,
    can_regenerate_draft,
    has_contract_permission,
)


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'contracts/login.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard with contract statistics"""
    today = timezone.now().date()
    
    # Get user's contracts (owned or participating)
    user_contracts = Contract.objects.filter(
        Q(owner=request.user) | Q(participants__user=request.user)
    ).distinct()
    
    # Statistics
    total_contracts = user_contracts.count()
    active_contracts = user_contracts.filter(status=ContractStatus.ACTIVE).count()
    expiring_soon_contracts = user_contracts.filter(status=ContractStatus.EXPIRING_SOON).count()
    legal_review_contracts = user_contracts.filter(status=ContractStatus.LEGAL_REVIEW).count()
    
    # Expiring in different periods (ACTIVE or EXPIRING_SOON contracts)
    expiring_30 = user_contracts.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30),
        status__in=[ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
    ).count()
    
    expiring_60 = user_contracts.filter(
        end_date__gte=today + timedelta(days=31),
        end_date__lte=today + timedelta(days=60),
        status__in=[ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
    ).count()
    
    expiring_90 = user_contracts.filter(
        end_date__gte=today + timedelta(days=61),
        end_date__lte=today + timedelta(days=90),
        status__in=[ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
    ).count()
    
    # Recent contracts
    recent_contracts = user_contracts.order_by('-created_at')[:10]
    
    # Contracts needing attention (in legal review, submitted, expiring, or expiring soon)
    needs_attention = user_contracts.filter(
        Q(status=ContractStatus.LEGAL_REVIEW) |
        Q(status=ContractStatus.SUBMITTED) |
        Q(status=ContractStatus.EXPIRING_SOON) |
        Q(status__in=[ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON],
          end_date__gte=today,
          end_date__lte=today + timedelta(days=30))
    ).distinct().order_by('end_date', '-created_at')[:5]
    
    context = {
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'expiring_soon_contracts': expiring_soon_contracts,
        'legal_review_contracts': legal_review_contracts,
        'expiring_30': expiring_30,
        'expiring_60': expiring_60,
        'expiring_90': expiring_90,
        'recent_contracts': recent_contracts,
        'needs_attention': needs_attention,
    }
    
    return render(request, 'contracts/dashboard.html', context)


@login_required
def contract_list(request):
    """List all contracts with filtering"""
    contracts = Contract.objects.filter(
        Q(owner=request.user) | Q(participants__user=request.user)
    ).distinct().order_by('-created_at')
    
    # Apply filters
    form = ContractFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('contract_type'):
            contracts = contracts.filter(contract_type=form.cleaned_data['contract_type'])
        
        if form.cleaned_data.get('status'):
            contracts = contracts.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('owner'):
            contracts = contracts.filter(owner=form.cleaned_data['owner'])
        
        if form.cleaned_data.get('start_date'):
            contracts = contracts.filter(start_date__gte=form.cleaned_data['start_date'])
        
        if form.cleaned_data.get('end_date'):
            contracts = contracts.filter(end_date__lte=form.cleaned_data['end_date'])
        
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            contracts = contracts.filter(
                Q(title__icontains=search) |
                Q(party_b__icontains=search) |
                Q(description__icontains=search)
            )
    
    context = {
        'contracts': contracts,
        'filter_form': form,
    }
    
    return render(request, 'contracts/contract_list.html', context)


@login_required
def contract_create(request):
    """Create a new contract"""
    def get_field_definitions(contract_type_code):
        type_def = ContractTypeDefinition.objects.filter(
            code=contract_type_code,
            active=True
        ).first()
        if not type_def or not type_def.is_template_based:
            return None
        return type_def.fields.all().order_by('position', 'label')

    def apply_gt_defaults(contract_obj, data_dict):
        from decimal import Decimal

        if not data_dict.get('party_b_name') and contract_obj.party_b:
            data_dict['party_b_name'] = contract_obj.party_b

        if not data_dict.get('contract_start_date') and contract_obj.start_date:
            data_dict['contract_start_date'] = contract_obj.start_date.strftime('%Y-%m-%d')

        if not data_dict.get('contract_end_date') and contract_obj.end_date:
            data_dict['contract_end_date'] = contract_obj.end_date.strftime('%Y-%m-%d')

        if not data_dict.get('total_purchase_target') and contract_obj.contract_value:
            data_dict['total_purchase_target'] = str(contract_obj.contract_value)

        total_target = data_dict.get('total_purchase_target')
        if total_target:
            try:
                total_decimal = Decimal(str(total_target))
                base = total_decimal // Decimal('4')
                remainder = total_decimal - (base * 4)

                if not data_dict.get('sales_target_q1'):
                    data_dict['sales_target_q1'] = str(base)
                if not data_dict.get('sales_target_q2'):
                    data_dict['sales_target_q2'] = str(base)
                if not data_dict.get('sales_target_q3'):
                    data_dict['sales_target_q3'] = str(base)
                if not data_dict.get('sales_target_q4'):
                    data_dict['sales_target_q4'] = str(base + remainder)
            except Exception:
                pass

        if contract_obj.start_date:
            start_date = contract_obj.start_date
            end_date = contract_obj.end_date

            def add_months(date_obj, months):
                month = date_obj.month - 1 + months
                year = date_obj.year + month // 12
                month = month % 12 + 1
                day = min(date_obj.day, [31,
                                         29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                return date_obj.replace(year=year, month=month, day=day)

            q1_start = start_date
            q2_start = add_months(start_date, 3)
            q3_start = add_months(start_date, 6)
            q4_start = add_months(start_date, 9)

            q1_end = q2_start - timedelta(days=1)
            q2_end = q3_start - timedelta(days=1)
            q3_end = q4_start - timedelta(days=1)
            q4_end = end_date if end_date else add_months(start_date, 12) - timedelta(days=1)

            def fmt(date_obj):
                return date_obj.strftime('%d %b %Y')

            if not data_dict.get('quarter_1_period'):
                data_dict['quarter_1_period'] = f"{fmt(q1_start)} - {fmt(q1_end)}"
            if not data_dict.get('quarter_2_period'):
                data_dict['quarter_2_period'] = f"{fmt(q2_start)} - {fmt(q2_end)}"
            if not data_dict.get('quarter_3_period'):
                data_dict['quarter_3_period'] = f"{fmt(q3_start)} - {fmt(q3_end)}"
            if not data_dict.get('quarter_4_period'):
                data_dict['quarter_4_period'] = f"{fmt(q4_start)} - {fmt(q4_end)}"

        return data_dict

    contract_type_code = request.POST.get('contract_type') or request.GET.get('contract_type') or ContractType.GENERAL_TRADE

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES)
        field_definitions = get_field_definitions(contract_type_code)
        data_form = ContractDataForm(request.POST, request.FILES, field_definitions=field_definitions) if field_definitions else None

        if form.is_valid():
            if data_form and not data_form.is_valid():
                return render(
                    request,
                    'contracts/contract_form.html',
                    {
                        'form': form,
                        'data_form': data_form,
                        'action': 'Create',
                        'contract_type_code': contract_type_code,
                    }
                )

            contract = form.save(commit=False)
            contract.created_by = request.user
            contract.owner = request.user
            # Auto-set Party A if not provided
            if not contract.party_a:
                contract.party_a = "PT. Your Company Name"
            contract.save()

            additional_docs = request.FILES.getlist('additional_documents')
            additional_titles = request.POST.getlist('additional_document_titles')
            if additional_docs:
                for idx, doc in enumerate(additional_docs):
                    title = ''
                    if idx < len(additional_titles):
                        title = additional_titles[idx].strip()
                    if not title:
                        title = doc.name
                    ContractDocument.objects.create(
                        contract=contract,
                        title=title,
                        document=doc,
                        uploaded_by=request.user
                    )

                AuditLog.objects.create(
                    contract=contract,
                    user=request.user,
                    action='DOCUMENT_UPLOAD',
                    details='Additional documents uploaded during creation'
                )

            # Create ContractData from form or auto-populated
            if field_definitions:
                if data_form:
                    # Use submitted data
                    clean_data = {k: str(v) if v else '' for k, v in data_form.cleaned_data.items()}
                else:
                    clean_data = {}
                
                # Apply auto-population for missing fields
                auto_data = apply_gt_defaults(contract, clean_data)

                contract_data = ContractData.objects.create(
                    contract=contract,
                    data=auto_data,
                    version=1,
                    submitted_by=request.user
                )

                if contract.status == ContractStatus.DRAFT:
                    contract.status = ContractStatus.SUBMITTED
                    contract.save(update_fields=['status'])

                AuditLog.objects.create(
                    contract=contract,
                    user=request.user,
                    action='DATA_SUBMITTED',
                    details='Contract data submitted during creation'
                )

                EmailService.send_data_submitted_email(contract, request.user)
                _generate_contract_draft(contract, user=request.user)

            messages.success(request, f'Contract "{contract.title}" created successfully')
            return redirect('contract_detail', pk=contract.pk)
        else:
            # Form validation failed - return form with errors
            return render(
                request,
                'contracts/contract_form.html',
                {
                    'form': form,
                    'action': 'Create',
                    'contract_type_code': contract_type_code,
                }
            )

    form = ContractForm(initial={'contract_type': contract_type_code})
    field_definitions = get_field_definitions(contract_type_code)
    data_form = ContractDataForm(field_definitions=field_definitions) if field_definitions else None
    return render(
        request,
        'contracts/contract_form.html',
        {
            'form': form,
            'data_form': data_form,
            'action': 'Create',
            'contract_type_code': contract_type_code,
        }
    )


@login_required
def contract_detail(request, pk):
    """View contract details"""
    contract = get_object_or_404(Contract, pk=pk)
    
    if not can_view_contract(request.user, contract):
        messages.error(request, 'You do not have permission to view this contract')
        return redirect('dashboard')
    
    # Get related data
    participants = contract.participants.filter(is_active=True)
    documents = contract.additional_documents.all()
    comments = contract.comments.all()
    audit_logs = contract.audit_logs.order_by('-timestamp')[:20]
    contract_data = contract.structured_data_versions.first()
    all_data_versions = contract.structured_data_versions.all()
    drafts = contract.drafts.all()
    
    # Check if user can upload final document
    can_upload_final = has_contract_permission(request.user, contract, 'upload_final_document')
    
    # Forms
    comment_form = CommentForm()
    document_form = ContractDocumentForm()
    participant_form = ContractParticipantForm()
    status_form = ContractStatusUpdateForm(instance=contract)
    
    # Final approved document form
    from .forms import FinalApprovedDocumentForm
    final_approval_form = FinalApprovedDocumentForm()
    
    context = {
        'contract': contract,
        'participants': participants,
        'documents': documents,
        'comments': comments,
        'audit_logs': audit_logs,
        'comment_form': comment_form,
        'document_form': document_form,
        'participant_form': participant_form,
        'status_form': status_form,
        'contract_data': contract_data,
        'all_data_versions': all_data_versions,
        'drafts': drafts,
        'final_approval_form': final_approval_form,
        'can_upload_final': can_upload_final,
    }
    
    return render(request, 'contracts/contract_detail.html', context)


@login_required
def upload_final_document(request, pk):
    """Upload final approved/signed contract document"""
    contract = get_object_or_404(Contract, pk=pk)
    
    if not can_view_contract(request.user, contract):
        messages.error(request, 'You do not have permission to view this contract')
        return redirect('dashboard')
    
    # Check permission to upload final document
    if not has_contract_permission(request.user, contract, 'upload_final_document'):
        messages.error(request, 'You do not have permission to upload the final contract document')
        return redirect('contract_detail', pk=pk)
    
    if request.method == 'POST':
        from .forms import FinalApprovedDocumentForm
        form = FinalApprovedDocumentForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Delete existing final document if any
            if hasattr(contract, 'final_approved_document'):
                contract.final_approved_document.delete()
            
            # Create new final approved document
            final_doc = form.save(commit=False)
            final_doc.contract = contract
            final_doc.uploaded_by = request.user
            final_doc.save()
            
            # Log action
            AuditLog.objects.create(
                contract=contract,
                action='FINAL_DOCUMENT_UPLOAD',
                user=request.user,
                details=f'Final contract document uploaded: {final_doc.document.name}'
            )
            
            messages.success(request, 'Final contract document uploaded successfully')
            return redirect('contract_detail', pk=pk)
        else:
            messages.error(request, 'Error uploading document. Please try again.')
            for error in form.errors.values():
                messages.error(request, str(error))
    
    return redirect('contract_detail', pk=pk)


@login_required
def contract_edit(request, pk):
    """Edit contract"""
    contract = get_object_or_404(Contract, pk=pk)
    
    # Check permission
    if not can_edit_contract(request.user, contract):
        messages.error(request, 'You do not have permission to edit this contract')
        return redirect('contract_detail', pk=pk)
    
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contract updated successfully')
            return redirect('contract_detail', pk=pk)
    else:
        form = ContractForm(instance=contract)
    
    return render(request, 'contracts/contract_form.html', {'form': form, 'action': 'Edit', 'contract': contract})


@login_required
def contract_delete(request, pk):
    """Delete contract"""
    contract = get_object_or_404(Contract, pk=pk)
    
    if not can_delete_contract(request.user, contract):
        messages.error(request, 'You do not have permission to delete this contract')
        return redirect('contract_detail', pk=pk)
    
    if request.method == 'POST':
        title = contract.title
        contract.delete()
        messages.success(request, f'Contract "{title}" deleted successfully')
        return redirect('contract_list')
    
    return render(request, 'contracts/contract_confirm_delete.html', {'contract': contract})


@login_required
def update_contract_status(request, pk):
    """Update contract status"""
    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=pk)
        
        # Check permission
        if not can_update_contract_status(request.user, contract):
            messages.error(request, 'You do not have permission to update this contract')
            return redirect('contract_detail', pk=pk)
        
        form = ContractStatusUpdateForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contract status updated successfully')
        else:
            messages.error(request, 'Error updating contract status')
    
    return redirect('contract_detail', pk=pk)


@login_required
def add_participant(request, pk):
    """Add participant to contract"""
    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=pk)
        
        # Check permission
        if not can_manage_participants(request.user, contract):
            messages.error(request, 'You do not have permission to add participants')
            return redirect('contract_detail', pk=pk)
        
        form = ContractParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.contract = contract
            participant.save()
            messages.success(request, f'Participant {participant.user.get_full_name()} added successfully')
        else:
            messages.error(request, 'Error adding participant')
    
    return redirect('contract_detail', pk=pk)


@login_required
def add_document(request, pk):
    """Add document to contract"""
    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=pk)
        
        if not can_add_document(request.user, contract):
            messages.error(request, 'You do not have permission to add documents')
            return redirect('contract_detail', pk=pk)

        form = ContractDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            from .services import DocumentVersionService

            document = DocumentVersionService.create_versioned_document(
                contract=contract,
                uploaded_by=request.user,
                title=form.cleaned_data['title'],
                file_obj=form.cleaned_data['document'],
                description=form.cleaned_data.get('description', '')
            )
            
            AuditLog.objects.create(
                contract=contract,
                action='DOCUMENT_UPLOAD',
                user=request.user,
                details=f'Document "{document.title}" uploaded'
            )
            if contract.contract_type in {ContractType.VENDOR, ContractType.PURCHASE}:
                if contract.status == ContractStatus.DRAFT:
                    contract.status = ContractStatus.SUBMITTED
                    contract.save(update_fields=['status'])
            
            messages.success(request, 'Document added successfully')
        else:
            messages.error(request, 'Error adding document')
    
    return redirect('contract_detail', pk=pk)


@login_required
def add_comment(request, pk):
    """Add comment to contract"""
    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=pk)
        
        if not can_add_comment(request.user, contract):
            messages.error(request, 'You do not have permission to add comments')
            return redirect('contract_detail', pk=pk)

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.contract = contract
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added successfully')
        else:
            messages.error(request, 'Error adding comment')
    
    return redirect('contract_detail', pk=pk)

def _generate_contract_draft(contract, user=None, is_regeneration=False):
    """Generate draft from active template and stored data"""
    contract_data = contract.structured_data_versions.first()
    if not contract_data or not contract_data.data:
        return None

    template = ContractTemplate.objects.filter(
        contract_type__code=contract.contract_type,
        active=True
    ).order_by('-version').first()
    if not template:
        return None

    last_version = ContractDraft.objects.filter(contract=contract).aggregate(v=Max('version'))['v'] or 0
    version = last_version + 1

    from .services import TemplateService
    context_data = TemplateService.build_template_context(contract, contract_data.data)

    rendered_html = Template(template.content).render(Context(context_data))
    file_name = f"contract_{slugify(contract.title)}_draft_v{version}.html"

    draft = ContractDraft(contract=contract, template=template, version=version)
    draft.file.save(file_name, ContentFile(rendered_html.encode('utf-8')), save=False)
    draft.save()

    AuditLog.objects.create(
        contract=contract,
        user=user,
        action='DRAFT_UPDATED' if is_regeneration else 'DRAFT_GENERATED',
        details=f"Draft v{version} generated from template {template.name} (v{template.version})"
    )

    EmailService.send_draft_generated_email(contract, draft, updated=is_regeneration)

    return draft


@login_required
def contract_data_input(request, pk):
    """Capture structured data based on contract type fields"""
    contract = get_object_or_404(Contract, pk=pk)

    if not can_edit_contract_data(request.user, contract):
        messages.error(request, 'You do not have permission to edit this contract data')
        return redirect('contract_detail', pk=pk)

    type_def = ContractTypeDefinition.objects.filter(code=contract.contract_type, active=True).first()
    if not type_def:
        messages.error(request, 'No contract type definition found for this contract')
        return redirect('contract_detail', pk=pk)

    field_definitions = type_def.fields.all().order_by('position', 'label')
    if not field_definitions:
        if request.user.is_staff:
            messages.warning(request, f'No fields configured for {contract.get_contract_type_display()}. Please add fields in the admin panel first.')
        else:
            messages.error(request, 'This contract type is not yet configured. Please contact an administrator.')
        return redirect('contract_detail', pk=pk)

    initial_data = {}
    latest_data = contract.structured_data_versions.first()
    if latest_data:
        initial_data = latest_data.data
    else:
        # Pre-fill with contract base information
        initial_data = {
            'party_a': contract.party_a,
            'party_b': contract.party_b,
            'party_b_name': contract.party_b,
            'party_b_address': '',
            'delivery_address': '',
            'business_form': '',
            'contract_start_date': contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
            'contract_end_date': contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
            'contract_value': str(contract.contract_value) if contract.contract_value else '',
            'total_purchase_target': str(contract.contract_value) if contract.contract_value else '',
            'quarter_1_period': '',
            'quarter_2_period': '',
            'quarter_3_period': '',
            'quarter_4_period': '',
        }

    if request.method == 'POST':
        form = ContractDataForm(request.POST, request.FILES, field_definitions=field_definitions)
        if form.is_valid():
            # Calculate next version
            last_version = contract.structured_data_versions.aggregate(v=Max('version'))['v'] or 0
            next_version = last_version + 1
            
            # Separate file fields from regular data
            clean_data = {}
            file_fields = []
            for key, value in form.cleaned_data.items():
                field_def = field_definitions.filter(field_key=key).first()
                if field_def and field_def.field_type == 'file' and value:
                    file_fields.append((key, value))
                    clean_data[key] = value.name  # Store filename in JSON
                else:
                    clean_data[key] = str(value) if value else ''
            
            # Create new data version
            contract_data = ContractData.objects.create(
                contract=contract,
                data=clean_data,
                version=next_version,
                submitted_by=request.user
            )
            
            # Save uploaded files
            for field_key, file_obj in file_fields:
                ContractDataFile.objects.create(
                    contract_data=contract_data,
                    field_key=field_key,
                    file=file_obj
                )

            # Update annual and quarterly targets for sales agreements
            if contract.is_sales_agreement:
                from .services import ContractTargetService
                ContractTargetService.upsert_targets(
                    contract,
                    clean_data.get('annual_target')
                )

            if contract.status == ContractStatus.DRAFT:
                contract.status = ContractStatus.SUBMITTED
                contract.save(update_fields=['status'])

            AuditLog.objects.create(
                contract=contract,
                user=request.user,
                action='DATA_SUBMITTED',
                details='Structured data submitted'
            )

            EmailService.send_data_submitted_email(contract, request.user)

            draft = _generate_contract_draft(contract, user=request.user)
            if draft:
                messages.success(request, 'Data saved and draft generated successfully')
            else:
                messages.warning(request, 'Data saved, but no active template found to generate draft')

            return redirect('contract_detail', pk=pk)
    else:
        form = ContractDataForm(field_definitions=field_definitions, initial=initial_data)

    context = {
        'contract': contract,
        'form': form,
        'field_definitions': field_definitions,
    }
    return render(request, 'contracts/contract_data_form.html', context)


@login_required
def regenerate_contract_draft(request, pk):
    """Allow legal/admin to regenerate draft when template changes"""
    contract = get_object_or_404(Contract, pk=pk)

    if not can_regenerate_draft(request.user, contract):
        messages.error(request, 'You do not have permission to regenerate drafts')
        return redirect('contract_detail', pk=pk)

    latest_data = contract.structured_data_versions.first()
    if not latest_data or not latest_data.data:
        messages.error(request, 'Cannot regenerate draft without submitted data')
        return redirect('contract_detail', pk=pk)

    draft = _generate_contract_draft(contract, user=request.user, is_regeneration=True)
    if draft:
        messages.success(request, f'Draft v{draft.version} regenerated successfully')
    else:
        messages.error(request, 'No active template available for this contract type')

    return redirect('contract_detail', pk=pk)


@login_required
def expiring_contracts(request):
    """View contracts expiring soon"""
    today = timezone.now().date()
    
    days_filter = request.GET.get('days', '30')
    try:
        days = int(days_filter)
    except ValueError:
        days = 30
    
    contracts = Contract.objects.filter(
        Q(owner=request.user) | Q(participants__user=request.user),
        end_date__gte=today,
        end_date__lte=today + timedelta(days=days),
        status__in=[ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
    ).distinct().order_by('end_date')
    
    context = {
        'contracts': contracts,
        'days': days,
    }
    
    return render(request, 'contracts/expiring_contracts.html', context)


@login_required
def terminated_contracts(request):
    """View terminated contracts"""
    contracts = Contract.objects.filter(
        Q(owner=request.user) | Q(participants__user=request.user),
        status=ContractStatus.TERMINATED
    ).distinct().order_by('-updated_at')
    
    return render(request, 'contracts/terminated_contracts.html', {'contracts': contracts})
