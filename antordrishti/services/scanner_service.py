"""
Antordrishti — Scanner Service
Unified interface for USB/standalone, IP, and network scanners.
Supports WIA (Windows Image Acquisition), eSCL/HTTP IP scanners,
and network scanner discovery.
"""

import os
import logging
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger("antordrishti.scanner")


# ── Enums & Data Models ─────────────────────────────────────

class ScannerType(Enum):
    USB = "USB / Standalone"
    IP = "IP Scanner"
    NETWORK = "Network Scanner"


class ColorMode(Enum):
    COLOR = "Color"
    GRAYSCALE = "Grayscale"
    BW = "Black & White"


class PaperSize(Enum):
    A4 = "A4 (210 × 297 mm)"
    LETTER = "Letter (8.5 × 11 in)"
    LEGAL = "Legal (8.5 × 14 in)"
    A3 = "A3 (297 × 420 mm)"
    CUSTOM = "Custom"


class ScanSource(Enum):
    FLATBED = "Flatbed"
    ADF_FRONT = "ADF (Front)"
    ADF_DUPLEX = "ADF (Duplex)"


DPI_OPTIONS = [150, 200, 300, 600, 1200]

# WIA constants
WIA_COLOR = 1
WIA_GRAYSCALE = 2
WIA_BW = 4

# WIA Item property IDs
WIA_HORIZONTAL_RESOLUTION = "6147"
WIA_VERTICAL_RESOLUTION = "6148"
WIA_COLOR_MODE = "6146"
WIA_FORMAT = "4106"
WIA_FORMAT_TIFF = "{B96B3CB1-0728-11D3-9D7B-0000F81EF32E}"
WIA_FORMAT_PNG = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
WIA_FORMAT_BMP = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"


@dataclass
class ScannerDevice:
    """Represents a detected scanner device."""
    device_id: str = ""
    name: str = ""
    scanner_type: ScannerType = ScannerType.USB
    manufacturer: str = ""
    model: str = ""
    ip_address: str = ""
    port: int = 0
    is_available: bool = True
    capabilities: Dict[str, Any] = field(default_factory=dict)

    def display_name(self) -> str:
        if self.scanner_type == ScannerType.IP:
            return f"{self.name} ({self.ip_address}:{self.port})"
        return self.name or self.device_id


@dataclass
class ScanSettings:
    """Configuration for a scan operation."""
    dpi: int = 300
    color_mode: ColorMode = ColorMode.COLOR
    paper_size: PaperSize = PaperSize.A4
    source: ScanSource = ScanSource.FLATBED
    output_format: str = "TIFF"  # TIFF or PNG
    multi_page: bool = False
    output_dir: str = ""

    def __post_init__(self):
        if not self.output_dir:
            self.output_dir = os.path.join(
                os.path.expanduser("~"), ".antordrishti", "scans"
            )
        os.makedirs(self.output_dir, exist_ok=True)


@dataclass
class ScanResult:
    """Result of a scan operation."""
    success: bool = False
    file_paths: List[str] = field(default_factory=list)
    error_message: str = ""
    page_count: int = 0
    scanner_name: str = ""
    dpi: int = 0
    color_mode: str = ""


# ── Scanner Backends ────────────────────────────────────────

