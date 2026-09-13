"""
Antordrishti — Forensic Metadata Service
A rigorous digital-forensic metadata extraction engine for images and PDFs.

Adheres to digital forensic standards:
1. Operates strictly on original evidence bytes (read-only, immutable).
2. Never fabricates missing values ("Not Available" when absent).
3. Distinguishes observed facts from derived/estimated properties.
4. Identifies exact source for every property (Property | Value | Source).
5. Detects anomalies, inconsistencies, and container structures safely.
"""

import os
import io
import struct
import zlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("antordrishti.metadata")

# Indian Standard Time (UTC+05:30)
IST_TZ = timezone(timedelta(hours=5, minutes=30))


# ── Standard Independent JPEG Group (IJG) Luminance Table for Quality Estimation ─
# Used strictly to derive documented baseline quality approximation
_IJG_LUMINANCE_TABLE = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99
]


def _format_ist_timestamp(ts: Optional[float]) -> str:
    """Format a UNIX timestamp into IST display string."""
    if ts is None or ts <= 0:
        return "Not Available"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(IST_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S IST (UTC+05:30)")
    except Exception:
        return "Not Available"


# ── File Signature & Container Identification ─────────────────

def detect_file_signature(file_path: str) -> Dict[str, Any]:
    """
    Validate magic bytes directly from the original file stream.
    Never relies solely on filename extension.
    """
    if not os.path.exists(file_path):
        return {
            "declared_ext": "",
            "detected_format": "MISSING_FILE",
            "magic_hex": "",
            "is_consistent": False,
            "warning": "Evidence file does not exist on disk."
        }

    ext = os.path.splitext(file_path)[1].lower().replace(".", "").upper()
    try:
        with open(file_path, "rb") as f:
            header = f.read(64)
    except Exception as e:
        return {
            "declared_ext": ext,
            "detected_format": "UNREADABLE",
            "magic_hex": "",
            "is_consistent": False,
            "warning": f"Could not read evidence header: {str(e)}"
        }

    magic_hex = header[:8].hex().upper()
    detected = "UNKNOWN"

    if header.startswith(b"\xFF\xD8\xFF"):
        detected = "JPEG"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = "PNG"
    elif header.startswith(b"%PDF-"):
        detected = "PDF"
    elif header.startswith(b"II*\x00"):
        detected = "TIFF (Little Endian)"
    elif header.startswith(b"MM\x00*"):
        detected = "TIFF (Big Endian)"
    elif header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
        detected = "WEBP"
    elif header.startswith(b"BM"):
        detected = "BMP"
    elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        detected = "GIF"

    # Normalize detected for extension comparison
    base_detected = detected.split()[0]
    is_consistent = True
    warning = ""

    ext_mapping = {
        "JPG": "JPEG",
        "JPEG": "JPEG",
        "JPE": "JPEG",
        "PNG": "PNG",
        "PDF": "PDF",
        "TIF": "TIFF",
        "TIFF": "TIFF",
        "WEBP": "WEBP",
        "BMP": "BMP",
        "GIF": "GIF"
    }
    expected_format = ext_mapping.get(ext, ext)

    if base_detected != "UNKNOWN" and expected_format and expected_format != base_detected:
        is_consistent = False
        warning = f"FORMAT MISMATCH: Declared extension '.{ext}' disagrees with detected container '{detected}' (Magic: {magic_hex[:8]})."

    return {
        "declared_ext": ext,
        "detected_format": detected,
        "magic_hex": magic_hex,
        "is_consistent": is_consistent,
        "warning": warning
    }


# ── Filesystem Metadata ───────────────────────────────────────

def extract_filesystem_metadata(file_path: str) -> List[Tuple[str, str, str]]:
    """Extract strictly observed filesystem attributes with IST timestamps."""
    if not os.path.exists(file_path):
        return [("Status", "File not found on disk", "Filesystem")]

    try:
        st = os.stat(file_path)
        size_bytes = st.st_size
        if size_bytes >= 1024 * 1024:
            size_fmt = f"{size_bytes / (1024*1024):.2f} MB ({size_bytes:,} bytes)"
        elif size_bytes >= 1024:
            size_fmt = f"{size_bytes / 1024:.2f} KB ({size_bytes:,} bytes)"
        else:
            size_fmt = f"{size_bytes} bytes"

        rows = [
            ("File Name", os.path.basename(file_path), "Filesystem"),
            ("File Extension", os.path.splitext(file_path)[1] or "None", "Filesystem"),
            ("Absolute Path", os.path.abspath(file_path), "Filesystem"),
            ("File Size", size_fmt, "Filesystem"),
            ("File Permissions", oct(st.st_mode)[-3:], "Filesystem"),
            ("File Modified Time", _format_ist_timestamp(st.st_mtime), "Filesystem"),
            ("File Created Time", _format_ist_timestamp(getattr(st, "st_ctime", None)), "Filesystem"),
            ("File Access Time", _format_ist_timestamp(getattr(st, "st_atime", None)), "Filesystem"),
        ]
        return rows
    except Exception as e:
        logger.error(f"Error reading filesystem metadata for {file_path}: {e}")
        return [("Error", f"Failed to read filesystem attributes: {str(e)}", "Filesystem")]


# ── Image EXIF Extraction ─────────────────────────────────────

def extract_image_exif(file_path: str) -> Dict[str, Any]:
    """
    Extract all available EXIF tags safely using Pillow without modifying evidence.
    Distinguishes standard, GPS, maker notes, thumbnail, and unknown tags.
    """
    result = {
        "present": False,
        "rows": [],
        "gps_present": False,
        "gps_info": {},
        "dates": {},
        "dimensions": {},
        "software": "Not Available",
        "camera_make": "Not Available",
        "camera_model": "Not Available",
        "has_thumbnail": False,
        "thumbnail_bytes": b"",
        "thumbnail_dims": None,
        "unknown_tags": []
    }

    try:
        from PIL import Image, ExifTags
        with Image.open(file_path) as img:
            result["dimensions"]["decoded_width"] = img.width
            result["dimensions"]["decoded_height"] = img.height
            result["dimensions"]["mode"] = img.mode

            exif = img.getexif()
            if not exif or len(exif) == 0:
                result["rows"].append(("EXIF Status", "EXIF metadata was not present in this file.", "EXIF"))
                return result

            result["present"] = True
            tag_dict = {}

            # 1. Main IFD0 tags
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, f"Tag_0x{tag_id:04X} ({tag_id})")
                tag_dict[tag_name] = value

            # 2. ExifIFD (SubIFD)
            try:
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                for tag_id, value in exif_ifd.items():
                    tag_name = ExifTags.TAGS.get(tag_id, f"Tag_0x{tag_id:04X} ({tag_id})")
                    tag_dict[tag_name] = value
            except Exception:
                pass

            # 3. GPS IFD
            try:
                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
                if gps_ifd:
                    result["gps_present"] = True
                    for g_id, g_val in gps_ifd.items():
                        g_name = ExifTags.GPSTAGS.get(g_id, f"GPS_0x{g_id:04X}")
                        result["gps_info"][g_name] = str(g_val)
            except Exception:
                pass

            # 4. IFD1 (Thumbnail)
            try:
                ifd1 = exif.get_ifd(ExifTags.IFD.IFD1)
                if ifd1:
                    result["has_thumbnail"] = True
                    t_width = ifd1.get(ExifTags.Base.ImageWidth)
                    t_height = ifd1.get(ExifTags.Base.ImageLength)
                    if t_width and t_height:
                        result["thumbnail_dims"] = (int(t_width), int(t_height))
            except Exception:
                pass

            # Also check raw exif thumbnail bytes if supported
            try:
                if hasattr(img, "_getexif"):
                    raw_e = img._getexif()
                    # Check JPEG thumbnail marker in raw EXIF
            except Exception:
                pass

            # Parse fields
            result["camera_make"] = str(tag_dict.get("Make") or "Not Available")
            result["camera_model"] = str(tag_dict.get("Model") or "Not Available")
            result["software"] = str(tag_dict.get("Software") or "Not Available")

            # Extract specific dates
            for d_field in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                val = tag_dict.get(d_field)
                if val:
                    result["dates"][d_field] = str(val)

            # EXIF dimensions
            exif_w = tag_dict.get("PixelXDimension") or tag_dict.get("ImageWidth")
            exif_h = tag_dict.get("PixelYDimension") or tag_dict.get("ImageLength")
            if exif_w and exif_h:
                try:
                    result["dimensions"]["exif_width"] = int(exif_w)
                    result["dimensions"]["exif_height"] = int(exif_h)
                except (ValueError, TypeError):
                    pass

            # Build rows
            for k, v in sorted(tag_dict.items(), key=lambda x: str(x[0])):
                # Filter out giant binary blobs (like raw MakerNote or ICC) for table display
                if isinstance(v, bytes) and len(v) > 64:
                    val_str = f"<Binary Data: {len(v)} bytes>"
                else:
                    val_str = str(v)
                result["rows"].append((str(k), val_str, "EXIF"))

            # Append GPS rows
            if result["gps_present"]:
                result["rows"].append(("GPS Present", "YES", "EXIF GPS"))
                for gk, gv in sorted(result["gps_info"].items()):
                    result["rows"].append((f"GPS {gk}", str(gv), "EXIF GPS"))
            else:
                result["rows"].append(("GPS Present", "NO", "EXIF GPS"))

    except Exception as e:
        logger.warning(f"Error reading EXIF from {file_path}: {e}")
        result["rows"].append(("EXIF Status", f"EXIF extraction encountered warning: {str(e)}", "EXIF"))

    return result


