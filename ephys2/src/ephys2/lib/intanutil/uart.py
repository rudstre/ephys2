import numpy as np

def decode_uart_from_ttl(binary_data: np.ndarray, fs: float, baud_rate: float):
    """Decode UART bytes from a TTL waveform.

    This matches the MATLAB implementation exactly:
      1. Detect falling edges as potential start bits
      2. Verify start and stop bits
      3. Extract 8 data bits at their midpoints
      4. Convert bits to bytes (LSB-first)

    Args:
        binary_data: TTL signal (0/1) as a NumPy array
        fs: Sampling frequency (Hz)
        baud_rate: UART baud rate (bits/sec)

    Returns:
        decoded_bytes: np.ndarray of decoded UART bytes (dtype uint8)
        byte_times:   np.ndarray of sample indices for each decoded byte
    """
    # Work with ints throughout
    binary_int = binary_data.astype(int)
    bit_samples = fs / baud_rate
    decoded_bytes = []
    byte_times = []

    # Find falling edges (MATLAB: find(diff(binaryData)==-1))
    start_bit_queue = np.where(np.diff(binary_int) == -1)[0]

    i = 0
    while i < len(start_bit_queue):
        idx = start_bit_queue[i]
        # Need 10 bit periods available
        if idx + 10 * bit_samples > len(binary_int):
            break

        # Center of start bit
        start_idx = idx + 1
        sb_idx = int(round(start_idx + 0.5 * bit_samples))
        if binary_int[sb_idx] != 0:
            i += 1
            continue

        # Center of stop bit
        stop_idx = int(round(start_idx + 9.5 * bit_samples))
        if binary_int[stop_idx] != 1:
            i += 1
            continue

        # Gather data‐bit sample indices
        data_bit_indices = []
        cur = start_idx + bit_samples
        end_limit = stop_idx - bit_samples
        while cur <= end_limit + 1e-6:
            data_bit_indices.append(int(round(cur)))
            cur += bit_samples

        # Must have exactly 8 bits
        if len(data_bit_indices) == 8:
            bits = binary_int[data_bit_indices]
            byte = 0
            for b_i, b in enumerate(bits):
                byte |= (b << b_i)  # LSB first
            decoded_bytes.append(byte)
            byte_times.append(start_idx)

            # Skip over any start bits inside this frame
            next_i = i + 1
            while next_i < len(start_bit_queue) and start_bit_queue[next_i] <= stop_idx:
                next_i += 1
            i = next_i
        else:
            i += 1

    return (
        np.array(decoded_bytes, dtype=np.uint8),
        np.array(byte_times, dtype=int),
    )


def decode_serial_packets(byte_vec: np.ndarray, byte_times: np.ndarray):
    """Group a stream of UART bytes into fixed-length packets."""
    packet_len = 11
    packets = []
    i = 0

    while i <= len(byte_vec) - packet_len:
        if byte_vec[i] == 0xAA:
            pkt = byte_vec[i : i + packet_len]
            channel_id = int(pkt[1])

            # Bytes 3–6 and 7–10 are raw durations in microseconds
            pulse_width_raw = int.from_bytes(pkt[2:6].tobytes(), "little")
            wait_time_raw   = int.from_bytes(pkt[6:10].tobytes(), "little")

            # Directly convert µs → ms with one divide-by-1000
            pulse_width_ms = pulse_width_raw / 1_000.0
            wait_time_ms   = wait_time_raw   / 1_000.0

            checksum = int(pkt[10])
            expected = sum(int(b) for b in pkt[1:6]) % 256
            valid = (checksum == expected)

            packets.append({
                "startMarker":  int(pkt[0]),
                "channelID":    channel_id,
                "detectionTime": int(byte_times[i]),
                "waitTime":      wait_time_ms,    # ms
                "pulseWidth":    pulse_width_ms,  # ms
                "valid":         valid,
            })
            i += packet_len
        else:
            i += 1

    return packets


def deserialize_teensy(data_serial: dict, chunk_start: int = None, chunk_end: int = None):
    """Reconstruct events from packet info using a sparse approach.

    Args:
        data_serial: dict with keys 'fs' (Hz) and 'packets' (from decode_serial_packets)
        chunk_start: Optional sample-index start for this chunk
        chunk_end:   Optional sample-index end for this chunk

    Returns:
        A binary (0/1) 2D NumPy array of shape
          (chunk_end-chunk_start, max_channel+1)
        or, if no packets/events, an empty array.
    """
    fs = data_serial["fs"]
    packets = data_serial["packets"]

    # No packets ⇒ empty result
    if not packets:
        return np.zeros((chunk_end - chunk_start, 2), dtype=np.uint8)

    # Determine max channel
    max_ch = max(p["channelID"] for p in packets)

    # Clip events to [0, chunk_end) if chunk_end given
    max_reasonable_length = chunk_end if chunk_end is not None else float("inf")
    events = []

    for p in packets:
        ch = p["channelID"]
        if ch > max_ch:
            continue

        # Convert ms→s, then to samples
        wait_s = p["waitTime"] / 1000.0
        cf_s = 0.36 / 1000.0
        start = p["detectionTime"] - int(round((wait_s + cf_s) * fs))

        pw_s = p["pulseWidth"] / 1000.0
        pw_samples = int(round(pw_s * fs))
        end = start + pw_samples

        # Bounds checks
        start = max(0, start)
        if pw_samples > 5 * fs:
            pw_samples = int(5 * fs)
        if end > max_reasonable_length:
            end = int(max_reasonable_length)

        # Skip if completely outside chunk
        if chunk_start is not None and chunk_end is not None:
            if end <= chunk_start or start >= chunk_end:
                continue

        if end > start:
            events.append((start, end, ch))

    # No valid events ⇒ empty array
    if not events:
        return np.zeros((chunk_end - chunk_start, max_ch + 1), dtype=np.uint8)

    # Determine output range
    result_start, result_end = chunk_start, chunk_end

    height = int(result_end - result_start)
    data_vec = np.zeros((height, max_ch + 1), dtype=np.uint8)

    # Stamp events into the array
    for start, end, ch in events:
        clip_s = max(start, result_start) - result_start
        clip_e = min(end, result_end) - result_start
        data_vec[clip_s:clip_e, ch] = 1

    return data_vec