class WIAScanner:
    """Windows Image Acquisition scanner backend for USB/standalone scanners."""

    def __init__(self):
        self._wia = None
        self._available = False
        self._init_wia()

    def _init_wia(self):
        """Initialize WIA COM interface."""
        try:
            import win32com.client
            self._wia = win32com.client.Dispatch("WIA.DeviceManager")
            self._available = True
            logger.info("WIA DeviceManager initialized successfully.")
        except Exception as e:
            logger.warning(f"WIA initialization failed: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def discover_devices(self) -> List[ScannerDevice]:
        """Enumerate connected WIA scanner devices."""
        devices = []
        if not self._available or self._wia is None:
            return devices

        try:
            import win32com.client
            device_infos = self._wia.DeviceInfos
            for i in range(1, device_infos.Count + 1):
                try:
                    info = device_infos.Item(i)
                    # WIA device type 1 = Scanner
                    if info.Type == 1:
                        dev = ScannerDevice(
                            device_id=info.DeviceID,
                            name=info.Properties("Name").Value if self._has_property(info, "Name") else f"Scanner {i}",
                            scanner_type=ScannerType.USB,
                            manufacturer=info.Properties("Manufacturer").Value if self._has_property(info, "Manufacturer") else "Unknown",
                            model=info.Properties("Description").Value if self._has_property(info, "Description") else "Unknown",
                        )
                        devices.append(dev)
                        logger.info(f"Found WIA scanner: {dev.name} (ID: {dev.device_id})")
                except Exception as e:
                    logger.warning(f"Failed to read WIA device {i}: {e}")
        except Exception as e:
            logger.error(f"WIA device enumeration failed: {e}")

        return devices

    def _has_property(self, info, prop_name: str) -> bool:
        """Check if a WIA device info has a named property."""
        try:
            _ = info.Properties(prop_name).Value
            return True
        except Exception:
            return False

    def scan(self, device_id: str, settings: ScanSettings,
             progress_callback=None) -> ScanResult:
        """Execute a scan using WIA."""
        result = ScanResult(dpi=settings.dpi, color_mode=settings.color_mode.value)

        if not self._available:
            result.error_message = "WIA is not available on this system."
            return result

        try:
            import win32com.client

            # Connect to the device
            if progress_callback:
                progress_callback(5, "Connecting to scanner...")

            device_manager = win32com.client.Dispatch("WIA.DeviceManager")
            device = None
            for i in range(1, device_manager.DeviceInfos.Count + 1):
                info = device_manager.DeviceInfos.Item(i)
                if info.DeviceID == device_id:
                    device = info.Connect()
                    result.scanner_name = info.Properties("Name").Value if self._has_property(info, "Name") else device_id
                    break

            if device is None:
                result.error_message = f"Scanner device '{device_id}' not found."
                return result

            if progress_callback:
                progress_callback(15, "Configuring scan settings...")

            # Get the scanner item (first item is typically the scanning element)
            item = device.Items(1)

            # Set scan properties
            self._set_wia_property(item, WIA_HORIZONTAL_RESOLUTION, settings.dpi)
            self._set_wia_property(item, WIA_VERTICAL_RESOLUTION, settings.dpi)

            # Color mode mapping
            wia_color_map = {
                ColorMode.COLOR: WIA_COLOR,
                ColorMode.GRAYSCALE: WIA_GRAYSCALE,
                ColorMode.BW: WIA_BW,
            }
            self._set_wia_property(item, WIA_COLOR_MODE, wia_color_map.get(settings.color_mode, WIA_COLOR))

            if progress_callback:
                progress_callback(25, "Scanning document...")

            # Perform the scan
            image = item.Transfer(WIA_FORMAT_BMP)

            if progress_callback:
                progress_callback(75, "Saving scanned image...")

            # Save to file
            ext = "tiff" if settings.output_format.upper() == "TIFF" else "png"
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"scan_{timestamp}_{uuid.uuid4().hex[:6]}.{ext}"
            filepath = os.path.join(settings.output_dir, filename)

            image.SaveFile(filepath)

            result.success = True
            result.file_paths.append(filepath)
            result.page_count = 1

            if progress_callback:
                progress_callback(100, "Scan complete.")

            logger.info(f"WIA scan complete: {filepath}")
            return result

        except Exception as e:
            result.error_message = f"WIA scan failed: {str(e)}"
            logger.error(result.error_message)
            return result

    def _set_wia_property(self, item, prop_id: str, value):
        """Set a WIA item property by ID."""
        try:
            for prop in item.Properties:
                if str(prop.PropertyID) == prop_id:
                    prop.Value = value
                    return True
        except Exception as e:
            logger.debug(f"Could not set WIA property {prop_id}: {e}")
        return False


class IPScanner:
    """IP/Network scanner backend using eSCL (AirScan) or HTTP API."""

    def __init__(self):
        self._session = None
        self._init_session()

    def _init_session(self):
        """Initialize HTTP session."""
        try:
            import requests
            self._session = requests.Session()
            self._session.timeout = 10
        except ImportError:
            logger.warning("requests library not available for IP scanner.")

    def test_connection(self, ip_address: str, port: int = 443) -> Dict[str, Any]:
        """Test connection to an IP scanner and retrieve its capabilities."""
        result = {"connected": False, "name": "", "capabilities": {}, "error": ""}

        if self._session is None:
            result["error"] = "HTTP client not available."
            return result

        # Try eSCL (AirScan) endpoint first
        escl_endpoints = [
            f"https://{ip_address}:{port}/eSCL/ScannerCapabilities",
            f"http://{ip_address}:{port}/eSCL/ScannerCapabilities",
            f"http://{ip_address}/eSCL/ScannerCapabilities",
            f"https://{ip_address}/eSCL/ScannerCapabilities",
        ]

        for url in escl_endpoints:
            try:
                resp = self._session.get(url, verify=False, timeout=5)
                if resp.status_code == 200:
                    result["connected"] = True
                    result["name"] = f"eSCL Scanner @ {ip_address}"
                    result["capabilities"] = self._parse_escl_capabilities(resp.text)
                    logger.info(f"eSCL scanner found at {url}")
                    return result
            except Exception:
                continue

        # Try generic HTTP health check
        try:
            resp = self._session.get(f"http://{ip_address}/", verify=False, timeout=5)
            if resp.status_code in (200, 301, 302):
                result["connected"] = True
                result["name"] = f"HTTP Scanner @ {ip_address}"
                return result
        except Exception:
            pass

        result["error"] = f"Could not connect to scanner at {ip_address}:{port}"
        return result

    def _parse_escl_capabilities(self, xml_text: str) -> Dict[str, Any]:
        """Parse eSCL ScannerCapabilities XML response."""
        caps = {"color_modes": [], "resolutions": [], "sources": []}
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_text)
            # Namespace handling for eSCL
            ns = {"scan": "http://schemas.hp.com/imaging/escl/2011/05/03"}

            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == "ColorMode" and elem.text:
                    caps["color_modes"].append(elem.text)
                elif tag == "XResolution" and elem.text:
                    try:
                        caps["resolutions"].append(int(elem.text))
                    except ValueError:
                        pass
                elif tag == "InputSource" and elem.text:
                    caps["sources"].append(elem.text)
        except Exception as e:
            logger.debug(f"eSCL capability parsing error: {e}")
        return caps

    def scan(self, ip_address: str, port: int, settings: ScanSettings,
             progress_callback=None) -> ScanResult:
        """Execute a scan via eSCL HTTP API."""
        result = ScanResult(
            dpi=settings.dpi,
            color_mode=settings.color_mode.value,
            scanner_name=f"IP Scanner @ {ip_address}"
        )

        if self._session is None:
            result.error_message = "HTTP client not available."
            return result

        try:
            if progress_callback:
                progress_callback(10, "Connecting to IP scanner...")

            # Build eSCL ScanSettings XML
            color_map = {
                ColorMode.COLOR: "RGB24",
                ColorMode.GRAYSCALE: "Grayscale8",
                ColorMode.BW: "BlackAndWhite1",
            }
            source_map = {
                ScanSource.FLATBED: "Platen",
                ScanSource.ADF_FRONT: "Feeder",
                ScanSource.ADF_DUPLEX: "Feeder",
            }

            scan_settings_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
                   xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
    <pwg:Version>2.0</pwg:Version>
    <scan:Intent>Document</scan:Intent>
    <pwg:ScanRegions>
        <pwg:ScanRegion>
            <pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>
            <pwg:Height>3508</pwg:Height>
            <pwg:Width>2480</pwg:Width>
            <pwg:XOffset>0</pwg:XOffset>
            <pwg:YOffset>0</pwg:YOffset>
        </pwg:ScanRegion>
    </pwg:ScanRegions>
    <pwg:InputSource>{source_map.get(settings.source, "Platen")}</pwg:InputSource>
    <scan:ColorMode>{color_map.get(settings.color_mode, "RGB24")}</scan:ColorMode>
    <scan:XResolution>{settings.dpi}</scan:XResolution>
    <scan:YResolution>{settings.dpi}</scan:YResolution>
    <pwg:DocumentFormat>image/png</pwg:DocumentFormat>
