import requests
from elasticsearch import Elasticsearch
from datetime import datetime
from scapy.all import IP, TCP, UDP, Raw
from scapy.utils import PcapReader


class PacketAnalyzer:
    def __init__(self, elasticsearch_host, elasticsearch_auth, pcap_file_path, target_ip, shodan_key, abuseipdb_key):
        self.es = Elasticsearch([elasticsearch_host], basic_auth=elasticsearch_auth)
        self.pcap_file_path = pcap_file_path
        self.target_ip = target_ip
        self.shodan_key = shodan_key
        self.abuseipdb_key = abuseipdb_key
        self.ip_cache = {}
        self.packet_count = 0

        self.api_endpoints = {
            'ip_api': 'http://ip-api.com/json/',
            'abuseipdb': 'https://api.abuseipdb.com/api/v2/check',
            'shodan': f'https://api.shodan.io/shodan/host/{{}}?key={self.shodan_key}',
        }

        self.headers = {
            'abuseipdb': {
                'Accept': 'application/json',
                'Key': self.abuseipdb_key,
            },
        }

    def _query_api(self, endpoint, ip, headers=None, params=None):
        response = requests.get(self.api_endpoints[endpoint] + ip, headers=headers, params=params)
        return response.json() if response.status_code == 200 else None

    def _query_ip_api(self, ip):
        return self._query_api('ip_api', ip)

    def _query_abuseipdb(self, ip):
        params = {'ipAddress': ip, 'maxAgeInDays': '90'}
        return self._query_api('abuseipdb', ip, headers=self.headers['abuseipdb'], params=params)

    def _query_shodan(self, ip):
        return self._query_api('shodan', ip)

    def _get_ip_info(self, ip, api="all"):
        if ip in self.ip_cache:
            return self.ip_cache[ip]

        ip_info = {}
        if api in ["ip_api", "all"]:
            ip_info["srcIPInfo"] = self._query_ip_api(ip)
        if api in ["abuseipdb", "all"]:
            ip_info["srcIPAbuseInfo"] = self._query_abuseipdb(ip)
        if api in ["shodan", "all"]:
            ip_info["srcIPShodanInfo"] = self._query_shodan(ip)

        self.ip_cache[ip] = ip_info

        return ip_info

    def process_packets(self):
        packets = PcapReader(self.pcap_file_path)

        for packet in packets:
            if packet[IP].dst != self.target_ip:
                continue
            self._process_packet(packet)
            self.packet_count += 1
            if self.packet_count % 5000 == 0:
                print(f"Amount processed: {self.packet_count}")

    def _process_packet(self, packet):
        packet_dict = {
            "packetName": packet.name,
            "packetTime": datetime.fromtimestamp(int(packet.time)),
            "srcIP": packet[IP].src if packet.haslayer(IP) else None,
            "dstIP": packet[IP].dst if packet.haslayer(IP) else None,
            "srcPort": packet.sport if hasattr(packet, 'sport') else 'N/A',
            "dstPort": packet.dport if hasattr(packet, 'dport') else 'N/A',
            "type": getattr(packet, 'type', None),
            "length": getattr(packet, 'len', None),
            "payload": str(packet.payload) if packet.payload else None,
            "decodedString": None,
            "decodedStringKey": None,
            "decodingError": None,
            "hexadecimalString": None,
        }

        if packet.haslayer(IP):
            ip_info = self._get_ip_info(packet[IP].src, api="all")
            packet_dict.update(ip_info)

        if packet.haslayer(Raw):
            packet_dict.update(self._decode_raw_data(packet[Raw].load))

        self.es.index(index="pcap-data", document=packet_dict)

    @staticmethod
    def _decode_raw_data(raw_bytes):
        try:
            decoded_string = raw_bytes.decode('utf-8')
            return {
                "decodedString": decoded_string,
                "decodedStringKey": {key.strip(): value.strip() for key, value in
                                     (line.split(':', 1) for line in decoded_string.split('\n') if ':' in line)},
            }
        except UnicodeDecodeError:
            return {
                "decodingError": "The bytes could not be decoded as a UTF-8 string",
                "hexadecimalString": raw_bytes.hex(),
            }

