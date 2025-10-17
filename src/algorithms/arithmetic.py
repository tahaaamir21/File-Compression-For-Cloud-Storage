"""
Arithmetic coding implementation for advanced compression.
"""
import math
from typing import Dict, Tuple, Any
from .base_compressor import BaseCompressor


class ArithmeticCompressor(BaseCompressor):
    """Arithmetic coding compressor implementation."""
    
    def __init__(self, precision: int = 32):
        super().__init__("Arithmetic")
        self.precision = precision
        self.max_value = (1 << precision) - 1
        self.half = 1 << (precision - 1)
        self.quarter = 1 << (precision - 2)
    
    def _build_frequency_table(self, data: bytes) -> Dict[int, int]:
        """Build frequency table for characters in data."""
        freq_table = {}
        for byte in data:
            freq_table[byte] = freq_table.get(byte, 0) + 1
        return freq_table
    
    def _build_cumulative_freq(self, freq_table: Dict[int, int]) -> Tuple[Dict[int, int], int]:
        """Build cumulative frequency table."""
        sorted_chars = sorted(freq_table.keys())
        cumulative = {}
        total = 0
        
        for char in sorted_chars:
            cumulative[char] = total
            total += freq_table[char]
        
        return cumulative, total
    
    def _normalize_frequencies(self, freq_table: Dict[int, int], total: int) -> Dict[int, float]:
        """Normalize frequencies to probabilities."""
        return {char: freq / total for char, freq in freq_table.items()}
    
    def compress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress data using arithmetic coding.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            Tuple of (compressed_data, metadata)
        """
        if not data:
            return b'', {'freq_table': {}, 'total_symbols': 0}
        
        # Build frequency table
        freq_table = self._build_frequency_table(data)
        total_symbols = len(data)
        
        # Normalize frequencies
        probabilities = self._normalize_frequencies(freq_table, total_symbols)
        
        # Build cumulative frequency table
        cumulative_freq, total_freq = self._build_cumulative_freq(freq_table)
        
        # Initialize range
        low = 0
        high = self.max_value
        
        # Encode data
        for byte in data:
            # Calculate new range
            range_size = high - low + 1
            char_low = low + (range_size * cumulative_freq[byte]) // total_freq
            char_high = low + (range_size * (cumulative_freq[byte] + freq_table[byte])) // total_freq - 1
            
            low = char_low
            high = char_high
            
            # Normalize range to prevent underflow
            while True:
                if high < self.half:
                    # Range in lower half
                    self._emit_bit(0)
                    low = 2 * low
                    high = 2 * high + 1
                elif low >= self.half:
                    # Range in upper half
                    self._emit_bit(1)
                    low = 2 * (low - self.half)
                    high = 2 * (high - self.half) + 1
                elif low >= self.quarter and high < 3 * self.quarter:
                    # Range in middle half
                    self._pending_bits += 1
                    low = 2 * (low - self.quarter)
                    high = 2 * (high - self.quarter) + 1
                else:
                    break
        
        # Emit final bits
        self._emit_bit(1)
        
        # Convert to bytes
        compressed_data = self._bits_to_bytes()
        
        metadata = {
            'freq_table': freq_table,
            'total_symbols': total_symbols,
            'cumulative_freq': cumulative_freq,
            'total_freq': total_freq
        }
        
        return compressed_data, metadata
    
    def _emit_bit(self, bit: int):
        """Emit a bit to the output stream."""
        if not hasattr(self, '_bit_buffer'):
            self._bit_buffer = 0
            self._bits_in_buffer = 0
            self._pending_bits = 0
        
        self._bit_buffer = (self._bit_buffer << 1) | bit
        self._bits_in_buffer += 1
        
        # Emit pending bits if any
        while self._pending_bits > 0:
            self._bit_buffer = (self._bit_buffer << 1) | (1 - bit)
            self._bits_in_buffer += 1
            self._pending_bits -= 1
        
        # Emit complete bytes
        if self._bits_in_buffer >= 8:
            if not hasattr(self, '_output_bytes'):
                self._output_bytes = bytearray()
            self._output_bytes.append(self._bit_buffer >> (self._bits_in_buffer - 8))
            self._bits_in_buffer -= 8
            self._bit_buffer &= (1 << self._bits_in_buffer) - 1
    
    def _bits_to_bytes(self) -> bytes:
        """Convert bit buffer to bytes."""
        if not hasattr(self, '_output_bytes'):
            return b''
        
        # Add remaining bits
        if self._bits_in_buffer > 0:
            self._output_bytes.append(self._bit_buffer << (8 - self._bits_in_buffer))
        
        return bytes(self._output_bytes)
    
    def decompress(self, compressed_data: bytes, metadata: Dict[str, Any]) -> bytes:
        """
        Decompress data using arithmetic coding.
        
        Args:
            compressed_data: Compressed bytes
            metadata: Compression metadata
            
        Returns:
            Original uncompressed data
        """
        if not compressed_data:
            return b''
        
        freq_table = metadata['freq_table']
        total_symbols = metadata['total_symbols']
        cumulative_freq = metadata['cumulative_freq']
        total_freq = metadata['total_freq']
        
        # Convert bytes to bits
        bits = self._bytes_to_bits(compressed_data)
        
        # Initialize decoder
        value = 0
        for i in range(min(self.precision, len(bits))):
            value = (value << 1) | int(bits[i])
        
        bit_index = self.precision
        
        # Initialize range
        low = 0
        high = self.max_value
        
        # Decode data
        result = bytearray()
        
        for _ in range(total_symbols):
            # Calculate range size
            range_size = high - low + 1
            
            # Find symbol
            target = ((value - low + 1) * total_freq - 1) // range_size
            
            # Binary search for symbol
            symbol = None
            for char, cum_freq in cumulative_freq.items():
                if cum_freq <= target < cum_freq + freq_table[char]:
                    symbol = char
                    break
            
            if symbol is None:
                break
            
            result.append(symbol)
            
            # Update range
            char_low = low + (range_size * cumulative_freq[symbol]) // total_freq
            char_high = low + (range_size * (cumulative_freq[symbol] + freq_table[symbol])) // total_freq - 1
            
            low = char_low
            high = char_high
            
            # Normalize range
            while True:
                if high < self.half:
                    low = 2 * low
                    high = 2 * high + 1
                    value = 2 * value + (int(bits[bit_index]) if bit_index < len(bits) else 0)
                    bit_index += 1
                elif low >= self.half:
                    low = 2 * (low - self.half)
                    high = 2 * (high - self.half) + 1
                    value = 2 * (value - self.half) + (int(bits[bit_index]) if bit_index < len(bits) else 0)
                    bit_index += 1
                elif low >= self.quarter and high < 3 * self.quarter:
                    low = 2 * (low - self.quarter)
                    high = 2 * (high - self.quarter) + 1
                    value = 2 * (value - self.quarter) + (int(bits[bit_index]) if bit_index < len(bits) else 0)
                    bit_index += 1
                else:
                    break
        
        return bytes(result)
    
    def _bytes_to_bits(self, data: bytes) -> str:
        """Convert bytes to bit string."""
        bits = ""
        for byte in data:
            bits += format(byte, '08b')
        return bits
    
    def get_compression_ratio(self) -> float:
        """Get compression ratio for the last compression."""
        if not self.compression_stats:
            return 0.0
        
        original = self.compression_stats['original_size']
        compressed = self.compression_stats['compressed_size']
        
        return compressed / original if original > 0 else 0.0
