"""
Cron jobs for the CRM application
This module contains all scheduled tasks for the CRM system.
"""

from datetime import datetime
import requests
import json


def log_crm_heartbeat():
    """
    Log a heartbeat message every 5 minutes to confirm CRM health.
    Optionally queries the GraphQL hello field to verify endpoint responsiveness.
    Format: DD/MM/YYYY-HH:MM:SS CRM is alive
    """
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    graphql_url = "http://localhost:8000/graphql"
    
    # Optional: Query GraphQL endpoint to verify it's responsive
    graphql_status = ""
    try:
        query = {
            "query": """
                query {
                    hello
                }
            """
        }
        
        response = requests.post(
            graphql_url,
            json=query,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('hello'):
                graphql_status = " (GraphQL: OK)"
            else:
                graphql_status = " (GraphQL: No response)"
        else:
            graphql_status = f" (GraphQL: HTTP {response.status_code})"
            
    except requests.exceptions.Timeout:
        graphql_status = " (GraphQL: Timeout)"
    except requests.exceptions.ConnectionError:
        graphql_status = " (GraphQL: Connection failed)"
    except Exception as e:
        graphql_status = f" (GraphQL: {str(e)[:30]})"
    
    # Create log message
    message = f"{timestamp} CRM is alive{graphql_status}\n"
    
    # Append to log file
    try:
        with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
            log_file.write(message)
        print(f"Heartbeat logged: {message.strip()}")
    except Exception as e:
        print(f"Error writing heartbeat log: {str(e)}")


def update_low_stock():
    """
    Execute the UpdateLowStockProducts mutation via GraphQL endpoint.
    Updates products with stock < 10 by incrementing their stock by 10.
    Logs updated product names and new stock levels.
    Runs every 12 hours.
    """
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    graphql_url = "http://localhost:8000/graphql"
    log_file_path = '/tmp/low_stock_updates_log.txt'
    
    # Define the GraphQL mutation
    mutation = {
        "query": """
            mutation {
                updateLowStockProducts {
                    success
                    message
                    products {
                        id
                        name
                        stock
                    }
                }
            }
        """
    }
    
    try:
        # Execute the mutation
        response = requests.post(
            graphql_url,
            json=mutation,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # Log the start of the update process
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"\n{'='*60}\n")
            log_file.write(f"{timestamp} - Low Stock Update Started\n")
            log_file.write(f"{'='*60}\n")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('data', {}).get('updateLowStockProducts', {})
            
            success = result.get('success', False)
            message = result.get('message', 'No message returned')
            products = result.get('products', [])
            
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")
                log_file.write(f"Message: {message}\n")
                log_file.write(f"Products Updated: {len(products)}\n")
                
                if products:
                    log_file.write("\nUpdated Products:\n")
                    log_file.write("-" * 60 + "\n")
                    for product in products:
                        product_name = product.get('name', 'Unknown')
                        product_id = product.get('id', 'N/A')
                        new_stock = product.get('stock', 0)
                        log_file.write(
                            f"  ID: {product_id} | Name: {product_name} | "
                            f"New Stock: {new_stock}\n"
                        )
                else:
                    log_file.write("\nNo products required restocking.\n")
                
                log_file.write("-" * 60 + "\n")
            
            print(f"Low stock update completed: {len(products)} products updated")
            
        else:
            error_msg = f"GraphQL request failed with status {response.status_code}"
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"ERROR: {error_msg}\n")
                log_file.write(f"Response: {response.text[:200]}\n")
            print(error_msg)
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout while connecting to GraphQL endpoint"
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{timestamp} - ERROR: {error_msg}\n")
        print(error_msg)
        
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error: Could not reach GraphQL endpoint"
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{timestamp} - ERROR: {error_msg}\n")
        print(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{timestamp} - ERROR: {error_msg}\n")
        print(error_msg)


# Allow running functions directly for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "heartbeat":
            log_crm_heartbeat()
        elif sys.argv[1] == "lowstock":
            update_low_stock()
        else:
            print("Usage: python cron.py [heartbeat|lowstock]")
    else:
        print("Running both functions for testing...")
        log_crm_heartbeat()
        print()
        update_low_stock()
