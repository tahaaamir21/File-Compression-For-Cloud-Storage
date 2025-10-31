"""
Base compressor class defining the interface for all compression algorithms.
"""
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
import time
import os
import json


class BaseCompressor(ABC):
    """Abstract base class for all compression algorithms."""
    
    def __init__(self, name: str):
        self.name = name
        self.compression_stats = {}
    
    @abstractmethod
    def compress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress the input data.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            Tuple of (compressed_data, metadata)
        """
        pass
    
    @abstractmethod
    def decompress(self, compressed_data: bytes, metadata: Dict[str, Any]) -> bytes:
        """
        Decompress the compressed data.
        
        Args:
            compressed_data: Compressed bytes
            metadata: Compression metadata
            
        Returns:
            Original uncompressed data
        """
        pass
    
    def compress_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Compress a file and save the result.
        
        Args:
            input_path: Path to input file
            output_path: Path to output compressed file
            
        Returns:
            Compression statistics
        """
        start_time = time.time()
        
        # Read input file
        with open(input_path, 'rb') as f:
            original_data = f.read()
        
        original_size = len(original_data)
        
        # Compress data
        compressed_data, metadata = self.compress(original_data)
        compressed_size = len(compressed_data)
        
        # Save compressed file
        with open(output_path, 'wb') as f:
            f.write(compressed_data)
        
        # Save metadata to a separate JSON file
        metadata_path = output_path + '.metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Calculate statistics
        compression_time = time.time() - start_time
        compression_ratio = compressed_size / original_size if original_size > 0 else 0
        space_saved = original_size - compressed_size
        
        stats = {
            'algorithm': self.name,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'space_saved': space_saved,
            'compression_time': compression_time,
            'metadata': metadata
        }
        
        self.compression_stats = stats
        return stats
    
    def decompress_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Decompress a file and save the result.
        
        Args:
            input_path: Path to compressed file
            output_path: Path to output decompressed file
            
        Returns:
            Decompression statistics
        """
        start_time = time.time()
        
        # Read compressed file
        with open(input_path, 'rb') as f:
            compressed_data = f.read()
        
        # Read metadata from JSON file
        metadata_path = input_path + '.metadata.json'
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            # Convert string keys to integers for dictionaries with numeric keys
            metadata = self._fix_json_keys(metadata)
        else:
            # Fallback to in-memory metadata if available
            metadata = self.compression_stats.get('metadata', {})
            if not metadata:
                raise FileNotFoundError(f"Metadata file not found: {metadata_path}. Cannot decompress without metadata.")
        
        # Decompress data
        original_data = self.decompress(compressed_data, metadata)
        
        # Save decompressed file
        with open(output_path, 'wb') as f:
            f.write(original_data)
        
        # Calculate statistics
        decompression_time = time.time() - start_time
        
        stats = {
            'algorithm': self.name,
            'decompression_time': decompression_time,
            'decompressed_size': len(original_data)
        }
        
        return stats
    
    def _fix_json_keys(self, data: Any) -> Any:
        """Recursively convert string keys to integers in nested structures."""
        if isinstance(data, dict):
            # Try to convert keys to int if they are numeric strings
            fixed_dict = {}
            for key, value in data.items():
                fixed_key = key
                if isinstance(key, str) and key.isdigit():
                    try:
                        fixed_key = int(key)
                    except ValueError:
                        pass
                fixed_dict[fixed_key] = self._fix_json_keys(value)
            return fixed_dict
        elif isinstance(data, list):
            return [self._fix_json_keys(item) for item in data]
        else:
            return data
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get the latest compression statistics."""
        return self.compression_stats.copy()
