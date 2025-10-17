"""
Simple cloud storage simulator to model upload/download bandwidth and storage costs.
"""
import os
import time
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PricingModel:
    storage_per_gb_month_usd: float = 0.02  # example cold storage pricing
    egress_per_gb_usd: float = 0.09
    ingress_per_gb_usd: float = 0.00


class CloudSimulator:
    """Simulates a minimal cloud object storage account."""

    def __init__(self, bucket_dir: str = ".cloud_bucket", upload_mbps: float = 100.0,
                 download_mbps: float = 200.0, pricing: PricingModel | None = None):
        self.bucket_dir = bucket_dir
        os.makedirs(self.bucket_dir, exist_ok=True)
        self.upload_mbps = max(upload_mbps, 1e-3)
        self.download_mbps = max(download_mbps, 1e-3)
        self.pricing = pricing or PricingModel()

    def _gb(self, bytes_count: int) -> float:
        return bytes_count / (1024 ** 3)

    def upload(self, local_path: str, object_name: str | None = None, simulate_latency: bool = True) -> Dict[str, Any]:
        if not os.path.exists(local_path):
            raise FileNotFoundError(local_path)
        object_name = object_name or os.path.basename(local_path)
        dest_path = os.path.join(self.bucket_dir, object_name)

        size_bytes = os.path.getsize(local_path)
        start = time.time()

        if simulate_latency:
            seconds = (size_bytes * 8) / (self.upload_mbps * 1_000_000)
            time.sleep(min(seconds, 2.0))  # cap wall sleep for demo

        # store (copy) file
        with open(local_path, "rb") as src, open(dest_path, "wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

        elapsed = time.time() - start
        ingress_cost = self._gb(size_bytes) * self.pricing.ingress_per_gb_usd

        return {
            "object": object_name,
            "size_bytes": size_bytes,
            "seconds": elapsed,
            "throughput_mbps": (size_bytes * 8 / 1_000_000) / elapsed if elapsed > 0 else 0.0,
            "ingress_cost_usd": ingress_cost,
        }

    def download(self, object_name: str, local_path: str, simulate_latency: bool = True) -> Dict[str, Any]:
        src_path = os.path.join(self.bucket_dir, object_name)
        if not os.path.exists(src_path):
            raise FileNotFoundError(src_path)

        size_bytes = os.path.getsize(src_path)
        start = time.time()

        if simulate_latency:
            seconds = (size_bytes * 8) / (self.download_mbps * 1_000_000)
            time.sleep(min(seconds, 2.0))

        with open(src_path, "rb") as src, open(local_path, "wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

        elapsed = time.time() - start
        egress_cost = self._gb(size_bytes) * self.pricing.egress_per_gb_usd

        return {
            "object": object_name,
            "size_bytes": size_bytes,
            "seconds": elapsed,
            "throughput_mbps": (size_bytes * 8 / 1_000_000) / elapsed if elapsed > 0 else 0.0,
            "egress_cost_usd": egress_cost,
        }

    def storage_summary(self) -> Dict[str, Any]:
        total_bytes = 0
        objects = []
        for name in os.listdir(self.bucket_dir):
            p = os.path.join(self.bucket_dir, name)
            if os.path.isfile(p):
                size = os.path.getsize(p)
                total_bytes += size
                objects.append({"object": name, "size_bytes": size})
        monthly_cost = self._gb(total_bytes) * self.pricing.storage_per_gb_month_usd
        return {
            "objects": objects,
            "total_bytes": total_bytes,
            "storage_gb": self._gb(total_bytes),
            "estimated_monthly_cost_usd": monthly_cost,
        }