</scan:ScanSettings>"""

            # Submit scan job
            base_urls = [
                f"https://{ip_address}:{port}",
                f"http://{ip_address}:{port}",
                f"http://{ip_address}",
            ]

            if progress_callback:
                progress_callback(25, "Submitting scan job...")

            job_url = None
            for base in base_urls:
                try:
                    resp = self._session.post(
                        f"{base}/eSCL/ScanJobs",
                        data=scan_settings_xml,
                        headers={"Content-Type": "text/xml"},
                        verify=False,
                        timeout=10
                    )
                    if resp.status_code == 201:
                        job_url = resp.headers.get("Location", "")
                        if not job_url.startswith("http"):
                            job_url = f"{base}{job_url}"
                        break
                except Exception:
                    continue

            if not job_url:
                result.error_message = "Failed to submit scan job to eSCL scanner."
                return result

            if progress_callback:
                progress_callback(40, "Scanning in progress...")

            # Poll for scan completion and download
            download_url = f"{job_url}/NextDocument"
            max_wait = 120  # 2 minutes timeout
            start = time.time()

            while time.time() - start < max_wait:
                try:
                    resp = self._session.get(download_url, verify=False, timeout=30)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        if progress_callback:
                            progress_callback(80, "Saving scanned image...")

                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        ext = "png"
                        filename = f"scan_ip_{timestamp}_{uuid.uuid4().hex[:6]}.{ext}"
                        filepath = os.path.join(settings.output_dir, filename)

                        with open(filepath, "wb") as f:
                            f.write(resp.content)

                        result.success = True
                        result.file_paths.append(filepath)
                        result.page_count = 1

                        if progress_callback:
                            progress_callback(100, "Scan complete.")

                        logger.info(f"IP scan complete: {filepath}")
                        return result
                    elif resp.status_code == 503:
                        # Scanner busy, wait and retry
                        time.sleep(2)
                        continue
                    else:
                        time.sleep(1)
                except Exception:
                    time.sleep(2)

            result.error_message = "Scan timed out waiting for scanner response."
            return result

        except Exception as e:
            result.error_message = f"IP scan failed: {str(e)}"
            logger.error(result.error_message)
            return result


class NetworkScanner:
    """Network scanner discovery and access."""

    def discover_scanners(self, timeout: int = 5) -> List[ScannerDevice]:
        """Discover scanners on the local network using mDNS/DNS-SD for eSCL."""
        devices = []

        # Method 1: Try WIA network devices
        try:
            wia = WIAScanner()
            if wia.is_available:
                wia_devices = wia.discover_devices()
                for dev in wia_devices:
                    dev.scanner_type = ScannerType.NETWORK
                    devices.append(dev)
        except Exception as e:
            logger.debug(f"WIA network discovery failed: {e}")

        # Method 2: Scan common IP ranges for eSCL scanners
        try:
            import socket
            local_ip = socket.gethostbyname(socket.gethostname())
            subnet = ".".join(local_ip.split(".")[:3])

            import requests
            for last_octet in range(1, 255):
                ip = f"{subnet}.{last_octet}"
                try:
                    resp = requests.get(
                        f"http://{ip}/eSCL/ScannerCapabilities",
                        timeout=0.5
                    )
                    if resp.status_code == 200:
                        dev = ScannerDevice(
                            device_id=f"escl_{ip}",
                            name=f"Network Scanner @ {ip}",
                            scanner_type=ScannerType.NETWORK,
                            ip_address=ip,
                            port=80,
                            is_available=True,
                        )
                        devices.append(dev)
                        logger.info(f"Found network eSCL scanner: {ip}")
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Network scan discovery failed: {e}")

        return devices


# ── Scan Worker Thread ──────────────────────────────────────

class ScanWorker(QObject):
    """Background worker for performing scan operations."""

    progress = pyqtSignal(int, str)  # percent, message
    finished = pyqtSignal(object)  # ScanResult
    error = pyqtSignal(str)

    def __init__(self, scanner_type: ScannerType, device: ScannerDevice,
                 settings: ScanSettings):
        super().__init__()
        self._scanner_type = scanner_type
        self._device = device
        self._settings = settings
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        """Execute the scan operation."""
        try:
            self.progress.emit(0, "Initializing scanner...")

            if self._cancelled:
                self.finished.emit(ScanResult(error_message="Scan cancelled."))
                return

            if self._scanner_type == ScannerType.USB:
                scanner = WIAScanner()
                result = scanner.scan(
                    self._device.device_id,
                    self._settings,
                    progress_callback=self._on_progress
                )
            elif self._scanner_type == ScannerType.IP:
                scanner = IPScanner()
                result = scanner.scan(
                    self._device.ip_address,
                    self._device.port or 443,
                    self._settings,
                    progress_callback=self._on_progress
                )
            elif self._scanner_type == ScannerType.NETWORK:
                # Network scanners route through IP or WIA depending on connection
                if self._device.ip_address:
                    scanner = IPScanner()
                    result = scanner.scan(
                        self._device.ip_address,
                        self._device.port or 80,
                        self._settings,
                        progress_callback=self._on_progress
                    )
                else:
                    scanner = WIAScanner()
                    result = scanner.scan(
                        self._device.device_id,
                        self._settings,
                        progress_callback=self._on_progress
                    )
            else:
                result = ScanResult(error_message="Unknown scanner type.")

            self.finished.emit(result)

        except Exception as e:
            error_msg = f"Scan operation failed: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            self.finished.emit(ScanResult(error_message=error_msg))

    def _on_progress(self, percent: int, message: str):
        if not self._cancelled:
            self.progress.emit(percent, message)


# ── Main Scanner Service ────────────────────────────────────

class ScannerService(QObject):
    """Central scanner service — manages discovery and scanning across all types."""

    devices_discovered = pyqtSignal(list)  # List[ScannerDevice]
    scan_started = pyqtSignal()
    scan_progress = pyqtSignal(int, str)
    scan_completed = pyqtSignal(object)  # ScanResult
    scan_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._wia = WIAScanner()
        self._ip = IPScanner()
        self._network = NetworkScanner()
        self._worker = None
        self._thread = None

    @property
    def wia_available(self) -> bool:
        return self._wia.is_available

    def discover_usb_scanners(self) -> List[ScannerDevice]:
        """Discover USB/standalone scanners via WIA."""
        return self._wia.discover_devices()

    def test_ip_scanner(self, ip_address: str, port: int = 443) -> Dict[str, Any]:
        """Test connection to an IP scanner."""
        return self._ip.test_connection(ip_address, port)

    def discover_network_scanners(self) -> List[ScannerDevice]:
        """Discover scanners on the local network."""
        return self._network.discover_scanners()

    def start_scan(self, device: ScannerDevice, settings: ScanSettings):
        """Start a scan operation in a background thread."""
        if self._thread is not None and self._thread.isRunning():
            self.scan_error.emit("A scan is already in progress.")
            return

        self._thread = QThread()
        self._worker = ScanWorker(device.scanner_type, device, settings)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.scan_progress.emit)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.error.connect(self.scan_error.emit)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self.scan_started.emit()
        self._thread.start()

    def cancel_scan(self):
        """Cancel the current scan operation."""
        if self._worker:
            self._worker.cancel()

    def _on_scan_finished(self, result: ScanResult):
        """Handle scan completion."""
        self._thread = None
        self._worker = None
        self.scan_completed.emit(result)

    @property
    def is_scanning(self) -> bool:
        return self._thread is not None and self._thread.isRunning()


# ── Module-level singleton ──────────────────────────────────

_scanner_service: Optional[ScannerService] = None


def get_scanner_service() -> ScannerService:
    """Get the global ScannerService singleton."""
    global _scanner_service
    if _scanner_service is None:
        _scanner_service = ScannerService()
    return _scanner_service
