import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cisco DNA Center credentials and URL
BASE_URL = "https://sandboxdnac2.cisco.com"
USERNAME = "devnetuser"
PASSWORD = "Cisco123!"

def get_token():
    """
    Fetches an authentication token from Cisco DNA Center.
    """
    url = f"{BASE_URL}/dna/system/api/v1/auth/token"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), headers=headers, verify=False)
    
    if response.status_code == 200:
        token = response.json()["Token"]
        print("Token fetched successfully.")
        return token
    else:
        print("Failed to retrieve token.")
        response.raise_for_status()

def get_device_id(device_name, token):
    """
    Retrieves the device ID for a specific device based on its name.
    """
    url = f"{BASE_URL}/dna/intent/api/v1/network-device"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        devices = response.json()["response"]
        for device in devices:
            if device["hostname"] == device_name:
                print(f"Device ID for '{device_name}' found: {device['id']}")
                return device["id"]
        print(f"Device '{device_name}' not found.")
    else:
        print("Failed to retrieve devices.")
        response.raise_for_status()
    return None

def get_interface_stats(device_id, token):
    """
    Fetches interface statistics for a given device ID.
    """
    url = f"{BASE_URL}/dna/intent/api/v1/interface/network-device/{device_id}"
    #removed /interface to make it work. 
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        interfaces = response.json()["response"]
        print("Interface statistics retrieved successfully.")
        return interfaces
    else:
        print("Failed to retrieve interface statistics.")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)  # <-- Added for debugging
        response.raise_for_status()

def main():
    # Replace 'YourDeviceHostname' with the actual hostname you want to query
    device_name = "switch2.ciscotest.com"
    
    # Step 1: Get the authentication token
    token = get_token()
    
    # Step 2: Retrieve the device ID for the specified device
    device_id = get_device_id(device_name, token)
    if not device_id:
        print("Unable to find device, please check the device name.")
        return

    # Step 3: Retrieve interface statistics for the specified device
    interfaces = get_interface_stats(device_id, token)
    if interfaces:
        print("\nInterface Statistics:")
        for interface in interfaces:
            print(f"Interface Name: {interface['portName']}")
            print(f"    Admin Status: {interface['adminStatus']}")
            print(f"    Operational Status: {interface['status']}")
            print(f"    Speed: {interface['speed']}")
            print(f"    CRC Errors: {interface.get('crcErrorCount', 'N/A')}")
            print("")
            
if __name__ == "__main__":
    main()