#!/usr/bin/env python3
"""nofio_probe.py - TCP control protocol probe for the Nofio wireless VR adapter.

Talks directly to the Base (or Head) station over TCP with no drivers and no
VirtualHere. The wire format below was reverse-engineered from the decompiled
original utility (nofioUtility.exe, C#); see docs/PROTOCOL.md.

Transport
    Base: 192.168.3.1:34566   (client identity: Device.PC  = 0)
    Head: 192.168.4.1:34568   (client identity: Device.PC2 = 3)

Packet framing (big-endian, 9-byte header + payload)
    [0]      source device
    [1]      destination device
    [2:6]    sequence (uint; increments per packet, receiver validates order)
    [6]      options: bit0 = start-of-message, bit1 = end-of-message
    [7:9]    payload length (max 65535)
    [9:...]  payload chunk

Message (reassembled payload of one or more packets)
    [0:2]    tag (ushort): (device << 14) | transaction id (14 bit)
    [2:4]    message type (ushort, see MSG_NAMES)
    [4:...]  message body

Handshake (mirrors NofioConnection.SendConnect + OnMessageReceived)
    1. TCP connect
    2. send Connect(protocol=80) with tag (dst << 14) | 1
    3. the station replies with its OWN Connect (body = its protocol version,
       same tag); the client must answer Ack (empty body, same tag)
    4. the station then acks the client's Connect (Ack, same tag)
    5. keepalive: Heartbeat(body=u32 0, tag 0) every second
    (a Nak with OldVersion means protocol mismatch; device versions < 49
    are treated as remote-old by the original utility)

Requests
    RequestStatus(body=u16 expected_reply_type) with a fresh transaction tag;
    the device replies with a message of the requested type echoing the tag.
    SoftwareVersion reply body: [u16 length][version string, may be multi-line]

Usage
    ./nofio_probe.py status                     # handshake + firmware version
    ./nofio_probe.py status --target head       # head, routed via the base
    ./nofio_probe.py monitor --duration 10      # print every incoming message
    ./nofio_probe.py raw 128 0086               # send arbitrary type/body

Routing (dynamically verified): packets whose Destination is Head (2) are
forwarded by the base over its wireless link, and the head's replies come
back on the same TCP connection with their own per-source sequence counter.
The routing is transparent: no base handshake is needed on a head-only
session. Rule of thumb: ONE TCP connection talks to ONE device - mixing
base-directed requests into a head-routed session makes the base disconnect.
The head can therefore be queried through the base without any direct
network path to 192.168.4.0/24 (--via base, the default for --target head;
--via direct connects to 192.168.4.1:34568 and only works when the head is
locally connected).
"""

import argparse
import socket
import struct
import sys
import threading
import time

BASE_IP = "192.168.3.1"
BASE_PORT = 34566
HEAD_IP = "192.168.4.1"
HEAD_PORT = 34568

PC, BASE, HEAD, PC2 = 0, 1, 2, 3
DEVICE_NAMES = {PC: "PC", BASE: "Base", HEAD: "Head", PC2: "PC2"}

PROTOCOL_VERSION = 80
CONNECT_TRANSACTION = 1

MSG_NAMES = {
    0: "Ack", 1: "Nak", 2: "Connect", 3: "Disconnect", 4: "Heartbeat",
    64: "HMDConnected", 65: "PCConnected", 66: "VideoLost", 67: "ConfirmVideoState",
    128: "RequestStatus", 129: "BaseStatus", 130: "HeadStatus",
    131: "HMDSuspended", 132: "BridgeParams", 133: "FoveationParams",
    134: "SoftwareVersion", 135: "SoftwareUpdateMeta", 136: "Statistics",
    137: "SoftwareUpdateData", 138: "SoftwareUpdateComplete",
    139: "FPGAErrorStatus", 140: "Protobuf", 141: "FPGAFramerConfiguration",
    142: "FPGAStatus", 143: "GenlockControl", 144: "Setup", 145: "Configuration",
    146: "TestFrameGenerator", 147: "VirtualHere", 148: "EDID", 149: "PeerInfo",
    150: "CodecParams", 152: "SourceConnected", 153: "VideoStatus",
    154: "AudioInfo", 155: "FrameCaptures", 156: "Wifi6ESim",
    157: "FPGARegisters", 158: "Pairing",
}

