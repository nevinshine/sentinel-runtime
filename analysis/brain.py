# analysis/brain.py
import random

class WiSARD:
    """
    A lightweight Weightless Neural Network for Runtime Security.
    (Simplified for Real-Time Demonstration)
    """
    def __init__(self):
        self.memory = {} # The "RAM" of the AI
        self.is_trained = False
        
    def encode(self, syscall_name):
        """
        Converts a syscall string (e.g., "mkdir") into a bit pattern.
        In a full version, this uses Thermometer Encoding.
        Here, we use a simple hash for speed.
        """
        # Simple hash to simulate binary features
        val = sum(bytearray(syscall_name, 'utf-8'))
        return bin(val)[2:].zfill(16) # 16-bit binary string

    def train(self, syscall_name):
        """
        Teach the AI that this syscall is 'Normal'.
        """
        pattern = self.encode(syscall_name)
        self.memory[pattern] = True
        self.is_trained = True
        print(f"[BRAIN] 🎓 Learned pattern for: {syscall_name}")

    def predict(self, syscall_name):
        """
        Check if we have seen this pattern before.
        """
        if not self.is_trained:
            return "UNCERTAIN (Untrained)"
            
        pattern = self.encode(syscall_name)
        if pattern in self.memory:
            return "✅ BENIGN"
        else:
            return "🚨 ANOMALY"
