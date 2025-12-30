import torch
import torch.nn as nn


class EFDLUT(nn.Module):
    """
    Weightless Lookup Table (RAM node bank)
    """

    def __init__(self, num_inputs, tuple_size=4):
        super().__init__()

        self.tuple_size = tuple_size
        self.num_luts = num_inputs // tuple_size
        self.lut_entries = 1 << tuple_size  # 2^tuple_size

        # Learnable LUT weights
        self.lut_weights = nn.Parameter(
            torch.empty(self.num_luts, self.lut_entries)
        )
        nn.init.uniform_(self.lut_weights, -0.1, 0.1)

        # Precompute bit powers for address calculation
        self.register_buffer(
            "powers_of_two",
            2 ** torch.arange(tuple_size)
        )

    def forward(self, x):
        """
        x: [Batch, Num_Inputs] binary tensor
        returns: [Batch] response score
        """

        batch_size = x.shape[0]

        # Truncate to full tuples
        limit = self.num_luts * self.tuple_size
        x = x[:, :limit]

        # Reshape to [Batch, Num_LUTs, Tuple_Size]
        x = x.view(batch_size, self.num_luts, self.tuple_size)

        # Compute LUT addresses
        # address = sum(bit * 2^k)
        addresses = (x * self.powers_of_two).sum(dim=-1).long()

        # Lookup LUT values
        # Output: [Batch, Num_LUTs]
        values = self.lut_weights.gather(1, addresses)

        # Sum across LUTs → final response
        return values.sum(dim=1)
