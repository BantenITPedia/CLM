from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin
from .models import (
    Contract, ContractParticipant, ContractSignature,
    ContractDocument, AuditLog, Comment,
    ContractField, ContractTemplate, ContractDraft,
    ContractTypeDefinition, ContractData, ContractDataFile,
    ReminderConfiguration, ReminderLog,
    ContractRolePermission, BusinessEntityDocument, CompanyProfile
)

# Customize the default admin site
admin.site.site_header = "Legal CLM - Admin Settings"
admin.site.site_title = "Admin Settings"
admin.site.index_title = "Welcome to Admin Settings"


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for company profile (Party A configuration)
    This is your company information used as default Party A in all contracts
    """
    list_display = ['name', 'business_entity_type', 'is_active', 'phone', 'email', 'updated_at']
    list_filter = ['business_entity_type', 'is_active']
    search_fields = ['name', 'short_name', 'npwp', 'nib', 'email']
    readonly_fields = ['created_at', 'updated_at', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'short_name',
                'business_entity_type',
                'is_active'
            ),
            'description': 'Company name and entity type. Only one profile can be active at a time.'
        }),
        ('Legal Documents', {
            'fields': (
                'npwp',
                'nib',
                'akta_pendirian_number'
            ),
            'description': 'Company registration and tax identification numbers'
        }),
        ('Contact Information', {
            'fields': (
                'address',
                'phone',
                'email',
                'website'
            )
        }),
        ('Legal Representative', {
            'fields': (
                'legal_representative_name',
                'legal_representative_title'
            ),
            'description': 'Person authorized to sign contracts on behalf of the company'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set updated_by to current user"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of active company profile"""
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


class ContractParticipantInline(admin.TabularInline):
    model = ContractParticipant
    extra = 1
    autocomplete_fields = ['user']
    fields = ['user', 'role', 'external_email', 'external_name', 'notification_preference', 'is_active']
    readonly_fields = []


class ContractSignatureInline(admin.TabularInline):
    model = ContractSignature
    extra = 0
    readonly_fields = ['user', 'signed_at', 'ip_address']
    can_delete = False


class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContractTypeDefinition)
class ContractTypeDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'active']
    list_filter = ['active']
    search_fields = ['name', 'code']


@admin.register(ContractField)
class ContractFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'field_key', 'contract_type', 'field_type', 'required', 'position']
    list_filter = ['contract_type', 'field_type', 'required']
    search_fields = ['label', 'field_key']
    ordering = ['contract_type', 'position']


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'contract_type', 'version', 'active', 'created_at']
    list_filter = ['contract_type', 'active']
    search_fields = ['name']
    ordering = ['contract_type', '-active', '-version']


@admin.register(ContractDraft)
class ContractDraftAdmin(admin.ModelAdmin):
    list_display = ['contract', 'version', 'template', 'created_at']
    list_filter = ['template__contract_type']
    search_fields = ['contract__title']


@admin.register(ContractData)
class ContractDataAdmin(admin.ModelAdmin):
    list_display = ['contract', 'version', 'submitted_by', 'submitted_at']
    list_filter = ['submitted_at']
    search_fields = ['contract__title']
    readonly_fields = ['version', 'submitted_at']


