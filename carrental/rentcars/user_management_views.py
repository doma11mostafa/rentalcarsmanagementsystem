# User Management Endpoints (Admin Only)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import CustomUser, Rental
import json

@csrf_exempt
@require_http_methods(["GET"])
def list_users(request):
    """List all users - Admin only"""
    try:
        users = CustomUser.objects.all().values(
            'id', 'username', 'email', 'first_name', 'last_name', 
            'is_admin', 'is_agent', 'is_active', 'date_joined'
        )
        users_list = list(users)
        for user in users_list:
            user['date_joined'] = user['date_joined'].strftime('%Y-%m-%d %H:%M:%S') if user['date_joined'] else None
        return JsonResponse({'status': 'success', 'data': users_list})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """Create a new user - Admin only"""
    try:
        data = json.loads(request.body)
        
        # Check if username already exists
        if CustomUser.objects.filter(username=data.get('username')).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists'}, status=400)
        
        # Check if email already exists
        if data.get('email') and CustomUser.objects.filter(email=data.get('email')).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already exists'}, status=400)
        
        user = CustomUser.objects.create_user(
            username=data.get('username'),
            email=data.get('email', ''),
            password=data.get('password'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_admin=data.get('is_admin', False),
            is_agent=data.get('is_agent', False),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'User created successfully',
            'user_id': user.id
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_user(request, user_id):
    """Update user details - Admin only"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        data = json.loads(request.body)
        
        # Check if username already exists (excluding current user)
        if 'username' in data and CustomUser.objects.filter(username=data['username']).exclude(id=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists'}, status=400)
        
        # Check if email already exists (excluding current user)
        if 'email' in data and data['email'] and CustomUser.objects.filter(email=data['email']).exclude(id=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already exists'}, status=400)
        
        # Update user fields
        for field in ['username', 'email', 'first_name', 'last_name', 'is_admin', 'is_agent', 'is_active']:
            if field in data:
                setattr(user, field, data[field])
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.save()
        return JsonResponse({'status': 'success', 'message': 'User updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    """Delete a user - Admin only"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent deleting the last admin
        if user.is_admin and CustomUser.objects.filter(is_admin=True).count() <= 1:
            return JsonResponse({'status': 'error', 'message': 'Cannot delete the last admin user'}, status=400)
        
        # Check if user has active rentals as agent
        active_rentals = Rental.objects.filter(agent=user, status='active').count()
        if active_rentals > 0:
            return JsonResponse({
                'status': 'error', 
                'message': f'Cannot delete user with {active_rentals} active rentals'
            }, status=400)
        
        user.delete()
        return JsonResponse({'status': 'success', 'message': 'User deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
