from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Contract, ContractSignature, ContractParticipant, AuditLog, Comment
from .services import EmailService


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(post_save, sender=Contract)
def contract_created_or_updated(sender, instance, created, **kwargs):
    """Handle contract creation and updates"""
    if created:
        # Create audit log
        AuditLog.objects.create(
            contract=instance,
            action='CREATE',
            user=instance.created_by,
            details=f"Contract '{instance.title}' created"
        )
        
        # Send email notification
        EmailService.send_contract_created_email(instance)
        
        # Add owner as participant
        if instance.owner:
            ContractParticipant.objects.get_or_create(
                contract=instance,
                user=instance.owner,
                defaults={'role': 'OWNER'}
            )
        
        # Auto-assign legal team members
        try:
            legal_group = Group.objects.get(name='Legal Team')
            for user in legal_group.user_set.all():
                ContractParticipant.objects.get_or_create(
                    contract=instance,
                    user=user,
                    defaults={'role': 'LEGAL'}
                )
        except Group.DoesNotExist:
            pass  # Legal Team group doesn't exist yet


@receiver(pre_save, sender=Contract)
def track_status_change(sender, instance, **kwargs):
    """Track status changes in contracts"""
    if instance.pk:
        try:
            old_instance = Contract.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed
                AuditLog.objects.create(
                    contract=instance,
                    action='STATUS_CHANGE',
                    details=f"Status changed from {old_instance.get_status_display()} to {instance.get_status_display()}",
                    old_value=old_instance.status,
                    new_value=instance.status
                )
                
                # Send appropriate email based on new status
                if instance.status == 'SUBMITTED':
                    EmailService.send_legal_review_email(instance)
                elif instance.status == 'LEGAL_REVIEW':
                    EmailService.send_legal_review_email(instance)
                elif instance.status == 'APPROVED':
                    EmailService.send_contract_approved_email(instance)
                elif instance.status == 'ACTIVE':
                    EmailService.send_contract_activated_email(instance)
        except Contract.DoesNotExist:
            pass


@receiver(post_save, sender=ContractParticipant)
def participant_added(sender, instance, created, **kwargs):
    """Handle participant additions"""
    if created:
        AuditLog.objects.create(
            contract=instance.contract,
            action='PARTICIPANT_ADDED',
            details=f"{instance.user.get_full_name() or instance.user.username} added as {instance.get_role_display()}"
        )
        
        # Send invitation email
        if instance.role == 'CUSTOMER':
            EmailService.send_customer_invitation_email(instance.contract, instance.user)


@receiver(post_save, sender=Comment)
def comment_added(sender, instance, created, **kwargs):
    """Handle comment additions"""
    if created:
        AuditLog.objects.create(
            contract=instance.contract,
            action='COMMENT_ADDED',
            user=instance.user,
            details=f"Comment added by {instance.user.get_full_name() or instance.user.username if instance.user else 'Unknown'}"
        )
