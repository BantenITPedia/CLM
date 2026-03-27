from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Contract, ContractSignature, ContractParticipant, AuditLog, Comment, NotificationType
from .services import EmailService, NotificationService


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

        # In-app notification for all participants
        NotificationService.notify_contract_participants(
            instance,
            NotificationType.CONTRACT_CREATED,
            title=f"New contract: {instance.title}",
            message=f"Contract '{instance.title}' has been created.",
            send_email=False,  # email already sent above
        )
        
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
                    NotificationService.notify_contract_participants(
                        instance, NotificationType.LEGAL_REVIEW,
                        title=f"Contract submitted for legal review: {instance.title}",
                        message=f"Contract '{instance.title}' has been submitted and is pending legal review.",
                        send_email=False,
                    )
                elif instance.status == 'LEGAL_REVIEW':
                    EmailService.send_legal_review_email(instance)
                    NotificationService.notify_contract_participants(
                        instance, NotificationType.LEGAL_REVIEW,
                        title=f"Legal review in progress: {instance.title}",
                        message=f"Contract '{instance.title}' is now under legal review.",
                        send_email=False,
                    )
                elif instance.status == 'APPROVED':
                    EmailService.send_contract_approved_email(instance)
                    NotificationService.notify_contract_participants(
                        instance, NotificationType.CONTRACT_APPROVED,
                        title=f"Contract approved: {instance.title}",
                        message=f"Contract '{instance.title}' has been approved.",
                        send_email=False,
                    )
                elif instance.status == 'ACTIVE':
                    EmailService.send_contract_activated_email(instance)
                    NotificationService.notify_contract_participants(
                        instance, NotificationType.CONTRACT_ACTIVATED,
                        title=f"Contract activated: {instance.title}",
                        message=f"Contract '{instance.title}' is now active.",
                        send_email=False,
                    )
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

        # In-app notification for the added participant
        if instance.user:
            NotificationService.notify_user(
                instance.user,
                instance.contract,
                NotificationType.PARTICIPANT_ADDED,
                title=f"You have been added to: {instance.contract.title}",
                message=f"You have been added as {instance.get_role_display()} on contract '{instance.contract.title}'.",
            )


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

        # Send email notification
        EmailService.send_comment_email(instance, instance.contract)

        # In-app notification for all participants except the commenter
        NotificationService.notify_contract_participants(
            instance.contract,
            NotificationType.COMMENT_ADDED,
            title=f"New comment on: {instance.contract.title}",
            message=f"A comment was added by {instance.user.get_full_name() or instance.user.username if instance.user else 'someone'}.",
            send_email=False,
        )
