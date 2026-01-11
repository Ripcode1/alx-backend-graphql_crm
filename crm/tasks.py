"""
Celery tasks for CRM application
"""
from celery import shared_task
from datetime import datetime
import requests


@shared_task
def generate_crm_report():
    """
    Generate a weekly CRM report summarizing total orders, customers, and revenue.
    Uses GraphQL queries to fetch the data and logs to /tmp/crm_report_log.txt
    """
    graphql_url = "http://localhost:8000/graphql"
    
    # GraphQL query to fetch report data
    query = """
        query {
            customers {
                id
            }
            orders {
                id
                totalAmount
            }
        }
    """
    
    try:
        # Execute GraphQL query
        response = requests.post(
            graphql_url,
            json={'query': query},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            
            # Calculate metrics
            customers = data.get('customers', [])
            orders = data.get('orders', [])
            
            total_customers = len(customers)
            total_orders = len(orders)
            total_revenue = sum(float(order.get('totalAmount', 0)) for order in orders)
            
            # Create report message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            report_message = (
                f"{timestamp} - Report: {total_customers} customers, "
                f"{total_orders} orders, {total_revenue:.2f} revenue.\n"
            )
            
            # Log the report
            with open('/tmp/crm_report_log.txt', 'a') as log_file:
                log_file.write(report_message)
            
            print(f"CRM Report generated: {report_message.strip()}")
            return {
                'success': True,
                'customers': total_customers,
                'orders': total_orders,
                'revenue': total_revenue
            }
        else:
            error_msg = f"GraphQL request failed with status {response.status_code}"
            print(error_msg)
            
            # Log error
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('/tmp/crm_report_log.txt', 'a') as log_file:
                log_file.write(f"{timestamp} - ERROR: {error_msg}\n")
            
            return {'success': False, 'error': error_msg}
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(error_msg)
        
        # Log error
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('/tmp/crm_report_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} - ERROR: {error_msg}\n")
        
        return {'success': False, 'error': error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        
        # Log error
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('/tmp/crm_report_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} - ERROR: {error_msg}\n")
        
        return {'success': False, 'error': error_msg}
