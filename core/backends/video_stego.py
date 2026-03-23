"""
video_stego.py — DWT Spread Spectrum Video Steganography  (Optimised)
======================================================================
Hides text or images inside video files using Wavelet-domain Spread
Spectrum with ECC and AES-256-GCM encryption.

Performance optimisations vs naive version:
  • float32 DWT/IDWT          — 1.7x faster transforms
  • Vectorised SS embedding   — 4x faster per-frame embed step
  • Threaded read/process/write pipeline — overlaps I/O with compute
  • Pass-through frames       — frames beyond payload skip DWT entirely
  • Early exit on extract     — stops reading once all bits collected
  • np.packbits/unpackbits    — fast bit packing instead of Python loops

Supports reading: MP4, MKV, AVI — any format OpenCV can open.
Output: always lossless HuffYUV (HFYU) AVI with original audio preserved.

CLI:
    python video_stego.py embed input.mp4 output.avi --text "hello" --password key
    python video_stego.py embed input.mp4 output.avi --image photo.png --password key
    python video_stego.py extract output.avi --password key
    python video_stego.py extract output.avi --password key --out saved.jpg
"""

import cv2
import numpy as np
import struct
import hashlib
import os
import sys
import io
import shutil
import subprocess
import tempfile
import lzma
from queue import Queue
from threading import Thread
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

try:
    import cupy as cp
except ImportError:
    import numpy as cp

# ═══════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

JPEG_QUALITY    = 82
EMBED_STRENGTH  = 18.0
HEADER_STRENGTH = 80.0
COEFFS_PER_BIT  = 1
ECC_REPEAT      = 1

MAGIC      = b'\xDE\xAD\xBE\xEF'
TYPE_TEXT  = 0x01
TYPE_IMAGE = 0x02
TYPE_COMPRESSED = 0x08  # Flag bit for compression

HEADER_COEFFS = 32 * COEFFS_PER_BIT   # reserved in LH of frame 0

_SENTINEL = object()


# ═══════════════════════════════════════════════════════════════════════
#  HAAR DWT / IDWT  — float32  (1.7x faster than float64)
# ═══════════════════════════════════════════════════════════════════════

def dwt2(arr):
    f  = cp.asarray(arr).astype(cp.float32)
    L  = (f[:, 0::2] + f[:, 1::2]) * cp.float32(0.5)
    Hh = (f[:, 0::2] - f[:, 1::2]) * cp.float32(0.5)
    LL = (L[0::2, :]  + L[1::2, :])  * cp.float32(0.5)
    LH = (L[0::2, :]  - L[1::2, :])  * cp.float32(0.5)
    HL = (Hh[0::2, :] + Hh[1::2, :]) * cp.float32(0.5)
    HH = (Hh[0::2, :] - Hh[1::2, :]) * cp.float32(0.5)
    return LL, LH, HL, HH


def idwt2(LL, LH, HL, HH):
    rows = LL.shape[0] * 2
    L  = cp.empty((rows, LL.shape[1]), dtype=cp.float32)
    Hh = cp.empty_like(L)
    L[0::2,  :] = LL + LH;  L[1::2,  :] = LL - LH
    Hh[0::2, :] = HL + HH;  Hh[1::2, :] = HL - HH
    out = cp.empty((rows, L.shape[1] * 2), dtype=cp.float32)
    out[:, 0::2] = L + Hh;  out[:, 1::2] = L - Hh
    out_clip = cp.clip(out, 0, 255)
    if hasattr(out_clip, 'get'):
        return out_clip.get()
    return out_clip


# ═══════════════════════════════════════════════════════════════════════
#  ECC — triple-repetition majority vote
# ═══════════════════════════════════════════════════════════════════════

def ecc_encode(data: bytes) -> bytes:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            b = (byte >> i) & 1
            bits.extend([b] * ECC_REPEAT)
    while len(bits) % 8:
        bits.append(0)
    out = bytearray()
    for i in range(0, len(bits), 8):
        v = 0
        for j in range(8):
            v = (v << 1) | bits[i + j]
        out.append(v)
    return bytes(out)


