"""
Compression ratio analysis and performance benchmarking.
"""
import time
import os
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd
try:
    import matplotlib.pyplot as plt
except Exception:  # fallback for headless envs
    plt = None
from ..algorithms.huffman import HuffmanCompressor
from ..algorithms.arithmetic import ArithmeticCompressor
from .file_type_detector import FileTypeDetector


class CompressionAnalyzer:
    """Analyzes compression performance across different algorithms and file types."""
    
    def __init__(self):
        self.algorithms = {
            'huffman': HuffmanCompressor(),
            'arithmetic': ArithmeticCompressor()
        }
        self.file_detector = FileTypeDetector()
        self.results = []
    
    def analyze_file(self, file_path: str, algorithms: List[str] = None) -> Dict[str, Any]:
        """
        Analyze compression performance for a single file.
        
        Args:
            file_path: Path to the file to analyze
            algorithms: List of algorithms to test (default: all)
            
        Returns:
            Analysis results
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        if algorithms is None:
            algorithms = list(self.algorithms.keys())
        
        # Detect file type
        file_info = self.file_detector.detect_file_type(file_path)
        
        # Test each algorithm
        results = {
            'file_info': file_info,
            'algorithms': {},
            'best_algorithm': None,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        best_ratio = float('inf')
        
        for algo_name in algorithms:
            if algo_name not in self.algorithms:
                continue
            
            try:
                algo_result = self._test_algorithm(file_path, algo_name)
                results['algorithms'][algo_name] = algo_result
                
                # Track best algorithm
                if algo_result['compression_ratio'] < best_ratio:
                    best_ratio = algo_result['compression_ratio']
                    results['best_algorithm'] = algo_name
                    
            except Exception as e:
                results['algorithms'][algo_name] = {
                    'error': str(e),
                    'compression_ratio': 1.0,
                    'compression_time': 0,
                    'decompression_time': 0
                }
        
        # Store results
        self.results.append(results)
        return results
    
    def _test_algorithm(self, file_path: str, algo_name: str) -> Dict[str, Any]:
        """Test a specific algorithm on a file."""
        algorithm = self.algorithms[algo_name]
        
        # Create temporary output file
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        compressed_path = f"temp_{base_name}_{algo_name}.compressed"
        decompressed_path = f"temp_{base_name}_{algo_name}_decompressed"
        
        try:
            # Compression test
            start_time = time.time()
            compression_stats = algorithm.compress_file(file_path, compressed_path)
            compression_time = time.time() - start_time
            
            # Decompression test
            start_time = time.time()
            decompression_stats = algorithm.decompress_file(compressed_path, decompressed_path)
            decompression_time = time.time() - start_time
            
            # Verify integrity by content
            with open(file_path, 'rb') as f1, open(decompressed_path, 'rb') as f2:
                original_bytes = f1.read()
                decompressed_bytes = f2.read()
            integrity_check = original_bytes == decompressed_bytes
            
            # Clean up temporary files
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
            if os.path.exists(decompressed_path):
                os.remove(decompressed_path)
            
            return {
                'compression_ratio': compression_stats['compression_ratio'],
                'space_saved': compression_stats['space_saved'],
                'space_saved_percent': (compression_stats['space_saved'] / compression_stats['original_size']) * 100,
                'compression_time': compression_time,
                'decompression_time': decompression_time,
                'total_time': compression_time + decompression_time,
                'compression_speed': compression_stats['original_size'] / compression_time if compression_time > 0 else 0,
                'decompression_speed': len(decompressed_bytes) / decompression_time if decompression_time > 0 else 0,
                'integrity_check': integrity_check,
                'original_size': compression_stats['original_size'],
                'compressed_size': compression_stats['compressed_size']
            }
            
        except Exception as e:
            # Clean up on error
            for temp_file in [compressed_path, decompressed_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            raise e
    
    def analyze_directory(self, directory_path: str, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Analyze compression performance for all files in a directory.
        
        Args:
            directory_path: Path to directory to analyze
            file_extensions: List of file extensions to include (default: all)
            
        Returns:
            Directory analysis results
        """
        if not os.path.isdir(directory_path):
            return {'error': 'Directory not found'}
        
        # Find files to analyze
        files_to_analyze = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file_extensions is None or any(file.lower().endswith(ext) for ext in file_extensions):
                    files_to_analyze.append(file_path)
        
        # Analyze each file
        directory_results = {
            'directory_path': directory_path,
            'total_files': len(files_to_analyze),
            'file_results': [],
            'summary': {},
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        for file_path in files_to_analyze:
            try:
                file_result = self.analyze_file(file_path)
                directory_results['file_results'].append(file_result)
            except Exception as e:
                directory_results['file_results'].append({
                    'file_path': file_path,
                    'error': str(e)
                })
        
        # Calculate summary statistics
        directory_results['summary'] = self._calculate_summary(directory_results['file_results'])
        
        return directory_results
    
    def _calculate_summary(self, file_results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from file results."""
        if not file_results:
            return {}
        
        # Collect data for each algorithm
        algorithm_data = {}
        
        for result in file_results:
            if 'algorithms' not in result:
                continue
            
            for algo_name, algo_result in result['algorithms'].items():
                if 'error' in algo_result:
                    continue
                
                if algo_name not in algorithm_data:
                    algorithm_data[algo_name] = {
                        'compression_ratios': [],
                        'compression_times': [],
                        'decompression_times': [],
                        'space_saved_percent': [],
                        'file_sizes': []
                    }
                
                algorithm_data[algo_name]['compression_ratios'].append(algo_result['compression_ratio'])
                algorithm_data[algo_name]['compression_times'].append(algo_result['compression_time'])
                algorithm_data[algo_name]['decompression_times'].append(algo_result['decompression_time'])
                algorithm_data[algo_name]['space_saved_percent'].append(algo_result['space_saved_percent'])
                algorithm_data[algo_name]['file_sizes'].append(algo_result['original_size'])
        
        # Calculate statistics
        summary = {}
        for algo_name, data in algorithm_data.items():
            if not data['compression_ratios']:
                continue
            
            summary[algo_name] = {
                'avg_compression_ratio': sum(data['compression_ratios']) / len(data['compression_ratios']),
                'min_compression_ratio': min(data['compression_ratios']),
                'max_compression_ratio': max(data['compression_ratios']),
                'avg_space_saved_percent': sum(data['space_saved_percent']) / len(data['space_saved_percent']),
                'avg_compression_time': sum(data['compression_times']) / len(data['compression_times']),
                'avg_decompression_time': sum(data['decompression_times']) / len(data['decompression_times']),
                'total_files_tested': len(data['compression_ratios']),
                'total_original_size': sum(data['file_sizes']),
                'total_compressed_size': sum(data['compression_ratios'][i] * data['file_sizes'][i] for i in range(len(data['compression_ratios'])))
            }
        
        return summary
    
    def generate_report(self, output_path: str = None) -> str:
        """Generate a comprehensive compression analysis report."""
        if not self.results:
            return "No analysis results available."
        
        # Create DataFrame for analysis
        data = []
        for result in self.results:
            file_info = result.get('file_info', {})
            for algo_name, algo_result in result.get('algorithms', {}).items():
                if 'error' not in algo_result:
                    data.append({
                        'file_name': file_info.get('name', 'unknown'),
                        'file_size': algo_result.get('original_size', 0),
                        'file_category': file_info.get('category', 'unknown'),
                        'algorithm': algo_name,
                        'compression_ratio': algo_result.get('compression_ratio', 1.0),
                        'space_saved_percent': algo_result.get('space_saved_percent', 0),
                        'compression_time': algo_result.get('compression_time', 0),
                        'decompression_time': algo_result.get('decompression_time', 0),
                        'compression_speed': algo_result.get('compression_speed', 0),
                        'decompression_speed': algo_result.get('decompression_speed', 0)
                    })
        
        if not data:
            return "No valid analysis data available."
        
        df = pd.DataFrame(data)
        
        # Generate report
        report = []
        report.append("=" * 80)
        report.append("COMPRESSION ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total files analyzed: {len(self.results)}")
        report.append("")
        
        # Overall statistics
        report.append("OVERALL STATISTICS")
        report.append("-" * 40)
        for algo in df['algorithm'].unique():
            algo_data = df[df['algorithm'] == algo]
            report.append(f"\n{algo.upper()} ALGORITHM:")
            report.append(f"  Average compression ratio: {algo_data['compression_ratio'].mean():.4f}")
            report.append(f"  Best compression ratio: {algo_data['compression_ratio'].min():.4f}")
            report.append(f"  Worst compression ratio: {algo_data['compression_ratio'].max():.4f}")
            report.append(f"  Average space saved: {algo_data['space_saved_percent'].mean():.2f}%")
            report.append(f"  Average compression speed: {algo_data['compression_speed'].mean():.2f} bytes/sec")
            report.append(f"  Average decompression speed: {algo_data['decompression_speed'].mean():.2f} bytes/sec")
        
        # Category analysis
        report.append("\n\nCATEGORY ANALYSIS")
        report.append("-" * 40)
        for category in df['file_category'].unique():
            if category == 'unknown':
                continue
            report.append(f"\n{category.upper()} FILES:")
            category_data = df[df['file_category'] == category]
            for algo in category_data['algorithm'].unique():
                algo_data = category_data[category_data['algorithm'] == algo]
                report.append(f"  {algo}: {algo_data['compression_ratio'].mean():.4f} avg ratio, {algo_data['space_saved_percent'].mean():.2f}% space saved")
        
        # Best algorithm recommendations
        report.append("\n\nALGORITHM RECOMMENDATIONS")
        report.append("-" * 40)
        best_by_category = df.groupby('file_category')['compression_ratio'].idxmin()
        for category, idx in best_by_category.items():
            if category != 'unknown':
                best_algo = df.loc[idx, 'algorithm']
                best_ratio = df.loc[idx, 'compression_ratio']
                report.append(f"{category}: {best_algo} (ratio: {best_ratio:.4f})")
        
        report_text = "\n".join(report)
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
        
        return report_text
    
    def create_visualization(self, output_path: str = None) -> None:
        """Create visualization charts for compression analysis."""
        if not self.results:
            return
        
        # Prepare data
        data = []
        for result in self.results:
            file_info = result.get('file_info', {})
            for algo_name, algo_result in result.get('algorithms', {}).items():
                if 'error' not in algo_result:
                    data.append({
                        'file_name': file_info.get('name', 'unknown'),
                        'file_category': file_info.get('category', 'unknown'),
                        'algorithm': algo_name,
                        'compression_ratio': algo_result.get('compression_ratio', 1.0),
                        'space_saved_percent': algo_result.get('space_saved_percent', 0)
                    })
        
        if not data or plt is None:
            return
        
        df = pd.DataFrame(data)
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Compression Analysis Visualization', fontsize=16)
        
        # 1. Compression ratio by algorithm
        df.boxplot(column='compression_ratio', by='algorithm', ax=axes[0, 0])
        axes[0, 0].set_title('Compression Ratio by Algorithm')
        axes[0, 0].set_xlabel('Algorithm')
        axes[0, 0].set_ylabel('Compression Ratio')
        
        # 2. Space saved by file category
        category_avg = df.groupby(['file_category', 'algorithm'])['space_saved_percent'].mean().unstack()
        category_avg.plot(kind='bar', ax=axes[0, 1])
        axes[0, 1].set_title('Average Space Saved by Category and Algorithm')
        axes[0, 1].set_xlabel('File Category')
        axes[0, 1].set_ylabel('Space Saved (%)')
        axes[0, 1].legend(title='Algorithm')
        
        # 3. Compression ratio distribution
        df['compression_ratio'].hist(bins=20, ax=axes[1, 0])
        axes[1, 0].set_title('Compression Ratio Distribution')
        axes[1, 0].set_xlabel('Compression Ratio')
        axes[1, 0].set_ylabel('Frequency')
        
        # 4. Algorithm comparison
        algo_avg = df.groupby('algorithm')['compression_ratio'].mean()
        algo_avg.plot(kind='bar', ax=axes[1, 1])
        axes[1, 1].set_title('Average Compression Ratio by Algorithm')
        axes[1, 1].set_xlabel('Algorithm')
        axes[1, 1].set_ylabel('Average Compression Ratio')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def save_results(self, output_path: str) -> None:
        """Save analysis results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
    
    def load_results(self, input_path: str) -> None:
        """Load analysis results from JSON file."""
        with open(input_path, 'r') as f:
            self.results = json.load(f)
