import os
import re
import sys
import time
import json
import requests
from datetime import datetime
from scapy.all import sniff, IP, TCP, UDP
from ipaddress import ip_address, ip_network
from elasticsearch import Elasticsearch

CACHE_FILE = "ip_cache.json"

try:
    with open(CACHE_FILE, 'r') as f:
        ip_cache = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    ip_cache = {}

def get_ip_details(ip_address):
    # Check cache first
    if ip_address in ip_cache:
        return ip_cache[ip_address]

    # If not in cache, query the API
    url = f"http://ip-api.com/json/{ip_address}"
    response = requests.get(url)
    if response.status_code == 200:
        ip_details = response.json()
        ip_cache[ip_address] = ip_details  # Store the result in the cache

        # Save the updated cache to the file
        with open(CACHE_FILE, 'w') as f:
            json.dump(ip_cache, f)

        return ip_details
    else:
        return {}


# Connect to the local Elasticsearch instance
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}], http_auth=('elastic', 'changeme'))

def send_to_elasticsearch(sip_data_dict):
    index_name = "sip_data"  # Name of the index

    # Index the data
    response = es.index(index=index_name, document=sip_data_dict)
    return response

def get_external_ip():
    try:
        response = requests.get('https://httpbin.org/ip')
        return response.json()['origin'].split(',')[0].strip()
    except:
        print("Error fetching external IP. Defaulting to 0.0.0.0")
        return "0.0.0.0"

EXTERNAL_IP = get_external_ip()
INTERNAL_RANGES = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

def is_internal(ip):
    for cidr in INTERNAL_RANGES:
        if ip_address(ip) in ip_network(cidr):
            return True
    return False

def parse_sip_data(sip_data_str):
    lines = sip_data_str.split('\n')
    sip_data_dict = {}

    for line in lines:
        parts = line.split(':', 1)
        if len(parts) == 2:
            key, value = parts
            sip_data_dict[key.strip()] = value.strip()

    # Extract additional fields from 'Authorization' if it exists
    if 'Authorization' in sip_data_dict:
        auth_details = sip_data_dict['Authorization'].replace('Digest', '').strip()
        key_value_pairs = re.findall(r'(\w+)=("[^"]+"|[\w/]+)', auth_details)
        for key, value in key_value_pairs:
            sip_data_dict[key] = value.strip('"')

    return sip_data_dict

def process_packet(packet):
    # Check if the packet has the IP layer
    if packet.haslayer(IP):
        dest_ip = packet[IP].dst
        if dest_ip != EXTERNAL_IP and not is_internal(dest_ip):
            return

        # Extract the timestamp
        timestamp = datetime.fromtimestamp(packet.time).isoformat()

        # Check if the packet is SIP over UDP or TCP
        if packet.haslayer(UDP) and (packet[UDP].sport == 5060 or packet[UDP].dport == 5060):
            payload = packet[UDP].payload
        elif packet.haslayer(TCP) and (packet[TCP].sport == 5060 or packet[TCP].dport == 5060 or 
                                       packet[TCP].sport == 5061 or packet[TCP].dport == 5061):
            payload = packet[TCP].payload
        else:
            return

        sip_data = bytes(payload)
        if sip_data:
            print("=" * 60)
            print("Source_IP: {}".format(packet[IP].src))
            print("Destination_IP: {}".format(packet[IP].dst))
            print("-" * 60)
            print(sip_data.decode('utf-8', errors='replace'))  # Decoding, replacing errors just in case

        sip_data_str = sip_data.decode('utf-8', errors='replace')
        sip_data_dict = parse_sip_data(sip_data_str)
        sip_data_dict["Timestamp"] = timestamp  # Add the timestamp to the dictionary

        # Extract Authorization header details
        auth_match = re.search(r'Authorization: Digest ([^\r\n]+)', sip_data_str)
        if auth_match:
            auth_details = auth_match.group(1)
            print("Authorization Details:")
            auth_dict = {}
            key_value_pairs = re.findall(r'(\w+)=("[^"]+"|[\w/]+)', auth_details)
            for key, value in key_value_pairs:
                print("{}: {}".format(key, value.strip('"')))
                auth_dict[key] = value.strip('"')
            sip_data_dict["Authorization_Details"] = auth_dict
            print("-" * 60)
            print("=" * 60)
        # Query IP details and add to sip_data_dict
        source_ip_details = get_ip_details(packet[IP].src)
        sip_data_dict["Source_IP_Details"] = source_ip_details
        # Send the data to Elasticsearch
        response = send_to_elasticsearch(sip_data_dict)

def main():
    try:
        # Start sniffing the network for SIP traffic
        print("Starting capture...")
        sniff(filter="port 5060 or port 5061", prn=process_packet, store=0)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