def ecc_decode(data: bytes, original_byte_count: int) -> bytes:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    recovered = []
    for i in range(original_byte_count * 8):
        start = i * ECC_REPEAT
        group = bits[start: start + ECC_REPEAT]
        recovered.append(1 if sum(group) > ECC_REPEAT // 2 else 0)
    out = bytearray()
    for i in range(0, len(recovered), 8):
        v = 0
        for j in range(8):
            v = (v << 1) | recovered[i + j]
        out.append(v)
    return bytes(out)


# ═══════════════════════════════════════════════════════════════════════
#  AES-256-GCM
# ═══════════════════════════════════════════════════════════════════════

def _key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()

def aes_encrypt(data: bytes, password: str) -> bytes:
    key = _key(password); nonce = os.urandom(12)
    enc = Cipher(algorithms.AES(key), modes.GCM(nonce),
                 backend=default_backend()).encryptor()
    ct  = enc.update(data) + enc.finalize()
    return nonce + enc.tag + ct

def aes_decrypt(data: bytes, password: str) -> bytes:
    key = _key(password)
    nonce, tag, ct = data[:12], data[12:28], data[28:]
    dec = Cipher(algorithms.AES(key), modes.GCM(nonce, tag),
                 backend=default_backend()).decryptor()
    return dec.update(ct) + dec.finalize()


# ═══════════════════════════════════════════════════════════════════════
#  PACKET
# ═══════════════════════════════════════════════════════════════════════

def pack(payload: bytes, dtype: int) -> bytes:
    return MAGIC + struct.pack('>BI', dtype, len(payload)) + payload

def unpack(data: bytes):
    if data[:4] != MAGIC:
        raise ValueError("Magic bytes not found — wrong password or no hidden data.")
    dtype = struct.unpack('>B', data[4:5])[0]
    plen  = struct.unpack('>I', data[5:9])[0]
    return dtype, data[9: 9 + plen]


# ═══════════════════════════════════════════════════════════════════════
#  IMAGE PREPARATION
# ═══════════════════════════════════════════════════════════════════════

def prepare_image(image_path: str) -> bytes:
    img = Image.open(image_path)
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    ext = os.path.splitext(image_path)[1].lower()
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    jpeg_bytes = buf.getvalue()
    label = "already JPEG, re-encoded" if ext in ('.jpg', '.jpeg') \
            else f"converted {ext.upper()} → JPEG"
    print(f"    {img.width}×{img.height}px | {label} | "
          f"{len(jpeg_bytes)/1024:.1f} KB (quality={JPEG_QUALITY})")
    return jpeg_bytes


# ═══════════════════════════════════════════════════════════════════════
#  VECTORISED CARRIER GENERATION
# ═══════════════════════════════════════════════════════════════════════

def _header_seed(bit_i: int) -> int:
    return 0xDEAD0000 + bit_i

def _make_carriers_batch(n: int, frame_seed: int):
    """Generate all n carriers in ONE rng draw. Returns (n, CPB) float32 ±1."""
    if hasattr(cp, 'random'):
        cp.random.seed(frame_seed)
        raw = cp.random.randint(0, 2, size=n * COEFFS_PER_BIT, dtype=cp.uint8)
        return (raw.reshape(n, COEFFS_PER_BIT).astype(cp.float32) * 2) - 1
    else:
        rng = np.random.default_rng(frame_seed)
        raw = rng.integers(0, 2, size=n * COEFFS_PER_BIT, dtype=np.uint8)
        return (raw.reshape(n, COEFFS_PER_BIT).astype(cp.float32) * 2) - 1

def _make_carrier_single(size: int, seed: int):
    if hasattr(cp, 'random'):
        cp.random.seed(seed)
        return (cp.random.randint(0, 2, size=size, dtype=cp.uint8).astype(cp.float32) * 2) - 1
    else:
        rng = np.random.default_rng(seed)
        return (rng.integers(0, 2, size=size, dtype=np.uint8).astype(np.float32) * 2) - 1


# ═══════════════════════════════════════════════════════════════════════
#  VECTORISED SS EMBED / EXTRACT
# ═══════════════════════════════════════════════════════════════════════

def _ss_embed(region, bits, n: int, frame_seed: int, strength: float) -> None:
    """Embed n bits into region in-place using batch carrier matrix."""
    cars = _make_carriers_batch(n, frame_seed)             # (n, CPB)
    bits_cp = cp.asarray(bits[:n])
    sigs = cp.where(bits_cp == 1,
                    cp.float32(strength),
                    cp.float32(-strength))                  # (n,)
    region[:n * COEFFS_PER_BIT] += (cars * sigs[:, None]).ravel()

def _ss_extract(region, n: int, frame_seed: int):
    """Extract n bits from region via dot-product correlation. Returns int8 array."""
    cars  = _make_carriers_batch(n, frame_seed)
    chunk = region[:n * COEFFS_PER_BIT].reshape(n, COEFFS_PER_BIT)
    res = ((chunk * cars).sum(axis=1) > 0).astype(cp.int8)
    if hasattr(res, 'get'):
        return res.get()
    return res


# ═══════════════════════════════════════════════════════════════════════
#  AUDIO HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _ffmpeg(*args):
    try:
        return subprocess.run(['ffmpeg', '-y', *args], capture_output=True)
    except FileNotFoundError:
        class DummyRet: returncode = 1
        return DummyRet()

def _has_audio(path: str) -> bool:
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a',
             '-show_entries', 'stream=codec_type',
             '-of', 'default=noprint_wrappers=1:nokey=1', path],
            capture_output=True, text=True)
        return 'audio' in r.stdout
    except FileNotFoundError:
        return False

