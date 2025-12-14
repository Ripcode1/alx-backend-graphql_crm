"""
GraphQL Schema for CRM
"""
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from datetime import datetime
import re

from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# ============================================================================
# Object Types
# ============================================================================

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock', 'created_at', 'updated_at', 'orders')
        filter_fields = ['name', 'price', 'stock']
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date', 'created_at', 'updated_at')
        filter_fields = ['total_amount', 'order_date']
        interfaces = (graphene.relay.Node,)


# ============================================================================
# Input Types
# ============================================================================

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


# ============================================================================
# Mutations
# ============================================================================

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    def validate_phone(phone):
        """Validate phone format"""
        if not phone:
            return True
        pattern = r'^\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$'
        return bool(re.match(pattern, phone))

    def mutate(self, info, input):
        try:
            # Check if email already exists
            if Customer.objects.filter(email=input.email).exists():
                return CreateCustomer(
                    customer=None,
                    message="Email already exists",
                    success=False
                )

            # Validate phone if provided
            if input.phone and not CreateCustomer.validate_phone(input.phone):
                return CreateCustomer(
                    customer=None,
                    message="Invalid phone format. Use formats like +1234567890 or 123-456-7890",
                    success=False
                )

            # Create customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone if input.phone else None
            )

            return CreateCustomer(
                customer=customer,
                message="Customer created successfully",
                success=True
            )

        except Exception as e:
            return CreateCustomer(
                customer=None,
                message=f"Error creating customer: {str(e)}",
                success=False
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success = graphene.Boolean()

    def mutate(self, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for idx, customer_data in enumerate(input):
                try:
                    # Check if email already exists
                    if Customer.objects.filter(email=customer_data.email).exists():
                        errors.append(f"Customer {idx + 1}: Email '{customer_data.email}' already exists")
                        continue

                    # Validate phone if provided
                    if customer_data.phone and not CreateCustomer.validate_phone(customer_data.phone):
                        errors.append(f"Customer {idx + 1}: Invalid phone format for '{customer_data.phone}'")
                        continue

                    # Create customer
                    customer = Customer.objects.create(
                        name=customer_data.name,
                        email=customer_data.email,
                        phone=customer_data.phone if customer_data.phone else None
                    )
                    created_customers.append(customer)

                except Exception as e:
                    errors.append(f"Customer {idx + 1}: {str(e)}")

        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors if errors else None,
            success=len(created_customers) > 0
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return CreateProduct(
                    product=None,
                    message="Price must be positive",
                    success=False
                )

            # Validate stock is non-negative
            if input.stock < 0:
                return CreateProduct(
                    product=None,
                    message="Stock cannot be negative",
                    success=False
                )

            # Create product
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=input.stock
            )

            return CreateProduct(
                product=product,
                message="Product created successfully",
                success=True
            )

        except Exception as e:
            return CreateProduct(
                product=None,
                message=f"Error creating product: {str(e)}",
                success=False
            )


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                return CreateOrder(
                    order=None,
                    message=f"Customer with ID {input.customer_id} does not exist",
                    success=False
                )

            # Validate at least one product is provided
            if not input.product_ids or len(input.product_ids) == 0:
                return CreateOrder(
                    order=None,
                    message="At least one product must be provided",
                    success=False
                )

            # Validate all products exist
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    return CreateOrder(
                        order=None,
                        message=f"Product with ID {product_id} does not exist",
                        success=False
                    )

            # Create order
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date if input.order_date else datetime.now()
                )

                # Add products to order
                order.products.set(products)

                # Calculate total amount
                total = order.calculate_total()
                order.save()

            return CreateOrder(
                order=order,
                message=f"Order created successfully with total amount ${total}",
                success=True
            )

        except Exception as e:
            return CreateOrder(
                order=None,
                message=f"Error creating order: {str(e)}",
                success=False
            )


# ============================================================================
# Query Class
# ============================================================================

class Query(graphene.ObjectType):
    # Simple field for Task 0
    hello = graphene.String(default_value="Hello, GraphQL!")

    # Customer queries
    all_customers = graphene.List(CustomerType)
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.String()
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.String()
    )

    # Individual retrievals
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))

    def resolve_all_customers(self, info, **kwargs):
        return Customer.objects.all()

    def resolve_all_products(self, info, **kwargs):
        order_by = kwargs.get('order_by', 'name')
        return Product.objects.all().order_by(order_by)

    def resolve_all_orders(self, info, **kwargs):
        order_by = kwargs.get('order_by', '-order_date')
        return Order.objects.all().order_by(order_by)

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None


# ============================================================================
# Mutation Class
# ============================================================================

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
