# app/urls.py
from django.urls import path
from . import views
from . import user_management_views as user_views

urlpatterns = [
    

        
    # Car endpoints
    path('api/cars/available/', views.available_cars, name='available_cars'),
    
    # Customer endpoints
    path('api/customers/register/', views.register_customer, name='register_customer'),
    
    # Rental endpoints
    path('api/rentals/create/', views.create_rental, name='create_rental'),
    path('api/rentals/complete/', views.complete_rental, name='complete_rental'),
    path('api/rentals/history/', views.get_rental_history, name='rental_history'),
    
    # Violation endpoints
    path('api/violations/add/', views.add_violation, name='add_violation'),
    
    # Invoice endpoints
    path('api/invoices/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    path('api/auth/login/', views.login_user, name='login'),
    path('api/auth/signup/', views.signup_user, name='signup'),          
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    
    path('api/cars/add/', views.add_car),
    path('api/cars/', views.get_all_cars),
    path('api/customers/', views.get_customers),    

    path('api/violations/add/', views.add_violation, name='add_violation'),

    # --- Invoice URLs ---
    path('api/invoices/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    path('api/customers/<int:customer_id>/update/', views.update_customer, name='update_customer'),
    path('api/customers/<int:customer_id>/delete/', views.delete_customer, name='delete_customer'),

    # Car CRUD endpoints
    path('api/cars/<int:car_id>/update/', views.update_car, name='update_car'),
    path('api/cars/<int:car_id>/delete/', views.delete_car, name='delete_car'),
    
    # Rental CRUD endpoints
    path('api/rentals/<int:rental_id>/update/', views.update_rental, name='update_rental'),
    path('api/rentals/<int:rental_id>/delete/', views.delete_rental, name='delete_rental'),

    # Maintenance and Reports
    path('api/maintenance/add/', views.add_maintenance, name='add_maintenance'),
    path('api/reports/daily/', views.daily_report, name='daily_report'),

    # User Management URLs (Admin Only)
    path('api/users/', user_views.list_users, name='list_users'),
    path('api/users/create/', user_views.create_user, name='create_user'),
    path('api/users/<int:user_id>/update/', user_views.update_user, name='update_user'),
    path('api/users/<int:user_id>/delete/', user_views.delete_user, name='delete_user'),
    
    # Contract generation
    path('api/rentals/<int:rental_id>/contract/', views.generate_rental_contract, name='generate_rental_contract'),
]
