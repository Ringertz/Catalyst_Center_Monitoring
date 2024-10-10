import requests
from requests.auth import HTTPBasicAuth
import urllib3
import matplotlib.pyplot as plt
from tabulate import tabulate

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#fråga teamet om detta. kan man få testa här, sen att återskapa ett error. 
USERNAME = 'devnetuser'
PASSWORD = 'Cisco123!'
BASE_URL = 'https://sandboxdnac2.cisco.com'

def get_token():
    url = f"{BASE_URL}/dna/system/api/v1/auth/token"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), headers=headers, verify=False)
    response.raise_for_status()
    return response.json()["Token"]

def get_device_id(device_name, token):
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

def get_interface_stats(device_id, token):
    url = f"{BASE_URL}/dna/intent/api/v1/interface/network-device/{device_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()["response"]

def get_interface_errors(device_id, token):
    url = f"{BASE_URL}/dna/intent/api/v1/interface/network-device/{device_id}/errors"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        return response.json()["response"]
    else:
        print("Failed to retrieve interface error statistics.")
        response.raise_for_status()

def display_top_crc_errors(errors_data, top_n=10):
    crc_errors = [
        {
            "portName": interface["portName"],
            "crcErrors": interface.get("crcErrors", 0)
        }
        for interface in errors_data
        if interface.get("crcErrors", 0) > 0
    ]
    
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

def main():
    device_name = "switch2.ciscotest.com"
    token = get_token()
    print("Token fetched successfully.")
    
    device_id = get_device_id(device_name, token)
    if device_id:
        print(f"Device ID for '{device_name}' found: {device_id}")
    else:
        print(f"Device '{device_name}' not found.")
        return

    try:
        interfaces = get_interface_stats(device_id, token)
        print("Interfaces for device:")
        print_interfaces_table(interfaces)
        
        errors_data = get_interface_errors(device_id, token)
        port_names, crc_counts = display_top_crc_errors(errors_data)
        
        if port_names:
            plot_crc_errors(port_names, crc_counts)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")

if __name__ == "__main__":
    main()