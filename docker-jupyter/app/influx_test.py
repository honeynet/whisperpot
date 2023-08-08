import os, time
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Read the token from the environment variable
token = os.environ.get("INFLUXDB_TOKEN")
org = "myorg"
url = "https://20.212.114.125:8086"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, verify_ssl=False)

bucket="mybucket2"

write_api = write_client.write_api(write_options=SYNCHRONOUS)

for value in range(5):
  point = (
    Point("measurement1")
    .tag("tagname1", "tagvalue1")
    .field("field1", value)
  )
  write_api.write(bucket=bucket, org="myorg", record=point)
  time.sleep(1) # separate points by 1 second
