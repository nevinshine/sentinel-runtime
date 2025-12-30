import argparse
import numpy as np
import torch

from data.sentinel_bridge import SentinelBridge
from models.dwn_classifier import DWNClassifier

def main(mode):
    bridge = SentinelBridge()
    syscalls = bridge.load_log("sentinel_log.csv")
    x = bridge.build_windows(syscalls)

    if len(x) == 0:
        raise RuntimeError("No samples generated from syscall log.")

    model = DWNClassifier(x.shape[1])
    model.eval()

    with torch.no_grad():
        scores = model(torch.from_numpy(x))

    out = f"experiments/scores_{mode}.npy"
    np.save(out, scores.numpy())
    print(f"[+] Saved {out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["normal", "abnormal"])
    args = parser.parse_args()
    main(args.mode)
