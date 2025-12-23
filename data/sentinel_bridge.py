import pandas as pd
import numpy as np
import torch


class SentinelBridge:
    """
    Interface between Linux Kernel syscalls and Weightless Neural Networks.

    Pipeline:
    1. Syscall stream (e.g. [59, 12, 1, ...])
    2. Sliding window over syscalls
    3. Temporal bucketing (coarse ordering)
    4. Histogram per bucket
    5. Thermometer encoding -> binary vector
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

        # Total input dimension after bucketing
        self.total_input_bits = (
            (self.max_syscall + 1)
            * self.resolution
            * self.num_buckets
        )

    def encode_thermometer(self, histogram):
        """
        Converts integer counts into thermometer encoding.

        Example (resolution=4):
        count = 2 -> [1, 1, 0, 0]
        count = 0 -> [0, 0, 0, 0]
        """
        counts = np.clip(histogram, 0, self.resolution)

        range_matrix = np.arange(self.resolution).reshape(1, -1)
        counts_matrix = counts.reshape(-1, 1)

        binary_matrix = (range_matrix < counts_matrix).astype(np.float32)
        return binary_matrix.flatten()

    def process_log(self, file_path):
        """
        Reads sentinel_log.csv and returns:
        - x_tensor: binary feature matrix
        - y_tensor: labels (currently all 0 = normal)
        """
        print(f"🔄 BRIDGE: Processing {file_path}...")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"❌ ERROR: Could not read log: {e}")
            return None, None

        if df.empty:
            print("⚠️ WARNING: Log is empty.")
            return None, None

        grouped = df.groupby("pid")["syscall_nr"].apply(list)

        binary_samples = []
        labels = []

        for pid, trace in grouped.items():
            if len(trace) < self.window_size:
                continue

            step = self.window_size // 2  # 50% overlap
            bucket_size = self.window_size // self.num_buckets

            for i in range(0, len(trace) - self.window_size, step):
                window = trace[i : i + self.window_size]

                bucket_features = []

                for b in range(self.num_buckets):
                    start = b * bucket_size
                    end = start + bucket_size
                    bucket = window[start:end]

                    hist = np.bincount(
                        bucket,
                        minlength=self.max_syscall + 1,
                    )

                    if len(hist) > self.max_syscall + 1:
                        hist = hist[: self.max_syscall + 1]

                    binary = self.encode_thermometer(hist)
                    bucket_features.append(binary)

                # Concatenate buckets (temporal order preserved)
                binary_vec = np.concatenate(bucket_features)
                binary_samples.append(binary_vec)
                labels.append(0)  # normal

        if not binary_samples:
            print("⚠️ WARNING: No valid windows found (traces too short).")
            return None, None

        x_tensor = torch.tensor(
            np.array(binary_samples),
            dtype=torch.float32,
        )
        y_tensor = torch.tensor(
            np.array(labels),
            dtype=torch.long,
        )

        print(
            f"✅ BRIDGE: Generated {x_tensor.shape[0]} samples. "
            f"Input Dim: {x_tensor.shape[1]} bits."
        )

        return x_tensor, y_tensor
