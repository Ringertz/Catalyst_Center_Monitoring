import requests
from requests.auth import HTTPBasicAuth
import urllib3

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

def main():
    device_name = "switch2.ciscotest.com"  # Update this as necessary
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
        print(f"Interfaces for device '{device_name}':")
        for interface in interfaces:
            print("\n--- Interface Information ---")
            print(f"Port Name: {interface.get('portName', 'N/A')}")
            print(f"Status: {interface.get('status', 'N/A')}")
            print(f"Admin Status: {interface.get('adminStatus', 'N/A')}")
            print(f"MAC Address: {interface.get('macAddress', 'N/A')}")
            print(f"Speed: {interface.get('speed', 'N/A')}")
            print(f"Duplex: {interface.get('duplex', 'N/A')}")
            print(f"MTU: {interface.get('mtu', 'N/A')}")
            print(f"VLAN ID: {interface.get('vlanId', 'N/A')}")
            print(f"IP Address: {interface.get('ipv4Address', 'N/A')}")
            print(f"IP Mask: {interface.get('ipv4Mask', 'N/A')}")
            print(f"Last Input: {interface.get('lastInput', 'N/A')}")
            print(f"Last Output: {interface.get('lastOutput', 'N/A')}")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")

if __name__ == "__main__":
    main()