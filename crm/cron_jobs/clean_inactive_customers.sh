#!/bin/bash

# Navigate to the project directory (adjust path as needed)
cd /path/to/alx-backend-graphql_crm || exit 1

# Execute Django shell command to delete inactive customers
python manage.py shell << 'PYTHON_SCRIPT'
from crm.models import Customer, Order
from datetime import datetime, timedelta
from django.utils import timezone

# Calculate the date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders or no orders in the last year
customers_with_no_orders = Customer.objects.filter(order__isnull=True).distinct()
customers_with_old_orders = Customer.objects.exclude(
    order__order_date__gte=one_year_ago
).distinct()

# Combine both querysets
inactive_customers = customers_with_no_orders | customers_with_old_orders
inactive_customers = inactive_customers.distinct()

# Count before deletion
count = inactive_customers.count()

# Delete inactive customers
if count > 0:
    inactive_customers.delete()

# Log the result
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
log_message = f"{timestamp} - Deleted {count} inactive customers\n"

with open('/tmp/customer_cleanup_log.txt', 'a') as log_file:
    log_file.write(log_message)

print(f"Deleted {count} inactive customers")
PYTHON_SCRIPT

echo "Customer cleanup script completed"
