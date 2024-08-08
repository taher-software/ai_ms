import argparse
import time
import threading
# from google.cloud import monitoring_v3
# from google import auth
from flask_rq2 import RQ
from src.main import app
import requests

# from src.config import Config
from src.config import Config

#Initialize the RQ instance with the Flask app context
app.config.from_object(Config)
rq = RQ(app)
redis_connection = rq.connection
#from src.integration_downloads.downloader import Downloader
from src.video_processing import re_enc
from src.integration_downloads.downloader import Downloader



# def get_project_id():
#     _, project_id = auth.default()
#     return project_id


# def get_instance_zone():
#     metadata_server_url = "http://metadata.google.internal/computeMetadata/v1/instance"
#     headers = {"Metadata-Flavor": "Google"}
#     metadata_zone_url = f"{metadata_server_url}/zone"
#     response = requests.get(metadata_zone_url, headers=headers)
#     if response.status_code == 200:
#         return response.text
#     else:
#         print(
#             f"Failed to retrieve instance zone. Status code: {response.status_code}")
#         return None


# def get_instance_id():
#     metadata_server = "http://metadata.google.internal/computeMetadata/v1/instance/id"
#     headers = {"Metadata-Flavor": "Google"}
#     response = requests.get(metadata_server, headers=headers)
#     if response.status_code == 200:
#         return response.text
#     else:
#         raise ValueError("Failed to retrieve instance ID from Metadata Server")


# def send_metric(project_id, metric_type, resource_labels, value):
#     client = monitoring_v3.MetricServiceClient()
#     project_name = f"projects/{project_id}"
#     series = monitoring_v3.TimeSeries()
#     series.metric.type = f"custom.googleapis.com/{metric_type}"
#     series.resource.type = "gce_instance"
#     series.resource.labels["instance_id"] = resource_labels["instance_id"]
#     series.resource.labels["zone"] = resource_labels["zone"]
#     series.metric.labels["TestLabel"] = "My Label Data"
#     now = time.time()
#     seconds = int(now)
#     nanos = int((now - seconds) * 10**9)
#     interval = monitoring_v3.TimeInterval(
#         {"end_time": {"seconds": seconds, "nanos": nanos}}
#     )
#     point = monitoring_v3.Point(
#         {"interval": interval, "value": {"double_value": value}}
#     )
#     series.points = [point]
#     client.create_time_series(name=project_name, time_series=[series])


# def monitor_queue_size(queue, project_id, instance_id, zone_id):
#     ctx = app.app_context()
#     ctx.push()
#     while True:
#         try:
#             queue_object = rq.get_queue(queue)
#             queue_size = queue_object.count
#             send_metric(
#                 project_id,
#                 "worker_job_queue_size",
#                 {"instance_id": instance_id, "zone": zone_id},
#                 queue_size,
#             )
#         except Exception as e:
#             print(f"Error monitoring queue size: {e}")
#         time.sleep(5)
#     ctx.pop()


def start_rq_worker(queue):
    ctx = app.app_context()
    ctx.push()
    try:
        worker = rq.get_worker(queue)
        worker.work(burst=Config.BURST_MODE)
    except Exception as e:
        print(f"Error starting worker: {e}")
    ctx.pop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", help="The name of the queue to listen on")
    args = parser.parse_args()

    # if Config.GCP_ENV:
    #     project_id = get_project_id()
    #     instance_id = get_instance_id()
    #     instance_zone = get_instance_zone()
    #     instance_zone = instance_zone.split("/")[-1]
    #     monitor_thread = threading.Thread(
    #         target=monitor_queue_size,
    #         args=(args.queue, project_id, instance_id, instance_zone),
    #     )
    #     monitor_thread.daemon = True
    #     monitor_thread.start()

    start_rq_worker(args.queue)
