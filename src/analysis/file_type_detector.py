"""
File type detection and classification for optimized compression strategies.
"""
import os
import mimetypes
from typing import Dict, List, Tuple, Optional
from PIL import Image
try:
    import magic  # optional: requires libmagic; may be unavailable on Windows
except Exception:
    magic = None


class FileTypeDetector:
    """Detects file types and suggests optimal compression strategies."""
    
    # File type categories for compression optimization
    TEXT_TYPES = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log'}
    IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    AUDIO_TYPES = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
    VIDEO_TYPES = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
    ARCHIVE_TYPES = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'}
    BINARY_TYPES = {'.exe', '.dll', '.so', '.dylib', '.bin', '.dat'}
    
    def __init__(self):
        self.mime = magic.Magic(mime=True) if magic else None
    
    def detect_file_type(self, file_path: str) -> Dict[str, any]:
        """
        Detect file type and return detailed information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file type information
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        file_info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'mime_type': None,
            'category': 'unknown',
            'compression_strategy': 'general',
            'is_text': False,
            'is_binary': True,
            'entropy': 0.0,
            'redundancy': 0.0
        }
        
        try:
            # Get MIME type
            if self.mime:
                file_info['mime_type'] = self.mime.from_file(file_path)
            else:
                guessed, _ = mimetypes.guess_type(file_path)
                file_info['mime_type'] = guessed or 'application/octet-stream'
            
            # Determine category
            file_info['category'] = self._categorize_file(file_info['extension'], file_info['mime_type'])
            
            # Determine compression strategy
            file_info['compression_strategy'] = self._get_compression_strategy(file_info['category'])
            
            # Analyze file content
            self._analyze_content(file_path, file_info)
            
        except Exception as e:
            file_info['error'] = f"Detection failed: {str(e)}"
        
        return file_info
    
    def _categorize_file(self, extension: str, mime_type: str) -> str:
        """Categorize file based on extension and MIME type."""
        if extension in self.TEXT_TYPES or (mime_type and mime_type.startswith('text/')):
            return 'text'
        elif extension in self.IMAGE_TYPES or (mime_type and mime_type.startswith('image/')):
            return 'image'
        elif extension in self.AUDIO_TYPES or (mime_type and mime_type.startswith('audio/')):
            return 'audio'
        elif extension in self.VIDEO_TYPES or (mime_type and mime_type.startswith('video/')):
            return 'video'
        elif extension in self.ARCHIVE_TYPES or (mime_type and 'compressed' in mime_type):
            return 'archive'
        elif extension in self.BINARY_TYPES or (mime_type and mime_type.startswith('application/')):
            return 'binary'
        else:
            return 'unknown'
    
    def _get_compression_strategy(self, category: str) -> str:
        """Get recommended compression strategy for file category."""
        strategies = {
            'text': 'huffman',      # Huffman works well for text
            'image': 'arithmetic',  # Arithmetic coding good for images
            'audio': 'arithmetic',  # Arithmetic coding for audio
            'video': 'arithmetic',  # Arithmetic coding for video
            'archive': 'skip',      # Skip already compressed files
            'binary': 'huffman',    # Huffman for binary data
            'unknown': 'huffman'    # Default to Huffman
        }
        return strategies.get(category, 'huffman')
    
    def _analyze_content(self, file_path: str, file_info: Dict) -> None:
        """Analyze file content for compression optimization."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 1MB for analysis
                sample_data = f.read(1024 * 1024)
            
            if not sample_data:
                return
            
            # Calculate entropy
            file_info['entropy'] = self._calculate_entropy(sample_data)
            
            # Determine if text or binary
            file_info['is_text'] = self._is_text_data(sample_data)
            file_info['is_binary'] = not file_info['is_text']
            
            # Calculate redundancy
            file_info['redundancy'] = self._calculate_redundancy(sample_data)
            
            # Special analysis for images
            if file_info['category'] == 'image':
                self._analyze_image(file_path, file_info)
                
        except Exception as e:
            file_info['analysis_error'] = str(e)
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of the data."""
        if not data:
            return 0.0
        
        # Count byte frequencies
        byte_counts = {}
        for byte in data:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        data_length = len(data)
        
        for count in byte_counts.values():
            probability = count / data_length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _is_text_data(self, data: bytes) -> bool:
        """Determine if data is text or binary."""
        if not data:
            return True
        
        # Check for null bytes (binary indicator)
        if b'\x00' in data:
            return False
        
        # Check for high percentage of printable ASCII
        printable_count = sum(1 for byte in data if 32 <= byte <= 126 or byte in [9, 10, 13])
        printable_ratio = printable_count / len(data)
        
        return printable_ratio > 0.7
    
    def _calculate_redundancy(self, data: bytes) -> float:
        """Calculate data redundancy (1 - entropy/8)."""
        entropy = self._calculate_entropy(data)
        return 1 - (entropy / 8.0)
    
    def _analyze_image(self, file_path: str, file_info: Dict) -> None:
        """Analyze image-specific properties."""
        try:
            with Image.open(file_path) as img:
                file_info['image_width'] = img.width
                file_info['image_height'] = img.height
                file_info['image_mode'] = img.mode
                file_info['image_format'] = img.format
                
                # Calculate compression potential
                if hasattr(img, 'info') and 'compression' in img.info:
                    file_info['already_compressed'] = True
                else:
                    file_info['already_compressed'] = False
                    
        except Exception as e:
            file_info['image_analysis_error'] = str(e)
    
    def get_compression_recommendations(self, file_info: Dict) -> List[Dict[str, any]]:
        """Get compression algorithm recommendations based on file analysis."""
        recommendations = []
        
        category = file_info.get('category', 'unknown')
        entropy = file_info.get('entropy', 0)
        redundancy = file_info.get('redundancy', 0)
        is_text = file_info.get('is_text', False)
        
        # Base recommendations
        if category == 'text' or is_text:
            recommendations.extend([
                {
                    'algorithm': 'huffman',
                    'priority': 1,
                    'reason': 'Optimal for text data with character frequency patterns',
                    'expected_ratio': 0.4 - 0.6
                },
                {
                    'algorithm': 'arithmetic',
                    'priority': 2,
                    'reason': 'Good for text with repetitive patterns',
                    'expected_ratio': 0.5 - 0.7
                }
            ])
        
        elif category == 'image':
            recommendations.extend([
                {
                    'algorithm': 'arithmetic',
                    'priority': 1,
                    'reason': 'Excellent for image data with patterns',
                    'expected_ratio': 0.3 - 0.8
                },
                {
                    'algorithm': 'huffman',
                    'priority': 2,
                    'reason': 'Good for images with color patterns',
                    'expected_ratio': 0.4 - 0.7
                }
            ])
        
        elif redundancy > 0.5:  # High redundancy
            recommendations.extend([
                {
                    'algorithm': 'arithmetic',
                    'priority': 1,
                    'reason': 'Arithmetic coding excels with high redundancy',
                    'expected_ratio': 0.2 - 0.5
                },
                {
                    'algorithm': 'huffman',
                    'priority': 2,
                    'reason': 'Huffman coding good for high redundancy data',
                    'expected_ratio': 0.3 - 0.6
                }
            ])
        
        else:  # Low redundancy or unknown
            recommendations.extend([
                {
                    'algorithm': 'huffman',
                    'priority': 1,
                    'reason': 'General purpose compression',
                    'expected_ratio': 0.6 - 0.9
                },
                {
                    'algorithm': 'arithmetic',
                    'priority': 2,
                    'reason': 'Theoretical optimal compression',
                    'expected_ratio': 0.7 - 0.9
                }
            ])
        
        return sorted(recommendations, key=lambda x: x['priority'])


# Import math for entropy calculation
import math
