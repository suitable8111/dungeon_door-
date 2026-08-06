"""순수 파이썬 UPnP/IGD 클라이언트 — 공유기에 포트포워딩 자동 요청.

목적: 호스트가 수동 포트포워딩 없이도 인터넷에서 접속받을 수 있게, 공유기(IGD)에
'외부포트 → 내 LAN:포트' 매핑을 자동 등록한다. 성공하면 공인 IP를 얻어 초대 코드에
담는다. C 확장(miniupnpc) 의존 없이 stdlib(SSDP 멀티캐스트 + SOAP)만 사용 —
배포 빌드에 그대로 번들된다.

한계: 공유기가 UPnP를 끄면 실패. CGNAT(공인 IP가 아닌 100.64/10 등) 환경은 UPnP가
'성공'해도 진짜 인터넷 도달이 안 되므로, 외부 IP가 사설/CGNAT면 인터넷 불가로 판정한다.
"""

from __future__ import annotations

import re
import socket
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

_SSDP_ADDR = "239.255.255.250"
_SSDP_PORT = 1900
_ST = "urn:schemas-upnp-org:device:InternetGatewayDevice:1"
_WAN_SVC = ("urn:schemas-upnp-org:service:WANIPConnection:1",
            "urn:schemas-upnp-org:service:WANPPPConnection:1")


def is_private_ip(ip: str) -> bool:
    """사설/특수/CGNAT 대역이면 True (= 진짜 공인 IP가 아님)."""
    try:
        p = [int(x) for x in ip.split(".")]
        if len(p) != 4:
            return True
    except ValueError:
        return True
    if p[0] == 10:                            return True
    if p[0] == 172 and 16 <= p[1] <= 31:      return True
    if p[0] == 192 and p[1] == 168:           return True
    if p[0] == 100 and 64 <= p[1] <= 127:     return True   # CGNAT 100.64/10
    if p[0] == 127:                           return True
    if p[0] == 169 and p[1] == 254:           return True
    if p[0] == 0 or p[0] >= 224:              return True
    return False


def discover(timeout: float = 2.0) -> str | None:
    """SSDP M-SEARCH로 IGD를 찾아 장치 설명 XML의 LOCATION URL을 반환."""
    msg = ("M-SEARCH * HTTP/1.1\r\n"
           f"HOST: {_SSDP_ADDR}:{_SSDP_PORT}\r\n"
           'MAN: "ssdp:discover"\r\n'
           "MX: 2\r\n"
           f"ST: {_ST}\r\n\r\n").encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(timeout)
    try:
        s.sendto(msg, (_SSDP_ADDR, _SSDP_PORT))
        while True:
            try:
                data, _ = s.recvfrom(65507)
            except socket.timeout:
                return None
            m = re.search(rb"(?i)location:\s*(\S+)", data)
            if m:
                return m.group(1).decode("utf-8", "replace").strip()
    except OSError:
        return None
    finally:
        s.close()


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_service_xml(xml: bytes, base_url: str) -> tuple[str, str] | None:
    """장치 설명 XML에서 WAN(IP/PPP)Connection 서비스의
    (제어URL 절대경로, serviceType)을 뽑는다."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    for svc in root.iter():
        if _strip_ns(svc.tag) != "service":
            continue
        stype = ctrl = None
        for child in svc:
            tag = _strip_ns(child.tag)
            if tag == "serviceType":
                stype = (child.text or "").strip()
            elif tag == "controlURL":
                ctrl = (child.text or "").strip()
        if stype in _WAN_SVC and ctrl:
            return urljoin(base_url, ctrl), stype
    return None


def find_service(location: str, timeout: float = 3.0) -> tuple[str, str] | None:
    """IGD 장치 설명 URL을 받아 WAN 서비스 (제어URL, serviceType) 반환."""
    try:
        with urllib.request.urlopen(location, timeout=timeout) as r:
            xml = r.read()
    except (OSError, ValueError):
        return None
    return parse_service_xml(xml, location)


def _soap(control_url: str, stype: str, action: str, args: str,
          timeout: float = 3.0) -> str | None:
    body = (
        '<?xml version="1.0"?>\n'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        f'<s:Body><u:{action} xmlns:u="{stype}">{args}'
        f'</u:{action}></s:Body></s:Envelope>'
    ).encode("utf-8")
    req = urllib.request.Request(
        control_url, data=body, method="POST",
        headers={"Content-Type": 'text/xml; charset="utf-8"',
                 "SOAPAction": f'"{stype}#{action}"'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except (OSError, ValueError):
        return None


def get_external_ip(control_url: str, stype: str) -> str | None:
    resp = _soap(control_url, stype, "GetExternalIPAddress", "")
    if not resp:
        return None
    m = re.search(r"<NewExternalIPAddress>([^<]*)</NewExternalIPAddress>", resp)
    return m.group(1).strip() if m and m.group(1).strip() else None


def add_port_mapping(control_url: str, stype: str, ext_port: int, int_ip: str,
                     int_port: int, desc: str = "DungeonDoor",
                     proto: str = "TCP") -> bool:
    args = (f"<NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{ext_port}</NewExternalPort>"
            f"<NewProtocol>{proto}</NewProtocol>"
            f"<NewInternalPort>{int_port}</NewInternalPort>"
            f"<NewInternalClient>{int_ip}</NewInternalClient>"
            f"<NewEnabled>1</NewEnabled>"
            f"<NewPortMappingDescription>{desc}</NewPortMappingDescription>"
            f"<NewLeaseDuration>0</NewLeaseDuration>")
    resp = _soap(control_url, stype, "AddPortMapping", args)
    return resp is not None and "AddPortMappingResponse" in resp


def delete_port_mapping(control_url: str, stype: str, ext_port: int,
                        proto: str = "TCP") -> bool:
    args = (f"<NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{ext_port}</NewExternalPort>"
            f"<NewProtocol>{proto}</NewProtocol>")
    resp = _soap(control_url, stype, "DeletePortMapping", args)
    return resp is not None


class PortForward:
    """포트포워딩 시도/정리를 관리. setup()이 공인 IP(인터넷 가능)면 그 IP를 반환."""

    def __init__(self, port: int):
        self.port = port
        self._control = None
        self._stype = None
        self.mapped = False
        self.external_ip = None      # 공유기가 보고한 외부 IP(사설/CGNAT일 수 있음)
        #: 'ok'(인터넷 가능) | 'cgnat'(외부IP가 사설) | 'no_igd' | 'failed'
        self.status = "failed"

    def setup(self, lan_ip: str) -> str | None:
        loc = discover()
        if not loc:
            self.status = "no_igd"
            return None
        svc = find_service(loc)
        if not svc:
            self.status = "no_igd"
            return None
        self._control, self._stype = svc
        self.external_ip = get_external_ip(self._control, self._stype)
        ok = add_port_mapping(self._control, self._stype, self.port,
                              lan_ip, self.port)
        self.mapped = ok
        if not ok:
            self.status = "failed"
            return None
        if self.external_ip and not is_private_ip(self.external_ip):
            self.status = "ok"
            return self.external_ip
        # 매핑은 됐지만 외부 IP가 사설/CGNAT → 진짜 인터넷 도달 불가
        self.status = "cgnat"
        return None

    def close(self):
        if self.mapped and self._control and self._stype:
            try:
                delete_port_mapping(self._control, self._stype, self.port)
            except Exception:
                pass
            self.mapped = False