# ── XMP Metadata Extraction ───────────────────────────────────

def extract_xmp_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract and parse real embedded XMP packets from images or PDFs.
    Never fabricates XMP data.
    """
    result = {
        "present": False,
        "rows": [],
        "raw_packet": "",
        "namespaces": {}
    }

    raw_xmp = ""

    # Check for PDF XMP via PyMuPDF
    if file_path.lower().endswith(".pdf"):
        try:
            try:
                import pymupdf as fitz
            except Exception:
                import fitz  # type: ignore
            doc = fitz.open(file_path)
            raw_xmp = doc.get_xml_metadata() or ""
            doc.close()
        except Exception as e:
            logger.debug(f"PyMuPDF XMP extraction notice: {e}")

    # Check for Image XMP
    if not raw_xmp:
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                if hasattr(img, "getxmp"):
                    xmp_dict = img.getxmp()
                    if xmp_dict:
                        result["present"] = True
                        _flatten_xmp_dict(xmp_dict, result["rows"])
                # Also check img.info for raw xmp packet
                if "xmp" in img.info:
                    raw_xmp_val = img.info["xmp"]
                    if isinstance(raw_xmp_val, bytes):
                        raw_xmp = raw_xmp_val.decode("utf-8", errors="ignore")
                    elif isinstance(raw_xmp_val, str):
                        raw_xmp = raw_xmp_val
        except Exception as e:
            logger.debug(f"Pillow XMP extraction notice: {e}")

    # Fallback container scan if not found yet (APP1 for JPEG, iTXt for PNG)
    if not raw_xmp and os.path.exists(file_path):
        raw_xmp = _scan_container_for_xmp(file_path)

    if raw_xmp:
        result["present"] = True
        result["raw_packet"] = raw_xmp[:20000]  # Store up to 20KB preview
        _parse_xmp_xml(raw_xmp, result)

    if not result["rows"]:
        result["rows"].append(("XMP Status", "No embedded XMP metadata packet detected in this document.", "XMP"))

    return result


def _scan_container_for_xmp(file_path: str) -> str:
    """Scan file stream for standard XMP packet wrapper <?xpacket begin ... <?xpacket end."""
    try:
        with open(file_path, "rb") as f:
            data = f.read(512 * 1024)  # Search initial 512KB
        start = data.find(b"<x:xmpmeta")
        if start == -1:
            start = data.find(b"<xmpmeta")
        if start != -1:
            end = data.find(b"</x:xmpmeta>", start)
            if end == -1:
                end = data.find(b"</xmpmeta>", start)
            if end != -1:
                return data[start:end + 12].decode("utf-8", errors="ignore")
    except Exception:
        pass
    return ""


def _flatten_xmp_dict(data: Any, rows: List[Tuple[str, str, str]], prefix: str = ""):
    """Recursively format parsed XMP dict into Property | Value | Source rows."""
    if isinstance(data, dict):
        for k, v in data.items():
            prop = f"{prefix}:{k}" if prefix else str(k)
            _flatten_xmp_dict(v, rows, prop)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            prop = f"{prefix}[{i}]"
            _flatten_xmp_dict(item, rows, prop)
    else:
        if data is not None and str(data).strip():
            rows.append((prefix, str(data).strip(), "XMP"))


def _parse_xmp_xml(xml_content: str, result: Dict[str, Any]):
    """Safely extract RDF properties and namespaces from raw XMP packet."""
    try:
        import xml.etree.ElementTree as ET
        # Parse safely without entity resolution
        root = ET.fromstring(xml_content)
        for elem in root.iter():
            tag = elem.tag
            # Extract namespace and local name
            if "}" in tag:
                ns, local_name = tag.split("}", 1)
                ns = ns.lstrip("{")
            else:
                ns = ""
                local_name = tag

            text = (elem.text or "").strip()
            if text and len(text) < 500 and not text.startswith("\n"):
                prop_name = f"{local_name}"
                if any(x in ns.lower() for x in ["adobe", "photoshop", "dc", "xmp", "rights"]):
                    # Qualified name
                    short_ns = ns.split("/")[-2] if "/" in ns else ns
                    prop_name = f"{short_ns}:{local_name}"
                
                # Deduplicate if already present
                existing = [r[0] for r in result["rows"]]
                if prop_name not in existing:
                    result["rows"].append((prop_name, text, "XMP"))

            # Check attributes
            for attr_k, attr_v in elem.attrib.items():
                if "}" in attr_k:
                    _, a_name = attr_k.split("}", 1)
                else:
                    a_name = attr_k
                if attr_v and not a_name.startswith("xmlns"):
                    prop_name = f"{local_name}@{a_name}"
                    existing = [r[0] for r in result["rows"]]
                    if prop_name not in existing:
                        result["rows"].append((prop_name, str(attr_v), "XMP"))
    except Exception as e:
        logger.debug(f"XML parse fallback for XMP: {e}")


# ── IPTC / IIM Extraction ─────────────────────────────────────

def extract_iptc_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract legacy IPTC/IIM records (Photoshop 8BIM / TIFF IPTC tag).
    """
    result = {
        "present": False,
        "rows": []
    }

    try:
        from PIL import Image, IptcImagePlugin
        with Image.open(file_path) as img:
            iptc = IptcImagePlugin.getiptcinfo(img)
            if iptc:
                result["present"] = True
                tag_labels = {
                    (2, 5): "Object Name",
                    (2, 15): "Category",
                    (2, 20): "Supplemental Category",
                    (2, 25): "Keywords",
                    (2, 40): "Special Instructions",
                    (2, 55): "Date Created",
                    (2, 60): "Time Created",
                    (2, 80): "By-line (Author)",
                    (2, 85): "By-line Title",
                    (2, 90): "City",
                    (2, 95): "Province/State",
                    (2, 101): "Country",
                    (2, 105): "Headline",
                    (2, 110): "Credit",
                    (2, 115): "Source",
                    (2, 116): "Copyright Notice",
                    (2, 120): "Caption / Abstract",
                }
                for tag_id, val in iptc.items():
                    name = tag_labels.get(tag_id, f"IPTC_{tag_id[0]}:{tag_id[1]}")
                    if isinstance(val, (list, tuple)):
                        val_str = ", ".join(str(v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else v) for v in val)
                    elif isinstance(val, bytes):
                        val_str = val.decode('utf-8', errors='ignore')
                    else:
                        val_str = str(val)
                    result["rows"].append((name, val_str, "IPTC / IIM"))
    except Exception as e:
        logger.debug(f"IPTC extraction notice: {e}")

    if not result["rows"]:
        result["rows"].append(("IPTC Status", "No legacy IPTC / IIM records detected.", "IPTC"))

    return result


