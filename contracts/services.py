from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from .models import AuditLog


class EmailService:
    """Centralized email service for all contract-related emails"""
    
    @staticmethod
    def _send_email(subject, template_name, context, recipient_list):
        """Helper method to send emails"""
        try:
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log email sent
            if 'contract' in context:
                AuditLog.objects.create(
                    contract=context['contract'],
                    action='EMAIL_SENT',
                    details=f"Email sent: {subject} to {', '.join(recipient_list)}"
                )
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def _get_participant_emails(contract, roles=None, notification_filter='critical'):
        """Get email addresses of contract participants based on notification preference"""
        participants = contract.participants.filter(is_active=True)
        
        if roles:
            participants = participants.filter(role__in=roles)
        
        # Filter by notification preference
        if notification_filter == 'critical':
            # Only send to 'critical' and 'all' users
            participants = participants.filter(notification_preference__in=['critical', 'all'])
        elif notification_filter == 'all':
            # Only send to 'all' users
            participants = participants.filter(notification_preference='all')
        
        # Get emails - prioritize external_email, fall back to user email
        emails = []
        for p in participants:
            if p.external_email:
                emails.append(p.external_email)
            elif p.user and p.user.email:
                emails.append(p.user.email)
        
        return emails
    
    @staticmethod
    def _get_participants_by_role(contract, roles=None, notification_filter='critical'):
        """Get participant objects by role with notification filtering"""
        participants = contract.participants.filter(is_active=True)
        
        if roles:
            participants = participants.filter(role__in=roles)
        
        if notification_filter == 'critical':
            participants = participants.filter(notification_preference__in=['critical', 'all'])
        elif notification_filter == 'all':
            participants = participants.filter(notification_preference='all')
        
        return participants
    
    @classmethod
    def send_contract_created_email(cls, contract):
        """Send email when contract is created"""
        subject = f"New Contract Created: {contract.title}"
        template_name = 'emails/contract_created.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract)
        if contract.owner and contract.owner.email:
            recipients.append(contract.owner.email)
        recipients = list(set(recipients))  # Remove duplicates
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_customer_invitation_email(cls, contract, user):
        """Send invitation to customer"""
        subject = f"You've been invited to review contract: {contract.title}"
        template_name = 'emails/customer_invitation.html'
        context = {
            'contract': contract,
            'user': user,
            'site_url': settings.SITE_URL,
        }
        recipients = [user.email] if user.email else []
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_legal_review_email(cls, contract):
        """Send email to legal team for review"""
        subject = f"Legal Review Required: {contract.title}"
        template_name = 'emails/legal_review.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract, roles=['LEGAL', 'APPROVER'])
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_contract_approved_email(cls, contract):
        """Send email when contract is approved"""
        subject = f"Contract Approved: {contract.title}"
        template_name = 'emails/contract_approved.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract)
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_signature_request_email(cls, contract):
        """Send signature request to signatories"""
        subject = f"Signature Required: {contract.title}"
        template_name = 'emails/signature_request.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract, roles=['SIGNATORY'])
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_contract_signed_email(cls, contract, signer):
        """Send email when contract is signed"""
        subject = f"Contract Signed: {contract.title}"
        template_name = 'emails/contract_signed.html'
        context = {
            'contract': contract,
            'signer': signer,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract)
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_contract_activated_email(cls, contract):
        """Send email when contract becomes active"""
        subject = f"Contract Activated: {contract.title}"
        template_name = 'emails/contract_activated.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract)
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_expiry_reminder_email(cls, contract):
        """Send reminder for expiring contract"""
        subject = f"Contract Expiring Soon: {contract.title}"
        template_name = 'emails/expiry_reminder.html'
        context = {
            'contract': contract,
            'days_remaining': contract.days_until_expiry,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract, roles=['OWNER', 'APPROVER'])
        if contract.owner and contract.owner.email:
            recipients.append(contract.owner.email)
        recipients = list(set(recipients))
        
        if recipients:
            AuditLog.objects.create(
                contract=contract,
                action='RENEWAL_REMINDER',
                details=f"Expiry reminder sent - {contract.days_until_expiry} days remaining"
            )
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_contract_expired_email(cls, contract):
        """Send email when contract expires"""
        subject = f"Contract Expired: {contract.title}"
        template_name = 'emails/contract_expired.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(contract, roles=['OWNER', 'APPROVER'])
        if contract.owner and contract.owner.email:
            recipients.append(contract.owner.email)
        recipients = list(set(recipients))
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_renewal_created_email(cls, contract, parent_contract):
        """Send email when renewal contract is created"""
        subject = f"Renewal Contract Created: {contract.title}"
        template_name = 'emails/renewal_created.html'
        context = {
            'contract': contract,
            'parent_contract': parent_contract,
            'site_url': settings.SITE_URL,
        }
        recipients = cls._get_participant_emails(parent_contract, roles=['OWNER', 'APPROVER'])
        
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)

    @classmethod
    def send_data_submitted_email(cls, contract, user):
        """Notify legal/admin that structured data was submitted - CRITICAL ACTION"""
        subject = f"[ACTION] Data Submitted for Contract: {contract.title}"
        template_name = 'emails/data_submitted.html'
        context = {
            'contract': contract,
            'user': user,
            'site_url': settings.SITE_URL,
        }
        # Send to LEGAL/APPROVER with 'critical' or 'all' preference
        recipients = cls._get_participant_emails(contract, roles=['LEGAL', 'APPROVER'], notification_filter='critical')
        if contract.owner and contract.owner.email:
            recipients.append(contract.owner.email)
        recipients = list(set(filter(None, recipients)))
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)

    @classmethod
    def send_draft_generated_email(cls, contract, draft, updated=False):
        """Notify stakeholders when a draft is generated or updated - CRITICAL ACTION"""
        status_text = 'Updated' if updated else 'Generated'
        subject = f"[DRAFT] {status_text}: {contract.title} (v{draft.version})"
        template_name = 'emails/draft_generated.html'
        context = {
            'contract': contract,
            'draft': draft,
            'updated': updated,
            'site_url': settings.SITE_URL,
        }
        # Send to all participants with 'critical' or 'all' preference
        recipients = cls._get_participant_emails(contract, notification_filter='critical')
        if contract.owner and contract.owner.email:
            recipients.append(contract.owner.email)
        recipients = list(set(filter(None, recipients)))
        if recipients:
            return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_signature_request_to_participant(cls, contract, participant):
        """Send signature request to specific participant - CRITICAL ACTION"""
        if not participant.email:
            return False
        
        subject = f"[ACTION REQUIRED] Signature Needed: {contract.title}"
        template_name = 'emails/signature_request_participant.html'
        context = {
            'contract': contract,
            'participant': participant,
            'participant_name': participant.name,
            'site_url': settings.SITE_URL,
        }
        
        # Only send if they opted in
        if participant.notification_preference != 'none':
            return cls._send_email(subject, template_name, context, [participant.email])
    
    @classmethod
    def send_approval_request_to_participant(cls, contract, participant):
        """Send approval request to specific participant - CRITICAL ACTION"""
        if not participant.email:
            return False
        
        subject = f"[ACTION REQUIRED] Approval Needed: {contract.title}"
        template_name = 'emails/approval_request_participant.html'
        context = {
            'contract': contract,
            'participant': participant,
            'participant_name': participant.name,
            'site_url': settings.SITE_URL,
        }
        
        # Only send if they opted in
        if participant.notification_preference != 'none':
            return cls._send_email(subject, template_name, context, [participant.email])
    
    @classmethod
    def send_expiry_reminder_email(cls, contract, recipients=None):
        """Send expiry reminder email to configured recipients"""
        if recipients is None:
            recipients = cls._get_participant_emails(contract, notification_filter='critical')
        
        if not recipients:
            return False
        
        subject = f"Reminder: Contract Expiring Soon - {contract.title}"
        template_name = 'emails/expiry_reminder.html'
        context = {
            'contract': contract,
            'days_until_expiry': contract.days_until_expiry,
            'site_url': settings.SITE_URL,
        }
        
        return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_signature_pending_reminder(cls, contract, recipients=None):
        """Send reminder for pending signatures"""
        if recipients is None:
            # Focus on signatories
            recipients = cls._get_participant_emails(
                contract,
                roles=['SIGNATORY'],
                notification_filter='critical'
            )
        
        if not recipients:
            return False
        
        subject = f"[ACTION REQUIRED] Pending Signature - {contract.title}"
        template_name = 'emails/signature_request.html'
        context = {
            'contract': contract,
            'site_url': settings.SITE_URL,
        }
        
        return cls._send_email(subject, template_name, context, recipients)
    
    @classmethod
    def send_renewal_reminder(cls, contract, recipients=None):
        """Send renewal notification reminder"""
        if recipients is None:
            recipients = cls._get_participant_emails(contract, notification_filter='critical')
        
        if not recipients:
            return False
        
        subject = f"Renewal Coming Up - {contract.title}"
        template_name = 'emails/renewal_created.html'
        context = {
            'contract': contract,
            'end_date': contract.end_date,
            'site_url': settings.SITE_URL,
        }
        
        return cls._send_email(subject, template_name, context, recipients)


