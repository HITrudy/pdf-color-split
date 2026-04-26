#!/usr/bin/env python3
"""
PDF 黑白/彩色分类 Web 服务
同一局域网下的设备可通过浏览器访问并使用。
"""

import os
import sys
import uuid
import atexit
import shutil

from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory

# Ensure the parent directory is on sys.path so we can import pdf_check
_parent = Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from pdf_check import split_pdf_by_color

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

app.config["UPLOAD_DIR"] = str(UPLOAD_DIR)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB limit


def cleanup_uploads():
    """Remove all files in the uploads directory."""
    if UPLOAD_DIR.exists():
        shutil.rmtree(str(UPLOAD_DIR))
    UPLOAD_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "pdf" not in request.files:
        return jsonify({"error": "请选择 PDF 文件"}), 400

    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "请选择 PDF 文件"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "仅支持 PDF 文件"}), 400

    # Save to unique filename
    uid = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{uid}_input.pdf"
    file.save(str(input_path))

    bw_output = UPLOAD_DIR / f"{uid}_bw.pdf"
    color_output = UPLOAD_DIR / f"{uid}_color.pdf"

    cutoff = request.form.get("cutoff", "").strip()
    cutoff_page = int(cutoff) if cutoff.isdigit() else None

    try:
        result = split_pdf_by_color(
            str(input_path), str(bw_output), str(color_output),
            cutoff_page=cutoff_page,
        )
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500
    finally:
        # Remove the uploaded input file after processing
        if input_path.exists():
            input_path.unlink()

    # Build download URLs
    download_urls = {}
    if result["bw_pages"]:
        download_urls["bw_url"] = f"/download/{uid}_bw.pdf"
    if result["color_pages"]:
        download_urls["color_url"] = f"/download/{uid}_color.pdf"

    return jsonify({
        **result,
        **download_urls,
    })


@app.route("/download/<filename>")
def download(filename):
    """Serve a processed PDF file for download."""
    return send_from_directory(
        str(UPLOAD_DIR), filename, as_attachment=True,
    )


def get_ip():
    """Try to determine the local IP address for display."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    cleanup_uploads()
    atexit.register(cleanup_uploads)
    ip = get_ip()
    print(f"服务启动：http://{ip}:5000")
    print(f"本机访问：http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