NAK_ERRORS = {
    0: "None", 1: "OldVersion", 2: "NoPath", 3: "AlreadyConnected",
    64: "InternalStart", 128: "InvalidStatusRequest",
    129: "IncorrectSoftwareUpdatePacket", 130: "IncorrectSoftwareUpdateFile",
    131: "SyncRebootFailed", 132: "WirelessChanged", 133: "InvalidRequest",
    134: "IncorrectResponse", 135: "ExceptionCaught", 136: "Busy",
    137: "Timeout", 138: "VideoNotConnected", 139: "VdmaNotIncluded",
    140: "SyncShutdownFailed",
}


def msg_name(msg_type):
    return MSG_NAMES.get(msg_type, "Unknown(0x%04x)" % msg_type)


def make_tag(device, transaction):
    return ((device & 0x03) << 14) | (transaction & 0x3FFF)


def encode_message(tag, msg_type, body=b""):
    return struct.pack(">HH", tag, msg_type) + body


def build_packets(source, destination, seq, message_bytes):
    """Chunk a message into 9-byte-headered packets, mirroring Packet.PackageMessage."""
    packets = []
    offset = 0
    total = len(message_bytes)
    while True:
        is_start = offset == 0
        chunk = message_bytes[offset:offset + 65535]
        offset += len(chunk)
        opts = (0x01 if is_start else 0x00) | (0x02 if offset >= total else 0x00)
        header = struct.pack(">BBIBH", source, destination, seq, opts, len(chunk))
        packets.append(header + chunk)
        seq += 1
        if offset >= total:
            return packets, seq


