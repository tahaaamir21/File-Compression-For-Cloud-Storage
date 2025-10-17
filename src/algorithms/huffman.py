"""
Huffman coding implementation for lossless data compression.
"""
import heapq
from collections import Counter, defaultdict
from typing import Dict, Tuple, Any
from .base_compressor import BaseCompressor


class HuffmanNode:
    """Node class for Huffman tree."""
    
    def __init__(self, char: int = None, freq: int = 0, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
    
    def __lt__(self, other):
        return self.freq < other.freq


class HuffmanCompressor(BaseCompressor):
    """Huffman coding compressor implementation."""
    
    def __init__(self):
        super().__init__("Huffman")
        self.huffman_codes = {}
        self.reverse_codes = {}
    
    def _build_frequency_table(self, data: bytes) -> Counter:
        """Build frequency table for characters in data."""
        return Counter(data)
    
    def _build_huffman_tree(self, freq_table: Counter) -> HuffmanNode:
        """Build Huffman tree from frequency table."""
        if len(freq_table) == 1:
            # Special case: only one unique character
            char, freq = freq_table.most_common(1)[0]
            root = HuffmanNode(char, freq)
            return root
        
        # Create priority queue (min heap)
        heap = []
        for char, freq in freq_table.items():
            node = HuffmanNode(char, freq)
            heapq.heappush(heap, node)
        
        # Build tree by combining nodes
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
            heapq.heappush(heap, merged)
        
        return heap[0]
    
    def _generate_codes(self, root: HuffmanNode, code: str = "") -> Dict[int, str]:
        """Generate Huffman codes by traversing the tree."""
        codes = {}
        
        if root.char is not None:
            # Leaf node
            codes[root.char] = code if code else "0"
        else:
            # Internal node
            if root.left:
                codes.update(self._generate_codes(root.left, code + "0"))
            if root.right:
                codes.update(self._generate_codes(root.right, code + "1"))
        
        return codes
    
    def _encode_data(self, data: bytes, codes: Dict[int, str]) -> str:
        """Encode data using Huffman codes."""
        encoded_bits = ""
        for byte in data:
            encoded_bits += codes[byte]
        return encoded_bits
    
    def _bits_to_bytes(self, bits: str) -> bytes:
        """Convert bit string to bytes."""
        # Pad with zeros to make length multiple of 8
        padding = (8 - len(bits) % 8) % 8
        bits += "0" * padding
        
        # Convert to bytes
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            result.append(int(byte_bits, 2))
        
        return bytes(result)
    
    def _bytes_to_bits(self, data: bytes, original_length: int) -> str:
        """Convert bytes back to bit string."""
        bits = ""
        for byte in data:
            bits += format(byte, '08b')
        
        # Remove padding
        return bits[:original_length]
    
    def compress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress data using Huffman coding.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            Tuple of (compressed_data, metadata)
        """
        if not data:
            return b'', {'huffman_codes': {}, 'original_length': 0, 'padding': 0}
        
        # Build frequency table
        freq_table = self._build_frequency_table(data)
        
        # Build Huffman tree
        root = self._build_huffman_tree(freq_table)
        
        # Generate codes
        codes = self._generate_codes(root)
        self.huffman_codes = codes
        self.reverse_codes = {v: k for k, v in codes.items()}
        
        # Encode data
        encoded_bits = self._encode_data(data, codes)
        
        # Convert to bytes
        compressed_data = self._bits_to_bytes(encoded_bits)
        
        # Calculate padding
        padding = (8 - len(encoded_bits) % 8) % 8
        
        metadata = {
            'huffman_codes': codes,
            'original_length': len(encoded_bits),
            'padding': padding
        }
        
        return compressed_data, metadata
    
    def decompress(self, compressed_data: bytes, metadata: Dict[str, Any]) -> bytes:
        """
        Decompress data using Huffman coding.
        
        Args:
            compressed_data: Compressed bytes
            metadata: Compression metadata
            
        Returns:
            Original uncompressed data
        """
        if not compressed_data:
            return b''
        
        codes = metadata['huffman_codes']
        original_length = metadata['original_length']
        
        # Rebuild reverse codes
        reverse_codes = {v: k for k, v in codes.items()}
        
        # Convert bytes back to bits
        bits = self._bytes_to_bits(compressed_data, original_length)
        
        # Decode data
        decoded_data = bytearray()
        current_code = ""
        
        for bit in bits:
            current_code += bit
            if current_code in reverse_codes:
                decoded_data.append(reverse_codes[current_code])
                current_code = ""
        
        return bytes(decoded_data)
    
    def get_compression_ratio(self) -> float:
        """Get compression ratio for the last compression."""
        if not self.compression_stats:
            return 0.0
        
        original = self.compression_stats['original_size']
        compressed = self.compression_stats['compressed_size']
        
        return compressed / original if original > 0 else 0.0
