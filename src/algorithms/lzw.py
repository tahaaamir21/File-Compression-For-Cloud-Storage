"""
LZW (Lempel-Ziv-Welch) compression algorithm implementation.
"""
from typing import Dict, List, Tuple, Any
from .base_compressor import BaseCompressor


class LZWCompressor(BaseCompressor):
    """LZW compression algorithm implementation."""
    
    def __init__(self):
        super().__init__("LZW")
        self.max_dict_size = 4096  # 12-bit codes
    
    def _initialize_dictionary(self) -> Dict[bytes, int]:
        """Initialize dictionary with single-byte entries."""
        dictionary = {}
        for i in range(256):
            dictionary[bytes([i])] = i
        return dictionary
    
    def _initialize_reverse_dictionary(self) -> Dict[int, bytes]:
        """Initialize reverse dictionary for decompression."""
        reverse_dict = {}
        for i in range(256):
            reverse_dict[i] = bytes([i])
        return reverse_dict
    
    def compress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress data using LZW algorithm.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            Tuple of (compressed_data, metadata)
        """
        if not data:
            return b'', {'compressed_codes': []}
        
        # Initialize dictionary
        dictionary = self._initialize_dictionary()
        next_code = 256
        
        # Compression
        compressed_codes = []
        current_sequence = bytes([data[0]])
        
        for i in range(1, len(data)):
            next_byte = bytes([data[i]])
            test_sequence = current_sequence + next_byte
            
            if test_sequence in dictionary:
                current_sequence = test_sequence
            else:
                # Output code for current sequence
                compressed_codes.append(dictionary[current_sequence])
                
                # Add new sequence to dictionary if not full
                if next_code < self.max_dict_size:
                    dictionary[test_sequence] = next_code
                    next_code += 1
                
                current_sequence = next_byte
        
        # Output code for last sequence
        compressed_codes.append(dictionary[current_sequence])
        
        # Convert codes to bytes (using 12-bit codes)
        compressed_data = self._codes_to_bytes(compressed_codes)
        
        metadata = {
            'compressed_codes': compressed_codes,
            'code_size': 12,  # bits per code
            'max_dict_size': self.max_dict_size
        }
        
        return compressed_data, metadata
    
    def _codes_to_bytes(self, codes: List[int]) -> bytes:
        """Convert list of codes to bytes using 12-bit encoding."""
        if not codes:
            return b''
        
        # Pack codes into bytes
        result = bytearray()
        bit_buffer = 0
        bits_in_buffer = 0
        
        for code in codes:
            # Add code to buffer
            bit_buffer = (bit_buffer << 12) | code
            bits_in_buffer += 12
            
            # Extract complete bytes
            while bits_in_buffer >= 8:
                result.append((bit_buffer >> (bits_in_buffer - 8)) & 0xFF)
                bits_in_buffer -= 8
                bit_buffer &= (1 << bits_in_buffer) - 1
        
        # Add remaining bits
        if bits_in_buffer > 0:
            result.append((bit_buffer << (8 - bits_in_buffer)) & 0xFF)
        
        return bytes(result)
    
    def _bytes_to_codes(self, data: bytes, num_codes: int) -> List[int]:
        """Convert bytes back to list of codes using 12-bit decoding."""
        if not data:
            return []
        
        codes = []
        bit_buffer = 0
        bits_in_buffer = 0
        byte_index = 0
        
        while len(codes) < num_codes and byte_index < len(data):
            # Add byte to buffer
            bit_buffer = (bit_buffer << 8) | data[byte_index]
            bits_in_buffer += 8
            byte_index += 1
            
            # Extract complete codes
            while bits_in_buffer >= 12 and len(codes) < num_codes:
                code = (bit_buffer >> (bits_in_buffer - 12)) & 0xFFF
                codes.append(code)
                bits_in_buffer -= 12
                bit_buffer &= (1 << bits_in_buffer) - 1
        
        return codes
    
    def decompress(self, compressed_data: bytes, metadata: Dict[str, Any]) -> bytes:
        """
        Decompress data using LZW algorithm.
        
        Args:
            compressed_data: Compressed bytes
            metadata: Compression metadata
            
        Returns:
            Original uncompressed data
        """
        if not compressed_data:
            return b''
        
        compressed_codes = metadata['compressed_codes']
        
        # Initialize reverse dictionary
        reverse_dict = self._initialize_reverse_dictionary()
        next_code = 256
        
        # Decompression
        result = bytearray()
        prev_sequence = reverse_dict[compressed_codes[0]]
        result.extend(prev_sequence)
        
        for i in range(1, len(compressed_codes)):
            code = compressed_codes[i]
            
            if code in reverse_dict:
                current_sequence = reverse_dict[code]
            else:
                # Special case: code not in dictionary yet
                current_sequence = prev_sequence + bytes([prev_sequence[0]])
            
            result.extend(current_sequence)
            
            # Add new sequence to dictionary if not full
            if next_code < self.max_dict_size:
                new_sequence = prev_sequence + bytes([current_sequence[0]])
                reverse_dict[next_code] = new_sequence
                next_code += 1
            
            prev_sequence = current_sequence
        
        return bytes(result)
    
    def get_compression_ratio(self) -> float:
        """Get compression ratio for the last compression."""
        if not self.compression_stats:
            return 0.0
        
        original = self.compression_stats['original_size']
        compressed = self.compression_stats['compressed_size']
        
        return compressed / original if original > 0 else 0.0
