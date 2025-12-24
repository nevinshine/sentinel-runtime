import pandas as pd
import numpy as np
import torch


class SentinelBridge:
    """
    Kernel → DWN Bridge

    Pipeline:
    1. Syscall stream (pid, syscall_nr, arg_class)
    2. Sliding windows
    3. Absolute temporal bucketing
    4. Joint-ID histogram (syscall × bucket + arg_class)
    5. Thermometer encoding
    """

    def __init__(
        self,
        window_size=100,
        max_syscall=335,
        thermometer_resolution=8,
        num_buckets=4,
    ):
        self.window_size = window_size
        self.max_syscall = max_syscall
        self.resolution = thermometer_resolution
        self.num_buckets = num_buckets

        # Joint ID space: (syscall_id * num_buckets) + arg_class
        self.num_bins = (self.max_syscall + 1) * self.num_buckets

        # Final binary dimensionality
        self.total_input_bits = self.num_bins * self.resolution * self.num_buckets

    # -------------------------------------------------------------

    def encode_thermometer(self, histogram: np.ndarray) -> np.ndarray:
        """
        Fixed-length thermometer encoding.

        histogram shape: [num_bins]
        output shape:    [num_bins * resolution]
        """
        histogram = np.clip(histogram, 0, self.resolution).astype(np.int64)

        levels = np.arange(self.resolution).reshape(1, -1)
        expanded = histogram.reshape(-1, 1)

        binary = (levels < expanded).astype(np.float32)
        return binary.flatten()

    # -------------------------------------------------------------

    def process_log(self, file_path):
        print(f"[BRIDGE] Processing {file_path}...")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"⚠️ Error reading file: {e}")
            return None, None

        if df.empty:
            print("⚠️ Empty trace file")
            return None, None

        required = {"pid", "syscall_nr", "arg_class"}
        if not required.issubset(df.columns):
            raise RuntimeError(f"Missing required columns: {required}")

        samples = []
        labels = []

        grouped = df.groupby("pid")

        for pid, proc in grouped:
            if len(proc) < self.window_size:
                continue

            step = self.window_size // 2
            bucket_size = self.window_size // self.num_buckets

            # Sliding window over full process trace
            for start in range(0, len(proc) - self.window_size + 1, step):

                bucket_bits = []

                # --- ABSOLUTE TEMPORAL BUCKETING ---
                for b in range(self.num_buckets):
                    b_start = start + b * bucket_size
                    b_end = b_start + bucket_size

                    # Slice directly from full trace
                    sub = proc.iloc[b_start:b_end]

                    # STRUCTURAL SAFETY: partial bucket → zero histogram
                    if len(sub) < bucket_size:
                        hist = np.zeros(self.num_bins, dtype=np.int64)
                    else:
                        s_nr = sub["syscall_nr"].astype(np.int64).values
                        a_cls = sub["arg_class"].astype(np.int64).values

                        # Joint categorical ID
                        joint_ids = s_nr * self.num_buckets + a_cls

                        # VALUE SAFETY: clamp to fixed categorical space
                        joint_ids = np.clip(
                            joint_ids,
                            0,
                            self.num_bins - 1
                        )

                        hist = np.bincount(
                            joint_ids,
                            minlength=self.num_bins
                        )

                    # Encode each bucket independently
                    bucket_bits.append(self.encode_thermometer(hist))

                # Concatenate fixed-size bucket encodings
                binary_vec = np.concatenate(bucket_bits)

                samples.append(binary_vec)
                labels.append(0)  # normal-only training

        if not samples:
            print("⚠️ No valid windows generated")
            return None, None

        # ---------- FINAL SAFETY CHECK ----------
        lengths = {len(v) for v in samples}
        print(f"Unique sample lengths: {lengths}")

        if len(lengths) != 1:
            raise RuntimeError(f"Inconsistent sample lengths: {lengths}")

        x = torch.tensor(np.array(samples), dtype=torch.float32)
        y = torch.tensor(labels, dtype=torch.long)

        print(
            f"[BRIDGE] Generated {x.shape[0]} samples. "
            f"Input Dim: {x.shape[1]} bits."
        )

        return x, y
