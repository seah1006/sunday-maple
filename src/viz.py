from __future__ import annotations

from pathlib import Path
import warnings

import matplotlib.pyplot as plt


def set_korean_font() -> None:
    try:
        plt.rcParams["font.family"] = "Malgun Gothic"
        plt.rcParams["axes.unicode_minus"] = False
    except Exception as exc:
        warnings.warn(f"한글 폰트 설정을 적용하지 못했습니다: {exc}", stacklevel=2)


def save_fig(fig, name: str, outdir: str = "outputs/figures") -> str:
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)
    path = out_path / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return str(path)
