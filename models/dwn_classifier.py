import torch
import torch.nn as nn
from models.efd_lut import EFDLUT


class DWNClassifier(nn.Module):
    def __init__(self, num_inputs, num_classes=2):
        super().__init__()
        self.discriminators = nn.ModuleList([
            EFDLUT(num_inputs)
            for _ in range(num_classes)
        ])

    def forward(self, x):
        responses = []
        for disc in self.discriminators:
            responses.append(disc(x))
        return torch.stack(responses, dim=1)