class ContractTargetService:
    """Service for calculating and managing quarterly targets for sales agreements"""

    @staticmethod
    def _add_months(source_date, months):
        """Add months to a date without external dependencies"""
        from datetime import date
        import calendar

        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    @staticmethod
    def calculate_quarters(start_date, end_date=None):
        """
        Calculate 4 quarters based on contract start date (no calendar year assumptions).

        Returns list of (quarter_number, start_date, end_date) tuples.
        """
        from datetime import timedelta

        if not start_date:
            return []

        quarters = []
        for i in range(1, 5):
            q_start = ContractTargetService._add_months(start_date, (i - 1) * 3)
            q_end = ContractTargetService._add_months(start_date, i * 3) - timedelta(days=1)

            if end_date and end_date < q_start:
                break

            if end_date and end_date < q_end:
                q_end = end_date

            quarters.append((i, q_start, q_end))

        return quarters

    @staticmethod
    def upsert_targets(contract, annual_target):
        """Create/update annual and quarterly targets for a sales agreement"""
        from decimal import Decimal, InvalidOperation
        from .models import ContractTarget, ContractQuarter

        if not contract.is_sales_agreement:
            return None

        if annual_target in (None, ''):
            return None

        try:
            annual_target_decimal = Decimal(str(annual_target))
        except (InvalidOperation, TypeError):
            return None

        target, _ = ContractTarget.objects.update_or_create(
            contract=contract,
            defaults={'annual_target': annual_target_decimal}
        )

        quarters = ContractTargetService.calculate_quarters(
            contract.start_date,
            contract.end_date
        )

        # Clear existing quarters to recalculate
        ContractQuarter.objects.filter(contract=contract).delete()

        if not quarters:
            return target

        base = (annual_target_decimal / Decimal('4')).quantize(Decimal('0.01'))
        running_total = Decimal('0.00')

        for quarter_number, start_date, end_date in quarters:
            if quarter_number < 4:
                amount = base
                running_total += amount
            else:
                amount = (annual_target_decimal - running_total).quantize(Decimal('0.01'))

            ContractQuarter.objects.create(
                contract=contract,
                quarter_number=quarter_number,
                start_date=start_date,
                end_date=end_date,
                target_amount=amount
            )

        return target

    @staticmethod
    def get_quarter_context(contract):
        """Return quarterly target context for templates"""
        from .models import ContractQuarter, ContractTarget

        quarters = list(
            ContractQuarter.objects.filter(contract=contract).order_by('quarter_number')
        )
        target = ContractTarget.objects.filter(contract=contract).first()

        quarter_context = []
        for q in quarters:
            quarter_context.append({
                'quarter_number': q.quarter_number,
                'start_date': q.start_date,
                'end_date': q.end_date,
                'target_amount': q.target_amount,
            })

        context = {
            'annual_target': target.annual_target if target else None,
            'quarters': quarter_context,
        }

        # Convenience fields: q1_start, q1_end, q1_target, etc.
        for q in quarters:
            context[f'q{q.quarter_number}_start'] = q.start_date
            context[f'q{q.quarter_number}_end'] = q.end_date
            context[f'q{q.quarter_number}_target'] = q.target_amount

        return context