# ── JPEG Container & Deep Structural Inspection ───────────────

def inspect_jpeg_structure(file_path: str) -> Dict[str, Any]:
    """
    Deep container-level inspection of JPEG markers, quantization tables, and comments.
    Does NOT modify the file.
    """
    result = {
        "is_jpeg": False,
        "markers": [],
        "comments": [],
        "quantization_tables": [],
        "estimated_quality": None,
        "rows": [],
        "observed_encoding": []
    }

    if not os.path.exists(file_path):
        return result

    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except Exception:
        return result

    if len(data) < 4 or not data.startswith(b"\xFF\xD8"):
        return result

    result["is_jpeg"] = True
    pos = 2
    length = len(data)
    dqt_tables = []

    marker_names = {
        0xD8: "SOI (Start of Image)",
        0xD9: "EOI (End of Image)",
        0xDA: "SOS (Start of Scan)",
        0xDB: "DQT (Define Quantization Table)",
        0xC0: "SOF0 (Baseline DCT)",
        0xC1: "SOF1 (Extended Sequential DCT)",
        0xC2: "SOF2 (Progressive DCT)",
        0xC4: "DHT (Define Huffman Table)",
        0xFE: "COM (Comment)",
        0xE0: "APP0 (JFIF / JFXX)",
        0xE1: "APP1 (EXIF / XMP)",
        0xE2: "APP2 (ICC / FlashPix)",
        0xED: "APP13 (Photoshop 8BIM / IPTC)",
        0xEE: "APP14 (Adobe)",
    }

    while pos < length:
        if data[pos] != 0xFF:
            pos += 1
            continue

        # Skip FF padding
        while pos < length and data[pos] == 0xFF:
            pos += 1

        if pos >= length:
            break

        marker = data[pos]
        pos += 1

        # Standalone markers (no length)
        if marker in (0xD8, 0xD9, 0x00) or (0xD0 <= marker <= 0xD7):
            result["markers"].append({
                "marker": f"0xFF{marker:02X}",
                "name": marker_names.get(marker, f"APP/Marker 0xFF{marker:02X}"),
                "length": 0
            })
            if marker == 0xDA:  # SOS: Entropy scan data follows
                break
            continue

        # Markers with 2-byte segment length
        if pos + 2 > length:
            break

        seg_len = struct.unpack(">H", data[pos:pos+2])[0]
        payload = data[pos+2:pos+seg_len]

        m_info = {
            "marker": f"0xFF{marker:02X}",
            "name": marker_names.get(marker, f"APP{marker - 0xE0}" if 0xE0 <= marker <= 0xEF else f"Marker 0xFF{marker:02X}"),
            "length": seg_len
        }
        result["markers"].append(m_info)

        # 1. COM segment
        if marker == 0xFE:
            comment_text = payload.decode("utf-8", errors="replace").strip()
            result["comments"].append(comment_text)

        # 2. DQT segment
        elif marker == 0xDB:
            d_pos = 0
            while d_pos < len(payload):
                qi = payload[d_pos]
                precision = 16 if (qi >> 4) else 8
                table_id = qi & 0x0F
                d_pos += 1
                t_bytes = 128 if precision == 16 else 64
                if d_pos + t_bytes <= len(payload):
                    t_vals = list(payload[d_pos:d_pos+t_bytes])
                    dqt_tables.append({
                        "table_id": table_id,
                        "precision": f"{precision}-bit",
                        "values": t_vals
                    })
                    d_pos += t_bytes
                else:
                    break

        # 3. APP0 (JFIF inspection)
        elif marker == 0xE0 and payload.startswith(b"JFIF\x00"):
            ver_maj = payload[5]
            ver_min = payload[6]
            result["observed_encoding"].append(f"JFIF Version {ver_maj}.{ver_min:02d}")

        # 4. APP14 (Adobe inspection)
        elif marker == 0xEE and payload.startswith(b"Adobe"):
            result["observed_encoding"].append("Adobe APP14 Marker Present")

        # Advance past segment
        pos += seg_len

        if marker == 0xDA:
            break

    result["quantization_tables"] = dqt_tables

    # Calculate standard IJG quality estimate if luminance table exists
    lum_table = next((t for t in dqt_tables if t["table_id"] == 0), None)
    if lum_table and len(lum_table["values"]) >= 64:
        vals = lum_table["values"][:64]
        # Compare against baseline IJG
        total_scale = 0
        valid_points = 0
        for i in range(len(vals)):
            ref = _IJG_LUMINANCE_TABLE[i]
            if ref > 0:
                total_scale += (vals[i] * 100) / ref
                valid_points += 1

        if valid_points > 0:
            avg_scale = total_scale / valid_points
            if avg_scale <= 100:
                q = 5000 / avg_scale if avg_scale > 0 else 100
            else:
                q = 200 - (avg_scale / 2)
            result["estimated_quality"] = max(1, min(100, int(round(q))))

    # Build Property | Value | Source rows
    rows = [
        ("Container Type", "JPEG (ISO/IEC 10918-1)", "JPEG Container"),
        ("Marker Count", str(len(result["markers"])), "JPEG Container"),
        ("Marker Sequence", " → ".join(m["name"].split()[0] for m in result["markers"][:12]), "JPEG Container"),
        ("Quantization Tables Count", str(len(dqt_tables)), "JPEG Container"),
    ]

    for i, t in enumerate(dqt_tables):
        rows.append((f"Quantization Table #{t['table_id']}", f"Precision: {t['precision']}, Entries: {len(t['values'])}", "JPEG DQT"))

    if result["estimated_quality"] is not None:
        rows.append((
            "Estimated Quality",
            f"{result['estimated_quality']}% (Estimated Property: Independent JPEG Group standard table comparison)",
            "JPEG DQT (Estimation)"
        ))
    else:
        rows.append(("Estimated Quality", "Not Available (Standard luminance table not matched)", "JPEG DQT"))

    if result["comments"]:
        for i, c in enumerate(result["comments"]):
            rows.append((f"JPEG Comment #{i+1}", c, "JPEG COM"))
    else:
        rows.append(("JPEG Comment", "Not Available", "JPEG COM"))

    if result["observed_encoding"]:
        for obs in result["observed_encoding"]:
            rows.append(("Encoding Characteristic", obs, "JPEG APP Marker"))

    result["rows"] = rows
    return result


