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
    path('contracts/create/', views.contract_create, name='contract_create'),
    path('contracts/<int:pk>/', views.contract_detail, name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.contract_edit, name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),
    
    # Contract Actions
    path('contracts/<int:pk>/status/', views.update_contract_status, name='update_status'),
    path('contracts/<int:pk>/participant/', views.add_participant, name='add_participant'),
    path('contracts/<int:pk>/document/', views.add_document, name='add_document'),
    path('contracts/<int:pk>/final-document/', views.upload_final_document, name='upload_final_document'),
    path('contracts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('contracts/<int:pk>/data/', views.contract_data_input, name='contract_data_input'),
    path('contracts/<int:pk>/drafts/regenerate/', views.regenerate_contract_draft, name='regenerate_contract_draft'),
    
    # Reports & Views
    path('contracts/expiring/', views.expiring_contracts, name='expiring_contracts'),
    path('contracts/terminated/', views.terminated_contracts, name='terminated_contracts'),
]
