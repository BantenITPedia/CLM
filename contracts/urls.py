from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Contract CRUD
    path('contracts/', views.contract_list, name='contract_list'),
    
    # Contract Creation Wizard (New Multi-Step Process)
    path('contracts/create/wizard/step1/', views.contract_wizard_step1, name='contract_wizard_step1'),
    path('contracts/create/wizard/step2/', views.contract_wizard_step2, name='contract_wizard_step2'),
    path('contracts/create/wizard/step3/', views.contract_wizard_step3, name='contract_wizard_step3'),
    path('contracts/create/wizard/step4/', views.contract_wizard_step4, name='contract_wizard_step4'),
    path('contracts/create/wizard/cancel/', views.contract_wizard_cancel, name='contract_wizard_cancel'),
    
    # Legacy direct contract creation (kept for backward compatibility)
    path('contracts/create/', views.contract_create, name='contract_create'),
    
    path('contracts/<int:pk>/', views.contract_detail, name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.contract_edit, name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),
    
    # Contract Actions
    path('contracts/<int:pk>/status/', views.update_contract_status, name='update_status'),
    path('contracts/<int:pk>/assign-number/', views.assign_contract_number, name='assign_contract_number'),
    path('contracts/<int:pk>/participant/', views.add_participant, name='add_participant'),
    path('contracts/<int:pk>/document/', views.add_document, name='add_document'),
    path('contracts/<int:pk>/final-document/', views.upload_final_document, name='upload_final_document'),
    path('contracts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('contracts/<int:pk>/data/', views.contract_data_input, name='contract_data_input'),
    path('contracts/<int:pk>/drafts/regenerate/', views.regenerate_contract_draft, name='regenerate_contract_draft'),
    
    # Document Revision Workflow
    path('contracts/<int:contract_id>/document/<int:document_id>/request-revision/', views.request_document_revision, name='request_document_revision'),
    path('contracts/<int:contract_id>/revision/<int:revision_request_id>/upload-revised/', views.upload_revised_document, name='upload_revised_document'),
    path('contracts/<int:contract_id>/revision/<int:revision_request_id>/approve/', views.approve_revised_document, name='approve_revised_document'),
    path('contracts/<int:contract_id>/revision/<int:revision_request_id>/reject/', views.reject_revised_document, name='reject_revised_document'),
    
    # Reports & Views
    path('contracts/expiring/', views.expiring_contracts, name='expiring_contracts'),
    path('contracts/terminated/', views.terminated_contracts, name='terminated_contracts'),
    
    # Settings
    path('settings/company/', views.company_settings, name='company_settings'),
    path('settings/permissions/', views.permission_matrix, name='permission_matrix'),
    path('settings/email/health-check/', views.email_health_check, name='email_health_check'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/json/', views.notifications_json, name='notifications_json'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