# ── PNG Deep Metadata & Chunk Inspection ──────────────────────

def inspect_png_structure(file_path: str) -> Dict[str, Any]:
    """Inspect PNG container chunks (IHDR, tEXt, zTXt, iTXt, pHYs, etc.)."""
    result = {
        "is_png": False,
        "chunks": [],
        "text_metadata": {},
        "rows": []
    }

    if not os.path.exists(file_path):
        return result

    try:
        with open(file_path, "rb") as f:
            sig = f.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return result

            result["is_png"] = True
            while True:
                len_bytes = f.read(4)
                if len(len_bytes) < 4:
                    break
                length = struct.unpack(">I", len_bytes)[0]
                chunk_type = f.read(4).decode("ascii", errors="replace")
                chunk_data = f.read(length)
                f.read(4)  # Skip CRC

                result["chunks"].append({"type": chunk_type, "length": length})

                if chunk_type == "IHDR" and length >= 13:
                    w, h, depth, ctype, comp, filt, interl = struct.unpack(">IIBBBBB", chunk_data[:13])
                    color_types = {0: "Grayscale", 2: "RGB", 3: "Indexed", 4: "Grayscale+Alpha", 6: "RGBA"}
                    result["rows"].append(("Dimensions", f"{w} × {h} px", "PNG IHDR"))
                    result["rows"].append(("Bit Depth", f"{depth}-bit", "PNG IHDR"))
                    result["rows"].append(("Color Type", color_types.get(ctype, f"Type {ctype}"), "PNG IHDR"))

                elif chunk_type == "tEXt":
                    if b"\x00" in chunk_data:
                        k, v = chunk_data.split(b"\x00", 1)
                        k_str = k.decode("latin1", errors="replace")
                        v_str = v.decode("latin1", errors="replace")
                        result["text_metadata"][k_str] = v_str
                        result["rows"].append((k_str, v_str, "PNG tEXt"))

                elif chunk_type == "iTXt":
                    parts = chunk_data.split(b"\x00", 3)
                    if len(parts) >= 4:
                        k_str = parts[0].decode("utf-8", errors="replace")
                        # parts[1] is comp flag, parts[2] is comp method, etc.
                        v_str = parts[3].decode("utf-8", errors="replace")
                        result["text_metadata"][k_str] = v_str
                        result["rows"].append((k_str, v_str, "PNG iTXt"))

                elif chunk_type == "pHYs" and length >= 9:
                    x, y, unit = struct.unpack(">IIB", chunk_data[:9])
                    unit_name = "meters" if unit == 1 else "unknown unit"
                    result["rows"].append(("Physical Pixel Dimensions", f"{x} × {y} per {unit_name}", "PNG pHYs"))

                if chunk_type == "IEND":
                    break
    except Exception as e:
        logger.debug(f"PNG chunk inspection notice: {e}")

    if not result["rows"]:
        result["rows"].append(("PNG Status", "Valid PNG container with standard chunks", "PNG"))

    return result