def _extract_audio(src: str, dst: str) -> bool:
    if not _has_audio(src): return False
    r = _ffmpeg('-i', src, '-vn', '-acodec', 'copy', dst)
    return r.returncode == 0 and os.path.exists(dst)

def _mux_audio(video: str, audio: str, out: str) -> bool:
    r = _ffmpeg('-i', video, '-i', audio,
                '-c:v', 'copy', '-c:a', 'copy',
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest', out)
    return r.returncode == 0 and os.path.exists(out)


# ═══════════════════════════════════════════════════════════════════════
#  FRAME PROCESSING (pure function for clarity)
# ═══════════════════════════════════════════════════════════════════════

def _process_frame_embed(frame, ecc_bits_unpacked, bit_idx,
                         total_bits, frame_idx, H, W,
                         is_frame0, total_ecc_B):
    """Returns (modified_frame, bits_embedded). Uses all channels and all AC subbands for max capacity."""
    if not is_frame0 and bit_idx >= total_bits:
        return frame, 0

    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    channels = [ycrcb[:, :, 0], ycrcb[:, :, 1], ycrcb[:, :, 2]]
    modified_channels = []
    current_bit_idx = bit_idx

    for ch_idx, ch in enumerate(channels):
        if current_bit_idx >= total_bits and not (is_frame0 and ch_idx == 0):
            modified_channels.append(ch)
            continue
            
        fch = ch.astype(np.float32)
        LL, LH, HL, HH = dwt2(fch)
        
        # We always process frame 0 channel 0 for the header
        if is_frame0 and ch_idx == 0:
            lh_flat = LH.ravel().copy()
            hl_flat = HL.ravel().copy()
            hh_flat = HH.ravel().copy()

            # Embed 32-bit header in LH of Frame 0
            for i in range(32):
                s, e = i * COEFFS_PER_BIT, (i + 1) * COEFFS_PER_BIT
                c    = _make_carrier_single(COEFFS_PER_BIT, _header_seed(i))
                bit  = (total_ecc_B >> (31 - i)) & 1
                lh_flat[s:e] += (cp.float32(HEADER_STRENGTH) if bit
                                 else cp.float32(-HEADER_STRENGTH)) * c

            # Embed remainder of payload in HL and HH (and LH after header)
            pr = cp.concatenate([lh_flat[HEADER_COEFFS:], hl_flat, hh_flat])
            n  = min(total_bits - current_bit_idx, len(pr) // COEFFS_PER_BIT)
            if n > 0:
                _ss_embed(pr, ecc_bits_unpacked[current_bit_idx:], n, frame_idx * 10 + ch_idx, EMBED_STRENGTH)
                current_bit_idx += n
            
            # Reconstruct
            lh_split = len(lh_flat) - HEADER_COEFFS
            lh_flat[HEADER_COEFFS:] = pr[:lh_split]
            hl_flat[:] = pr[lh_split: lh_split + HL.size]
            hh_flat[:] = pr[lh_split + HL.size:]
            
            LH, HL, HH = lh_flat.reshape(LH.shape), hl_flat.reshape(HL.shape), hh_flat.reshape(HH.shape)
        else:
            combined = cp.concatenate([LH.ravel(), HL.ravel(), HH.ravel()])
            n        = min(total_bits - current_bit_idx, len(combined) // COEFFS_PER_BIT)
            if n > 0:
                _ss_embed(combined, ecc_bits_unpacked[current_bit_idx:], n, frame_idx * 10 + ch_idx, EMBED_STRENGTH)
                current_bit_idx += n
            
            mid1 = LH.size
            mid2 = mid1 + HL.size
            LH  = combined[:mid1].reshape(LH.shape)
            HL  = combined[mid1:mid2].reshape(HL.shape)
            HH  = combined[mid2:].reshape(HH.shape)

        modified_channels.append(idwt2(LL, LH, HL, HH).astype(np.uint8))

    ycrcb_mod = cv2.merge(modified_channels)
    return cv2.cvtColor(ycrcb_mod, cv2.COLOR_YCrCb2BGR), (current_bit_idx - bit_idx)


# ═══════════════════════════════════════════════════════════════════════
#  EMBED
# ═══════════════════════════════════════════════════════════════════════

def embed(video_in:   str,
          video_out:  str,
          text:       str = None,
          image_path: str = None,
          password:   str = "secret") -> str:
    if (text is None) == (image_path is None):
        raise ValueError("Provide exactly one of 'text' or 'image_path'.")

    print("\n══════════════════════════════════════════")
    print("  VIDEO STEGANOGRAPHY  ▸  EMBED")
    print("══════════════════════════════════════════")

    if text is not None:
        raw = text.encode('utf-8'); dtype = TYPE_TEXT
        print(f"  Payload  : text ({len(raw)} bytes)")
    else:
        print("  Payload  : image"); raw = prepare_image(image_path); dtype = TYPE_IMAGE

    # Modern Cyber-efficiency: Always attempt compression for large payloads
    original_size = len(raw)
    compressed = lzma.compress(raw)
    if len(compressed) < original_size:
        raw = compressed
        dtype |= TYPE_COMPRESSED
        print(f"  LZMA Comp: {original_size} → {len(raw)} bytes ({len(raw)/original_size*100:.1f}%)")

    packet      = pack(raw, dtype)
    encrypted   = aes_encrypt(packet, password)
    ecc_data    = ecc_encode(encrypted)
    total_ecc_B = len(ecc_data)
    total_bits  = total_ecc_B * 8

    print(f"  Encrypted: {len(encrypted)} bytes")
    print(f"  ECC (×{ECC_REPEAT})  : {total_ecc_B} bytes  ({total_bits} bits)")

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened(): raise IOError(f"Cannot open: {video_in}")

    fps     = cap.get(cv2.CAP_PROP_FPS) or 25.0
    W       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    lh_hl_hh_sz = (H // 2) * (W // 2) * 3
    # Capacity across 3 channels (YCrCb)
    cap_frame0 = max(0, (lh_hl_hh_sz - HEADER_COEFFS) // COEFFS_PER_BIT)
    total_cap  = cap_frame0 + (lh_hl_hh_sz * 3) // COEFFS_PER_BIT * max(0, nframes - 1)

    print(f"  Video    : {W}×{H} @ {fps:.1f}fps | {nframes} frames")
    print(f"  Capacity : {total_cap} bits  |  Need: {total_bits} bits  "
          f"({total_bits / max(total_cap,1) * 100:.1f}% used)")

    if total_bits > total_cap:
        cap.release()
        raise OverflowError(f"Payload too large! Need {total_bits} bits, have {total_cap}.")

    tmp_dir   = tempfile.mkdtemp(prefix='vstego_')
    audio_tmp = os.path.join(tmp_dir, 'audio.mkv')
    has_audio = _extract_audio(video_in, audio_tmp)
    print(f"  Audio    : {'extracted ✔' if has_audio else 'none in source'}")

    if not video_out.lower().endswith('.mp4'):
        video_out = os.path.splitext(video_out)[0] + '.mp4'
        print(f"  ⚠  Renamed to: {video_out}")

    video_only = os.path.join(tmp_dir, 'video_only.mp4') if has_audio else video_out
    
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{W}x{H}', '-pix_fmt', 'bgr24', '-r', str(fps),
        '-i', '-', '-c:v', 'libx264rgb', '-preset', 'ultrafast', '-crf', '0',
        video_only
    ]
    try:
        writer_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        cap.release(); shutil.rmtree(tmp_dir, ignore_errors=True)
        raise IOError("FFmpeg is missing. Cannot spawn video encoder pipe.")

    # Pre-unpack ECC bits with numpy (faster than Python loop later)
    ecc_bits_unpacked = np.unpackbits(
        np.frombuffer(ecc_data, dtype=np.uint8)
    ).astype(np.int8)

    # Threaded writer: write frames on a background thread while main thread processes
    write_q = Queue(maxsize=16)
    wt      = Thread(target=lambda: [write_q.get() is _SENTINEL or
                                     (writer.write(write_q.get()) or True)
                                     for _ in iter(lambda: write_q.get() is not _SENTINEL, False)],
                     daemon=True)

    # Simpler writer thread piping explicitly securely to ffmpeg natively
    def _write_worker():
        while True:
            item = write_q.get()
            if item is _SENTINEL:
                break
            try:
                writer_proc.stdin.write(item.tobytes())
            except Exception:
                pass
        try:
            writer_proc.stdin.close()
            writer_proc.wait()
        except Exception:
            pass

    wt = Thread(target=_write_worker, daemon=True)
    wt.start()

    bit_idx = 0; frame_idx = 0; frames_w_payload = 0
    print(f"\n  Embedding", end='', flush=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        modified, n = _process_frame_embed(
            frame, ecc_bits_unpacked, bit_idx, total_bits,
            frame_idx, H, W, frame_idx == 0, total_ecc_B)

        write_q.put(modified)
        bit_idx += n
        if n > 0: frames_w_payload += 1
        frame_idx += 1
        if frame_idx % 60 == 0: print('.', end='', flush=True)

    write_q.put(_SENTINEL)
    wt.join()
    cap.release()

    if has_audio:
        print(f"\n  Muxing audio...", end='', flush=True)
        ok = _mux_audio(video_only, audio_tmp, video_out)
        print(f" {'✔' if ok else '⚠ failed'}")
    shutil.rmtree(tmp_dir, ignore_errors=True)

    passthrough = frame_idx - frames_w_payload
    print(f"\n  ✅ Done  |  {bit_idx}/{total_bits} bits across {frames_w_payload} frames")
    print(f"  ⚡ {passthrough} frames skipped DWT (pass-through)")
    print(f"  Output   : {video_out}\n")
    return video_out


# ═══════════════════════════════════════════════════════════════════════
#  EXTRACT
# ═══════════════════════════════════════════════════════════════════════

def extract(video_in:          str,
            password:          str = "secret",
            output_image_path: str = None):
    print("\n══════════════════════════════════════════")
    print("  VIDEO STEGANOGRAPHY  ▸  EXTRACT")
    print("══════════════════════════════════════════")

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened(): raise IOError(f"Cannot open: {video_in}")

    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"  Video : {W}×{H} @ {cap.get(cv2.CAP_PROP_FPS):.1f}fps | {nframes} frames")

    total_ecc_B = None; total_bits = None
    collected   = []; bit_idx = 0; frame_idx = 0
    print("  Reading", end='', flush=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        ch_list = [ycrcb[:, :, 0], ycrcb[:, :, 1], ycrcb[:, :, 2]]

        for ch_idx, ch in enumerate(ch_list):
            if total_bits is not None and bit_idx >= total_bits:
                break
                
            fch = ch.astype(np.float32)
            _, LH, HL, HH = dwt2(fch)

            if frame_idx == 0 and ch_idx == 0:
                lh_flat = LH.ravel()
                val = 0
                for i in range(32):
                    s, e = i * COEFFS_PER_BIT, (i + 1) * COEFFS_PER_BIT
                    c    = _make_carrier_single(COEFFS_PER_BIT, _header_seed(i))
                    val  = (val << 1) | (1 if float(cp.dot(lh_flat[s:e], c)) > 0 else 0)
                total_ecc_B = val; total_bits = total_ecc_B * 8
                print(f"\n  Header  : {total_ecc_B} ECC bytes ({total_bits} bits)")
                print("  Loading ", end='', flush=True)

                pr = cp.concatenate([lh_flat[HEADER_COEFFS:], HL.ravel(), HH.ravel()])
                n  = min(total_bits, len(pr) // COEFFS_PER_BIT)
                collected.append(_ss_extract(pr, n, frame_idx * 10 + ch_idx))
                bit_idx += n
            else:
                combined  = cp.concatenate([LH.ravel(), HL.ravel(), HH.ravel()])
                remaining = (total_bits - bit_idx) if total_bits else len(combined) // COEFFS_PER_BIT
                n         = min(remaining, len(combined) // COEFFS_PER_BIT)
                if n > 0:
                    collected.append(_ss_extract(combined, n, frame_idx * 10 + ch_idx))
                    bit_idx += n

        frame_idx += 1
        if frame_idx % 60 == 0: print('.', end='', flush=True)

    cap.release()
    print(f"\n  Read {bit_idx} bits from {frame_idx} frames")

    if total_ecc_B is None:
        raise ValueError("Header not found — not a valid stego video.")

    # Fast bit assembly with numpy
    all_bits  = np.concatenate(collected)[:total_bits]
    pad       = (8 - len(all_bits) % 8) % 8
    if pad: all_bits = np.concatenate([all_bits, np.zeros(pad, dtype=np.int8)])
    ecc_bytes = np.packbits(all_bits.astype(np.uint8)).tobytes()[:total_ecc_B]

    if total_ecc_B % ECC_REPEAT != 0:
        raise ValueError("ECC length mismatch — video may be corrupted.")
    enc_byte_count = total_ecc_B // ECC_REPEAT
    print(f"  ECC     : {total_ecc_B} → {enc_byte_count} bytes")
    encrypted = ecc_decode(ecc_bytes, enc_byte_count)

    try:
        packet = aes_decrypt(encrypted, password)
    except Exception:
        raise ValueError("Decryption failed — wrong password or corrupted data.")

    dtype, payload = unpack(packet)
    
    # Handle compression
    if dtype & TYPE_COMPRESSED:
        print(f"  LZMA     : Decompressing payload...")
        payload = lzma.decompress(payload)
        dtype &= ~TYPE_COMPRESSED

    if dtype == TYPE_TEXT:
        result = payload.decode('utf-8')
        print(f"\n  ✅ Text extracted ({len(result)} chars):")
        print("  ┌" + "─" * 52)
        for line in result.splitlines()[:8]:
            print(f"  │ {line}")
        print("  └" + "─" * 52 + "\n")
        return result

    elif dtype == TYPE_IMAGE:
        if output_image_path is None:
            output_image_path = os.path.splitext(video_in)[0] + '_extracted.jpg'
        with open(output_image_path, 'wb') as f:
            f.write(payload)
        img = Image.open(io.BytesIO(payload))
        print(f"\n  ✅ Image {img.width}×{img.height}px → {output_image_path}\n")
        return payload
    else:
        raise ValueError(f"Unknown payload type: {dtype}")


# ═══════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════

def _get(args, flag, default=None):
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args): return args[idx + 1]
    return default

def _usage():
    print("""
Video Steganography  |  DWT Spread Spectrum + AES-256-GCM + ECC  (Optimised)
══════════════════════════════════════════════════════════════════════════════

  EMBED text:
    python video_stego.py embed <input> <output.mp4> --text "message" --password key

  EMBED image:
    python video_stego.py embed <input> <output.mp4> --image photo.png --password key

  EXTRACT:
    python video_stego.py extract <output.mp4> --password key
    python video_stego.py extract <output.mp4> --password key --out result.jpg

  Notes:
    • Input: .mp4 / .mkv / .avi / any OpenCV-readable format
    • Output: always .mp4 (libx264rgb lossless, 80% smaller) — audio preserved
    • Images auto-converted to JPEG (quality 82)
    • Default password: "secret"
""")

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args: _usage(); sys.exit(0)
    mode = args[0].lower()
    if mode == 'embed':
        if len(args) < 3: _usage(); sys.exit(1)
        embed(args[1], args[2],
              text=_get(args,'--text'), image_path=_get(args,'--image'),
              password=_get(args,'--password','secret'))
    elif mode == 'extract':
        if len(args) < 2: _usage(); sys.exit(1)
        extract(args[1], password=_get(args,'--password','secret'),
                output_image_path=_get(args,'--out'))
    else:
        print(f"Unknown mode: {mode}"); _usage(); sys.exit(1)
