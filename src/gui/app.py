import io
import json
import os
import sys
import tempfile
import time
import streamlit as st

# Support running via "streamlit run src/gui/app.py" (no package context)
try:
    from ..algorithms.huffman import HuffmanCompressor
    from ..algorithms.lzw import LZWCompressor
    from ..algorithms.arithmetic import ArithmeticCompressor
    from ..analysis.compression_analyzer import CompressionAnalyzer
    from ..analysis.file_type_detector import FileTypeDetector
    from ..storage.cloud_simulator import CloudSimulator
except Exception:
    # Fallback to absolute imports by appending project root to sys.path
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from src.algorithms.huffman import HuffmanCompressor
    from src.algorithms.lzw import LZWCompressor
    from src.algorithms.arithmetic import ArithmeticCompressor
    from src.analysis.compression_analyzer import CompressionAnalyzer
    from src.analysis.file_type_detector import FileTypeDetector
    from src.storage.cloud_simulator import CloudSimulator


ALGORITHMS = {
    "Huffman": HuffmanCompressor,
    "LZW": LZWCompressor,
    "Arithmetic": ArithmeticCompressor,
}


def get_analyzer() -> CompressionAnalyzer:
    if "_analyzer" not in st.session_state:
        st.session_state._analyzer = CompressionAnalyzer()
    return st.session_state._analyzer


def get_cloud() -> CloudSimulator:
    if "_cloud" not in st.session_state:
        st.session_state._cloud = CloudSimulator()
    return st.session_state._cloud


st.set_page_config(page_title="Compression Toolkit", layout="wide")
st.title("Compression Toolkit (Huffman, LZW, Arithmetic)")

tabs = st.tabs(["Compress / Decompress", "Analyze", "Cloud"],)


with tabs[0]:
    st.header("Compress / Decompress")
    uploaded = st.file_uploader("Upload a file", type=None)
    algo_name = st.selectbox("Algorithm", list(ALGORITHMS.keys()), index=0)
    compressor = ALGORITHMS[algo_name]()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Compress")
        if uploaded is not None:
            data = uploaded.read()
            if st.button("Run Compression", use_container_width=True):
                start = time.time()
                compressed, metadata = compressor.compress(data)
                comp_time = time.time() - start
                ratio = len(compressed) / len(data) if len(data) > 0 else 0

                st.success("Compression complete")
                st.write({
                    "algorithm": algo_name,
                    "original_size": len(data),
                    "compressed_size": len(compressed),
                    "compression_ratio": ratio,
                    "compression_time_s": comp_time,
                })

                st.download_button(
                    label="Download compressed data",
                    data=compressed,
                    file_name=f"{uploaded.name}.compressed",
                )
                st.download_button(
                    label="Download metadata (JSON)",
                    data=json.dumps(metadata).encode("utf-8"),
                    file_name=f"{uploaded.name}.metadata.json",
                )

                st.session_state.last_compressed_bytes = compressed
                st.session_state.last_metadata_json = json.dumps(metadata)
                st.session_state.last_algo = algo_name

    with col2:
        st.subheader("Decompress")
        comp_file = st.file_uploader("Compressed file", key="comp_upl")
        meta_file = st.file_uploader("Metadata JSON", type=["json"], key="meta_upl")
        algo_for_decomp = st.selectbox("Algorithm for decompression", list(ALGORITHMS.keys()), index=0, key="algo_dec")
        decomp_compressor = ALGORITHMS[algo_for_decomp]()

        if st.button("Run Decompression", use_container_width=True):
            try:
                comp_bytes = (
                    comp_file.read() if comp_file is not None else st.session_state.get("last_compressed_bytes")
                )
                meta_json = (
                    meta_file.read().decode("utf-8") if meta_file is not None else st.session_state.get("last_metadata_json")
                )
                if not comp_bytes or not meta_json:
                    st.error("Provide compressed bytes and metadata JSON (or compress first).")
                else:
                    metadata = json.loads(meta_json)
                    start = time.time()
                    restored = decomp_compressor.decompress(comp_bytes, metadata)
                    dec_time = time.time() - start
                    st.success("Decompression complete")
                    st.write({
                        "algorithm": algo_for_decomp,
                        "decompressed_size": len(restored),
                        "decompression_time_s": dec_time,
                    })
                    st.download_button(
                        label="Download decompressed data",
                        data=restored,
                        file_name=f"restored_{int(time.time())}",
                    )
            except Exception as e:
                st.error(f"Decompression failed: {e}")


with tabs[1]:
    st.header("Analyze Files / Directories")
    analyzer = get_analyzer()
    target_type = st.radio("Target", ["Single file", "Directory"], horizontal=True)

    if target_type == "Single file":
        upl = st.file_uploader("Choose a file to analyze", key="ana_file")
        if upl is not None and st.button("Analyze file", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(upl.read())
                tmp_path = tmp.name
            res = analyzer.analyze_file(tmp_path)
            st.code(json.dumps(res, indent=2, default=str))
            os.unlink(tmp_path)
            report = analyzer.generate_report()
            st.text(report)
    else:
        dir_path = st.text_input("Directory path")
        if dir_path and os.path.isdir(dir_path) and st.button("Analyze directory", use_container_width=True):
            res = analyzer.analyze_directory(dir_path)
            st.code(json.dumps(res, indent=2, default=str))
            report = analyzer.generate_report()
            st.text(report)


with tabs[2]:
    st.header("Cloud Storage Simulation")
    cloud = get_cloud()
    uploaded_cloud = st.file_uploader("Upload file to cloud bucket", key="cloud_upl")
    if uploaded_cloud is not None and st.button("Upload to cloud", use_container_width=True):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_cloud.read())
            tmp_path = tmp.name
        res = cloud.upload(tmp_path, object_name=uploaded_cloud.name)
        os.unlink(tmp_path)
        st.write(res)

    st.subheader("Bucket summary")
    if st.button("Refresh summary"):
        st.write(cloud.storage_summary())

    st.subheader("Download from cloud")
    object_name = st.text_input("Object name to download")
    if object_name and st.button("Download object", use_container_width=True):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            out_path = tmp.name
        res = cloud.download(object_name, out_path)
        with open(out_path, "rb") as fh:
            data = fh.read()
        os.unlink(out_path)
        st.write(res)
        st.download_button("Download file", data=data, file_name=object_name)


