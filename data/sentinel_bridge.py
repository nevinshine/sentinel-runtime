import numpy as np
import pandas as pd
import torch


class SentinelBridge:
    def __init__(
        self,
        window_size=100,
        max_syscall=335,
        num_buckets=4,
        resolution=8
    ):
        self.window_size = window_size
        self.max_syscall = max_syscall
        self.num_buckets = num_buckets
        self.resolution = resolution

        # joint bins: syscall × bucket
        self.num_bins = (self.max_syscall + 1) * self.num_buckets
        self.total_input_bits = self.num_bins * self.resolution

    def encode_thermometer(self, histogram):
        """
        Convert integer histogram to thermometer encoding.
        """
        counts = np.clip(histogram, 0, self.resolution)
        r = np.arange(self.resolution).reshape(1, -1)
        c = counts.reshape(-1, 1)
        return (r < c).astype(np.float32).flatten()

    def process_log(self, file_path):
        """
        Ingest sentinel_log.csv and return:
        X : torch.FloatTensor [N, D]
        y : torch.LongTensor  [N]  (normal-only → zeros)
        """
        print(f"[BRIDGE] Processing {file_path}...")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read trace file: {e}")

        if df.empty:
            raise RuntimeError("Trace file is empty")

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

            for start in range(0, len(proc) - self.window_size + 1, step):
                bucket_bits = []

                for b in range(self.num_buckets):
                    b_start = start + b * bucket_size
                    b_end = b_start + bucket_size

                    sub = proc.iloc[b_start:b_end]

                    if len(sub) < bucket_size:
                        hist = np.zeros(self.num_bins, dtype=np.int64)
                    else:
                        s_nr = sub["syscall_nr"].astype(np.int64).values
                        a_cls = sub["arg_class"].astype(np.int64).values

                        joint_ids = s_nr * self.num_buckets + a_cls
                        joint_ids = np.clip(joint_ids, 0, self.num_bins - 1)

                        hist = np.bincount(joint_ids, minlength=self.num_bins)

                    bucket_bits.append(self.encode_thermometer(hist))

                binary_vec = np.concatenate(bucket_bits)
                samples.append(binary_vec)
                labels.append(0)

        if not samples:
            raise RuntimeError("No valid windows generated")

        X = torch.tensor(np.array(samples), dtype=torch.float32)
        y = torch.tensor(labels, dtype=torch.long)

        print(f"[BRIDGE] Generated {X.shape[0]} samples | Dim={X.shape[1]}")
        return X, y