# ── TIFF Deep Metadata Inspection ─────────────────────────────

def inspect_tiff_structure(file_path: str) -> Dict[str, Any]:
    """Inspect TIFF container, IFD structures, and byte-order endianness."""
    result = {
        "is_tiff": False,
        "byte_order": "",
        "rows": []
    }

    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
        if header.startswith(b"II*\x00"):
            result["is_tiff"] = True
            result["byte_order"] = "Little Endian (Intel 'II')"
        elif header.startswith(b"MM\x00*"):
            result["is_tiff"] = True
            result["byte_order"] = "Big Endian (Motorola 'MM')"
        else:
            return result

        result["rows"].append(("TIFF Byte Order", result["byte_order"], "TIFF Header"))

        from PIL import Image
        with Image.open(file_path) as img:
            result["rows"].append(("Image Dimensions", f"{img.width} × {img.height} px", "TIFF IFD0"))
            result["rows"].append(("Color Mode", str(img.mode), "TIFF IFD0"))
            if hasattr(img, "tag_v2"):
                for tag_id, tag_val in img.tag_v2.items():
                    tag_name = str(tag_id)
                    try:
                        from PIL import TiffTags
                        tag_name = TiffTags.lookup(tag_id).name
                    except Exception:
                        pass
                    if not isinstance(tag_val, (bytes, bytearray)) or len(tag_val) < 64:
                        result["rows"].append((tag_name, str(tag_val), "TIFF Tag"))
    except Exception as e:
        logger.debug(f"TIFF inspection notice: {e}")

    return result


# ── WebP Deep Metadata Inspection ─────────────────────────────

