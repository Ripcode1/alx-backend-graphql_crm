"""
Django Filters for CRM Models
"""
import django_filters
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    """Filter for Customer model"""
    # Case-insensitive partial match
    name = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    created_at__gte = django_filters.DateTimeFilter(
        field_name='created_at', 
        lookup_expr='gte'
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name='created_at', 
        lookup_expr='lte'
    )
    
    # Custom filter for phone pattern (starts with specific pattern)
    phone_pattern = django_filters.CharFilter(
        field_name='phone', 
        lookup_expr='startswith'
    )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone']


class ProductFilter(django_filters.FilterSet):
    """Filter for Product model"""
    # Case-insensitive partial match
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Price range filters
    price__gte = django_filters.NumberFilter(
        field_name='price', 
        lookup_expr='gte'
    )
    price__lte = django_filters.NumberFilter(
        field_name='price', 
        lookup_expr='lte'
    )
    
    # Stock range filters
    stock__gte = django_filters.NumberFilter(
        field_name='stock', 
        lookup_expr='gte'
    )
    stock__lte = django_filters.NumberFilter(
        field_name='stock', 
        lookup_expr='lte'
    )
    stock = django_filters.NumberFilter(field_name='stock', lookup_expr='exact')
    
    # Low stock filter (less than 10)
    low_stock = django_filters.BooleanFilter(
        method='filter_low_stock',
        label='Low Stock (< 10)'
    )

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']

    def filter_low_stock(self, queryset, name, value):
        """Custom filter for low stock products"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset


class OrderFilter(django_filters.FilterSet):
    """Filter for Order model"""
    # Total amount range filters
    total_amount__gte = django_filters.NumberFilter(
        field_name='total_amount', 
        lookup_expr='gte'
    )
    total_amount__lte = django_filters.NumberFilter(
        field_name='total_amount', 
        lookup_expr='lte'
    )
    
    # Order date range filters
    order_date__gte = django_filters.DateTimeFilter(
        field_name='order_date', 
        lookup_expr='gte'
    )
    order_date__lte = django_filters.DateTimeFilter(
        field_name='order_date', 
        lookup_expr='lte'
    )
    
    # Related field lookups
    customer_name = django_filters.CharFilter(
        field_name='customer__name', 
        lookup_expr='icontains'
    )
    product_name = django_filters.CharFilter(
        field_name='products__name', 
        lookup_expr='icontains'
    )
    
    # Filter by specific product ID
    product_id = django_filters.NumberFilter(
        field_name='products__id', 
        lookup_expr='exact'
    )

    class Meta:
        model = Order
        fields = ['total_amount', 'order_date', 'customer_name', 'product_name']