@admin.register(ContractDataFile)
class ContractDataFileAdmin(admin.ModelAdmin):
    list_display = ['contract_data', 'field_key', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['contract_data__contract__title', 'field_key']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'contract_type', 'status', 'party_b',
        'start_date', 'end_date', 'days_until_expiry',
        'owner', 'created_at'
    ]
    list_filter = [
        'status', 'contract_type', 'auto_renew',
        'created_at', 'start_date', 'end_date'
    ]
    search_fields = ['title', 'party_a', 'party_b', 'description']
    readonly_fields = [
        'created_at', 'updated_at', 'created_by',
        'days_until_expiry', 'is_expiring_soon', 'is_expired'
    ]
    autocomplete_fields = ['owner', 'parent_contract']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'contract_type', 'description', 'status')
        }),
        ('Parties', {
            'fields': ('party_a', 'party_b')
        }),
        ('Financial', {
            'fields': ('contract_value',)
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'days_until_expiry', 'is_expiring_soon', 'is_expired')
        }),
        ('Renewal Settings', {
            'fields': ('renewal_reminder_days', 'auto_renew', 'renewal_period_months', 'parent_contract')
        }),
        ('Ownership', {
            'fields': ('created_by', 'owner')
        }),
        ('Documents', {
            'fields': ('document',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        ContractParticipantInline,
        ContractSignatureInline,
        ContractDocumentInline,
        CommentInline
    ]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            if not obj.owner:
                obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContractParticipant)
class ContractParticipantAdmin(admin.ModelAdmin):
    list_display = ['name_display', 'email_display', 'contract', 'role', 'notification_preference', 'is_active']
    list_filter = ['role', 'is_active', 'notification_preference', 'added_at']
    search_fields = ['contract__title', 'user__username', 'user__email', 'external_email', 'external_name']
    autocomplete_fields = ['contract', 'user']
    
    fieldsets = (
        ('Internal User', {
            'fields': ('contract', 'user', 'role'),
            'description': 'Select if participant is an internal system user'
        }),
        ('External Participant (Optional)', {
            'fields': ('external_name', 'external_email'),
            'description': 'Fill this if participant is external (vendor, customer, etc)',
            'classes': ('collapse',)
        }),
        ('Notification Settings', {
            'fields': ('notification_preference', 'is_active')
        }),
        ('Metadata', {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['added_at']
    
    def name_display(self, obj):
        return obj.name
    name_display.short_description = 'Participant Name'
    
    def email_display(self, obj):
        return obj.email or '(no email)'
    email_display.short_description = 'Email Address'


@admin.register(ContractSignature)
class ContractSignatureAdmin(admin.ModelAdmin):
    list_display = ['contract', 'user', 'signed_at', 'ip_address']
    list_filter = ['signed_at']
    search_fields = ['contract__title', 'user__username']
    readonly_fields = ['contract', 'user', 'signed_at', 'ip_address', 'user_agent']


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'contract', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['title', 'contract__title']
    readonly_fields = ['uploaded_at']


@admin.register(ContractRolePermission)
class ContractRolePermissionAdmin(admin.ModelAdmin):
    list_display = ['get_role_display_custom', 'get_permission_display_custom', 'allowed_icon', 'allowed', 'updated_at']
    list_filter = ['role', 'permission', 'allowed']
    list_editable = ['allowed']
    search_fields = ['role', 'permission']
    ordering = ['role', 'permission']
    
    fieldsets = (
        (None, {
            'fields': ('role', 'permission', 'allowed'),
            'description': 'Configure which roles have which permissions. Changes take effect immediately.'
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['updated_at']
    
    def get_role_display_custom(self, obj):
        """Display role with icon"""
        icons = {
            'OWNER': '👑',
            'SALES': '💼',
            'LEGAL': '⚖️',
            'CUSTOMER': '👤',
            'SIGNATORY': '✍️',
            'APPROVER': '✅',
        }
        icon = icons.get(obj.role, '•')
        return f"{icon} {obj.get_role_display()}"
    get_role_display_custom.short_description = 'Role'
    get_role_display_custom.admin_order_field = 'role'
    
    def get_permission_display_custom(self, obj):
        """Display permission with better formatting"""
        return obj.get_permission_display()
    get_permission_display_custom.short_description = 'Permission'
    get_permission_display_custom.admin_order_field = 'permission'
    
    def allowed_icon(self, obj):
        """Display checkmark or cross for allowed status"""
        from django.utils.html import format_html
        if obj.allowed:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    allowed_icon.short_description = 'Allowed'
    allowed_icon.admin_order_field = 'allowed'
    
    class Media:
        css = {
            'all': ('admin/css/custom_permissions.css',)
        }


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['contract', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['contract__title', 'user__username', 'details']
    readonly_fields = ['contract', 'action', 'user', 'timestamp', 'details', 'ip_address', 'old_value', 'new_value']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['contract', 'user', 'created_at', 'is_internal']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['contract__title', 'user__username', 'text']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ReminderConfiguration)
class ReminderConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for configurable email reminders
    
    Allows admins to:
    - Create global reminder schedules (apply to all contracts)
    - Create contract-type-specific schedules
    - Create per-contract overrides
    - Configure frequency, timing, and recipient roles
    - Enable/disable reminders without deleting config
    """
    list_display = [
        'reminder_type', 'scope', 'enabled', 'days_before_trigger',
        'frequency', 'max_occurrences', 'updated_at'
    ]
    list_filter = [
        'reminder_type', 'scope', 'enabled', 'frequency',
        'updated_at'
    ]
    search_fields = [
        'description', 'contract_type__name', 'contract__title'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Reminder Type & Scope', {
            'fields': (
                'reminder_type',
                ('scope', 'contract_type', 'contract'),
                'description'
            ),
            'description': (
                'Choose reminder type and scope:\n'
                '- GLOBAL: Applies to all contracts\n'
                '- TYPE: Applies to specific contract type\n'
                '- CONTRACT: Applies to single contract (override)'
            )
        }),
        ('Schedule Configuration', {
            'fields': (
                ('days_before_trigger', 'frequency'),
                ('max_occurrences', 'enabled'),
            ),
            'description': (
                'Configure when and how often reminder is sent:\n'
                '- days_before_trigger: Days before event to send reminder\n'
                '- frequency: ONCE (single), DAILY (repeated), WEEKLY (repeated)\n'
                '- max_occurrences: 0 = unlimited'
            )
        }),
        ('Recipients', {
            'fields': ('recipient_roles',),
            'description': (
                'Comma-separated list of roles to notify (e.g., "OWNER,SIGNATORY")\n'
                'Leave blank to notify all participants'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Show appropriate fields based on scope
        if obj:
            if obj.scope == 'GLOBAL':
                # Hide contract_type and contract for global
                fieldsets = list(fieldsets)
                fieldsets[0] = (
                    fieldsets[0][0],
                    {
                        **fieldsets[0][1],
                        'fields': ('reminder_type', 'scope', 'description')
                    }
                )
        return fieldsets


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    """
    Read-only admin view for reminder delivery logs
    
    Tracks all sent/scheduled reminders for:
    - Audit purposes
    - Troubleshooting delivery issues
    - Preventing duplicate reminders (via throttling logic)
    """
    list_display = [
        'reminder_type', 'contract', 'status',
        'scheduled_date', 'sent_date', 'created_at'
    ]
    list_filter = [
        'reminder_type', 'status',
        'scheduled_date', 'sent_date',
        'created_at'
    ]
    search_fields = [
        'contract__title', 'recipients',
        'email_subject', 'error_message'
    ]
    readonly_fields = [
        'reminder_config', 'contract', 'reminder_type',
        'scheduled_date', 'sent_date', 'recipients',
        'status', 'error_message', 'email_subject',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Reminder Details', {
            'fields': (
                'reminder_config',
                'contract',
                ('reminder_type', 'status'),
                'email_subject'
            )
        }),
        ('Schedule & Delivery', {
            'fields': (
                ('scheduled_date', 'sent_date'),
                'recipients'
            )
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """ReminderLogs are created by tasks, not manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Preserve audit trail"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Logs are read-only"""
        return False


@admin.register(BusinessEntityDocument)
class BusinessEntityDocumentAdmin(admin.ModelAdmin):
    """
    Admin interface for business entity documents
    """
    list_display = ['document_type', 'contract', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['contract__title', 'notes']
    readonly_fields = ['uploaded_at']
    autocomplete_fields = ['contract', 'uploaded_by']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('contract', 'document_type', 'document')
        }),
        ('Upload Details', {
            'fields': ('uploaded_by', 'uploaded_at', 'notes')
        }),)


# Unregister and re-register User and Group with Unfold integration
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """
    Custom User admin with Unfold integration and bulk actions enabled
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'groups', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        ('Account', {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Select groups and permissions for this user'
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Enable bulk actions
    actions = ['delete_selected']
    
    def delete_selected(self, request, queryset):
        """Bulk delete action for users"""
        return super().delete_selected(request, queryset)
    delete_selected.short_description = "Delete selected users"


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """
    Custom Group admin with Unfold integration and bulk actions enabled
    """
    list_display = ['name']
    search_fields = ['name']
    
    # Enable bulk actions
    actions = ['delete_selected']
    
    def delete_selected(self, request, queryset):
        """Bulk delete action for groups"""
        return super().delete_selected(request, queryset)
    delete_selected.short_description = "Delete selected groups"