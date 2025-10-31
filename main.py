import argparse
import os
from src.algorithms.huffman import HuffmanCompressor
from src.algorithms.lzw import LZWCompressor
from src.algorithms.arithmetic import ArithmeticCompressor
from src.analysis.compression_analyzer import CompressionAnalyzer
from src.analysis.file_type_detector import FileTypeDetector
from src.storage.cloud_simulator import CloudSimulator


ALGORITHMS = {
    "huffman": HuffmanCompressor,
    "lzw": LZWCompressor,
    "arithmetic": ArithmeticCompressor,
}


def cmd_compress(args):
    compressor = ALGORITHMS[args.algorithm]()
    stats = compressor.compress_file(args.input, args.output)
    print("Compressed", args.input, "->", args.output)
    print(stats)


def cmd_decompress(args):
    compressor = ALGORITHMS[args.algorithm]()
    stats = compressor.decompress_file(args.input, args.output)
    print("Decompressed", args.input, "->", args.output)
    print(stats)


def cmd_analyze(args):
    analyzer = CompressionAnalyzer()
    if os.path.isdir(args.path):
        result = analyzer.analyze_directory(args.path)
    else:
        result = analyzer.analyze_file(args.path)
    print(analyzer.generate_report())


def cmd_detect(args):
    info = FileTypeDetector().detect_file_type(args.path)
    print(info)


def cmd_cloud(args):
    cloud = CloudSimulator()
    if args.action == "upload":
        compress = getattr(args, 'compress', False)
        algorithm = getattr(args, 'algorithm', None)
        res = cloud.upload(args.path, compress=compress, algorithm=algorithm)
        print(res)
    elif args.action == "download":
        res = cloud.download(args.object, args.path)
        print(res)
    else:
        print(cloud.storage_summary())


def build_parser():
    p = argparse.ArgumentParser(description="Compression toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compress")
    c.add_argument("algorithm", choices=list(ALGORITHMS.keys()))
    c.add_argument("input")
    c.add_argument("output")
    c.set_defaults(func=cmd_compress)

    d = sub.add_parser("decompress")
    d.add_argument("algorithm", choices=list(ALGORITHMS.keys()))
    d.add_argument("input")
    d.add_argument("output")
    d.set_defaults(func=cmd_decompress)

    a = sub.add_parser("analyze")
    a.add_argument("path")
    a.set_defaults(func=cmd_analyze)

    t = sub.add_parser("detect")
    t.add_argument("path")
    t.set_defaults(func=cmd_detect)

    cl = sub.add_parser("cloud")
    cl.add_argument("action", choices=["upload", "download", "summary"])
    cl.add_argument("path", nargs="?", help="File path (local file for upload, output path for download)")
    cl.add_argument("object", nargs="?", help="Cloud object name (for download)")
    cl.add_argument("--compress", action="store_true", help="Compress file before upload")
    cl.add_argument("--algorithm", choices=list(ALGORITHMS.keys()), help="Compression algorithm")
    cl.set_defaults(func=cmd_cloud)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


