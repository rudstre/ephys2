"""
Utility class and methods for reading auxiliary data from Intan RHD2000 datasets.
"""

import gc
import os

import h5py
import numpy as np

from ephys2.lib.h5 import *
from ephys2.lib.intanutil.uart import (decode_serial_packets,
                                       decode_uart_from_ttl,
                                       deserialize_teensy)
from ephys2.lib.singletons import global_metadata, global_state, logger
from ephys2.lib.types import *
from ephys2.pipeline.input.base import *
from ephys2.lib.mpi import MPI


class RHDAuxStage(ProcessingStage):

    @staticmethod
    def parameters(
        dio_chs: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        aio_chs: List[int] = [1, 2, 3, 4, 5, 6],
    ) -> Parameters:
        # Two aux types: digital rising-edge times (with optional UART decode) and analog samples
        return {
            "aux_output_dir": StringParameter(
                units=None,
                description="Custom output directory for auxiliary data files. Use empty string '' to use the default session path."
            ),
            "aux_channels": MultiParameter(
                units=None,
                description="aux channels: digital_in (rising edges, with optional UART decode) or analog_in",
                options=[
                    # 1) Rising-edge only
                    DictParameter(
                        None,
                        "Digital aux; rising edges only",
                        {
                            "digital_in": MultiCategoricalParameter(None, "", dio_chs),
                            "name": StringParameter(None, ""),
                        },
                    ),
                    # 2) Rising-edge + UART decode
                    DictParameter(
                        None,
                        "Digital aux; rising edges + UART decode",
                        {
                            "digital_in": MultiCategoricalParameter(None, "", dio_chs),
                            "name": StringParameter(None, ""),
                            "decode_teensy": BoolParameter(
                                None, "whether to decode TTL as UART frames"
                            ),
                            "baud_rate": IntParameter(
                                "baud_rate", "UART baud rate", 1, np.inf
                            ),
                        },
                    ),
                    # 3) Analog inputs (downsampled)
                    DictParameter(
                        None,
                        "Analog aux; downsampled continuous data",
                        {
                            "analog_in": MultiCategoricalParameter(None, "", aio_chs),
                            "name": StringParameter(None, ""),
                            "downsample": IntParameter(
                                "samples", "downsample ratio", 1, np.inf
                            ),
                        },
                    ),
                ],
            )
        }

    def initialize(self):
        # Force collection to start with clean memory
        gc.collect()

        # Whether auxiliary serializers are enabled
        self.digital_in = False
        self.analog_in = False
        self.decode_teensy = False

        super(type(self), self).initialize()

        assert "session_splits" in global_metadata
        assert "session_paths" in global_metadata
        assert len(global_metadata["session_splits"]) == len(
            global_metadata["session_paths"]
        )

        # Get custom output directory if specified
        aux_output_dir_raw = self.cfg.get("aux_output_dir", "")
        self.aux_output_dir = aux_output_dir_raw if aux_output_dir_raw.strip() else None
        
        # Create the output directory if it doesn't exist
        if self.aux_output_dir and not os.path.exists(self.aux_output_dir):
            try:
                os.makedirs(self.aux_output_dir, exist_ok=True)
                logger.print(f"Created output directory: {self.aux_output_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory {self.aux_output_dir}: {e}")

        # Create serializers for auxiliary data as needed
        self.digital_chs = []
        self.digital_serializers = []
        self.analog_chs = []
        self.analog_serializers = []
        self.uart_serializers = {}  # Dictionary keyed by session index
        for aux_decl in self.cfg["aux_channels"]:

            if "digital_in" in aux_decl:
                assert (
                    self.cfg["batch_overlap"] == 0
                ), "batch_overlap must be zero for aux"
                # rising-edge digital
                self.digital_chs = np.array(aux_decl["digital_in"], dtype=np.intp)
                self.digital_in = True
                # optional UART decode flag
                self.decode_teensy = bool(aux_decl.get("decode_teensy", False))
                if self.decode_teensy:
                    assert (
                        len(self.digital_chs) == 1
                    ), "decode_teensy supports exactly one digital pin"
                    self.baud_rate = aux_decl.get("baud_rate", 3000)
                # create serializers per session

                for i, path in enumerate(global_metadata["session_paths"]):
                    # Use custom output directory if provided
                    output_path = self.aux_output_dir if self.aux_output_dir else path
                    
                    # Make sure the directory exists (for nested directories)
                    os.makedirs(output_path, exist_ok=True)
                    
                    # edge-time serializer
                    s = H5TMultiBatchSerializer(
                        full_check=global_state.debug,
                        rank=self.rank,
                        n_workers=self.n_workers,
                    )
                    s.initialize(os.path.join(output_path, f'session_{i}_{aux_decl["name"]}'))
                    self.digital_serializers.append(s)
                    # UART decode serializer if requested
                    if self.decode_teensy:
                        base, ext = os.path.splitext(aux_decl["name"])
                        uart_name = f"{base}_teensy{ext}"
                        # use TMultiBatchSerializer to write event times per channel
                        ts = H5TMultiBatchSerializer(
                            full_check=global_state.debug,
                            rank=self.rank,
                            n_workers=self.n_workers,
                        )
                        ts.initialize(os.path.join(output_path, f"session_{i}_{uart_name}"))
                        self.uart_serializers[i] = ts  # Store with session index as key

            if "analog_in" in aux_decl:
                assert (
                    self.cfg["batch_overlap"] == 0
                ), "nonzero batch_overlap not supported with aux channel persistence, for now"
                self.analog_ds = aux_decl["downsample"]
                self.analog_chs = (
                    np.array(aux_decl["analog_in"], dtype=np.intp) - 1
                )  # Analog is 1-indexed
                for i, path in enumerate(global_metadata["session_paths"]):
                    # Use custom output directory if provided
                    output_path = self.aux_output_dir if self.aux_output_dir else path
                    
                    # Make sure the directory exists (for nested directories)
                    os.makedirs(output_path, exist_ok=True)
                    
                    s = H5SBatchSerializer(
                        full_check=global_state.debug,
                        rank=self.rank,
                        n_workers=self.n_workers,
                    )
                    s.initialize(os.path.join(output_path, f'session_{i}_{aux_decl["name"]}'))
                    self.analog_serializers.append(s)

        # Initialize full-session TTL buffers if UART decode is enabled
        if self.decode_teensy:
            # prepare raw TTL signal and time accumulators per session
            self.ttl_signal_accum = {
                i: np.array([], dtype=int) for i in self.uart_serializers.keys()
            }
            self.ttl_time_accum = {
                i: np.array([], dtype=int) for i in self.uart_serializers.keys()
            }

    def validate_aux_metadata(self, header: Optional[dict] = None):
        for aux_decl in self.cfg["aux_channels"]:
            if "digital_in" in aux_decl:
                if header is not None:
                    assert (
                        len(header["board_dig_in_channels"]) > 0
                    ), "No digital inputs in header"
                self.dio_chs = np.array(aux_decl["digital_in"], dtype=np.intp)
                self.digital_in = True
                self.decode_teensy = bool(aux_decl.get("decode_teensy", False))
            if "analog_in" in aux_decl:
                if not (header is None):
                    h_anains = [
                        port["native_channel_name"]
                        for port in header["aux_input_channels"]
                    ]
                    for ch in aux_decl["analog_in"]:
                        possible_channel_names = [f"{prefix}-AUX{ch}" for prefix in ["A", "B", "C", "D"]]
                        assert any(name in h_anains for name in possible_channel_names), \
                            f"Aux analog input {ch} (tried prefixes A,B,C,D) was not found in the enabled ones:\n\t{h_anains}"
                self.aio_chs = np.array(aux_decl["analog_in"], dtype=np.intp) - 1
                self.analog_in = True

    def capture_dio(
        self,
        md: InputMetadata,
        digital_data: npt.NDArray[np.uint16],
        time: np.ndarray,
        start_offset: int,
    ):
        # Save digital in
        if digital_data.size > 0:
            items = dict()
            for ch in self.digital_chs:
                # Indices of lo -> hi
                # Convention is that any leading 1 is ignored.
                mask = np.diff((digital_data & (1 << ch))) == 1
                items[str(ch)] = TBatch(
                    time=time[(1 - start_offset) :][mask], overlap=0  # Change times
                )
            self.digital_batches[md.session].append(TMultiBatch(items=items))
            # optional: accumulate raw TTL for full-session UART decoding
            if self.decode_teensy:
                ch = int(self.digital_chs[0])
                raw_ttl = ((digital_data & (1 << ch)) > 0).astype(int)
                aligned_signal = raw_ttl[start_offset:]
                aligned_times = time
                self.ttl_signal_accum[md.session] = np.concatenate(
                    [self.ttl_signal_accum[md.session], aligned_signal]
                )
                self.ttl_time_accum[md.session] = np.concatenate(
                    [self.ttl_time_accum[md.session], aligned_times]
                )

    def capture_aio(
        self,
        md: InputMetadata,
        analog_data: np.ndarray,
        time: np.ndarray,
        start_offset: int,
        fs: int,
    ):
        # Save analog in
        if analog_data.size > 0:
            analog_time = time
            analog_data = analog_data[start_offset:, self.analog_chs]
            if self.analog_ds > 1:
                mask = time % self.analog_ds == 0
                analog_time = analog_time[mask]
                analog_data = analog_data[mask]
            assert analog_time.shape[0] == analog_data.shape[0]
            self.analog_batches[md.session].append(
                SBatch(
                    time=analog_time,
                    data=analog_data,
                    overlap=0,
                    fs=fs,  # Although analog data is downsampled, the timestamps reflect the original sampling rate.
                )
            )

    def initialize_aux_batches(self):
        self.digital_batches = [
            TMultiBatch(items={str(ch): TBatch.empty() for ch in self.digital_chs})
            for _ in self.digital_serializers
        ]
        self.analog_batches = [
            SBatch.empty(len(self.analog_chs), global_metadata["sampling_rate"])
            for _ in self.analog_serializers
        ]
        # No per-chunk UART batch writing; full-session decode in finalize

    def write_aux_batches(self):
        """
        Serialize auxiliary data in chunks

        NOTE: this follows the principle of everyone writes once, every call.
        i.e. initialize_aux_batches() / write_aux_batches() should be called in pairs,
        once per call during this stages's load() method
        """
        # Write out digital and analog batches
        for serializer, batch in zip(
            self.digital_serializers + self.analog_serializers,
            self.digital_batches + self.analog_batches,
        ):
            serializer.write(batch)

        # Full-session UART events are written in finalize; no per-chunk writes here

    def finalize(self):
        # Persist final aux data
        if not (self.digital_serializers is None):
            for s in self.digital_serializers:
                s.serialize()
                s.cleanup()
                logger.print(f"Wrote digital out file: {s.out_path}")
        if not (self.analog_serializers is None):
            for s in self.analog_serializers:
                s.serialize()
                s.cleanup()
                logger.print(f"Wrote analog out file: {s.out_path}")
        if self.decode_teensy:
            comm = MPI.COMM_WORLD
            fs = global_metadata["sampling_rate"]
            for session_idx, serializer in self.uart_serializers.items():
                local_signal = self.ttl_signal_accum.get(session_idx, np.array([], dtype=int))
                local_times  = self.ttl_time_accum.get(session_idx, np.array([], dtype=int))
                all_signals  = comm.gather(local_signal, root=0)
                all_times    = comm.gather(local_times, root=0)
                if comm.Get_rank() == 0:
                    if len(all_signals) > 0:
                        ts_signal = np.concatenate(all_signals)
                        ts_times  = np.concatenate(all_times)
                        order     = np.argsort(ts_times)
                        ts_signal = ts_signal[order]
                        ts_times  = ts_times[order]
                    else:
                        ts_signal = np.array([], dtype=int)
                        ts_times  = np.array([], dtype=int)
                    if ts_signal.size == 0:
                        events = {}
                    else:
                        decoded_bytes, rel_times = decode_uart_from_ttl(ts_signal, fs, self.baud_rate)
                        abs_times = ts_times[rel_times]
                        packets   = decode_serial_packets(decoded_bytes, abs_times)
                        events    = {}
                        cf_ms = 0.36  # constant offset in ms
                        for p in packets:
                            if not p.get("valid", True):
                                continue
                            wait_ms = p["waitTime"]
                            # subtract wait time plus constant factor (in samples)
                            offset = int(round(((wait_ms + cf_ms) / 1000.0) * fs))
                            event_time = p["detectionTime"] - offset
                            cid = str(p["channelID"])
                            events.setdefault(cid, []).append(event_time)
                else:
                    events = None
                # Broadcast decoded events to all ranks
                events = comm.bcast(events, root=0)
                # Assemble TMultiBatch of event times
                items = {cid: TBatch(time=np.array(times), overlap=0) for cid, times in events.items()}
                mm    = TMultiBatch(items=items)
                # Only the root rank writes the batch
                if comm.Get_rank() == 0:
                    serializer.write(mm)
                # All ranks participate in serialization and cleanup
                serializer.serialize()
                serializer.cleanup()
                if comm.Get_rank() == 0:
                    logger.print(f"Wrote UART decode events file: {serializer.out_path}")

    def cleanup(self):
        # Clean up temporary files, for testing purposes
        for s in (
            self.digital_serializers
            + self.analog_serializers
            + self.uart_serializers.values()
        ):
            s.cleanup()
