"""Compare the base and edited model weights and write results/diff.md.

Reads two safetensors files, fails hard on any structural mismatch, and
reports which tensors differ, how many weights changed and by how much.
No model is run: this only reads stored numbers.

Usage: python -I src/diff_weights.py BASE.safetensors EDITED.safetensors OUT.md
"""
import sys
from pathlib import Path

import torch
from safetensors import safe_open


def main(base_path: str, edited_path: str, out_path: str) -> None:
    lines: list[str] = []
    with safe_open(base_path, "pt") as base, safe_open(edited_path, "pt") as edited:
        base_keys, edited_keys = set(base.keys()), set(edited.keys())
        if base_keys != edited_keys:
            raise SystemExit(
                f"tensor names differ: only in base {sorted(base_keys - edited_keys)[:5]}, "
                f"only in edited {sorted(edited_keys - base_keys)[:5]}"
            )
        total_weights = 0
        dtypes: dict[str, int] = {}
        changed = []
        for name in sorted(base_keys):
            a, b = base.get_tensor(name), edited.get_tensor(name)
            if a.shape != b.shape or a.dtype != b.dtype:
                raise SystemExit(f"{name}: shape or dtype differs: {a.shape} {a.dtype} vs {b.shape} {b.dtype}")
            total_weights += a.numel()
            dtypes[str(a.dtype)] = dtypes.get(str(a.dtype), 0) + a.numel()
            if torch.equal(a, b):
                continue
            a32, b32 = a.float(), b.float()
            delta = b32 - a32
            mask = delta != 0
            cols = mask.any(dim=0).nonzero().flatten().tolist() if a.dim() == 2 else []
            rows = mask.any(dim=1).nonzero().flatten().tolist() if a.dim() == 2 else []
            changed.append(
                {
                    "name": name,
                    "shape": tuple(a.shape),
                    "dtype": str(a.dtype),
                    "n_changed": int(mask.sum()),
                    "cols": cols,
                    "rows": rows,
                    "rel_norm": float(delta.norm() / a32.norm()),
                    "max_abs_delta": float(delta.abs().max()),
                    "mean_abs_delta_changed": float(delta[mask].abs().mean()),
                    "mean_abs_base_changed": float(a32[mask].abs().mean()),
                    "mean_abs_base_all": float(a32.abs().mean()),
                }
            )

    n_changed = sum(c["n_changed"] for c in changed)
    lines += [
        "# Weight diff: base model vs edited model",
        "",
        "Produced by `src/diff_weights.py`. Only stored weights were read; no model was run.",
        "",
        f"- Base file: `{base_path}`",
        f"- Edited file: `{edited_path}`",
        f"- Tensors compared: {len(base_keys)}, all with matching names, shapes and dtypes",
        f"- Total weights: {total_weights:,}",
        f"- Stored precision: {', '.join(f'{k} ({v:,} weights)' for k, v in dtypes.items())}",
        f"- Tensors that differ: {len(changed)}",
        f"- Weights that differ: {n_changed:,} ({100 * n_changed / total_weights:.4f}% of all weights)",
        "",
        "## Tensors that differ",
        "",
    ]
    for c in changed:
        lines += [
            f"### `{c['name']}`",
            "",
            f"- Shape: {c['shape']}, dtype {c['dtype']}",
            f"- Weights changed: {c['n_changed']:,}",
            f"- Columns touched: {len(c['cols'])} of {c['shape'][1] if len(c['shape']) == 2 else 'n/a'}"
            f" (indices {c['cols'][:8]}{'...' if len(c['cols']) > 8 else ''})",
            f"- Rows touched: {len(c['rows'])} of {c['shape'][0] if len(c['shape']) == 2 else 'n/a'}",
            f"- Size of change relative to the whole tensor (norm of change / norm of tensor): {100 * c['rel_norm']:.2f}%",
            f"- Largest single change: {c['max_abs_delta']:.6f}",
            f"- Mean absolute change, changed weights only: {c['mean_abs_delta_changed']:.6f}",
            f"- Mean absolute base value, changed weights only: {c['mean_abs_base_changed']:.6f}",
            f"- Mean absolute base value, whole tensor: {c['mean_abs_base_all']:.6f}",
            "",
        ]
    Path(out_path).write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
