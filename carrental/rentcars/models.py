from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)  
    is_agent = models.BooleanField(default=False)  

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

class Customer(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    National_ID = models.CharField(max_length=20, unique=True)
    Nationality = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    License_Number = models.CharField(max_length=20, unique=True)
    License_Expiry_Date = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='customer_profiles/', blank=True, null=True)
    license_image = models.ImageField(upload_to='customer_licenses/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.License_Expiry_Date and self.License_Expiry_Date <= date.today():
            raise ValidationError("License expiry date must be in the future")
        if self.date_of_birth and self.date_of_birth >= date.today():
            raise ValidationError("Date of birth must be in the past")
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-created_at']

class Car(models.Model):
    BRAND_CHOICES = [
        ('Audi', 'Audi'),
        ('BMW', 'BMW'),
        ('Chevrolet', 'Chevrolet'),
        ('Ford', 'Ford'),
        ('Honda', 'Honda'),
        ('Hyundai', 'Hyundai'),
        ('Infiniti', 'Infiniti'),
        ('Jaguar', 'Jaguar'),
        ('Kia', 'Kia'),
        ('Land Rover', 'Land Rover'),
        ('Lexus', 'Lexus'),
        ('Mazda', 'Mazda'),
        ('Mercedes', 'Mercedes'),
        ('Mitsubishi', 'Mitsubishi'),
        ('Nissan', 'Nissan'),
        ('Peugeot', 'Peugeot'),
        ('Porsche', 'Porsche'),
        ('Renault', 'Renault'),
        ('Subaru', 'Subaru'),
        ('Tesla', 'Tesla'),
        ('Toyota', 'Toyota'),
        ('Volkswagen', 'Volkswagen'),
        ('Volvo', 'Volvo'),
    ]
    
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES, default='Toyota')
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    license_plate = models.CharField(max_length=15, unique=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    main_image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    interior_image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    exterior_image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        current_year = date.today().year
        if self.year > current_year + 1:
            raise ValidationError("Year cannot be more than next year")
        if self.year < 1900:
            raise ValidationError("Year cannot be less than 1900")
    
    def __str__(self):
        return f"{self.brand} {self.model} {self.year} ({self.license_plate})"

    @classmethod
    def available_cars_by_model(cls, model_name):
        return cls.objects.filter(model__icontains=model_name, available=True)
    
    @classmethod
    def available_cars_by_brand(cls, brand_name):
        return cls.objects.filter(brand=brand_name, available=True)
    
    class Meta:
        verbose_name = "Car"
        verbose_name_plural = "Cars"
        ordering = ['-created_at']

class Rental(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='rentals')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals')
    agent = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,  # <-- add blank=True
        limit_choices_to={'is_agent': True}, related_name='handled_rentals'
    )
    
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")
        if self.start_date < date.today():
            raise ValidationError("Start date cannot be in the past")
        # Prevent double booking
        overlapping = Rental.objects.filter(
            car=self.car,
            status='active',
        ).exclude(id=self.id).filter(
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        )
        if overlapping.exists():
            raise ValidationError("This car is already rented for the selected period.")
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            days = (self.end_date - self.start_date).days
            self.total_price = self.car.price_per_day * days
        super().save(*args, **kwargs)
    
    @property
    def rental_days(self):
        return (self.end_date - self.start_date).days
    
    @property
    def total_violations_amount(self):
        return sum(v.fine_amount for v in self.violations.all())
    
    @property
    def final_amount(self):
        return self.total_price + self.total_violations_amount

    def __str__(self):
        return f"Rental: {self.customer.full_name} - {self.car.license_plate}"
    
    class Meta:
        verbose_name = "Rental"
        verbose_name_plural = "Rentals"
        ordering = ['-created_at']

class Violation(models.Model):
    VIOLATION_TYPES = [
        ('speeding', 'Speeding'),
        ('parking', 'Illegal Parking'),
        ('traffic_light', 'Running Red Light'),
        ('accident', 'Accident'),
        ('other', 'Other'),
    ]
    
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='violations')
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPES, default='other')
    description = models.TextField()
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_reported = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_violation_type_display()} - {self.rental.car.license_plate} - {self.fine_amount} AED"
    
    class Meta:
        verbose_name = "Violation"
        verbose_name_plural = "Violations"
        ordering = ['-date_reported']

class Invoice(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='invoice')
    issued_date = models.DateTimeField(auto_now_add=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.final_price:
            # Calculate final price including violations and tax
            base_amount = self.rental.final_amount - self.discount_amount
            self.tax_amount = base_amount * Decimal('0.05')  # 5% tax
            self.final_price = base_amount + self.tax_amount
        super().save(*args, **kwargs)
    
    @property
    def invoice_number(self):
        return f"INV-{self.id:06d}"

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.rental.customer.full_name}"
    
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ['-issued_date']

class Maintenance(models.Model):
    """Per-car maintenance/fixing expense ("fixing recycle")."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='maintenances')
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car.license_plate} - {self.amount} on {self.date}"

    class Meta:
        verbose_name = "Maintenance"
        verbose_name_plural = "Maintenances"
        ordering = ['-date', '-created_at']
