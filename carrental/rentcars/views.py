from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Car, Customer, Rental, Invoice, Violation, CustomUser, Maintenance
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json
from datetime import date, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import base64
from django.template.loader import render_to_string
from django.template import Template, Context

def available_cars(request):
    """Get available cars with optional filtering"""
    try:
        model_name = request.GET.get('model')
        brand_name = request.GET.get('brand')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        
        cars = Car.objects.filter(available=True)
        
        if model_name:
            cars = cars.filter(model__icontains=model_name)
        if brand_name:
            cars = cars.filter(brand=brand_name)
        if min_price:
            cars = cars.filter(price_per_day__gte=min_price)
        if max_price:
            cars = cars.filter(price_per_day__lte=max_price)
            
        data = [
            {
                "id": car.id,
                "brand": car.brand,
                "model": car.model,
                "year": car.year,
                "license_plate": car.license_plate,
                "color": car.color,
                "price_per_day": float(car.price_per_day),
                "description": car.description,
                "main_image_url": car.main_image.url if car.main_image else None,
                "interior_image_url": car.interior_image.url if car.interior_image else None,
                "exterior_image_url": car.exterior_image.url if car.exterior_image else None,
            }
            for car in cars
        ]
        return JsonResponse({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def register_customer(request):
    """Register a new customer with image support"""
    try:
        # Handle multipart form data for file uploads
        if request.content_type.startswith('multipart/form-data'):
            data = request.POST.dict()
            profile_image = request.FILES.get('profile_image')
            license_image = request.FILES.get('license_image')
        else:
            # Handle JSON data (backward compatibility)
            data = json.loads(request.body)
            profile_image = None
            license_image = None
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'National_ID', 'License_Number']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'status': 'error',
                    'message': f'{field} is required'
                }, status=400)
        
        # Check if customer already exists
        if Customer.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Customer with this email already exists'
            }, status=400)
            
        if Customer.objects.filter(National_ID=data['National_ID']).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Customer with this National ID already exists'
            }, status=400)
        
        customer = Customer(
            full_name=data['full_name'],
            email=data['email'],
            phone_number=data.get('phone_number'),
            address=data.get('address'),
            National_ID=data['National_ID'],
            Nationality=data.get('Nationality'),
            date_of_birth=parse_date(data.get('date_of_birth')) if data.get('date_of_birth') else None,
            License_Number=data['License_Number'],
            License_Expiry_Date=parse_date(data.get('License_Expiry_Date')) if data.get('License_Expiry_Date') else None,
            profile_image=profile_image,
            license_image=license_image
        )
        customer.full_clean()  # <-- This line enforces model validation!
        customer.save()
        
        return JsonResponse({
            'status': 'success',
            'customer_id': customer.id,
            'message': 'Customer registered successfully',
            'profile_image_url': customer.profile_image.url if customer.profile_image else None,
            'license_image_url': customer.license_image.url if customer.license_image else None
        })
        
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def create_rental(request):
    print("Request body:", request.body)
    try:
        data = json.loads(request.body)
        print("Parsed data:", data)
        
        # Validate required fields
        required_fields = ['customer_id', 'car_id', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'status': 'error',
                    'message': f'{field} is required'
                }, status=400)
        
        # Get objects
        customer = get_object_or_404(Customer, id=data['customer_id'])
        car = get_object_or_404(Car, id=data['car_id'])
        agent = None
        if data.get('agent_id'):
            agent = get_object_or_404(CustomUser, id=data['agent_id'], is_agent=True)
        
        # Check if car is available
        if not car.available:
            return JsonResponse({
                'status': 'error',
                'message': 'Car is not available'
            }, status=400)
        
        # Parse dates
        start_date = parse_date(data['start_date'])
        end_date = parse_date(data['end_date'])
        
        if not start_date or not end_date:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format'
            }, status=400)
        
        # Create rental
        rental = Rental(
            customer=customer,
            car=car,
            agent=request.user if request.user.is_authenticated else agent,
            start_date=start_date,
            end_date=end_date
        )
        rental.full_clean()  # This will raise ValidationError if double booking
        rental.save()
        
        # Create invoice with tax and discount if provided
        tax_amount = float(data.get('tax_amount', 0))
        discount_amount = float(data.get('discount_amount', 0))
        
        if tax_amount > 0 or discount_amount > 0:
            # Create invoice immediately with custom tax and discount
            invoice = Invoice.objects.create(
                rental=rental,
                tax_amount=tax_amount,
                discount_amount=discount_amount
            )
            # Manually calculate final price since we have custom values
            base_amount = rental.total_price - discount_amount
            if tax_amount == 0:
                # Apply default 5% tax if no custom tax provided
                invoice.tax_amount = base_amount * 0.05
            invoice.final_price = base_amount + invoice.tax_amount
            invoice.save()
        
        # Update car availability
        car.available = False
        car.save()
        
        return JsonResponse({
            'status': 'success',
            'rental_id': rental.id,
            'total_price': float(rental.total_price),
            'rental_days': rental.rental_days,
            'tax_amount': tax_amount,
            'discount_amount': discount_amount,
            'message': 'Rental created successfully'
        })
        
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_violation(request):
    """Add violation to a rental"""
    try:
        data = json.loads(request.body)
        
        rental = get_object_or_404(Rental, id=data['rental_id'])
        
        violation = Violation.objects.create(
            rental=rental,
            violation_type=data.get('violation_type', 'other'),
            description=data['description'],
            fine_amount=data['fine_amount']
        )
        
        return JsonResponse({
            'status': 'success',
            'violation_id': violation.id,
            'message': 'Violation added successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def complete_rental(request):
    """Complete rental and generate invoice"""
    try:
        data = json.loads(request.body)
        rental = get_object_or_404(Rental, id=data['rental_id'])
        
        # Update rental status
        rental.status = 'completed'
        rental.save()
        
        # Make car available again
        rental.car.available = True
        rental.car.save()
        
        # Create or get invoice
        invoice, created = Invoice.objects.get_or_create(rental=rental)
        
        return JsonResponse({
            'status': 'success',
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'final_price': float(invoice.final_price),
            'message': 'Rental completed and invoice generated'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def generate_invoice_pdf(request, invoice_id):
    """Generate PDF invoice"""
    try:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        rental = invoice.rental
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("RENTAL INVOICE", title_style))
        story.append(Spacer(1, 20))
        
        # Invoice info
        invoice_data = [
            ['Invoice Number:', invoice.invoice_number],
            ['Issue Date:', invoice.issued_date.strftime('%Y-%m-%d %H:%M')],
            ['Status:', 'Paid' if invoice.is_paid else 'Unpaid'],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Customer info
        story.append(Paragraph("Customer Information", styles['Heading2']))
        customer_data = [
            ['Name:', rental.customer.full_name],
            ['Email:', rental.customer.email],
            ['Phone:', rental.customer.phone_number or 'N/A'],
            ['National ID:', rental.customer.National_ID],
            ['License Number:', rental.customer.License_Number],
        ]
        
        customer_table = Table(customer_data, colWidths=[2*inch, 3*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(customer_table)
        story.append(Spacer(1, 20))
        
        # Car and rental info
        story.append(Paragraph("Rental Details", styles['Heading2']))
        rental_data = [
            ['Car:', f"{rental.car.brand} {rental.car.model} {rental.car.year}"],
            ['License Plate:', rental.car.license_plate],
            ['Color:', rental.car.color or 'N/A'],
            ['Start Date:', rental.start_date.strftime('%Y-%m-%d')],
            ['End Date:', rental.end_date.strftime('%Y-%m-%d')],
            ['Rental Days:', str(rental.rental_days)],
            ['Price per Day:', f"{rental.car.price_per_day} AED"],
        ]
        
        rental_table = Table(rental_data, colWidths=[2*inch, 3*inch])
        rental_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(rental_table)
        story.append(Spacer(1, 20))
        
        # Violations (if any)
        violations = rental.violations.all()
        if violations:
            story.append(Paragraph("Violations", styles['Heading2']))
            violation_data = [['Type', 'Description', 'Fine Amount']]
            for violation in violations:
                violation_data.append([
                    violation.get_violation_type_display(),
                    violation.description[:50] + '...' if len(violation.description) > 50 else violation.description,
                    f"{violation.fine_amount} AED"
                ])
            
            violation_table = Table(violation_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
            violation_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(violation_table)
            story.append(Spacer(1, 20))
        
        # Price breakdown
        story.append(Paragraph("Price Breakdown", styles['Heading2']))
        price_data = [
            ['Rental Cost:', f"{rental.total_price} AED"],
            ['Violations:', f"{rental.total_violations_amount} AED"],
            ['Subtotal:', f"{rental.final_amount} AED"],
            ['Discount:', f"-{invoice.discount_amount} AED"],
            ['Tax (5%):', f"{invoice.tax_amount} AED"],
            ['Final Total:', f"{invoice.final_price} AED"],
        ]
        
        price_table = Table(price_data, colWidths=[3*inch, 2*inch])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0, -1), (-1, -1), colors.darkblue),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('BACKGROUND', (0, 0), (0, -2), colors.lightgrey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(price_table)
        
        # Build PDF
        doc.build(story)
        
        # Return PDF response
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def get_rental_history(request):
    """Get rental history with filtering"""
    try:
        customer_id = request.GET.get('customer_id')
        status = request.GET.get('status')
        
        rentals = Rental.objects.all()
        
        if customer_id:
            rentals = rentals.filter(customer_id=customer_id)
        if status:
            rentals = rentals.filter(status=status)
            
        data = []
        for rental in rentals:
            rental_data = {
                'id': rental.id,
                'customer': rental.customer.full_name,
                'car': str(rental.car),
                'start_date': rental.start_date.strftime('%Y-%m-%d'),
                'end_date': rental.end_date.strftime('%Y-%m-%d'),
                'total_price': float(rental.total_price),
                'status': rental.status,
                'violations_count': rental.violations.count(),
                'violations_amount': float(rental.total_violations_amount),
                'final_amount': float(rental.final_amount),
                'has_invoice': hasattr(rental, 'invoice'),
                'tax_amount': 0,
                'discount_amount': 0,
            }
            if hasattr(rental, 'invoice'):
                rental_data['invoice_id'] = rental.invoice.id
                rental_data['invoice_number'] = rental.invoice.invoice_number
                rental_data['tax_amount'] = float(rental.invoice.tax_amount)
                rental_data['discount_amount'] = float(rental.invoice.discount_amount)
            data.append(rental_data)
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def get_customers(request):
    customers = Customer.objects.all()
    data = [{
        'id': c.id,
        'full_name': c.full_name,
        'email': c.email,
        'phone_number': c.phone_number,
        'National_ID': c.National_ID,
        'License_Number': c.License_Number
    } for c in customers]
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt  
def get_cars(request):
    cars = Car.objects.all()
    data = [{
        'id': c.id,
        'brand': c.brand,
        'model': c.model,
        'year': c.year,
        'license_plate': c.license_plate,
        'price_per_day': float(c.price_per_day),
        'available': c.available,
        'main_image_url': c.main_image.url if c.main_image else None,
        'interior_image_url': c.interior_image.url if c.interior_image else None,
        'exterior_image_url': c.exterior_image.url if c.exterior_image else None
    } for c in cars]
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user is admin (either custom is_admin field or Django superuser)
                is_admin = getattr(user, "is_admin", False) or getattr(user, "is_superuser", False)
                is_agent = getattr(user, "is_agent", False)
                
                return JsonResponse({
                    "status": "success",
                    "username": user.username,
                    "email": user.email,
                    "is_agent": is_agent,
                    "is_admin": is_admin,
                })
            else:
                return JsonResponse({"status": "error", "message": "Invalid credentials"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@csrf_exempt
def signup_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            if not all([username, email, password]):
                return JsonResponse({"status": "error", "message": "All fields required"}, status=400)
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({"status": "error", "message": "Username already exists"}, status=400)
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({"status": "error", "message": "Email already exists"}, status=400)
            
            # Check if email is admin domain
            is_admin = email.lower().endswith("@carrentality.com")
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_admin=is_admin,
                is_agent=not is_admin
            )
            return JsonResponse({"status": "success", "message": "User created", "is_admin": is_admin})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

def dashboard_stats(request):
    stats = {
        'total_cars': Car.objects.count(),
        'available_cars': Car.objects.filter(available=True).count(),
        'active_rentals': Rental.objects.filter(status='active').count(),
        'total_customers': Customer.objects.count(),
        'total_violations': Violation.objects.count(),
        'unpaid_invoices': Invoice.objects.filter(is_paid=False).count()
    }
    return JsonResponse({'status': 'success', 'data': stats})

@csrf_exempt
@require_http_methods(["POST"])
def add_maintenance(request):
    """Add a new maintenance/fix expense for a car.
    Expects JSON or form-data with: car_id, amount, optional description, optional date (YYYY-MM-DD).
    """
    try:
        if request.content_type.startswith('multipart/form-data'):
            data = request.POST.dict()
        else:
            data = json.loads(request.body)

        car_id = data.get('car_id')
        amount = data.get('amount')
        description = data.get('description')
        date_str = data.get('date')

        if not car_id or not amount:
            return JsonResponse({'status': 'error', 'message': 'car_id and amount are required'}, status=400)

        car = get_object_or_404(Car, id=car_id)

        # parse amount and date
        try:
            amount_val = float(amount)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'amount must be a number'}, status=400)

        maint_date = parse_date(date_str) if date_str else None

        maintenance = Maintenance.objects.create(
            car=car,
            amount=amount_val,
            description=description,
            date=maint_date if maint_date else timezone.now().date()
        )

        return JsonResponse({
            'status': 'success',
            'maintenance_id': maintenance.id,
            'message': 'Maintenance added successfully'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def daily_report(request):
    """Daily report for a given date.
    Query param: date=YYYY-MM-DD. If missing or invalid, use today.
    Returns rentals_count, rentals_revenue, maintenance_total for that date.
    Rentals are counted by start_date matching the day.
    """
    try:
        date_str = request.GET.get('date')
        target_date = parse_date(date_str) if date_str else None
        if not target_date:
            target_date = timezone.now().date()

        # Rentals that start on target_date
        rentals_qs = Rental.objects.filter(start_date=target_date)
        rentals_count = rentals_qs.count()
        rentals_revenue = rentals_qs.aggregate(total=Sum('total_price'))['total'] or 0

        # Maintenance on target_date
        maintenance_qs = Maintenance.objects.filter(date=target_date)
        maintenance_total = maintenance_qs.aggregate(total=Sum('amount'))['total'] or 0

        return JsonResponse({
            'status': 'success',
            'date': target_date.strftime('%Y-%m-%d'),
            'rentals_count': rentals_count,
            'rentals_revenue': float(rentals_revenue),
            'maintenance_total': float(maintenance_total),
            'message': 'No data for this date' if rentals_count == 0 and maintenance_total == 0 else 'OK'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_car(request):
    """Add a new car with image support"""
    try:
        # Handle multipart form data for file uploads
        if request.content_type.startswith('multipart/form-data'):
            data = request.POST.dict()
            main_image = request.FILES.get('main_image')
            interior_image = request.FILES.get('interior_image')
            exterior_image = request.FILES.get('exterior_image')
        else:
            # Handle JSON data (backward compatibility)
            data = json.loads(request.body)
            main_image = None
            interior_image = None
            exterior_image = None
        
        # Validate required fields
        required_fields = ['brand', 'model', 'year', 'license_plate', 'price_per_day']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'status': 'error',
                    'message': f'{field} is required'
                }, status=400)
        
        # Check if car with same license plate already exists
        if Car.objects.filter(license_plate=data['license_plate']).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Car with this license plate already exists'
            }, status=400)
        
        car = Car(
            brand=data['brand'],
            model=data['model'],
            year=int(data['year']),
            license_plate=data['license_plate'],
            color=data.get('color'),
            price_per_day=data['price_per_day'],
            description=data.get('description'),
            main_image=main_image,
            interior_image=interior_image,
            exterior_image=exterior_image
        )
        car.full_clean()  # Enforce model validation
        car.save()
        
        return JsonResponse({
            'status': 'success',
            'car_id': car.id,
            'message': 'Car added successfully',
            'main_image_url': car.main_image.url if car.main_image else None,
            'interior_image_url': car.interior_image.url if car.interior_image else None,
            'exterior_image_url': car.exterior_image.url if car.exterior_image else None
        })
        
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def get_customers(request):
    customers = Customer.objects.all()
    data = [{
        'id': c.id,
        'full_name': c.full_name,
        'email': c.email,
        'phone_number': c.phone_number,
        'National_ID': c.National_ID,
        'License_Number': c.License_Number
    } for c in customers]
    return JsonResponse({'status': 'success', 'data': data})

def get_all_cars(request):
    cars = Car.objects.all()
    data = [{
        'id': c.id,
        'brand': c.brand,
        'model': c.model,
        'year': c.year,
        'license_plate': c.license_plate,
        'color': c.color,
        'price_per_day': float(c.price_per_day),
        'available': c.available,
        'main_image_url': c.main_image.url if c.main_image else None,
        'interior_image_url': c.interior_image.url if c.interior_image else None,
        'exterior_image_url': c.exterior_image.url if c.exterior_image else None
    } for c in cars]
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
def get_violations(request):
    """Get all violations with rental info"""
    violations = Violation.objects.select_related('rental', 'rental__customer', 'rental__car').all()
    data = []
    for violation in violations:
        data.append({
            'id': violation.id,
            'rental_id': violation.rental.id,
            'customer_name': violation.rental.customer.full_name,
            'car': f"{violation.rental.car.brand} {violation.rental.car.model}",
            'license_plate': violation.rental.car.license_plate,
            'violation_type': violation.get_violation_type_display(),
            'description': violation.description,
            'fine_amount': float(violation.fine_amount),
            'date_reported': violation.date_reported.strftime('%Y-%m-%d'),
            'is_paid': violation.is_paid
        })
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
def get_all_invoices(request):
    """Get all invoices"""
    invoices = Invoice.objects.select_related('rental', 'rental__customer', 'rental__car').all()
    data = []
    for invoice in invoices:
        data.append({
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'customer_name': invoice.rental.customer.full_name,
            'car': f"{invoice.rental.car.brand} {invoice.rental.car.model}",
            'issued_date': invoice.issued_date.strftime('%Y-%m-%d %H:%M'),
            'final_price': float(invoice.final_price),
            'tax_amount': float(invoice.tax_amount),
            'discount_amount': float(invoice.discount_amount),
            'is_paid': invoice.is_paid,
            'payment_date': invoice.payment_date.strftime('%Y-%m-%d %H:%M') if invoice.payment_date else None
        })
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
@require_http_methods(["POST"])
def mark_invoice_paid(request):
    """Mark invoice as paid"""
    data = json.loads(request.body)
    invoice = get_object_or_404(Invoice, id=data['invoice_id'])
    invoice.is_paid = True
    invoice.payment_date = timezone.now()
    invoice.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Invoice marked as paid'
    })

@csrf_exempt
@require_http_methods(["POST"])
def mark_violation_paid(request):
    """Mark violation as paid"""
    data = json.loads(request.body)
    violation = get_object_or_404(Violation, id=data['violation_id'])
    violation.is_paid = True
    violation.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Violation marked as paid'
    })

@csrf_exempt
def get_rental_details(request, rental_id):
    """Get detailed rental information including violations"""
    rental = get_object_or_404(Rental, id=rental_id)
    violations = rental.violations.all()
    
    violations_data = []
    for violation in violations:
        violations_data.append({
            'id': violation.id,
            'type': violation.get_violation_type_display(),
            'description': violation.description,
            'fine_amount': float(violation.fine_amount),
            'date_reported': violation.date_reported.strftime('%Y-%m-%d'),
            'is_paid': violation.is_paid
        })
    
    data = {
        'rental': {
            'id': rental.id,
            'customer': rental.customer.full_name,
            'car': f"{rental.car.brand} {rental.car.model}",
            'license_plate': rental.car.license_plate,
            'start_date': rental.start_date.strftime('%Y-%m-%d'),
            'end_date': rental.end_date.strftime('%Y-%m-%d'),
            'total_price': float(rental.total_price),
            'status': rental.status,
            'rental_days': rental.rental_days,
            'total_violations_amount': float(rental.total_violations_amount),
            'final_amount': float(rental.final_amount)
        },
        'violations': violations_data,
        'has_invoice': hasattr(rental, 'invoice')
    }
    
    if hasattr(rental, 'invoice'):
        data['invoice'] = {
            'id': rental.invoice.id,
            'invoice_number': rental.invoice.invoice_number,
            'final_price': float(rental.invoice.final_price),
            'is_paid': rental.invoice.is_paid
        }
    
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    data = json.loads(request.body)
    for field in ['full_name', 'email', 'phone_number', 'address', 'National_ID', 'Nationality', 'date_of_birth', 'License_Number', 'License_Expiry_Date']:
        if field in data:
            setattr(customer, field, data[field])
    customer.full_clean()
    customer.save()
    return JsonResponse({'status': 'success', 'message': 'Customer updated'})

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    return JsonResponse({'status': 'success', 'message': 'Customer deleted'})

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_car(request, car_id):
    """Update an existing car"""
    try:
        car = get_object_or_404(Car, id=car_id)
        data = json.loads(request.body)
        
        # Update fields if provided
        for field in ['brand', 'model', 'year', 'license_plate', 'color', 'description', 'price_per_day', 'available']:
            if field in data:
                setattr(car, field, data[field])
        
        car.full_clean()  # Validate the model
        car.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Car updated successfully',
            'data': {
                'id': car.id,
                'brand': car.brand,
                'model': car.model,
                'year': car.year,
                'license_plate': car.license_plate,
                'color': car.color,
                'description': car.description,
                'price_per_day': float(car.price_per_day),
                'available': car.available
            }
        })
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_car(request, car_id):
    """Delete a car"""
    try:
        car = get_object_or_404(Car, id=car_id)
        
        # Check if car has active rentals
        active_rentals = car.rentals.filter(status='active')
        if active_rentals.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot delete car with active rentals'
            }, status=400)
        
        car.delete()
        return JsonResponse({
            'status': 'success', 
            'message': 'Car deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_rental(request, rental_id):
    """Update an existing rental"""
    try:
        rental = get_object_or_404(Rental, id=rental_id)
        data = json.loads(request.body)
        
        # Update fields if provided
        for field in ['start_date', 'end_date', 'status']:
            if field in data:
                if field in ['start_date', 'end_date']:
                    setattr(rental, field, parse_date(data[field]))
                else:
                    setattr(rental, field, data[field])
        
        # Update car if provided
        if 'car_id' in data:
            car = get_object_or_404(Car, id=data['car_id'])
            rental.car = car
        
        # Update customer if provided
        if 'customer_id' in data:
            customer = get_object_or_404(Customer, id=data['customer_id'])
            rental.customer = customer
        
        rental.full_clean()  # Validate the model
        rental.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Rental updated successfully',
            'data': {
                'id': rental.id,
                'customer': rental.customer.full_name,
                'car': f"{rental.car.brand} {rental.car.model}",
                'start_date': rental.start_date.strftime('%Y-%m-%d'),
                'end_date': rental.end_date.strftime('%Y-%m-%d'),
                'total_price': float(rental.total_price),
                'status': rental.status
            }
        })
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_rental(request, rental_id):
    """Delete a rental"""
    try:
        rental = get_object_or_404(Rental, id=rental_id)
        
        # Check if rental has violations or invoices
        if rental.violations.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot delete rental with violations. Please resolve violations first.'
            }, status=400)
        
        if hasattr(rental, 'invoice'):
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot delete rental with invoice. Please handle invoice first.'
            }, status=400)
        
        # Make car available again if rental is being deleted
        if rental.status == 'active':
            rental.car.available = True
            rental.car.save()
        
        rental.delete()
        return JsonResponse({
            'status': 'success', 
            'message': 'Rental deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

import os

def generate_rental_contract(request, rental_id):
    """Generate rental contract HTML with database data"""
    try:
        rental = get_object_or_404(Rental, id=rental_id)
        
        # Encode logo as base64 for embedding
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'desktopapp', 'renty.png')
        logo_base64 = ""
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as logo_file:
                logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
        
        # Contract template with real data
        
        # Render template with context
        template = Template(contract_template)
        context = Context({
            'rental': rental,
            'logo_base64': logo_base64
        })
        
        html_content = template.render(context)
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)