class NofioClient:
    def __init__(self, host, port, identity, destination, timeout=5.0, verbose=True,
                 via_base=False):
        self.host = host
        self.port = port
        self.identity = identity
        self.destination = destination
        self.timeout = timeout
        self.verbose = verbose
        self.via_base = via_base  # transport goes to the base even for head destinations
        self.seq = 0
        self.rx_expected = {}     # per-source expected packet sequence
        self.rx_synced = set()
        self.transaction = CONNECT_TRANSACTION + 1
        self.device_protocol_version = None
        self.sock = None
        self._t0 = time.time()
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread = None
        self._send_lock = threading.Lock()  # heartbeat + queries share the socket

    @property
    def heartbeat_targets(self):
        # one TCP connection talks to ONE device: mixing base-directed traffic
        # into a head-routed session makes the base disconnect us
        return {self.destination}

    # -- low level -----------------------------------------------------------

    def log(self, *args):
        if self.verbose:
            print("[%7.2fs]" % (time.time() - self._t0), *args, file=sys.stderr)

    def connect_tcp(self):
        self._t0 = time.time()
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)
        self.log("TCP connected to %s:%d (identity=%s -> %s)"
                 % (self.host, self.port, DEVICE_NAMES[self.identity],
                    DEVICE_NAMES[self.destination]))

    def handshake(self, to=None):
        """Connect exchange with one device: send Connect, ack its Connect."""
        dest = to if to is not None else self.destination
        our_tag = make_tag(dest, CONNECT_TRANSACTION)
        self.send_message(2, struct.pack(">I", PROTOCOL_VERSION), tag=our_tag, to=dest)
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            rtag, rtype, rbody = self.recv_message()
            if rtype == 2 and rtag == our_tag:  # station's Connect -> Ack it
                self.device_protocol_version = struct.unpack(">I", rbody[:4])[0]
                self.log("%s Connect: protocol version %d"
                         % (DEVICE_NAMES.get(dest, dest), self.device_protocol_version))
                if self.device_protocol_version < 49:
                    self.log("!! station version < 49: original utility treats this as remote-old")
                self.send_message(0, tag=rtag, to=dest)  # Ack echoing the station's tag
                self.log("handshake with %s complete" % DEVICE_NAMES.get(dest, dest))
                return True
            if rtype == 1 and rtag == our_tag:  # Nak
                code = struct.unpack(">I", rbody[:4])[0] if len(rbody) >= 4 else None
                raise RuntimeError("Connect to %s rejected: Nak(%s)"
                                   % (DEVICE_NAMES.get(dest, dest), NAK_ERRORS.get(code, code)))
            if rtype == 3:  # Disconnect
                raise RuntimeError("station disconnected during handshake")
            self.log("(ignoring %s during handshake)" % msg_name(rtype))
        raise TimeoutError("no Connect exchange with %s" % DEVICE_NAMES.get(dest, dest))

    def establish(self):
        """Handshake with the destination device only.

        Base routing is transparent: a connection that only carries
        head-addressed packets needs no base handshake (verified live). The
        base disconnects a session that mixes base-directed requests after a
        head session, so keep one TCP connection per target device.
        """
        self.handshake()

    def start_heartbeat(self, interval=1.0):
        def beat():
            while not self._heartbeat_stop.wait(interval):
                for target in self.heartbeat_targets:
                    try:
                        self.send_message(4, struct.pack(">I", 0), tag=0, to=target)
                    except OSError:
                        return
        self._heartbeat_thread = threading.Thread(target=beat, daemon=True)
        self._heartbeat_thread.start()

    def send_message(self, msg_type, body=b"", tag=None, to=None):
        """Send one message to a device; returns the tag used."""
        dest = to if to is not None else self.destination
        if tag is None:
            tag = make_tag(dest, self.transaction)
            self.transaction += 1
        message = encode_message(tag, msg_type, body)
        with self._send_lock:
            packets, self.seq = build_packets(self.identity, dest, self.seq, message)
            for pkt in packets:
                self.sock.sendall(pkt)
        self.log(">> %s to=%s tag=0x%04x body=%d bytes"
                 % (msg_name(msg_type), DEVICE_NAMES.get(dest, dest), tag, len(body)))
        return tag

    def recv_message(self):
        """Read packets until one full message is reassembled; returns (tag, type, body)."""
        message = b""
        while True:
            header = self._read_exact(9)
            src, dst, seq, opts, length = struct.unpack(">BBIBH", header)
            if src > 3 or dst > 3 or opts > 3:
                raise ValueError("invalid packet header: %s" % header.hex())
            # sequence counters are per SOURCE device (head packets arriving via
            # the base carry their own counter)
            if src not in self.rx_synced:
                self.rx_synced.add(src)
                self.rx_expected[src] = seq
            elif seq != self.rx_expected.get(src, seq):
                self.log("!! sequence gap from %s: got %d, expected %d"
                         % (DEVICE_NAMES.get(src, src), seq, self.rx_expected.get(src)))
            self.rx_expected[src] = seq + 1
            body = self._read_exact(length) if length else b""
            message += body
            if opts & 0x02:  # end-of-message
                if len(message) < 4:
                    raise ValueError("short message: %s" % message.hex())
                tag, msg_type = struct.unpack(">HH", message[:4])
                self.log("<< %s from=%s tag=0x%04x body=%d bytes"
                         % (msg_name(msg_type), DEVICE_NAMES.get(src, src), tag,
                            len(message) - 4))
                return tag, msg_type, message[4:]

    # -- protocol ------------------------------------------------------------

    def _read_exact(self, count):
        data = b""
        while len(data) < count:
            chunk = self.sock.recv(count - len(data))
            if not chunk:
                raise ConnectionError("connection closed by device")
            data += chunk
        return data

    def stop_heartbeat(self):
        self._heartbeat_stop.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)

    def request(self, expecting_reply, wait=5.0):
        """SendRequest equivalent: RequestStatus + wait for the expected reply type."""
        tag = self.send_message(128, struct.pack(">H", expecting_reply))
        deadline = time.time() + wait
        while time.time() < deadline:
            rtag, rtype, rbody = self.recv_message()
            if rtype == expecting_reply and rtag == tag:
                return rbody
            if rtype == 1 and rtag == tag:  # Nak for our transaction
                code = struct.unpack(">I", rbody[:4])[0] if len(rbody) >= 4 else None
                raise RuntimeError("request refused: Nak(%s)" % NAK_ERRORS.get(code, code))
            self.log("(deferred %s tag=0x%04x)" % (msg_name(rtype), rtag))
        raise TimeoutError("no reply of type %s" % msg_name(expecting_reply))

    def close(self):
        for target in self.heartbeat_targets:
            try:
                self.send_message(3, to=target)  # polite Disconnect
            except OSError:
                pass
        try:
            self.sock.close()
        except OSError:
            pass


