from django.contrib import admin
from django.utils.html import format_html
from .models import Car, Customer, Rental, Violation, Invoice, CustomUser, Maintenance

class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'license_plate', 'price_per_day', 'available', 'main_image_preview')
    list_filter = ('brand', 'available', 'year')
    search_fields = ('model', 'license_plate', 'brand')
    readonly_fields = ('main_image_preview', 'interior_image_preview', 'exterior_image_preview')
    
    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.main_image.url)
        return "No Image"
    main_image_preview.short_description = "Main Image"
    
    def interior_image_preview(self, obj):
        if obj.interior_image:
            return format_html('<img src="{}" width="100" height="75" style="border-radius: 5px;" />', obj.interior_image.url)
        return "No Image"
    interior_image_preview.short_description = "Interior Image"
    
    def exterior_image_preview(self, obj):
        if obj.exterior_image:
            return format_html('<img src="{}" width="100" height="75" style="border-radius: 5px;" />', obj.exterior_image.url)
        return "No Image"
    exterior_image_preview.short_description = "Exterior Image"

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'National_ID', 'License_Number', 'profile_image_preview')
    search_fields = ('full_name', 'email', 'National_ID')
    readonly_fields = ('profile_image_preview', 'license_image_preview')
    
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_image.url)
        return "No Image"
    profile_image_preview.short_description = "Profile"
    
    def license_image_preview(self, obj):
        if obj.license_image:
            return format_html('<img src="{}" width="100" height="75" style="border-radius: 5px;" />', obj.license_image.url)
        return "No Image"
    license_image_preview.short_description = "License Image"

class RentalAdmin(admin.ModelAdmin):
    exclude = ('agent',)  # Hide agent field from the form
    list_display = ('customer', 'car', 'start_date', 'end_date', 'status', 'total_price')
    list_filter = ('status', 'start_date')
    search_fields = ('customer__full_name', 'car__license_plate')

    def save_model(self, request, obj, form, change):
        if not obj.agent:
            obj.agent = request.user
        obj.save()

admin.site.register(Car, CarAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Rental, RentalAdmin)  # Use the custom admin
admin.site.register(Violation)
admin.site.register(Invoice)
admin.site.register(CustomUser)
@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('car', 'amount', 'date', 'description')
    list_filter = ('date', 'car__brand')
    search_fields = ('car__license_plate', 'car__model', 'description')
