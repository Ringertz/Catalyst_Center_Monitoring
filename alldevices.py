import requests
from requests.auth import HTTPBasicAuth
import urllib3
import matplotlib.pyplot as plt
from tabulate import tabulate
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace these with your own Cisco DNA Center credentials and URL
USERNAME = 'devnetuser'
PASSWORD = 'Cisco123!'
BASE_URL = 'https://sandboxdnac2.cisco.com'

def get_token():
    """
    Authenticates with Cisco DNA Center and retrieves an authentication token.
    """
    url = f"{BASE_URL}/dna/system/api/v1/auth/token"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), headers=headers, verify=False)
    response.raise_for_status()
    token = response.json()["Token"]
    return token

def get_device_id(device_name, token):
    """
    Fetches the device ID based on the device name.
    """
    url = f"{BASE_URL}/dna/intent/api/v1/network-device"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()

    devices = response.json()["response"]
    for device in devices:
        if device["hostname"] == device_name:
            return device["id"]
    return None

#new function, gets all the devices instead of just one hehe. 
def get_all_devices(token):
    """
    Fetches all device IDs and hostnames in the DNA Center.
    """
    url = f"{BASE_URL}/dna/intent/api/v1/network-device"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()

    devices = response.json()["response"]
    return [(device["id"], device["hostname"]) for device in devices]

#jobbar här.
def get_interface_stats(device_id, token):
    """
    Fetches interface details for a given device ID.
    """
    url = f"{BASE_URL}/dna/intent/api/v1/interface/network-device/{device_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()

    interfaces = response.json()["response"]
    return interfaces

def get_interface_errors(device_id, token):
    url = f"{BASE_URL}/dna/intent/api/v1/interface/network-device/{device_id}/errors"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        return response.json()["response"]
    #return response.json().get("response", [])
    else:
        print("Failed to retrieve interface error statistics.")
        response.raise_for_status()

def display_top_crc_errors(errors_data, top_n=10):
    # Filter out interfaces with CRC errors
    # Does not seem to work because cRc is not up, however the problem seems to come when I can not g
    crc_errors = [
        {
            "portName": interface["portName"],
            "crcErrors": interface.get("crcErrors", 0)
        }
        for interface in errors_data
        if interface.get("crcErrors", 0) > 0
    ]
    
    # Sort interfaces by CRC error count in descending order
    crc_errors_sorted = sorted(crc_errors, key=lambda x: x["crcErrors"], reverse=True)
    
    print(f"\nTop {top_n} Interfaces with CRC Errors:")
    for interface in crc_errors_sorted[:top_n]:
        print(f"Interface {interface['portName']}: {interface['crcErrors']} CRC errors")

    return [interface["portName"] for interface in crc_errors_sorted[:top_n]], [interface["crcErrors"] for interface in crc_errors_sorted[:top_n]]

def plot_crc_errors(port_names, crc_counts):
    if not port_names:
        print("No CRC errors to plot.")
        return
    plt.figure(figsize=(10, 5))
    plt.bar(port_names, crc_counts, color='blue')
    plt.xlabel('Interface Port Names')
    plt.ylabel('CRC Error Count')
    plt.title('Top 10 Interfaces with CRC Errors')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
def print_interfaces_table(interfaces):
    table = []
    headers = ["Port Name", "Status", "Admin Status", "MAC Address", "Speed", "Duplex", "MTU", "VLAN ID", "IP Address", "IP Mask"]
    for interface in interfaces:
        row = [
            interface.get("portName", "N/A"),
            interface.get("status", "N/A"),
            interface.get("adminStatus", "N/A"),
            interface.get("macAddress", "N/A"),
            interface.get("speed", "N/A"),
            interface.get("duplex", "N/A"),
            interface.get("mtu", "N/A"),
            interface.get("vlanId", "N/A"),
            interface.get("ipv4Address", "N/A"),
            interface.get("ipv4Mask", "N/A")
        ]
        table.append(row)
    print(tabulate(table, headers, tablefmt="grid"))



def get_interface_usage(device_id, interface_id, token):
    #test of fake data:

    # Set the date range to the last 30 days
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)    
    url = f"{BASE_URL}/dna/intent/api/v1/interface/{interface_id}/statistics"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }

    params = {
        "startTime": int(start_time.timestamp() * 1000),  # Convert to milliseconds
        "endTime": int(end_time.timestamp() * 1000)
    }
    
    response = requests.get(url, headers=headers, params=params, verify=False)
    
    if response.status_code == 200:
        return response.json()["response"]
    elif response.status_code == 404:
        print(f"No usage data available for interface {interface_id}. It may be unsupported in the lab environment.")
        return None
    else:
        print("Failed to retrieve interface usage statistics.")
        return None

def main():
    token = get_token()
    print("Token fetched successfully.")
    
    devices = get_all_devices(token)
    if not devices:
        print("No devices found.")
        return
    
    for device_id, device_name in devices:
        print(f"\n--- Processing device '{device_name}' ---")
        try:
            interfaces = get_interface_stats(device_id, token)
            print(f"Interfaces for device '{device_name}':")
            print_interfaces_table(interfaces)
            
            # CRC error check and plot
            errors_data = get_interface_errors(device_id, token)
            port_names, crc_counts = display_top_crc_errors(errors_data)
            plot_crc_errors(port_names, crc_counts)

            # Interface usage check
            for interface in interfaces:
                port_name = interface.get("portName", "N/A")
                usage_stats = get_interface_usage_stats(device_id, port_name, token)
                if usage_stats:
                    display_interface_usage(usage_stats, port_name)
                else:
                    print(f"Could not retrieve usage data for port {port_name}")
        
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")
if __name__ == "__main__":
    main()

    