# -- interpreters --------------------------------------------------------------

def describe(msg_type, body):
    """Human-readable one-liner for known message bodies."""
    try:
        if msg_type == 134 and len(body) >= 2:  # SoftwareVersion: [u16 len][string]
            length = struct.unpack(">H", body[:2])[0]
            text = body[2:2 + length].decode("utf-8", "replace")
            return "firmware version: %r" % text
        if msg_type == 1 and len(body) >= 4:  # Nak: u32 error code
            code = struct.unpack(">I", body[:4])[0]
            return "error: %s" % NAK_ERRORS.get(code, code)
        if msg_type == 140 and len(body) >= 3:  # Protobuf: [u8 pktcount][u16 type][content]
            inner = struct.unpack(">H", body[1:3])[0]
            return "protobuf content-type %s (%d bytes)" % (msg_name(inner), len(body) - 3)
        if msg_type == 2 and len(body) >= 4:  # Connect: u32 protocol version
            return "protocol version %d" % struct.unpack(">I", body[:4])[0]
    except Exception:
        pass
    return "body[%d]: %s" % (len(body), body.hex())


def parse_software_version(body):
    length = struct.unpack(">H", body[:2])[0]
    return body[2:2 + length].decode("utf-8", "replace")


# -- protobuf decoding (schema: docs/protos/nofio.proto) ----------------------

BASE_STATUS_FIELDS = {
    1: ("WirelessLink", "bool"), 2: ("BridgeLink", "bool"),
    3: ("ControllerInterface", "bool"), 4: ("ControllerDevice", "bool"),
    5: ("CpuTemp", "uint"), 6: ("FpgaTemp", "uint"), 7: ("BasebandTemp", "uint"),
    8: ("RadioTemp", "uint"), 9: ("WirelessTxMcs", "uint"), 10: ("WirelessRxMcs", "uint"),
    11: ("WirelessChannel", "uint"), 12: ("SignalStrength", "uint"),
    13: ("CpuLoad", "repeated uint"), 14: ("BridgeTxSpeed", "int"),
    15: ("BridgeRxSpeed", "int"), 16: ("BridgeRxMaxSpeed", "int"),
    17: ("ControllerState", "uint"), 18: ("WirelessState", "bitfield"),
    19: ("Sector", "repeated uint"), 20: ("VideoRxSpeed", "uint"),
    21: ("PeakVideoRXSpeed", "uint"), 22: ("PeakUncompressedVideoTXSpeed", "uint"),
    23: ("RSSI", "int"), 24: ("SQI", "uint"), 25: ("Radios", "repeated msg"),
    26: ("PeakUncompressedVideoTXSpeed64", "uint"), 27: ("Isax", "bool"),
    28: ("ChannelFreq", "uint MHz"),
}

WIRELESS_STATE_FLAGS = ["PairingNone", "PairingStarted", "PairingSuccess", "PairingFailure",
                        "ConnectionLost", "WifiError", "WipciError", "PairingUnpaired",
                        "ConnectionOk", "WitoolError"]

