#!/usr/bin/env python
"""
Order Reminders Script
Queries GraphQL endpoint for pending orders from the last 7 days and logs reminders.
"""

import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# GraphQL endpoint configuration
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE = '/tmp/order_reminders_log.txt'


def get_pending_orders():
    """
    Query the GraphQL endpoint for orders from the last 7 days.
    Returns the result data or None if an error occurs.
    """
    # Define the GraphQL query
    query = gql("""
        query GetPendingOrders($startDate: String!) {
            orders(orderDateGte: $startDate) {
                id
                orderDate
                customer {
                    email
                    name
                }
            }
        }
    """)
    
    try:
        # Setup GraphQL client
        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            verify=True,
            retries=3,
        )
        client = Client(
            transport=transport,
            fetch_schema_from_transport=False
        )
        
        # Calculate date 7 days ago
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Execute query
        variables = {"startDate": seven_days_ago}
        result = client.execute(query, variable_values=variables)
        
        return result
        
    except Exception as e:
        print(f"Error querying GraphQL endpoint: {str(e)}")
        return None


def log_order_reminders(orders_data):
    """
    Log order reminders to the log file.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(LOG_FILE, 'a') as log_file:
        if orders_data and orders_data.get('orders'):
            orders = orders_data['orders']
            log_file.write(f"\n{timestamp} - Processing {len(orders)} pending orders:\n")
            
            for order in orders:
                order_id = order.get('id', 'N/A')
                customer_email = order.get('customer', {}).get('email', 'N/A')
                customer_name = order.get('customer', {}).get('name', 'Unknown')
                order_date = order.get('orderDate', 'N/A')
                
                log_entry = (
                    f"{timestamp} - Order ID: {order_id}, "
                    f"Customer Email: {customer_email}, "
                    f"Customer Name: {customer_name}, "
                    f"Order Date: {order_date}\n"
                )
                log_file.write(log_entry)
        else:
            log_file.write(f"{timestamp} - No pending orders found in the last 7 days\n")


def main():
    """
    Main function to execute the order reminders process.
    """
    try:
        # Get pending orders from GraphQL
        orders_data = get_pending_orders()
        
        if orders_data is not None:
            # Log the reminders
            log_order_reminders(orders_data)
            print("Order reminders processed!")
            return 0
        else:
            # Log error
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(LOG_FILE, 'a') as log_file:
                log_file.write(
                    f"{timestamp} - Error: Failed to retrieve orders from GraphQL endpoint\n"
                )
            print("Error: Failed to retrieve orders")
            return 1
            
    except Exception as e:
        # Log unexpected errors
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} - Unexpected error: {str(e)}\n")
        print(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
