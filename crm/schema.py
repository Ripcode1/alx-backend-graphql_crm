"""
GraphQL Schema for CRM Application
Includes queries for products and orders, and mutation for updating low stock products.
"""

import graphene
from graphene_django import DjangoObjectType
from crm.models import Product, Order, Customer


class CustomerType(DjangoObjectType):
    """GraphQL type for Customer model"""
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at')


class ProductType(DjangoObjectType):
    """GraphQL type for Product model"""
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'stock', 'created_at', 'updated_at')


class OrderType(DjangoObjectType):
    """GraphQL type for Order model"""
    class Meta:
        model = Order
        fields = ('id', 'customer', 'order_date', 'total_amount', 'status')


class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to update low-stock products (stock < 10) by incrementing stock by 10.
    This simulates a restocking process.
    """
    
    class Arguments:
        # No arguments needed for this mutation
        pass
    
    # Return fields
    success = graphene.Boolean()
    message = graphene.String()
    products = graphene.List(ProductType)
    
    def mutate(self, info):
        """
        Execute the mutation to update low stock products.
        """
        try:
            # Query products with stock < 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            # Store updated products
            updated_products = []
            
            # Update each product
            for product in low_stock_products:
                # Increment stock by 10 (simulating restocking)
                product.stock += 10
                product.save()
                updated_products.append(product)
            
            # Prepare response message
            if updated_products:
                message = f"Successfully restocked {len(updated_products)} low-stock product(s)"
                success = True
            else:
                message = "No low-stock products found (all products have stock >= 10)"
                success = True
            
            return UpdateLowStockProducts(
                success=success,
                message=message,
                products=updated_products
            )
        
        except Exception as e:
            return UpdateLowStockProducts(
                success=False,
                message=f"Error updating low-stock products: {str(e)}",
                products=[]
            )


class Query(graphene.ObjectType):
    """
    Root Query for the CRM GraphQL API
    """
    
    # Simple hello query for health checks
    hello = graphene.String()
    
    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.Int())
    low_stock_products = graphene.List(ProductType, threshold=graphene.Int(default_value=10))
    
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.Int())
    
    # Order queries
    orders = graphene.List(
        OrderType,
        order_date_gte=graphene.String(),
        customer_id=graphene.Int()
    )
    order = graphene.Field(OrderType, id=graphene.Int())
    
    def resolve_hello(self, info):
        """Health check endpoint"""
        return "Hello from CRM GraphQL API!"
    
    def resolve_products(self, info):
        """Get all products"""
        return Product.objects.all()
    
    def resolve_product(self, info, id):
        """Get a single product by ID"""
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_low_stock_products(self, info, threshold=10):
        """Get products with stock below threshold"""
        return Product.objects.filter(stock__lt=threshold)
    
    def resolve_customers(self, info):
        """Get all customers"""
        return Customer.objects.all()
    
    def resolve_customer(self, info, id):
        """Get a single customer by ID"""
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_orders(self, info, order_date_gte=None, customer_id=None):
        """
        Get orders with optional filters
        - order_date_gte: Filter orders from this date onwards (format: YYYY-MM-DD)
        - customer_id: Filter orders by customer ID
        """
        queryset = Order.objects.all()
        
        if order_date_gte:
            from datetime import datetime
            try:
                date_filter = datetime.strptime(order_date_gte, '%Y-%m-%d').date()
                queryset = queryset.filter(order_date__gte=date_filter)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset
    
    def resolve_order(self, info, id):
        """Get a single order by ID"""
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None


class Mutation(graphene.ObjectType):
    """
    Root Mutation for the CRM GraphQL API
    """
    
    update_low_stock_products = UpdateLowStockProducts.Field()


# Create the schema
schema = graphene.Schema(query=Query, mutation=Mutation)