HEAD_STATUS_FIELDS = {
    1: ("BaseStatus", "nested"), 2: ("PowerSource", "enum"),
    3: ("VoltageIn", "uint"), 4: ("ChargeCurrent", "int"),
    5: ("BatteryVoltage", "uint mV?"), 6: ("VideoTxSpeed", "uint"),
    7: ("VideoBufferReady", "bool"), 8: ("VideoBufferGeneratedPackets", "uint"),
    9: ("PacketErrorRate", "uint"),
    10: ("LeftBatteryCharge", "head powerpack %"),
    11: ("RightBatteryCharge", "second powerpack %"),
}


def pb_walk(data):
    """Generic protobuf parse -> {field_number: [values]}."""
    fields = {}
    i = 0
    while i < len(data):
        key = 0
        shift = 0
        while True:
            b = data[i]; i += 1
            key |= (b & 0x7f) << shift
            shift += 7
            if not b & 0x80:
                break
        f, wt = key >> 3, key & 7
        if wt == 0:
            v = 0
            shift = 0
            nbytes = 0
            while True:
                b = data[i]; i += 1
                v |= (b & 0x7f) << shift
                shift += 7
                nbytes += 1
                if not b & 0x80:
                    break
            # negative protobuf ints are always 10-byte two's complement
            if nbytes == 10 and v >= 1 << 63:
                v -= 1 << 64
            fields.setdefault(f, []).append(v)
        elif wt == 2:
            ln = 0
            shift = 0
            while True:
                b = data[i]; i += 1
                ln |= (b & 0x7f) << shift
                shift += 7
                if not b & 0x80:
                    break
            fields.setdefault(f, []).append(data[i:i + ln])
            i += ln
        elif wt == 5:
            fields.setdefault(f, []).append(data[i:i + 4]); i += 4
        elif wt == 1:
            fields.setdefault(f, []).append(data[i:i + 8]); i += 8
        else:
            break
    return fields


def _unpack_packed_varints(blob):
    """Decode a protobuf packed repeated varint field."""
    out = []
    i = 0
    while i < len(blob):
        v = 0
        shift = 0
        while True:
            b = blob[i]; i += 1
            v |= (b & 0x7f) << shift
            shift += 7
            if not b & 0x80:
                break
        out.append(v)
    return out


def print_status(name, fields, schema, indent="  "):
    print("%s=== %s ===" % (indent, name))
    for f in sorted(fields):
        values = fields[f]
        entry = schema.get(f, ("field_%d" % f, "?"))
        fname, ftype = entry
        # packed repeated numeric fields arrive as a single bytes blob
        if ftype.startswith("repeated uint") and len(values) == 1 \
                and isinstance(values[0], (bytes, bytearray)):
            values = _unpack_packed_varints(values[0])
        for v in values:
            if ftype == "nested" and isinstance(v, (bytes, bytearray)):
                print_status(fname, pb_walk(v), BASE_STATUS_FIELDS, indent + "    ")
                continue
            if ftype == "bitfield":
                bits = [WIRELESS_STATE_FLAGS[b] for b in range(10) if v & (1 << b)]
                extra = " (0x%x: %s)" % (v, ", ".join(bits)) if v else ""
            elif ftype == "repeated msg" and isinstance(v, (bytes, bytearray)):
                sub = pb_walk(v)
                extra = " (RF=%r Temp=%s)" % (
                    sub.get(1, [b""])[0].decode("utf-8", "replace"),
                    sub.get(2, ["?"])[0])
            else:
                extra = ""
            print("%s  %-36s = %s%s" % (indent, fname, v, extra))


# -- subcommands ----------------------------------------------------------------

def cmd_status(args):
    client = NofioClient(args.host, args.port, args.identity, args.device, args.timeout,
                         via_base=args.via_base)
    client.connect_tcp()
    try:
        client.establish()
        if not args.no_heartbeat:
            client.start_heartbeat()
        body = client.request(134)  # SoftwareVersion
        version = parse_software_version(body)
        print("=== %s:%d ===" % (args.host, args.port))
        if client.device_protocol_version is not None:
            print("station protocol version: %d" % client.device_protocol_version)
        print("SoftwareVersion reply:")
        for line in version.splitlines():
            print("  %s" % line)
        if not version.strip():
            print("  (empty version string)")
    finally:
        client.stop_heartbeat()
        client.close()


