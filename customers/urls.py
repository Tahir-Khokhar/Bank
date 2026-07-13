from django.urls import path  # Imports the function for defining URL routes.

from .views import (  # Imports customer-related views.
    AccountOpenView,
    AccountStatusView,
    CustomerChangePasswordView,
    CustomerCreateView,
    CustomerLoginView,
    CustomerLogoutView,
    CustomerManageListView,
    CustomerProfileEditView,
    CustomerProfileView,
    CustomerRegisterView,
    CustomerStaffDetailView,
    CustomerStaffEditView,
    CustomerToggleActiveView,
)


urlpatterns = [  # Maps customer URLs to their corresponding views.
    # Authentication
    path('login/', CustomerLoginView.as_view(), name='customer-login'),
    path('register/', CustomerRegisterView.as_view(), name='customer-register'),
    path('logout/', CustomerLogoutView.as_view(), name='customer-logout'),

    # Self-service profile
    path('profile/', CustomerProfileView.as_view(), name='customer-profile'),
    path('profile/edit/', CustomerProfileEditView.as_view(), name='customer-profile-edit'),
    path('password/', CustomerChangePasswordView.as_view(), name='customer-change-password'),

    # Staff-facing customer management
    path('manage/', CustomerManageListView.as_view(), name='customer-manage-list'),
    path('manage/create/', CustomerCreateView.as_view(), name='customer-create'),
    path('<int:pk>/', CustomerStaffDetailView.as_view(), name='customer-staff-detail'),
    path('<int:pk>/edit/', CustomerStaffEditView.as_view(), name='customer-staff-edit'),
    path('<int:pk>/toggle-active/', CustomerToggleActiveView.as_view(), name='customer-toggle-active'),
    path('<int:pk>/open-account/', AccountOpenView.as_view(), name='account-open'),
    path('account/<int:pk>/status/', AccountStatusView.as_view(), name='account-status'),
]
