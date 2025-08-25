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
        self.has_teensy_decode = False

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

        # Store configurations for each auxiliary channel type
        self.digital_configs = []  # List of digital input configurations
        self.analog_configs = []   # List of analog input configurations
        
        # Create serializers for auxiliary data as needed
        self.digital_serializers = []
        self.analog_serializers = []
        self.uart_serializers = {}  # Dictionary keyed by (config_idx, session_idx)
        
        for config_idx, aux_decl in enumerate(self.cfg["aux_channels"]):

            if "digital_in" in aux_decl:
                assert (
                    self.cfg["batch_overlap"] == 0
                ), "batch_overlap must be zero for aux"
                
                # Store this digital configuration
                digital_config = {
                    'channels': np.array(aux_decl["digital_in"], dtype=np.intp),
                    'name': aux_decl["name"],
                    'decode_teensy': bool(aux_decl.get("decode_teensy", False)),
                    'baud_rate': aux_decl.get("baud_rate", 3000),
                    'config_idx': config_idx
                }
                
                if digital_config['decode_teensy']:
                    assert (
                        len(digital_config['channels']) == 1
                    ), "decode_teensy supports exactly one digital pin"
                    self.has_teensy_decode = True
                
                self.digital_configs.append(digital_config)
                self.digital_in = True

                # Create serializers per session for this configuration
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
                    if digital_config['decode_teensy']:
                        base, ext = os.path.splitext(aux_decl["name"])
                        uart_name = f"{base}_decoded{ext}"
                        # use TMultiBatchSerializer to write event times per channel
                        ts = H5TMultiBatchSerializer(
                            full_check=global_state.debug,
                            rank=self.rank,
                            n_workers=self.n_workers,
                        )
                        ts.initialize(os.path.join(output_path, f"session_{i}_{uart_name}"))
                        self.uart_serializers[(config_idx, i)] = ts

            if "analog_in" in aux_decl:
                assert (
                    self.cfg["batch_overlap"] == 0
                ), "nonzero batch_overlap not supported with aux channel persistence, for now"
                
                # Store this analog configuration  
                analog_config = {
                    'channels': np.array(aux_decl["analog_in"], dtype=np.intp) - 1,  # Analog is 1-indexed
                    'name': aux_decl["name"],
                    'downsample': aux_decl["downsample"],
                    'config_idx': config_idx
                }
                
                self.analog_configs.append(analog_config)
                self.analog_in = True
                
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

        # Initialize full-session TTL buffers if any UART decode is enabled
        if self.has_teensy_decode:
            # prepare raw TTL signal and time accumulators per (config_idx, session)
            self.ttl_signal_accum = {}
            self.ttl_time_accum = {}
            for (config_idx, session_idx) in self.uart_serializers.keys():
                self.ttl_signal_accum[(config_idx, session_idx)] = np.array([], dtype=int)
                self.ttl_time_accum[(config_idx, session_idx)] = np.array([], dtype=int)

    def validate_aux_metadata(self, header: Optional[dict] = None):
        for aux_decl in self.cfg["aux_channels"]:
            if "digital_in" in aux_decl:
                if header is not None:
                    assert (
                        len(header["board_dig_in_channels"]) > 0
                    ), "No digital inputs in header"
                # Note: removed global variable assignments since we now use config objects
                self.digital_in = True
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
                self.analog_in = True

    def capture_dio(
        self,
        md: InputMetadata,
        digital_data: npt.NDArray[np.uint16],
        time: np.ndarray,
        start_offset: int,
    ):
        # Save digital in for each configuration
        if digital_data.size > 0:
            for config_idx, digital_config in enumerate(self.digital_configs):
                items = dict()
                
                for ch in digital_config['channels']:
                    # Map requested channel number to actual native_order from header
                    native_ch = None
                    if hasattr(md, 'header') and 'board_dig_in_channels' in md.header:
                        for header_ch in md.header['board_dig_in_channels']:
                            if header_ch['native_order'] == ch:
                                native_ch = ch
                                break
                    
                    # If no mapping found, use the requested channel number directly
                    if native_ch is None:
                        native_ch = ch
                    
                    # Indices of lo -> hi
                    # Convention is that any leading 1 is ignored.
                    # Build boolean signal then detect 0->1 transitions across chunk boundary
                    sig = (digital_data & (1 << native_ch)) > 0
                    mask = (~sig[:-1]) & (sig[1:])
                    
                    items[str(ch)] = TBatch(
                        time=time[(1 - start_offset) :][mask], overlap=0  # Change times
                    )
                
                # Get the corresponding serializer index
                serializer_idx = config_idx
                self.digital_batches[serializer_idx].append(TMultiBatch(items=items))
                
                # optional: accumulate raw TTL for full-session UART decoding
                if digital_config['decode_teensy']:
                    ch = int(digital_config['channels'][0])
                    # Use the same native_order mapping for UART decoding
                    native_ch = None
                    if hasattr(md, 'header') and 'board_dig_in_channels' in md.header:
                        for header_ch in md.header['board_dig_in_channels']:
                            if header_ch['native_order'] == ch:
                                native_ch = ch
                                break
                    
                    if native_ch is None:
                        native_ch = ch
                    
                    raw_ttl = ((digital_data & (1 << native_ch)) > 0).astype(int)
                    aligned_signal = raw_ttl[start_offset:]
                    aligned_times = time
                    
                    key = (config_idx, md.session)
                    self.ttl_signal_accum[key] = np.concatenate(
                        [self.ttl_signal_accum[key], aligned_signal]
                    )
                    self.ttl_time_accum[key] = np.concatenate(
                        [self.ttl_time_accum[key], aligned_times]
                    )
        else:
            pass

    def capture_aio(
        self,
        md: InputMetadata,
        analog_data: np.ndarray,
        time: np.ndarray,
        start_offset: int,
        fs: int,
    ):
        # Save analog in for each configuration
        if analog_data.size > 0:
            for config_idx, analog_config in enumerate(self.analog_configs):
                analog_time = time
                config_analog_data = analog_data[start_offset:, analog_config['channels']]
                if analog_config['downsample'] > 1:
                    mask = time % analog_config['downsample'] == 0
                    analog_time = analog_time[mask]
                    config_analog_data = config_analog_data[mask]
                assert analog_time.shape[0] == config_analog_data.shape[0]
                
                # Get the corresponding serializer index (offset by number of digital configs)
                serializer_idx = len(self.digital_configs) + config_idx
                self.analog_batches[config_idx].append(
                    SBatch(
                        time=analog_time,
                        data=config_analog_data,
                        overlap=0,
                        fs=fs,  # Although analog data is downsampled, the timestamps reflect the original sampling rate.
                    )
                )

    def initialize_aux_batches(self):
        # Initialize batches for each digital configuration
        self.digital_batches = []
        for digital_config in self.digital_configs:
            batch = TMultiBatch(items={str(ch): TBatch.empty() for ch in digital_config['channels']})
            self.digital_batches.append(batch)
        
        # Initialize batches for each analog configuration  
        self.analog_batches = []
        for analog_config in self.analog_configs:
            batch = SBatch.empty(len(analog_config['channels']), global_metadata["sampling_rate"])
            self.analog_batches.append(batch)
        
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
        if self.digital_serializers:
            for s in self.digital_serializers:
                s.serialize()
                s.cleanup()
                logger.print(f"Wrote digital out file: {s.out_path}")
        if self.analog_serializers:
            for s in self.analog_serializers:
                s.serialize()
                s.cleanup()
                logger.print(f"Wrote analog out file: {s.out_path}")
        
        if self.has_teensy_decode:
            comm = MPI.COMM_WORLD
            fs = global_metadata["sampling_rate"]
            
            for (config_idx, session_idx), serializer in self.uart_serializers.items():
                # Get the configuration for this UART serializer
                digital_config = self.digital_configs[config_idx]
                
                local_signal = self.ttl_signal_accum.get((config_idx, session_idx), np.array([], dtype=int))
                local_times  = self.ttl_time_accum.get((config_idx, session_idx), np.array([], dtype=int))
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
                        decoded_bytes, rel_times = decode_uart_from_ttl(ts_signal, fs, digital_config['baud_rate'])
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
            + list(self.uart_serializers.values())
        ):
            s.cleanup()