def cmd_monitor(args):
    client = NofioClient(args.host, args.port, args.identity, args.device, args.timeout,
                         via_base=args.via_base)
    client.connect_tcp()
    client.establish()
    client.start_heartbeat()
    print("=== monitoring %s:%d for %s seconds (Ctrl-C to stop) ==="
          % (args.host, args.port, args.duration))
    end = time.time() + args.duration
    try:
        while time.time() < end:
            tag, msg_type, body = client.recv_message()
            print("%s  tag=0x%04x  %s" % (msg_name(msg_type), tag, describe(msg_type, body)))
    except KeyboardInterrupt:
        pass
    finally:
        client.stop_heartbeat()
        client.close()


def cmd_state(args):
    """Query BaseStatus (base) or HeadStatus (head) and print named fields."""
    expecting = 129 if args.target == "base" else 130  # content type to expect
    schema = BASE_STATUS_FIELDS if args.target == "base" else HEAD_STATUS_FIELDS
    client = NofioClient(args.host, args.port, args.identity, args.device, args.timeout,
                         via_base=args.via_base)
    client.connect_tcp()
    try:
        client.establish()
        if not args.no_heartbeat:
            client.start_heartbeat()
        # RequestStatus asks for the content type; the reply arrives wrapped
        # in a Protobuf(140) message that echoes our tag
        tag = client.send_message(128, struct.pack(">H", expecting))
        deadline = time.time() + 5.0
        content = None
        while time.time() < deadline:
            rtag, rtype, rbody = client.recv_message()
            if rtag == tag and rtype == 140 and len(rbody) >= 3:
                content = rbody[3:]
                break
            if rtag == tag and rtype == 1:
                code = struct.unpack(">I", rbody[:4])[0] if len(rbody) >= 4 else None
                raise RuntimeError("request refused: Nak(%s)" % NAK_ERRORS.get(code, code))
        if content is None:
            raise TimeoutError("no %sStatus reply" % args.target)
        print_status("%sStatus" % args.target.capitalize(), pb_walk(content), schema)
        if args.hex:
            print("  protobuf hex: %s" % content.hex())
    finally:
        client.stop_heartbeat()
        client.close()


def cmd_battery(args):
    """Poll the head's hot-swap powerpack charge (Left/RightBatteryCharge)."""
    # the batteries live on the HEAD unit: force it as the target
    args.target = "head"
    args.host, args.port = BASE_IP, BASE_PORT
    args.identity, args.device = PC, HEAD
    args.via_base = True
    client = NofioClient(args.host, args.port, args.identity, args.device, args.timeout,
                         via_base=True)
    client.connect_tcp()
    try:
        client.establish()
        if not args.no_heartbeat:
            client.start_heartbeat()
        count = args.count if args.watch else 1
        for i in range(count):
            tag = client.send_message(128, struct.pack(">H", 130))  # HeadStatus
            deadline = time.time() + 5.0
            fields = None
            while time.time() < deadline:
                rtag, rtype, rbody = client.recv_message()
                if rtag == tag and rtype == 140 and len(rbody) >= 3:
                    fields = pb_walk(rbody[3:])
                    break
            if fields is None:
                raise TimeoutError("no HeadStatus reply")
            def charge(field_no):
                v = fields.get(field_no, [None])[0]
                return "%d%%" % v if isinstance(v, int) and v >= 0 else "n/a"
            stamp = time.strftime("%H:%M:%S")
            print("%s  head battery: left=%s  right=%s"
                  % (stamp, charge(10), charge(11)))
            if i + 1 < count:
                time.sleep(args.interval)
    finally:
        client.stop_heartbeat()
        client.close()


