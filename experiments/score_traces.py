import sys
import os

# Add project root to PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import torch
import numpy as np


from models.dwn_classifier import DWNClassifier
from data.sentinel_bridge import SentinelBridge

# -------------------------------
# CONFIG
# -------------------------------
MODEL_PATH = "sentinel_model.pt" # change if needed
LOG_FILE = "sentinel_log.csv"

WINDOW_SIZE = 100
THERMO_RES = 8
NUM_BUCKETS = 4
TUPLE_SIZE = 4

# -------------------------------
# LOAD DATA
# -------------------------------
bridge = SentinelBridge(
    window_size=WINDOW_SIZE,
    thermometer_resolution=THERMO_RES,
    num_buckets=NUM_BUCKETS
)

x, _ = bridge.process_log(LOG_FILE)

if x is None:
    raise RuntimeError("No samples generated from syscall log.")

print(f"[+] Loaded {x.shape[0]} syscall windows")

# -------------------------------
# LOAD MODEL
# -------------------------------
num_inputs = x.shape[1]

model = DWNClassifier(
    num_inputs=num_inputs,
    tuple_size=TUPLE_SIZE,
    num_classes=2
)

model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

print("[+] Model loaded")

# -------------------------------
# SCORE WINDOWS
# -------------------------------
with torch.no_grad():
    scores = model(x)  # [Batch, 2]

normal_scores = scores[:, 0]
attack_scores = scores[:, 1]

anomaly_scores = normal_scores - attack_scores

# -------------------------------
# ANALYSIS
# -------------------------------
def summarize(name, tensor):
    arr = tensor.numpy()
    print(f"\n{name}")
    print(f"  mean: {arr.mean():.4f}")
    print(f"  std : {arr.std():.4f}")
    print(f"  min : {arr.min():.4f}")
    print(f"  max : {arr.max():.4f}")

summarize("Normal Discriminator Response", normal_scores)
summarize("Attack Discriminator Response", attack_scores)
summarize("Anomaly Score (Normal - Attack)", anomaly_scores)
