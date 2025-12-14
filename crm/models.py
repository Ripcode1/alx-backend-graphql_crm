"""
CRM Models - Customer, Product, and Order
"""
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from decimal import Decimal


class Customer(models.Model):
    """Customer model"""
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    
    # Phone validator for formats like +1234567890 or 123-456-7890
    phone_regex = RegexValidator(
        regex=r'^\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$',
        message="Phone number must be in format: '+999999999' or '123-456-7890'"
    )
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"


class Product(models.Model):
    """Product model"""
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - ${self.price}"


class Order(models.Model):
    """Order model"""
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    products = models.ManyToManyField(Product, related_name='orders')
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    order_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name} - ${self.total_amount}"

    def calculate_total(self):
        """Calculate total amount from associated products"""
        total = sum(product.price for product in self.products.all())
        self.total_amount = total
        return total