class TemplateService:
    """Service for loading, validating, and rendering contract templates"""
    
    @staticmethod
    def get_template_for_contract_type(contract_type_code):
        """
        Load the active template for a given contract type.
        
        Args:
            contract_type_code: Contract type code (e.g., 'GENERAL_TRADE')
            
        Returns:
            ContractTemplate instance or None if not found
            
        Raises:
            ValueError if contract type is non-template based
        """
        from .models import ContractTypeDefinition, ContractTemplate
        
        # Verify contract type exists and is template-based
        type_def = ContractTypeDefinition.objects.filter(
            code=contract_type_code,
            active=True
        ).first()
        
        if not type_def:
            raise ValueError(f"Contract type '{contract_type_code}' not found or inactive")
        
        if not type_def.is_template_based:
            raise ValueError(
                f"Contract type '{contract_type_code}' does not use templates. "
                f"This contract type requires document upload."
            )
        
        # Get active template for this type
        template = ContractTemplate.objects.filter(
            contract_type=type_def,
            active=True
        ).order_by('-version').first()
        
        if not template:
            raise ValueError(
                f"No active template found for contract type '{contract_type_code}'. "
                f"Please create or activate a template in admin."
            )
        
        return template
    
    @staticmethod
    def build_template_context(contract, contract_data_dict):
        """
        Build the context dictionary for template rendering.
        
        Combines contract metadata with submitted form data.
        
        Args:
            contract: Contract instance
            contract_data_dict: Dictionary of field values from form submission
            
        Returns:
            Dictionary with all variables for template injection
        """
        from datetime import timedelta
        from decimal import Decimal
        from django.utils import timezone

        quarter_context = ContractTargetService.get_quarter_context(contract)
        
        context = {
            # Contract metadata
            'contract': contract,
            'contract_id': contract.id,
            'contract_title': contract.title,
            'contract_type': contract.get_contract_type_display(),
            'party_a': contract.party_a,
            'party_b': contract.party_b,
            'contract_value': contract.contract_value,
            'start_date': contract.start_date,
            'end_date': contract.end_date,
            'created_at': contract.created_at,
            'owner': contract.owner,
            
            # System dates
            'today': timezone.now().date(),
            'generated_date': timezone.now(),
            
            # Form-submitted data
            **contract_data_dict
        }

        # Ensure key GT template variables have defaults
        if not context.get('party_b_name') and contract.party_b:
            context['party_b_name'] = contract.party_b

        # Alias keys for alternate template variable names
        if not context.get('party_b_legal_name') and context.get('party_b_name'):
            context['party_b_legal_name'] = context.get('party_b_name')

        if not context.get('party_b_registered_address') and context.get('party_b_address'):
            context['party_b_registered_address'] = context.get('party_b_address')

        if not context.get('party_b_authorized_representative_name') and context.get('party_b_representative_name'):
            context['party_b_authorized_representative_name'] = context.get('party_b_representative_name')

        if not context.get('party_b_authorized_representative_title') and context.get('party_b_representative_title'):
            context['party_b_authorized_representative_title'] = context.get('party_b_representative_title')

        if not context.get('contract_number'):
            context['contract_number'] = str(contract.id)

        # Format dates in Indonesian (DD Bulan YYYY)
        def format_date_indonesian(date_obj):
            """Format date as DD Bulan YYYY in Indonesian"""
            months = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }
            return f"{date_obj.day} {months[date_obj.month]} {date_obj.year}"
        
        def format_number_with_separator(num_str):
            """Format number with thousand separator using dots: Rp. xxx.xxx.xxx"""
            try:
                num = int(float(num_str))
                return f"Rp. {num:,}".replace(',', '.')
            except:
                return num_str

        if not context.get('contract_signing_date'):
            today = timezone.now().date()
            context['contract_signing_date'] = format_date_indonesian(today)

        if not context.get('contract_start_date') and contract.start_date:
            context['contract_start_date'] = format_date_indonesian(contract.start_date)

        if not context.get('contract_effective_start_date') and context.get('contract_start_date'):
            context['contract_effective_start_date'] = context.get('contract_start_date')

        if not context.get('contract_end_date') and contract.end_date:
            context['contract_end_date'] = format_date_indonesian(contract.end_date)

        if not context.get('contract_effective_end_date') and context.get('contract_end_date'):
            context['contract_effective_end_date'] = context.get('contract_end_date')

        if not context.get('total_purchase_target') and contract.contract_value:
            context['total_purchase_target'] = str(contract.contract_value)

        if not context.get('total_annual_purchase_target') and context.get('total_purchase_target'):
            context['total_annual_purchase_target'] = context.get('total_purchase_target')
        
        # Format total purchase target with thousand separator
        if context.get('total_purchase_target'):
            context['total_purchase_target_formatted'] = format_number_with_separator(context.get('total_purchase_target'))

        total_target = context.get('total_purchase_target')
        if total_target:
            try:
                total_decimal = Decimal(str(total_target))
                base = total_decimal // Decimal('4')
                remainder = total_decimal - (base * 4)

                if not context.get('sales_target_q1'):
                    context['sales_target_q1'] = str(base)
                if not context.get('sales_target_q2'):
                    context['sales_target_q2'] = str(base)
                if not context.get('sales_target_q3'):
                    context['sales_target_q3'] = str(base)
                if not context.get('sales_target_q4'):
                    context['sales_target_q4'] = str(base + remainder)
                
                # Format sales targets with thousand separator
                if not context.get('sales_target_q1_formatted'):
                    context['sales_target_q1_formatted'] = format_number_with_separator(context.get('sales_target_q1'))
                if not context.get('sales_target_q2_formatted'):
                    context['sales_target_q2_formatted'] = format_number_with_separator(context.get('sales_target_q2'))
                if not context.get('sales_target_q3_formatted'):
                    context['sales_target_q3_formatted'] = format_number_with_separator(context.get('sales_target_q3'))
                if not context.get('sales_target_q4_formatted'):
                    context['sales_target_q4_formatted'] = format_number_with_separator(context.get('sales_target_q4'))
            except Exception:
                pass

        if contract.start_date:
            start_date = contract.start_date
            
            # Calculate end date: 12 months from start month/year (ignore day)
            # If start is February 2026, end is January 2027
            start_month = start_date.month
            start_year = start_date.year
            
            end_month = start_month - 1 if start_month > 1 else 12
            end_year = start_year if start_month > 1 else start_year + 1
            
            # Get last day of end month
            if end_month == 2:
                # February - check for leap year
                last_day = 29 if end_year % 4 == 0 and (end_year % 100 != 0 or end_year % 400 == 0) else 28
            elif end_month in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 31
            
            end_date = start_date.replace(year=end_year, month=end_month, day=last_day)

            def add_months(date_obj, months):
                month = date_obj.month - 1 + months
                year = date_obj.year + month // 12
                month = month % 12 + 1
                day = min(date_obj.day, [31,
                                         29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                return date_obj.replace(year=year, month=month, day=day)

            # Get month names for quarter labels
            months_id = {
                1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
                9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
            }

            # Quarter starts - each 3 months apart
            q1_start = start_date
            q2_start = add_months(start_date, 3)
            q3_start = add_months(start_date, 6)
            q4_start = add_months(start_date, 9)

            # Quarter ends - 3 months before the next quarter start
            q1_end = add_months(start_date, 3)
            q1_end = q1_end.replace(day=1) - timedelta(days=1)
            
            q2_end = add_months(start_date, 6)
            q2_end = q2_end.replace(day=1) - timedelta(days=1)
            
            q3_end = add_months(start_date, 9)
            q3_end = q3_end.replace(day=1) - timedelta(days=1)
            
            # Q4 ends at contract end date (or 1 month before start, next year)
            q4_end = end_date

            # Create quarter labels like "Sales Target Q1 (Feb-Apr)"
            if not context.get('sales_target_label_q1'):
                context['sales_target_label_q1'] = f"Sales Target Q1 ({months_id[q1_start.month]}-{months_id[q1_end.month]})"
            if not context.get('sales_target_label_q2'):
                context['sales_target_label_q2'] = f"Sales Target Q2 ({months_id[q2_start.month]}-{months_id[q2_end.month]})"
            if not context.get('sales_target_label_q3'):
                context['sales_target_label_q3'] = f"Sales Target Q3 ({months_id[q3_start.month]}-{months_id[q3_end.month]})"
            if not context.get('sales_target_label_q4'):
                context['sales_target_label_q4'] = f"Sales Target Q4 ({months_id[q4_start.month]}-{months_id[q4_end.month]})"

            # Keep old date range format for backward compatibility
            def fmt(date_obj):
                return date_obj.strftime('%d %b %Y')

            if not context.get('quarter_1_period'):
                context['quarter_1_period'] = f"{fmt(q1_start)} - {fmt(q1_end)}"
            if not context.get('quarter_2_period'):
                context['quarter_2_period'] = f"{fmt(q2_start)} - {fmt(q2_end)}"
            if not context.get('quarter_3_period'):
                context['quarter_3_period'] = f"{fmt(q3_start)} - {fmt(q3_end)}"
            if not context.get('quarter_4_period'):
                context['quarter_4_period'] = f"{fmt(q4_start)} - {fmt(q4_end)}"

        # Alias v2 template quarter variable names
        if not context.get('q1_period') and context.get('quarter_1_period'):
            context['q1_period'] = context.get('quarter_1_period')
        if not context.get('q2_period') and context.get('quarter_2_period'):
            context['q2_period'] = context.get('quarter_2_period')
        if not context.get('q3_period') and context.get('quarter_3_period'):
            context['q3_period'] = context.get('quarter_3_period')
        if not context.get('q4_period') and context.get('quarter_4_period'):
            context['q4_period'] = context.get('quarter_4_period')

        # Alias v2 template sales target names
        if not context.get('q1_sales_target') and context.get('sales_target_q1'):
            context['q1_sales_target'] = context.get('sales_target_q1')
        if not context.get('q2_sales_target') and context.get('sales_target_q2'):
            context['q2_sales_target'] = context.get('sales_target_q2')
        if not context.get('q3_sales_target') and context.get('sales_target_q3'):
            context['q3_sales_target'] = context.get('sales_target_q3')
        if not context.get('q4_sales_target') and context.get('sales_target_q4'):
            context['q4_sales_target'] = context.get('sales_target_q4')

        # Alias v2 template delivery address and other fields
        if not context.get('party_b_delivery_address') and context.get('delivery_address'):
            context['party_b_delivery_address'] = context.get('delivery_address')

        if not context.get('party_b_business_form') and context.get('business_form'):
            context['party_b_business_form'] = context.get('business_form')

        if not context.get('customer_partner_code') and context.get('cvcode_number'):
            context['customer_partner_code'] = context.get('cvcode_number')

        # Add quarterly target context without overwriting submitted values
        for key, value in quarter_context.items():
            if key == 'quarters':
                context[key] = value
                continue

            if key not in context or context[key] in (None, ''):
                context[key] = value
        
        return context
    
    @staticmethod
    def validate_template_variables(template_content, contract_data_dict):
        """
        Validate that all required template variables are present in data.
        
        Args:
            template_content: Template string with {{ variable }} syntax
            contract_data_dict: Dictionary of available data
            
        Returns:
            Tuple of (is_valid, missing_variables, available_variables)
        """
        import re
        
        # Extract all {{ variable }} references from template
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        template_vars = set(re.findall(pattern, template_content))
        
        # Check which are missing
        available_vars = set(contract_data_dict.keys())
        # Add system variables
        available_vars.update([
            'contract', 'contract_id', 'contract_title', 'contract_type',
            'party_a', 'party_b', 'contract_value', 'annual_target',
            'start_date', 'end_date', 'created_at', 'owner',
            'today', 'generated_date', 'quarters',
            'q1_start', 'q1_end', 'q1_target',
            'q2_start', 'q2_end', 'q2_target',
            'q3_start', 'q3_end', 'q3_target',
            'q4_start', 'q4_end', 'q4_target'
        ])
        
        missing_vars = template_vars - available_vars
        
        return (len(missing_vars) == 0, missing_vars, template_vars)
    
    @staticmethod
    def render_template(template_instance, context_dict):
        """
        Render a template with provided context.
        
        Args:
            template_instance: ContractTemplate instance
            context_dict: Dictionary of context variables
            
        Returns:
            Rendered HTML string
            
        Raises:
            Exception if template rendering fails
        """
        from django.template import Template, Context
        
        try:
            template = Template(template_instance.content)
            rendered = template.render(Context(context_dict))
            return rendered
        except Exception as e:
            raise Exception(
                f"Error rendering template '{template_instance.name}': {str(e)}"
            )


class ContractDraftService:
    """Service for generating and managing contract drafts"""
    
    @staticmethod
    def generate_draft(contract, submitted_data, user=None, is_regeneration=False):
        """
        Generate a draft document from template and submitted data.
        
        Args:
            contract: Contract instance (must be template-based)
            submitted_data: Dictionary of form field values
            user: User who triggered generation
            is_regeneration: Whether this is a template update regeneration
            
        Returns:
            ContractDraft instance or None if generation failed
            
        Raises:
            ValueError if contract is not template-based
        """
        from .models import ContractTemplate, ContractDraft, AuditLog
        from django.utils import timezone
        from django.utils.text import slugify
        from django.core.files.base import ContentFile
        from django.db.models import Max
        
        # Validate contract type is template-based
        if not contract.is_template_based:
            raise ValueError(
                f"Contract '{contract.title}' is not template-based. "
                f"Cannot generate draft for this contract type."
            )
        
        # Load template
        try:
            template = TemplateService.get_template_for_contract_type(
                contract.contract_type
            )
        except ValueError as e:
            return None  # No template available
        
        # Build context with contract + submitted data
        context_dict = TemplateService.build_template_context(
            contract,
            submitted_data
        )
        
        # Validate all required variables are available
        is_valid, missing_vars, _ = TemplateService.validate_template_variables(
            template.content,
            submitted_data
        )
        
        if not is_valid:
            # Log warning but continue with available data
            # (template might have optional variables)
            pass
        
        # Render template
        try:
            rendered_content = TemplateService.render_template(
                template,
                context_dict
            )
        except Exception as e:
            return None  # Rendering failed
        
        # Calculate next version
        last_version = ContractDraft.objects.filter(
            contract=contract
        ).aggregate(v=Max('version'))['v'] or 0
        version = last_version + 1
        
        # Create draft file
        file_name = f"contract_{slugify(contract.title)}_draft_v{version}.html"
        
        # Save draft
        draft = ContractDraft(
            contract=contract,
            template=template,
            version=version
        )
        draft.file.save(
            file_name,
            ContentFile(rendered_content.encode('utf-8')),
            save=False
        )
        draft.save()
        
        # Update contract tracking
        contract.is_draft_generated = True
        contract.draft_generated_at = timezone.now()
        contract.save(update_fields=['is_draft_generated', 'draft_generated_at'])
        
        # Create audit log
        action = 'DRAFT_UPDATED' if is_regeneration else 'DRAFT_GENERATED'
        AuditLog.objects.create(
            contract=contract,
            user=user,
            action=action,
            details=f"Draft v{version} generated from template '{template.name}' (v{template.version})"
        )
        
        return draft
    
    @staticmethod
    def regenerate_draft_from_latest_data(contract, user=None):
        """
        Regenerate draft using the latest submitted data.
        
        Useful when template is updated.
        
        Args:
            contract: Contract instance
            user: User who triggered regeneration
            
        Returns:
            ContractDraft instance or None
        """
        from .models import ContractData
        
        # Get latest submitted data
        latest_data = ContractData.objects.filter(
            contract=contract
        ).order_by('-version').first()
        
        if not latest_data:
            return None  # No data submitted yet
        
        # Regenerate with existing data
        return ContractDraftService.generate_draft(
            contract=contract,
            submitted_data=latest_data.data,
            user=user,
            is_regeneration=True
        )
    
    @staticmethod
    def get_draft_download_url(draft):
        """
        Get the download URL for a draft document.
        
        Args:
            draft: ContractDraft instance
            
        Returns:
            URL string for download
        """
        if draft.file:
            return draft.file.url
        return None
    
    @staticmethod
    def list_drafts_for_contract(contract, limit=None):
        """
        Get draft versions for a contract.
        
        Args:
            contract: Contract instance
            limit: Maximum number to return (None = all)
            
        Returns:
            QuerySet of ContractDraft instances ordered by version desc
        """
        from .models import ContractDraft
        
        drafts = ContractDraft.objects.filter(
            contract=contract
        ).order_by('-version')
        
        if limit:
            drafts = drafts[:limit]
        
        return drafts


class DocumentVersionService:
    """Service for versioned document uploads (non-template agreements)"""

    @staticmethod
    def create_versioned_document(contract, uploaded_by, title, file_obj, description=''):
        """
        Create a new versioned contract document.

        Args:
            contract: Contract instance
            uploaded_by: User instance
            title: Document title
            file_obj: Uploaded file
            description: Optional description

        Returns:
            ContractDocument instance
        """
        from django.db.models import Max
        from .models import ContractDocument

        last_version = ContractDocument.objects.filter(
            contract=contract
        ).aggregate(v=Max('version'))['v'] or 0

        version = last_version + 1

        # Mark existing documents as not current
        ContractDocument.objects.filter(
            contract=contract,
            is_current=True
        ).update(is_current=False)

        document = ContractDocument.objects.create(
            contract=contract,
            title=title,
            document=file_obj,
            description=description,
            uploaded_by=uploaded_by,
            version=version,
            is_current=True
        )

        return document

class ReminderService:
    """
    Service layer for automated email reminders as defined in core_clm_spec.md
    
    Supports configurable reminder schedules for:
    - Contract expiration
    - Signature pending
    - Renewal notification
    
    Features:
    - Configurable schedules (global, type-specific, or per-contract)
    - Throttling to prevent duplicate reminders
    - Audit logging of all reminders
    - Support for multiple frequencies (once, daily, weekly)
    """
    
    @staticmethod
    def get_due_reminders(reminder_type=None, contract_type=None):
        """
        Get reminders that are due to be sent
        
        Respects ReminderConfiguration and throttling rules.
        Returns reminders filtered by configuration matching, throttling, and max occurrences.
        
        Args:
            reminder_type: Specific reminder type to check (e.g., 'EXPIRY'), or None for all
            contract_type: Specific contract type code, or None for all
            
        Returns:
            list of tuples: [(contract, reminder_config, trigger_date), ...]
        """
        from django.utils import timezone
        from datetime import timedelta
        from .models import (
            Contract, ReminderConfiguration, ReminderLog, ReminderType, 
            ContractStatus, ContractTypeDefinition
        )
        
        today = timezone.now().date()
        due_reminders = []
        
        # Get active configurations
        configs = ReminderConfiguration.objects.filter(enabled=True)
        if reminder_type:
            configs = configs.filter(reminder_type=reminder_type)
        
        for config in configs:
            # Get contracts to check
            if config.scope == 'CONTRACT':
                # Single contract override
                contracts = Contract.objects.filter(id=config.contract_id)
            elif config.scope == 'TYPE':
                # Contract type-specific config
                if contract_type and contract_type != config.contract_type.code:
                    continue
                contracts = Contract.objects.filter(
                    contract_type=config.contract_type.code,
                    status__in=[ContractStatus.ACTIVE, ContractStatus.PENDING_SIGNATURE, 
                               ContractStatus.SIGNED, ContractStatus.EXPIRING_SOON]
                )
            else:  # GLOBAL
                contracts = Contract.objects.filter(
                    status__in=[ContractStatus.ACTIVE, ContractStatus.PENDING_SIGNATURE,
                               ContractStatus.SIGNED, ContractStatus.EXPIRING_SOON]
                )
            
            # Check each contract against this configuration
            for contract in contracts:
                trigger_date = ReminderService._calculate_trigger_date(
                    contract, config.reminder_type, config.days_before_trigger
                )
                
                if trigger_date is None:
                    continue
                
                # Check if reminder should be sent based on trigger date
                if trigger_date > today:
                    continue
                
                # Check throttling - has this reminder been sent recently?
                if not ReminderService._should_send_reminder(contract, config):
                    continue
                
                # Check max occurrences
                if config.max_occurrences > 0:
                    sent_count = ReminderLog.objects.filter(
                        contract=contract,
                        reminder_config=config,
                        status='SENT'
                    ).count()
                    if sent_count >= config.max_occurrences:
                        continue
                
                due_reminders.append((contract, config, trigger_date))
        
        return due_reminders
    
    @staticmethod
    def _calculate_trigger_date(contract, reminder_type, days_before):
        """
        Calculate when a reminder should be triggered
        
        Args:
            contract: Contract instance
            reminder_type: Type of reminder (EXPIRY, SIGNATURE_PENDING, RENEWAL)
            days_before: Days before the triggering date
            
        Returns:
            date or None if not applicable
        """
        from datetime import timedelta
        from .models import ReminderType, ContractStatus
        
        if reminder_type == ReminderType.EXPIRY:
            # Expiry reminders trigger N days before end_date
            if contract.end_date:
                return contract.end_date - timedelta(days=days_before)
        
        elif reminder_type == ReminderType.SIGNATURE_PENDING:
            # Signature pending reminders trigger N days after entering pending_signature status
            # Use created_at or a timestamp if available
            from django.utils import timezone
            pending_since = contract.updated_at
            return pending_since.date() + timedelta(days=days_before)
        
        elif reminder_type == ReminderType.RENEWAL:
            # Renewal reminders trigger N days before end_date (similar to expiry but with custom message)
            if contract.end_date:
                return contract.end_date - timedelta(days=days_before)
        
        return None
    
    @staticmethod
    def _should_send_reminder(contract, config):
        """
        Check throttling rules - should we send this reminder?
        
        Implements frequency throttling:
        - ONCE: Send only once ever
        - DAILY: Send at most once per day
        - WEEKLY: Send at most once per week
        
        Args:
            contract: Contract instance
            config: ReminderConfiguration instance
            
        Returns:
            bool: True if reminder should be sent
        """
        from django.utils import timezone
        from datetime import timedelta
        from .models import ReminderLog
        
        today = timezone.now().date()
        
        # Get recent logs for this reminder/contract combination
        recent_logs = ReminderLog.objects.filter(
            contract=contract,
            reminder_config=config,
            status__in=['SENT', 'SKIPPED']
        ).order_by('-sent_date')
        
        if not recent_logs.exists():
            return True
        
        last_log = recent_logs.first()
        last_sent = last_log.sent_date or last_log.created_at
        last_sent_date = last_sent.date()
        
        if config.frequency == 'ONCE':
            # Never send again if already sent
            return False
        elif config.frequency == 'DAILY':
            # Send only if not sent today
            return last_sent_date < today
        elif config.frequency == 'WEEKLY':
            # Send only if not sent in last 7 days
            return (today - last_sent_date).days >= 7
        
        return True
    
    @staticmethod
    def schedule_reminders(dry_run=False):
        """
        Find all due reminders and create ReminderLog entries
        
        This is the main orchestration method called by Celery tasks.
        It identifies due reminders and prepares them for sending.
        
        Args:
            dry_run: If True, don't actually create logs (just report what would happen)
            
        Returns:
            dict with summary of scheduled reminders
        """
        from django.utils import timezone
        from .models import ReminderLog
        
        due_reminders = ReminderService.get_due_reminders()
        scheduled_count = 0
        
        for contract, config, trigger_date in due_reminders:
            if not dry_run:
                # Create ReminderLog entry
                recipients_list = ReminderService._get_recipient_emails(contract, config)
                
                reminder_log = ReminderLog.objects.create(
                    reminder_config=config,
                    contract=contract,
                    reminder_type=config.reminder_type,
                    scheduled_date=timezone.now(),
                    recipients=','.join(recipients_list),
                    status='SCHEDULED'
                )
                scheduled_count += 1
            else:
                scheduled_count += 1
        
        return {
            'scheduled': scheduled_count,
            'dry_run': dry_run,
            'timestamp': str(timezone.now())
        }
    
    @staticmethod
    def send_reminder_batch(batch_size=100):
        """
        Send all scheduled reminders
        
        Retrieves scheduled ReminderLog entries and sends corresponding emails.
        Updates log status based on send success/failure.
        
        Args:
            batch_size: Max reminders to send in this batch
            
        Returns:
            dict with summary of sent reminders
        """
        from django.utils import timezone
        from .models import ReminderLog, ReminderType
        
        sent_count = 0
        failed_count = 0
        
        # Get scheduled reminders
        pending_logs = ReminderLog.objects.filter(
            status='SCHEDULED'
        ).select_related('contract', 'reminder_config')[:batch_size]
        
        for log in pending_logs:
            try:
                # Send the email based on reminder type
                success = ReminderService._send_reminder_email(
                    log.contract,
                    log.reminder_config,
                    log.recipients
                )
                
                if success:
                    log.status = 'SENT'
                    log.sent_date = timezone.now()
                    log.email_subject = ReminderService._get_email_subject(
                        log.contract, log.reminder_config
                    )
                    sent_count += 1
                else:
                    log.status = 'FAILED'
                    log.error_message = 'Email send returned False'
                    failed_count += 1
                
            except Exception as e:
                log.status = 'FAILED'
                log.error_message = str(e)
                failed_count += 1
            
            log.save()
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': sent_count + failed_count,
            'timestamp': str(timezone.now())
        }
    
    @staticmethod
    def _send_reminder_email(contract, config, recipients_str):
        """
        Send email for a specific reminder
        
        Args:
            contract: Contract instance
            config: ReminderConfiguration instance
            recipients_str: Comma-separated email addresses
            
        Returns:
            bool: True if email sent successfully
        """
        from .models import ReminderType
        
        recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
        if not recipients:
            return False
        
        if config.reminder_type == ReminderType.EXPIRY:
            return EmailService.send_expiry_reminder_email(contract, recipients)
        elif config.reminder_type == ReminderType.SIGNATURE_PENDING:
            return EmailService.send_signature_pending_reminder(contract, recipients)
        elif config.reminder_type == ReminderType.RENEWAL:
            return EmailService.send_renewal_reminder(contract, recipients)
        
        return False
    
    @staticmethod
    def _get_email_subject(contract, config):
        """Get email subject for a reminder type"""
        from .models import ReminderType
        
        subjects = {
            ReminderType.EXPIRY: f"Reminder: Contract Expiring - {contract.title}",
            ReminderType.SIGNATURE_PENDING: f"Action Required: Pending Signature - {contract.title}",
            ReminderType.RENEWAL: f"Renewal Coming Up - {contract.title}",
        }
        return subjects.get(config.reminder_type, f"Reminder: {contract.title}")
    
    @staticmethod
    def _get_recipient_emails(contract, config):
        """
        Get email recipients for a reminder based on configuration
        
        Filters by roles if configured, and respects notification preferences.
        
        Args:
            contract: Contract instance
            config: ReminderConfiguration instance
            
        Returns:
            list of email addresses
        """
        roles_filter = config.get_recipient_roles()
        
        recipients = EmailService._get_participant_emails(
            contract,
            roles=roles_filter if roles_filter else None,
            notification_filter='critical'  # Use critical notifications for reminders
        )
        
        # Always include contract owner
        if contract.owner and contract.owner.email:
            recipients.append(contract.owner.email)
        
        return list(set(recipients))  # Remove duplicates