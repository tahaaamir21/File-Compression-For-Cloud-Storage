"""
Simple cloud storage simulator to model upload/download bandwidth and storage costs.
"""
import os
import time
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from ..algorithms.huffman import HuffmanCompressor
from ..algorithms.arithmetic import ArithmeticCompressor


@dataclass
class PricingModel:
    storage_per_gb_month_usd: float = 0.02  # example cold storage pricing
    egress_per_gb_usd: float = 0.09
    ingress_per_gb_usd: float = 0.00


# Algorithm mapping for compression
ALGORITHMS = {
    'huffman': HuffmanCompressor,
    'arithmetic': ArithmeticCompressor,
    None: None
}


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

    def upload(self, local_path: str, object_name: str | None = None, simulate_latency: bool = True,
               compress: bool = False, algorithm: str | None = None) -> Dict[str, Any]:
        if not os.path.exists(local_path):
            raise FileNotFoundError(local_path)
        object_name = object_name or os.path.basename(local_path)
        
        # Original file size
        original_size = os.path.getsize(local_path)
        
        # Compress if requested
        compression_stats = None
        if compress and algorithm and algorithm in ALGORITHMS:
            compressor = ALGORITHMS[algorithm]()
            with open(local_path, "rb") as f:
                original_data = f.read()
            compressed_data, metadata = compressor.compress(original_data)
            
            # Save compressed version
            compressed_path = os.path.join(self.bucket_dir, object_name + '.compressed')
            with open(compressed_path, "wb") as f:
                f.write(compressed_data)
            
            # Save metadata
            metadata_path = os.path.join(self.bucket_dir, object_name + '.metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            # Save compression info
            info_path = os.path.join(self.bucket_dir, object_name + '.info.json')
            compression_info = {
                'algorithm': algorithm,
                'original_size': original_size,
                'compressed_size': len(compressed_data),
                'compression_ratio': len(compressed_data) / original_size if original_size > 0 else 0
            }
            with open(info_path, 'w') as f:
                json.dump(compression_info, f)
            
            size_bytes = len(compressed_data)
            dest_path = compressed_path
            compression_stats = compression_info
        else:
            # No compression
            dest_path = os.path.join(self.bucket_dir, object_name)
            with open(local_path, "rb") as src, open(dest_path, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            size_bytes = original_size

        start = time.time()
        if simulate_latency:
            seconds = (size_bytes * 8) / (self.upload_mbps * 1_000_000)
            time.sleep(min(seconds, 2.0))

        elapsed = time.time() - start
        ingress_cost = self._gb(size_bytes) * self.pricing.ingress_per_gb_usd
        
        result = {
            "object": object_name,
            "size_bytes": size_bytes,
            "original_size": original_size if compress else size_bytes,
            "compressed": compress,
            "seconds": elapsed,
            "throughput_mbps": (size_bytes * 8 / 1_000_000) / elapsed if elapsed > 0 else 0.0,
            "ingress_cost_usd": ingress_cost,
        }
        
        if compression_stats:
            result['compression_stats'] = compression_stats
            
        return result

    def download(self, object_name: str, local_path: str, simulate_latency: bool = True) -> Dict[str, Any]:
        compressed_path = os.path.join(self.bucket_dir, object_name + '.compressed')
        info_path = os.path.join(self.bucket_dir, object_name + '.info.json')
        
        # Check if this is a compressed file
        is_compressed = os.path.exists(compressed_path) and os.path.exists(info_path)
        
        if is_compressed:
            src_path = compressed_path
            with open(info_path, 'r') as f:
                compression_info = json.load(f)
            algorithm = compression_info['algorithm']
        else:
            src_path = os.path.join(self.bucket_dir, object_name)
            if not os.path.exists(src_path):
                raise FileNotFoundError(src_path)
        
        size_bytes = os.path.getsize(src_path)
        start = time.time()

        if simulate_latency:
            seconds = (size_bytes * 8) / (self.download_mbps * 1_000_000)
            time.sleep(min(seconds, 2.0))

        # Download and decompress if needed
        if is_compressed and algorithm in ALGORITHMS:
            # Read compressed data
            with open(src_path, "rb") as f:
                compressed_data = f.read()
            
            # Read metadata
            metadata_path = os.path.join(self.bucket_dir, object_name + '.metadata.json')
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Decompress
            compressor = ALGORITHMS[algorithm]()
            metadata = compressor._fix_json_keys(metadata)
            original_data = compressor.decompress(compressed_data, metadata)
            
            # Write decompressed data
            with open(local_path, "wb") as f:
                f.write(original_data)
            
            original_size = len(original_data)
        else:
            # No compression, copy as-is
            with open(src_path, "rb") as src, open(local_path, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            original_size = size_bytes

        elapsed = time.time() - start
        egress_cost = self._gb(size_bytes) * self.pricing.egress_per_gb_usd

        result = {
            "object": object_name,
            "size_bytes": size_bytes,
            "downloaded_size": original_size if is_compressed else size_bytes,
            "compressed": is_compressed,
            "seconds": elapsed,
            "throughput_mbps": (size_bytes * 8 / 1_000_000) / elapsed if elapsed > 0 else 0.0,
            "egress_cost_usd": egress_cost,
        }
        
        if is_compressed:
            result['savings_bytes'] = original_size - size_bytes
            result['savings_percent'] = ((original_size - size_bytes) / original_size * 100) if original_size > 0 else 0
        
        return result

    def storage_summary(self) -> Dict[str, Any]:
        total_bytes = 0
        objects = []
        for name in os.listdir(self.bucket_dir):
            # Skip metadata and info files in summary
            if name.endswith('.metadata.json') or name.endswith('.info.json'):
                continue
                
            p = os.path.join(self.bucket_dir, name)
            if os.path.isfile(p):
                size = os.path.getsize(p)
                total_bytes += size
                
                # Check if this is compressed
                info_path = os.path.join(self.bucket_dir, name.replace('.compressed', '') + '.info.json')
                if os.path.exists(info_path):
                    with open(info_path, 'r') as f:
                        info = json.load(f)
                    objects.append({
                        "object": name.replace('.compressed', ''),
                        "size_bytes": size,
                        "original_size": info.get('original_size', size),
                        "compressed": True,
                        "compression_ratio": info.get('compression_ratio', 0)
                    })
                else:
                    objects.append({"object": name, "size_bytes": size, "compressed": False})
        
        monthly_cost = self._gb(total_bytes) * self.pricing.storage_per_gb_month_usd
        return {
            "objects": objects,
            "total_bytes": total_bytes,
            "storage_gb": self._gb(total_bytes),
            "estimated_monthly_cost_usd": monthly_cost,
        }