def cmd_raw(args):
    client = NofioClient(args.host, args.port, args.identity, args.device, args.timeout,
                         via_base=args.via_base)
    client.connect_tcp()
    try:
        client.establish()
        if not args.no_heartbeat:
            client.start_heartbeat()
        body = bytes.fromhex(args.hex) if args.hex else b""
        tag = client.send_message(args.type, body)
        print("sent %s (type=%d) tag=0x%04x body=%r" % (msg_name(args.type), args.type, tag, body))
        if not args.no_reply:
            end = time.time() + args.wait
            while time.time() < end:
                rtag, rtype, rbody = client.recv_message()
                print("%s  tag=0x%04x  %s" % (msg_name(rtype), rtag, describe(rtype, rbody)))
                if rtag == tag:
                    break
    finally:
        client.stop_heartbeat()
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Nofio TCP control protocol probe (reverse-engineered, no drivers)")
    sub = parser.add_subparsers(dest="command")

    def common(p):
        p.add_argument("--host", default=BASE_IP,
                       help="device address (default: %(default)s)")
        p.add_argument("--port", type=int, default=None,
                       help="device port (default: 34566 for base, 34568 for head)")
        p.add_argument("--target", choices=["base", "head"], default="base",
                       help="which station to talk to (default: %(default)s)")
        p.add_argument("--via", choices=["base", "direct"], default=None,
                       help="head routing: 'base' forwards packets through the base "
                            "wireless link (default for --target head), 'direct' "
                            "connects to 192.168.4.1:34568 (head must be local)")
        p.add_argument("--timeout", type=float, default=5.0)
        p.add_argument("--protocol-version", type=int, default=PROTOCOL_VERSION,
                       help="Connect protocol version (app uses 80)")
        p.add_argument("--no-heartbeat", action="store_true")

    p_status = sub.add_parser("status", help="handshake + read firmware version")
    common(p_status)

    p_state = sub.add_parser("state", help="query BaseStatus/HeadStatus (decoded fields)")
    common(p_state)
    p_state.add_argument("--hex", action="store_true", help="also print raw protobuf hex")

    p_battery = sub.add_parser("battery", help="head hot-swap powerpack charge %")
    common(p_battery)
    p_battery.add_argument("--watch", action="store_true",
                            help="keep polling instead of a single read")
    p_battery.add_argument("--interval", type=float, default=30.0,
                           help="seconds between polls with --watch (default: %(default)s)")
    p_battery.add_argument("--count", type=int, default=1000,
                           help="max polls with --watch (default: until Ctrl-C)")

    p_monitor = sub.add_parser("monitor", help="print all incoming messages")
    common(p_monitor)
    p_monitor.add_argument("--duration", type=float, default=10.0)

    p_raw = sub.add_parser("raw", help="send an arbitrary message type")
    common(p_raw)
    p_raw.add_argument("type", type=int, help="MessageType value to send")
    p_raw.add_argument("hex", nargs="?", default="",
                       help="message body as hex (e.g. 0086)")
    p_raw.add_argument("--wait", type=float, default=5.0,
                       help="seconds to listen for replies")
    p_raw.add_argument("--no-reply", action="store_true")

    args = parser.parse_args()
    if args.command is None:
        args.command = "status"

    args.via_base = False
    if args.target == "head":
        via = args.via or "base"  # default: route through the base
        if via == "direct":
            args.host = HEAD_IP if args.host == BASE_IP else args.host
            args.port = args.port or HEAD_PORT
            args.identity, args.device = PC2, HEAD
        else:  # via base: transport to the base, packets addressed to the head
            args.host = BASE_IP if args.host == BASE_IP else args.host
            args.port = args.port or BASE_PORT
            args.identity, args.device = PC, HEAD
            args.via_base = True
    else:
        args.port = args.port or BASE_PORT
        args.identity, args.device = PC, BASE
    global PROTOCOL_VERSION
    PROTOCOL_VERSION = args.protocol_version

    try:
        {"status": cmd_status, "state": cmd_state, "battery": cmd_battery,
     "monitor": cmd_monitor, "raw": cmd_raw}[args.command](args)
    except (ConnectionRefusedError, ConnectionError) as exc:
        print("error: %s (is the device reachable on %s?)" % (exc, args.host), file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
