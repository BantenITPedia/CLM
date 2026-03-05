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
    ContractTypeDefinition, ContractDataFile, ContractType,
    BusinessEntityDocument, CompanyProfile, DocumentRevisionRequest
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
    get_allowed_next_statuses,
    can_transition_to_status,
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
    
    # Get user's contracts (or all if staff/admin)
    if request.user.is_staff or request.user.is_superuser:
        user_contracts = Contract.objects.all()
    else:
        user_contracts = Contract.objects.filter(
            Q(owner=request.user) | Q(participants__user=request.user)
        ).distinct()
    
    # Statistics
    total_contracts = user_contracts.count()
    active_contracts = user_contracts.filter(status__in=[ContractStatus.ACTIVE, ContractStatus.APPROVED]).count()
    expiring_soon_contracts = user_contracts.filter(status=ContractStatus.EXPIRING_SOON).count()
    legal_review_contracts = user_contracts.filter(status=ContractStatus.LEGAL_REVIEW).count()
    draft_contracts = user_contracts.filter(status=ContractStatus.DRAFT).count()
    
    # Expiring in different periods (APPROVED, ACTIVE or EXPIRING_SOON contracts)
    expiring_30 = user_contracts.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30),
        status__in=[ContractStatus.APPROVED, ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
    ).count()
    
    expiring_60 = user_contracts.filter(
        end_date__gte=today + timedelta(days=31),
        end_date__lte=today + timedelta(days=60),
        status__in=[ContractStatus.APPROVED, ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
    ).count()
    
    expiring_90 = user_contracts.filter(
        end_date__gte=today + timedelta(days=61),
        end_date__lte=today + timedelta(days=90),
        status__in=[ContractStatus.APPROVED, ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON]
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
        'draft_contracts': draft_contracts,
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
    # Staff/Admin users see all contracts; regular users see only their own
    if request.user.is_staff or request.user.is_superuser:
        contracts = Contract.objects.all().order_by('-created_at')
    else:
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
                from .models import CompanyProfile
                company = CompanyProfile.get_active()
                contract.party_a = company.name if company else "PT. Your Company Name"
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
    business_entity_documents = contract.business_entity_documents.all()
    open_revision_document_ids = list(
        DocumentRevisionRequest.objects.filter(
            document__contract=contract,
            status__in=[
                DocumentRevisionRequest.RevisionStatus.PENDING,
                DocumentRevisionRequest.RevisionStatus.REVISED,
            ]
        ).values_list('document_id', flat=True).distinct()
    )
    comments = contract.comments.all()
    audit_logs = contract.audit_logs.order_by('-timestamp')[:20]
    contract_data = contract.structured_data_versions.first()
    all_data_versions = contract.structured_data_versions.all()
    drafts = contract.drafts.all()
    
    allowed_next_statuses = get_allowed_next_statuses(request.user, contract)
    can_update_status = bool(allowed_next_statuses)

    # Check if user can upload final document (only after legal approval)
    can_upload_final = (
        has_contract_permission(request.user, contract, 'upload_final_document')
        and contract.status in [ContractStatus.APPROVED, ContractStatus.ACTIVE]
    )
    
    # Forms
    comment_form = CommentForm()
    document_form = ContractDocumentForm()
    participant_form = ContractParticipantForm()
    status_form = ContractStatusUpdateForm(instance=contract, user=request.user, contract=contract)
    
    # Final approved document form
    from .forms import FinalApprovedDocumentForm
    final_approval_form = FinalApprovedDocumentForm()
    
    context = {
        'contract': contract,
        'participants': participants,
        'documents': documents,
        'business_entity_documents': business_entity_documents,
        'open_revision_document_ids': open_revision_document_ids,
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
        'can_update_status': can_update_status,
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

    if contract.status not in [ContractStatus.APPROVED, ContractStatus.ACTIVE]:
        messages.error(request, 'Final signed document can only be uploaded after Legal Approval (Approved status)')
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

            previous_status = contract.status
            status_changed = False
            if contract.status != ContractStatus.ACTIVE:
                contract.status = ContractStatus.ACTIVE
                contract.save(update_fields=['status'])
                status_changed = True
            
            # Log action
            AuditLog.objects.create(
                contract=contract,
                action='FINAL_DOCUMENT_UPLOAD',
                user=request.user,
                details=f'Final contract document uploaded: {final_doc.document.name}'
            )

            if status_changed:
                AuditLog.objects.create(
                    contract=contract,
                    action='STATUS_CHANGE',
                    user=request.user,
                    old_value=previous_status,
                    new_value=ContractStatus.ACTIVE,
                    details='Status moved to Active after signed final document upload'
                )

            EmailService.send_contract_signed_email(contract, request.user)
            
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

        if not can_update_contract_status(request.user, contract):
            messages.error(request, 'You do not have permission to update this contract')
            return redirect('contract_detail', pk=pk)

        new_status = request.POST.get('status')
        if not can_transition_to_status(request.user, contract, new_status):
            messages.error(request, 'Status transition is not allowed for your role or current workflow state')
            return redirect('contract_detail', pk=pk)

        previous_status = contract.status
        previous_status_label = contract.get_status_display()
        
        form = ContractStatusUpdateForm(request.POST, instance=contract, user=request.user, contract=contract)
        if form.is_valid():
            updated_contract = form.save(commit=False)
            updated_contract.status = new_status
            updated_contract.save()

            new_status_label = updated_contract.get_status_display()

            AuditLog.objects.create(
                contract=updated_contract,
                action='STATUS_CHANGE',
                user=request.user,
                old_value=previous_status,
                new_value=new_status,
                details=f'Status changed from {previous_status_label} to {new_status_label}'
            )

            if new_status == ContractStatus.LEGAL_REVIEW:
                EmailService.send_legal_review_email(updated_contract)
            elif new_status == ContractStatus.APPROVED:
                EmailService.send_contract_approved_email(updated_contract)
            elif (
                new_status == ContractStatus.DRAFT
                and previous_status in [ContractStatus.SUBMITTED, ContractStatus.LEGAL_REVIEW]
            ):
                EmailService.send_data_revision_requested_email(
                    updated_contract,
                    request.user,
                    previous_status_label=previous_status_label,
                )

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


# ===== Contract Creation Wizard =====

@login_required
def contract_wizard_step1(request):
    """
    Step 1: Select Business Entity Type
    Users choose between PT, CV, or Perorangan
    """
    from .forms import BusinessEntityTypeForm
    
    if request.method == 'POST':
        form = BusinessEntityTypeForm(request.POST)
        if form.is_valid():
            # Store entity type in session
            request.session['wizard_entity_type'] = form.cleaned_data['business_entity_type']
            return redirect('contract_wizard_step2')
    else:
        form = BusinessEntityTypeForm()
    
    return render(request, 'contracts/wizard_step1_entity_type.html', {'form': form, 'step': 1})


@login_required
def contract_wizard_step2(request):
    """
    Step 2: Upload Required Documents
    Based on entity type selected in step 1
    """
    from .forms import BusinessEntityDocumentForm
    from .models import BusinessEntityDocument, BusinessDocumentType
    
    # Check if step 1 completed
    entity_type = request.session.get('wizard_entity_type')
    if not entity_type:
        messages.warning(request, 'Please select business entity type first')
        return redirect('contract_wizard_step1')
    
    if request.method == 'POST':
        form = BusinessEntityDocumentForm(request.POST, request.FILES, entity_type=entity_type)
        if form.is_valid():
            # Get company profile for Party A
            from .models import CompanyProfile
            company = CompanyProfile.get_active()
            
            # Create a temporary contract record to attach documents
            contract = Contract.objects.create(
                title='Draft Contract - Pending',
                contract_type=ContractType.OTHER,
                party_a=company.name if company else 'PT. Your Company Name',
                party_b='To be specified',
                created_by=request.user,
                owner=request.user,
                business_entity_type=entity_type,
                status=ContractStatus.DRAFT
            )
            
            # Save uploaded documents
            from .models import BusinessDocumentType
            doc_mapping = {
                'akta_pendirian': BusinessDocumentType.AKTA_PENDIRIAN,
                'npwp': BusinessDocumentType.NPWP,
                'nib': BusinessDocumentType.NIB,
                'ktp_penanggung_jawab': BusinessDocumentType.KTP_PENANGGUNG_JAWAB,
                'perizinan_lainnya': BusinessDocumentType.PERIZINAN_LAINNYA,
                'ktp': BusinessDocumentType.KTP,
            }
            
            for field_name, doc_type in doc_mapping.items():
                if field_name in form.cleaned_data and form.cleaned_data[field_name]:
                    BusinessEntityDocument.objects.create(
                        contract=contract,
                        document_type=doc_type,
                        document=form.cleaned_data[field_name],
                        uploaded_by=request.user
                    )
            
            # Store contract ID in session for step 3
            request.session['wizard_contract_id'] = contract.id
            messages.success(request, 'Documents uploaded successfully. Now fill in contract details.')
            return redirect('contract_wizard_step3')
    else:
        form = BusinessEntityDocumentForm(entity_type=entity_type)
    
    # Get display name for entity type
    from .models import BusinessEntityType
    entity_display = dict(BusinessEntityType.choices).get(entity_type, entity_type)
    
    context = {
        'form': form,
        'entity_type': entity_type,
        'entity_display': entity_display,
        'step': 2
    }
    
    return render(request, 'contracts/wizard_step2_documents.html', context)


@login_required
def contract_wizard_step3(request):
    """
    Step 3: Fill Basic Contract Information
    Reuses existing contract form but updates the draft contract from step 2
    """
    # Check if previous steps completed
    contract_id = request.session.get('wizard_contract_id')
    if not contract_id:
        messages.warning(request, 'Please complete document upload first')
        return redirect('contract_wizard_step2')
    
    contract = get_object_or_404(Contract, id=contract_id, created_by=request.user)

    contract_type_code = request.POST.get('contract_type') or request.GET.get('contract_type') or contract.contract_type

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)

        if form.is_valid():
            contract = form.save(commit=False)
            # Party A should already be set from step 2, keep owner/creator
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

            # Move to step 4 for structured data
            return redirect('contract_wizard_step4')
        else:
            return render(
                request,
                'contracts/wizard_step3_contract_info.html',
                {
                    'form': form,
                    'action': 'Create',
                    'contract_type_code': contract_type_code,
                    'step': 3
                }
            )

    form = ContractForm(instance=contract, initial={'contract_type': contract_type_code})

    context = {
        'form': form,
        'action': 'Create',
        'contract_type_code': contract_type_code,
        'step': 3
    }

    return render(request, 'contracts/wizard_step3_contract_info.html', context)


@login_required
def contract_wizard_step4(request):
    """
    Step 4: Fill Structured Data (Required)
    This step handles the contract-specific structured data fields
    """
    # Check if previous steps completed
    contract_id = request.session.get('wizard_contract_id')
    if not contract_id:
        messages.warning(request, 'Please complete contract information first')
        return redirect('contract_wizard_step3')
    
    contract = get_object_or_404(Contract, id=contract_id, created_by=request.user)
    
    def get_field_definitions(contract_type_code):
        type_def = ContractTypeDefinition.objects.filter(
            code=contract_type_code,
            active=True
        ).first()
        if not type_def or not type_def.is_template_based:
            return None
        return type_def.fields.all().order_by('position', 'label')

    def apply_gt_defaults(contract_instance, data_dict):
        """Auto-populate GT-specific fields from contract metadata"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta

        def add_months(start_date, n_months):
            return start_date + relativedelta(months=n_months)

        def format_currency_idr(value):
            """Format currency in Indonesian Rupiah style"""
            try:
                if isinstance(value, str):
                    value = value.replace('.', '').replace(',', '')
                value = float(value)
                return f"Rp {value:,.0f}".replace(',', '.')
            except (ValueError, TypeError):
                return "Rp 0"

        if not data_dict.get('party_a_name'):
            data_dict['party_a_name'] = contract_instance.party_a
        if not data_dict.get('party_b_name'):
            data_dict['party_b_name'] = contract_instance.party_b

        if contract_instance.contract_value and not data_dict.get('target_value'):
            data_dict['target_value'] = format_currency_idr(contract_instance.contract_value)

        if contract_instance.start_date:
            start_date = contract_instance.start_date
            if not data_dict.get('effective_date'):
                data_dict['effective_date'] = start_date.strftime('%d %B %Y')

            if not data_dict.get('contract_year'):
                data_dict['contract_year'] = start_date.strftime('%Y')

            q1_start = start_date
            q2_start = add_months(start_date, 3)
            q3_start = add_months(start_date, 6)
            q4_start = add_months(start_date, 9)

            q1_end = q2_start - timedelta(days=1)
            q2_end = q3_start - timedelta(days=1)
            q3_end = q4_start - timedelta(days=1)
            q4_end = contract_instance.end_date if contract_instance.end_date else add_months(start_date, 12) - timedelta(days=1)

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

    contract_type_code = contract.contract_type
    field_definitions = get_field_definitions(contract_type_code)
    
    # If no structured data fields defined, skip this step
    if not field_definitions:
        # Clear wizard session data
        request.session.pop('wizard_entity_type', None)
        request.session.pop('wizard_contract_id', None)
        messages.success(request, f'Contract "{contract.title}" created successfully!')
        return redirect('contract_detail', pk=contract.pk)

    if request.method == 'POST':
        data_form = ContractDataForm(request.POST, request.FILES, field_definitions=field_definitions)

        if data_form.is_valid():
            clean_data = {k: str(v) if v else '' for k, v in data_form.cleaned_data.items()}
            auto_data = apply_gt_defaults(contract, clean_data)

            ContractData.objects.create(
                contract=contract,
                data=auto_data,
                version=1,
                submitted_by=request.user
            )

            if contract.status == ContractStatus.DRAFT:
                contract.status = ContractStatus.LEGAL_REVIEW
                contract.save(update_fields=['status'])

            AuditLog.objects.create(
                contract=contract,
                user=request.user,
                action='LEGAL_REVIEW_REQUESTED',
                details='Contract submitted to legal team for review'
            )

            EmailService.send_legal_review_email(contract)
            _generate_contract_draft(contract, user=request.user)

            # Clear wizard session data
            request.session.pop('wizard_entity_type', None)
            request.session.pop('wizard_contract_id', None)

            messages.success(request, f'Contract "{contract.title}" created successfully!')
            return redirect('contract_detail', pk=contract.pk)
    else:
        data_form = ContractDataForm(field_definitions=field_definitions)

    # Pre-fill with auto-populated data for preview
    initial_data = apply_gt_defaults(contract, {})
    
    context = {
        'contract': contract,
        'data_form': data_form,
        'initial_data': initial_data,
        'step': 4
    }

    return render(request, 'contracts/wizard_step4_structured_data.html', context)


@login_required
def contract_wizard_cancel(request):
    """Cancel wizard and clean up"""
    # Delete draft contract if exists
    contract_id = request.session.get('wizard_contract_id')
    if contract_id:
        try:
            contract = Contract.objects.get(id=contract_id, created_by=request.user, status=ContractStatus.DRAFT)
            contract.delete()
        except Contract.DoesNotExist:
            pass
    
    # Clear session
    request.session.pop('wizard_entity_type', None)
    request.session.pop('wizard_contract_id', None)
    
    messages.info(request, 'Contract creation cancelled')
    return redirect('dashboard')


# ===== Company Settings =====

@login_required
@login_required
def company_settings(request):
    """
    Manage company profile (Party A information)
    Only accessible to admin/staff users
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access company settings')
        return redirect('dashboard')
    
    from .models import CompanyProfile
    company = CompanyProfile.get_active()
    
    # If no company profile exists, create one
    if not company:
        company = CompanyProfile.objects.create(
            name='Your Company Name',
            business_entity_type='PT',
            is_active=True,
            updated_by=request.user
        )
    
    if request.method == 'POST':
        company.name = request.POST.get('name', company.name)
        company.short_name = request.POST.get('short_name', '')
        company.business_entity_type = request.POST.get('business_entity_type', company.business_entity_type)
        company.address = request.POST.get('address', '')
        company.phone = request.POST.get('phone', '')
        company.email = request.POST.get('email', '')
        company.website = request.POST.get('website', '')
        company.npwp = request.POST.get('npwp', '')
        company.nib = request.POST.get('nib', '')
        company.akta_pendirian_number = request.POST.get('akta_pendirian_number', '')
        company.legal_representative_name = request.POST.get('legal_representative_name', '')
        company.legal_representative_title = request.POST.get('legal_representative_title', '')
        company.updated_by = request.user
        
        company.save()
        messages.success(request, 'Company profile updated successfully')
        return redirect('company_settings')
    
    from .models import BusinessEntityType
    entity_choices = BusinessEntityType.choices
    
    context = {
        'company': company,
        'entity_choices': entity_choices,
    }
    
    return render(request, 'contracts/company_settings.html', context)


@login_required
def permission_matrix(request):
    """
    Display role-permission matrix for staff users
    Shows which roles have which permissions in an easy-to-read table
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view permissions')
        return redirect('dashboard')
    
    from .models import ContractRolePermission, ParticipantRole, ContractPermission
    from collections import defaultdict
    
    # Get all permissions from database or use defaults
    db_permissions = ContractRolePermission.objects.all()
    
    # Build permission matrix
    matrix = defaultdict(dict)
    
    if db_permissions.exists():
        # Use database values
        for perm in db_permissions:
            matrix[perm.permission][perm.role] = perm.allowed
    else:
        # Use default PERMISSION_ROLE_MAP  
        from .permissions import PERMISSION_ROLE_MAP
        for permission, allowed_roles in PERMISSION_ROLE_MAP.items():
            for role in ParticipantRole:
                matrix[permission][role] = role in allowed_roles
    
    # Prepare data for template
    roles = [role for role in ParticipantRole]
    permissions = [perm for perm in ContractPermission]
    
    # Role descriptions
    role_descriptions = {
        'OWNER': 'Contract creator/owner',
        'SALES': 'Sales representative',
        'LEGAL': 'Legal team reviewer',
        'CUSTOMER': 'External customer',
        'SIGNATORY': 'Authorized signer',
        'APPROVER': 'Final approver'
    }
    
    context = {
        'roles': roles,
        'permissions': permissions,
        'matrix': matrix,
        'role_descriptions': role_descriptions,
        'total_permissions': len(permissions),
        'total_roles': len(roles),
    }
    
    return render(request, 'contracts/permission_matrix.html', context)


@login_required
def request_document_revision(request, contract_id, document_id):
    """
    Legal reviewer requests a document to be revised/corrected
    """
    contract = get_object_or_404(Contract, id=contract_id)
    document = get_object_or_404(BusinessEntityDocument, id=document_id, contract=contract)
    
    # Check if user is legal reviewer
    if not can_update_contract_status(request.user, contract):
        messages.error(request, "You don't have permission to request document revisions.")
        return redirect('contract_detail', pk=contract_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, "Please provide a reason for the revision request.")
            return redirect('contract_detail', pk=contract_id)

        if document.revision_requests.filter(
            status__in=[
                DocumentRevisionRequest.RevisionStatus.PENDING,
                DocumentRevisionRequest.RevisionStatus.REVISED,
            ]
        ).exists():
            messages.warning(request, "This document already has an open revision request.")
            return redirect('contract_detail', pk=contract_id)
        
        # Create revision request
        revision_request = DocumentRevisionRequest.objects.create(
            document=document,
            requested_by=request.user,
            reason=reason
        )

        AuditLog.objects.create(
            contract=contract,
            action='DOCUMENT_REVISION_REQUESTED',
            user=request.user,
            details=(
                f"Revision requested for {document.get_document_type_display()}: {reason}"
            )
        )

        EmailService.send_document_revision_requested_email(
            contract=contract,
            document=document,
            requested_by=request.user,
            reason=reason,
        )
        
        messages.success(request, "Revision request sent to document uploader.")
        return redirect('contract_detail', pk=contract_id)
    
    context = {
        'contract': contract,
        'document': document,
    }
    return render(request, 'contracts/request_document_revision.html', context)


@login_required
def upload_revised_document(request, contract_id, revision_request_id):
    """
    Sales person uploads a revised/corrected document
    """
    contract = get_object_or_404(Contract, id=contract_id)
    revision_request = get_object_or_404(
        DocumentRevisionRequest,
        id=revision_request_id,
        document__contract=contract,
    )
    
    # Check if user is document owner or contract owner
    if request.user != revision_request.document.uploaded_by and request.user != contract.owner:
        messages.error(request, "You don't have permission to upload revisions for this document.")
        return redirect('contract_detail', pk=contract_id)
    
    if request.method == 'POST':
        if revision_request.status != DocumentRevisionRequest.RevisionStatus.PENDING:
            messages.error(request, "This revision request is not in pending state.")
            return redirect('contract_detail', pk=contract_id)

        revised_file = request.FILES.get('revised_document')
        
        if not revised_file:
            messages.error(request, "Please select a file to upload.")
            return redirect('contract_detail', pk=contract_id)
        
        # Update revision request with revised document
        revision_request.revised_document = revised_file
        revision_request.revised_by = request.user
        revision_request.revised_at = timezone.now()
        revision_request.status = DocumentRevisionRequest.RevisionStatus.REVISED
        revision_request.save()

        AuditLog.objects.create(
            contract=contract,
            action='DOCUMENT_REVISION_UPLOADED',
            user=request.user,
            details=(
                f"Revised document uploaded for "
                f"{revision_request.document.get_document_type_display()}"
            )
        )

        EmailService.send_document_revision_uploaded_email(
            contract=contract,
            revision_request=revision_request,
            uploaded_by=request.user,
        )
        
        messages.success(request, "Revised document uploaded successfully. Awaiting legal review.")
        return redirect('contract_detail', pk=contract_id)
    
    context = {
        'contract': contract,
        'revision_request': revision_request,
        'document': revision_request.document,
    }
    return render(request, 'contracts/upload_revised_document.html', context)


@login_required
def approve_revised_document(request, contract_id, revision_request_id):
    """
    Legal reviewer approves the revised document
    """
    contract = get_object_or_404(Contract, id=contract_id)
    revision_request = get_object_or_404(
        DocumentRevisionRequest,
        id=revision_request_id,
        document__contract=contract,
    )
    
    # Check if user is legal reviewer
    if not can_update_contract_status(request.user, contract):
        messages.error(request, "You don't have permission to approve documents.")
        return redirect('contract_detail', pk=contract_id)
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '').strip()

        if not revision_request.revised_document:
            messages.error(request, "No revised document found to approve.")
            return redirect('contract_detail', pk=contract_id)
        
        # Update original document with revised version
        revision_request.document.document = revision_request.revised_document
        revision_request.document.save()
        
        # Mark revision request as approved
        revision_request.status = DocumentRevisionRequest.RevisionStatus.APPROVED
        revision_request.approved_by = request.user
        revision_request.approved_at = timezone.now()
        revision_request.approval_notes = approval_notes
        revision_request.save()

        AuditLog.objects.create(
            contract=contract,
            action='DOCUMENT_REVISION_APPROVED',
            user=request.user,
            details=(
                f"Revised document approved for "
                f"{revision_request.document.get_document_type_display()}"
            )
        )

        EmailService.send_document_revision_result_email(
            contract=contract,
            revision_request=revision_request,
            approved=True,
            reviewed_by=request.user,
            notes=approval_notes,
        )
        
        messages.success(request, "Document approved successfully.")
        return redirect('contract_detail', pk=contract_id)
    
    context = {
        'contract': contract,
        'revision_request': revision_request,
    }
    return render(request, 'contracts/approve_revised_document.html', context)


@login_required
def reject_revised_document(request, contract_id, revision_request_id):
    """
    Legal reviewer rejects the revised document and requires re-submission
    """
    contract = get_object_or_404(Contract, id=contract_id)
    revision_request = get_object_or_404(
        DocumentRevisionRequest,
        id=revision_request_id,
        document__contract=contract,
    )
    
    # Check if user is legal reviewer
    if not can_update_contract_status(request.user, contract):
        messages.error(request, "You don't have permission to reject documents.")
        return redirect('contract_detail', pk=contract_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            messages.error(request, "Please provide a reason for rejection.")
            return redirect('contract_detail', pk=contract_id)

        EmailService.send_document_revision_result_email(
            contract=contract,
            revision_request=revision_request,
            approved=False,
            reviewed_by=request.user,
            notes=rejection_reason,
        )

        # Reset revision request to PENDING so it can be revised again
        revision_request.status = DocumentRevisionRequest.RevisionStatus.PENDING
        revision_request.revised_document = None
        revision_request.revised_by = None
        revision_request.revised_at = None
        revision_request.approval_notes = rejection_reason
        revision_request.save()

        AuditLog.objects.create(
            contract=contract,
            action='DOCUMENT_REVISION_REJECTED',
            user=request.user,
            details=(
                f"Revised document rejected for "
                f"{revision_request.document.get_document_type_display()}: {rejection_reason}"
            )
        )
        
        messages.success(request, "Document rejected. Document uploader has been notified to revise again.")
        return redirect('contract_detail', pk=contract_id)
    
    context = {
        'contract': contract,
        'revision_request': revision_request,
    }
    return render(request, 'contracts/reject_revised_document.html', context)