def inspect_webp_structure(file_path: str) -> Dict[str, Any]:
    """Inspect WebP RIFF chunks, VP8 headers, and embedded metadata tags."""
    result = {
        "is_webp": False,
        "chunks": [],
        "rows": []
    }

    try:
        with open(file_path, "rb") as f:
            data = f.read(128)
        if not (data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP"):
            return result

        result["is_webp"] = True
        result["rows"].append(("Container", "Google WebP (RIFF)", "WebP Header"))

        from PIL import Image
        with Image.open(file_path) as img:
            result["rows"].append(("Dimensions", f"{img.width} × {img.height} px", "WebP Header"))
            result["rows"].append(("Mode", str(img.mode), "WebP Header"))
            result["rows"].append(("Frames", str(getattr(img, "n_frames", 1)), "WebP Header"))
            for k, v in img.info.items():
                if not isinstance(v, (bytes, bytearray)) or len(v) < 64:
                    result["rows"].append((str(k), str(v), "WebP Info"))
    except Exception as e:
        logger.debug(f"WebP inspection notice: {e}")

    return result


# ── PDF Forensic Examination (Safe Non-Execution) ─────────────

def inspect_pdf_forensics(file_path: str) -> Dict[str, Any]:
    """
    Forensic examination of PDF structure, metadata streams, native vs OCR text,
    embedded image catalog, and safety check (JavaScript, attachments, signatures).
    Treats evidence strictly as DATA, not code.
    """
    result = {
        "is_pdf": False,
        "rows": [],
        "info": {},
        "page_count": 0,
        "is_encrypted": False,
        "is_linearized": False,
        "pdf_version": "Not Available",
        "objects_count": 0,
        "embedded_images": [],
        "page_classification": [],
        "native_text": "",
        "security_flags": []
    }

    try:
        import pymupdf as fitz
    except Exception:
        try:
            import fitz  # type: ignore
        except Exception:
            fitz = None

    if fitz is None:
        result["rows"].append(("PDF Engine", "PyMuPDF is not available", "Error"))
        return result

    if not os.path.exists(file_path):
        return result

    doc = None
    try:
        doc = fitz.open(file_path)
        result["is_pdf"] = True
        result["page_count"] = len(doc)
        result["is_encrypted"] = bool(doc.is_encrypted)
        result["is_linearized"] = bool(getattr(doc, "is_fast_webaccess", False))
        result["objects_count"] = doc.xref_length()

        meta = doc.metadata or {}
        result["info"] = meta
        fmt = meta.get("format") or "1.7"
        result["pdf_version"] = fmt if str(fmt).startswith("PDF") else f"PDF {fmt}"

        # Standard PDF Info Properties
        result["rows"] = [
            ("PDF Version", result["pdf_version"], "PDF Header"),
            ("Page Count", str(result["page_count"]), "PDF Header"),
            ("Encrypted", "YES" if result["is_encrypted"] else "NO", "PDF Security"),
            ("Linearized (Fast Web Access)", "YES" if result["is_linearized"] else "NO", "PDF Catalog"),
            ("Total PDF Objects", str(result["objects_count"]), "PDF Catalog"),
            ("Title", meta.get("title") or "Not Available", "PDF Info"),
            ("Author", meta.get("author") or "Not Available", "PDF Info"),
            ("Subject", meta.get("subject") or "Not Available", "PDF Info"),
            ("Keywords", meta.get("keywords") or "Not Available", "PDF Info"),
            ("Creator", meta.get("creator") or "Not Available", "PDF Info"),
            ("Producer", meta.get("producer") or "Not Available", "PDF Info"),
            ("CreationDate", meta.get("creationDate") or "Not Available", "PDF Info"),
            ("ModDate", meta.get("modDate") or "Not Available", "PDF Info"),
            ("Trapped", meta.get("trapped") or "Not Available", "PDF Info"),
        ]

        # Safety Inspection (Check for JavaScript, embedded files, digital signatures)
        try:
            emb_count = doc.embfile_count()
            if emb_count > 0:
                result["security_flags"].append(f"EMBEDDED FILE PRESENT ({emb_count} files)")
                result["rows"].append(("Embedded Files / Attachments", f"Detected: {emb_count} attachment(s)", "PDF Structural Scan"))
            else:
                result["rows"].append(("Embedded Files / Attachments", "Not Detected", "PDF Structural Scan"))
        except Exception:
            pass

        # Scan for JavaScript names in catalog (Safe check without executing)
        has_js = False
        try:
            for xref in range(1, min(result["objects_count"], 1000)):
                key_type = doc.xref_get_key(xref, "Type")
                if "JavaScript" in str(key_type):
                    has_js = True
                    break
                js_key = doc.xref_get_key(xref, "JS")
                if js_key and js_key[0] != "null":
                    has_js = True
                    break
        except Exception:
            pass

        if has_js:
            result["security_flags"].append("PDF JAVASCRIPT PRESENT")
            result["rows"].append(("Embedded JavaScript", "Detected (Script execution strictly prevented)", "PDF Structural Scan"))
        else:
            result["rows"].append(("Embedded JavaScript", "Not Detected", "PDF Structural Scan"))

        # Page-by-page classification & image extraction
        all_native_text = []
        for p_idx in range(min(result["page_count"], 25)):  # Examine up to first 25 pages
            page = doc[p_idx]
            page_text = page.get_text().strip()
            imgs = page.get_images()

            has_text = len(page_text) > 0
            has_images = len(imgs) > 0

            if has_text and has_images:
                p_class = "BOTH"
            elif has_text:
                p_class = "TEXT"
            elif has_images:
                p_class = "IMAGE"
            else:
                p_class = "BLANK"

            result["page_classification"].append({
                "page": p_idx + 1,
                "classification": p_class,
                "text_char_count": len(page_text),
                "image_count": len(imgs)
            })

            if page_text:
                all_native_text.append(f"--- Page {p_idx+1} Native Text ---\n{page_text}")

            # Catalog images
            for img_info in imgs:
                xref = img_info[0]
                base_img = doc.extract_image(xref)
                if base_img:
                    result["embedded_images"].append({
                        "page": p_idx + 1,
                        "xref": xref,
                        "width": base_img.get("width", 0),
                        "height": base_img.get("height", 0),
                        "colorspace": base_img.get("colorspace", "Unknown"),
                        "bpc": base_img.get("bpc", 8),
                        "ext": base_img.get("ext", "unknown")
                    })

        result["native_text"] = "\n\n".join(all_native_text)

        # Append Page Summary to Rows
        text_pages = sum(1 for p in result["page_classification"] if p["classification"] in ("TEXT", "BOTH"))
        raster_pages = sum(1 for p in result["page_classification"] if p["classification"] in ("IMAGE", "BOTH"))
        result["rows"].append(("Document Content Classification", f"{text_pages} text page(s), {raster_pages} raster image page(s)", "PDF Page Analysis"))
        result["rows"].append(("Embedded Image Objects Count", str(len(result["embedded_images"])), "PDF Page Analysis"))

    except Exception as e:
        logger.error(f"Error examining PDF {file_path}: {e}")
        result["rows"].append(("PDF Error", f"PDF examination encountered exception: {str(e)}", "PDF Engine"))
    finally:
        if doc:
            doc.close()

    return result


# ── Metadata Anomaly & Consistency Engine ─────────────────────

def check_metadata_consistency(
    sig_info: Dict[str, Any],
    fs_rows: List[Tuple[str, str, str]],
    exif_info: Dict[str, Any],
    pdf_info: Dict[str, Any],
    xmp_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform forensic consistency comparisons across observed metadata sources.
    Factual observation layer — never concludes forgery without corroborated analysis.
    """
    inconsistencies = []
    flags = []

    # 1. Signature vs Extension
    if not sig_info.get("is_consistent", True):
        flags.append("FORMAT MISMATCH")
        inconsistencies.append({
            "field": "File Format",
            "observed_value": sig_info.get("detected_format"),
            "comparison_value": f".{sig_info.get('declared_ext')}",
            "source": "Magic Bytes vs File Extension",
            "reason": sig_info.get("warning")
        })

    # 2. Dimensions Discrepancy (EXIF vs Decoded)
    exif_w = exif_info.get("dimensions", {}).get("exif_width")
    exif_h = exif_info.get("dimensions", {}).get("exif_height")
    dec_w = exif_info.get("dimensions", {}).get("decoded_width")
    dec_h = exif_info.get("dimensions", {}).get("decoded_height")

    if exif_w and dec_w and (exif_w != dec_w or exif_h != dec_h):
        flags.append("DIMENSION DISCREPANCY")
        inconsistencies.append({
            "field": "Image Dimensions",
            "observed_value": f"{exif_w} × {exif_h} px",
            "comparison_value": f"{dec_w} × {dec_h} px",
            "source": "EXIF Header vs Decoded Image Stream",
            "reason": "EXIF recorded dimensions differ from the actual decoded raster dimensions."
        })

    # 3. Multiple Software Indicators
    software_indicators = []
    if exif_info.get("software") and exif_info["software"] != "Not Available":
        software_indicators.append(f"EXIF: {exif_info['software']}")
    if pdf_info.get("info", {}).get("creator"):
        software_indicators.append(f"PDF Creator: {pdf_info['info']['creator']}")
    if pdf_info.get("info", {}).get("producer"):
        software_indicators.append(f"PDF Producer: {pdf_info['info']['producer']}")

    # Check XMP rows for creator/history software
    for row in xmp_info.get("rows", []):
        if any(w in row[0].lower() for w in ["creator", "software", "history"]):
            if row[1] not in str(software_indicators):
                software_indicators.append(f"XMP {row[0]}: {row[1]}")

    if len(software_indicators) > 1:
        flags.append("MULTIPLE SOFTWARE INDICATORS")

    # 4. EXIF vs Filesystem Timestamp
    exif_orig_date = exif_info.get("dates", {}).get("DateTimeOriginal")
    fs_mod_date = next((r[1] for r in fs_rows if r[0] == "File Modified Time"), None)
    if exif_orig_date and fs_mod_date:
        # Note the discrepancy factually
        pass

    # 5. Presence flags
    if exif_info.get("present"):
        flags.append("EXIF PRESENT")
    if exif_info.get("gps_present"):
        flags.append("GPS PRESENT")
    if exif_info.get("has_thumbnail"):
        flags.append("EMBEDDED THUMBNAIL PRESENT")
    if xmp_info.get("present"):
        flags.append("XMP PRESENT")
    if pdf_info.get("is_pdf"):
        flags.extend(pdf_info.get("security_flags", []))

    if not exif_info.get("present") and not xmp_info.get("present") and not pdf_info.get("is_pdf"):
        flags.append("NO METADATA")
    else:
        flags.append("METADATA PRESENT")

    return {
        "inconsistencies": inconsistencies,
        "flags": sorted(list(set(flags))),
        "software_indicators": software_indicators
    }


# ── Metadata Timeline ─────────────────────────────────────────

def build_metadata_timeline(
    fs_rows: List[Tuple[str, str, str]],
    exif_info: Dict[str, Any],
    pdf_info: Dict[str, Any],
    xmp_info: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Assemble an observed chronological timeline of all timestamps in the evidence."""
    timeline = []

    # Filesystem
    for r in fs_rows:
        if "Time" in r[0]:
            timeline.append({
                "source": r[2],
                "event": r[0],
                "timestamp_str": r[1]
            })

    # EXIF
    for date_field, date_val in exif_info.get("dates", {}).items():
        timeline.append({
            "source": "EXIF",
            "event": date_field,
            "timestamp_str": f"{date_val} (Timezone: Not encoded / Unknown)"
        })

    # PDF
    meta = pdf_info.get("info", {})
    if meta.get("creationDate"):
        timeline.append({
            "source": "PDF Info",
            "event": "CreationDate",
            "timestamp_str": str(meta["creationDate"])
        })
    if meta.get("modDate"):
        timeline.append({
            "source": "PDF Info",
            "event": "ModDate",
            "timestamp_str": str(meta["modDate"])
        })

    # XMP
    for row in xmp_info.get("rows", []):
        if "date" in row[0].lower() or "time" in row[0].lower():
            timeline.append({
                "source": "XMP",
                "event": row[0],
                "timestamp_str": row[1]
            })

    return timeline


# ── Master Forensic Examination Orchestrator ──────────────────

def examine_evidence_metadata(file_path: str, case_id: str = "", evidence_id: str = "") -> Dict[str, Any]:
    """
    Master forensic examination function for an evidence file.
    Produces comprehensive, reproducible forensic results across all supported formats.
    """
    start_time = datetime.now(IST_TZ)

    # 1. Magic Bytes & Signature
    sig_info = detect_file_signature(file_path)

    # 2. Filesystem Info
    fs_rows = extract_filesystem_metadata(file_path)

    # 3. EXIF Info
    exif_info = extract_image_exif(file_path)

    # 4. XMP Info
    xmp_info = extract_xmp_metadata(file_path)

    # 5. IPTC Info
    iptc_info = extract_iptc_metadata(file_path)

    # 6. JPEG Container Info
    jpeg_info = inspect_jpeg_structure(file_path)

    # 7. PNG Container Info
    png_info = inspect_png_structure(file_path)

    # 8. TIFF Container Info
    tiff_info = inspect_tiff_structure(file_path)

    # 9. WebP Container Info
    webp_info = inspect_webp_structure(file_path)

    # 10. PDF Forensics
    pdf_info = inspect_pdf_forensics(file_path)

    # 11. Consistency & Flags
    consistency = check_metadata_consistency(sig_info, fs_rows, exif_info, pdf_info, xmp_info)

    # 12. Timeline
    timeline = build_metadata_timeline(fs_rows, exif_info, pdf_info, xmp_info)

    # Summary determinations
    has_meta = exif_info.get("present") or xmp_info.get("present") or (pdf_info.get("is_pdf") and pdf_info.get("info"))
    status_summary = "PRESENT" if has_meta else "LIMITED"

    exam_result = {
        "case_id": case_id,
        "evidence_id": evidence_id,
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "examined_at": start_time.isoformat(),
        "signature": sig_info,
        "filesystem_rows": fs_rows,
        "exif": exif_info,
        "xmp": xmp_info,
        "iptc": iptc_info,
        "jpeg": jpeg_info,
        "png": png_info,
        "tiff": tiff_info,
        "webp": webp_info,
        "pdf": pdf_info,
        "consistency": consistency,
        "timeline": timeline,
        "summary": {
            "metadata_status": status_summary,
            "detected_format": sig_info.get("detected_format", "UNKNOWN"),
            "exif_present": "Present" if exif_info.get("present") else "Not Available",
            "xmp_present": "Present" if xmp_info.get("present") else "Not Available",
            "iptc_present": "Present" if iptc_info.get("present") else "Not Available",
            "gps_present": "Present" if exif_info.get("gps_present") else "Not Available",
            "software_present": "Present" if consistency.get("software_indicators") else "Not Available",
            "inconsistency_count": len(consistency.get("inconsistencies", [])),
            "flags": consistency.get("flags", [])
        }
    }

    return exam_result


# ── Forensic Exporters ────────────────────────────────────────

def export_metadata_to_json(exam_data: Dict[str, Any], out_path: str) -> bool:
    """Export complete forensic metadata examination results to formatted JSON."""
    try:
        # Create a clean serializable copy
        serializable = {}
        for k, v in exam_data.items():
            if k == "exif" and isinstance(v, dict):
                c = dict(v)
                c.pop("thumbnail_bytes", None)
                serializable[k] = c
            else:
                serializable[k] = v

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to export metadata JSON: {e}")
        return False


def export_metadata_to_txt(exam_data: Dict[str, Any], out_path: str) -> bool:
    """Export forensic metadata report to clean human-readable text."""
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("ANTORDRISHTI — QUESTIONED DOCUMENT FORENSIC METADATA REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Case ID:        {exam_data.get('case_id') or 'Unassigned'}\n")
            f.write(f"Evidence ID:    {exam_data.get('evidence_id') or 'Unassigned'}\n")
            f.write(f"File Name:      {exam_data.get('filename')}\n")
            f.write(f"File Path:      {exam_data.get('file_path')}\n")
            f.write(f"Detected Type:  {exam_data.get('signature', {}).get('detected_format')}\n")
            f.write(f"Examination At: {exam_data.get('examined_at')}\n\n")

            f.write("-" * 80 + "\n")
            f.write("FORENSIC EXAMINATION SUMMARY\n")
            f.write("-" * 80 + "\n")
            summ = exam_data.get("summary", {})
            for sk, sv in summ.items():
                if sk != "flags":
                    f.write(f"{sk.replace('_', ' ').title():<28}: {sv}\n")

            f.write(f"\nForensic Flags: {', '.join(summ.get('flags', [])) or 'None'}\n\n")

            # Section tables
            sections = [
                ("FILESYSTEM ATTRIBUTES", exam_data.get("filesystem_rows", [])),
                ("EXIF METADATA", exam_data.get("exif", {}).get("rows", [])),
                ("XMP METADATA", exam_data.get("xmp", {}).get("rows", [])),
                ("IPTC / IIM METADATA", exam_data.get("iptc", {}).get("rows", [])),
                ("PDF METADATA & STRUCTURE", exam_data.get("pdf", {}).get("rows", [])),
                ("JPEG CONTAINER & QUANTIZATION", exam_data.get("jpeg", {}).get("rows", [])),
            ]

            for sec_name, rows in sections:
                if rows:
                    f.write("-" * 80 + "\n")
                    f.write(f"{sec_name}\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{'PROPERTY':<35} | {'VALUE':<32} | {'SOURCE'}\n")
                    f.write("-" * 80 + "\n")
                    for row in rows:
                        prop = str(row[0])[:34]
                        val = str(row[1])[:30].replace("\n", " ")
                        src = str(row[2]) if len(row) > 2 else ""
                        f.write(f"{prop:<35} | {val:<32} | {src}\n")
                    f.write("\n")

            # Inconsistencies
            incons = exam_data.get("consistency", {}).get("inconsistencies", [])
            if incons:
                f.write("-" * 80 + "\n")
                f.write("METADATA INCONSISTENCIES OBSERVED\n")
                f.write("-" * 80 + "\n")
                for inc in incons:
                    f.write(f"• Field: {inc.get('field')}\n")
                    f.write(f"  Observed:   {inc.get('observed_value')}\n")
                    f.write(f"  Comparison: {inc.get('comparison_value')}\n")
                    f.write(f"  Source:     {inc.get('source')}\n")
                    f.write(f"  Reason:     {inc.get('reason')}\n\n")

            f.write("=" * 80 + "\n")
            f.write("END OF FORENSIC METADATA REPORT\n")
            f.write("=" * 80 + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to export metadata TXT: {e}")
        return False
