import torch
from data.sentinel_bridge import SentinelBridge
from models.dwn_classifier import DWNClassifier

MODEL_PATH = "sentinel_model.pt"
LOG_FILE = "sentinel_log.csv"

WINDOW_SIZE = 100
RESOLUTION = 8

def main():
    print("[*] Loading Sentinel Bridge...")
    bridge = SentinelBridge(
        window_size=WINDOW_SIZE,
        thermometer_resolution=RESOLUTION
    )

    x, _ = bridge.process_log(LOG_FILE)
    if x is None:
        print("No data to score.")
        return

    print("[*] Loading trained DWN model...")
    model = DWNClassifier(num_inputs=x.shape[1])
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()

    with torch.no_grad():
        scores = model(x)
        normal = scores[:, 0]
        attack = scores[:, 1]
        anomaly = normal - attack

    print("\n=== ANOMALY SCORE DISTRIBUTION ===")
    print(f"Samples : {len(anomaly)}")
    print(f"Mean    : {anomaly.mean():.3f}")
    print(f"Std     : {anomaly.std():.3f}")
    print(f"Min     : {anomaly.min():.3f}")
    print(f"Max     : {anomaly.max():.3f}")

if __name__ == "__main__":
    main()
