from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    real_data_gate: str

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        mode = os.getenv("HIVEMIND_MODE", "fixture").strip().lower()
        gate = os.getenv("REAL_DATA_GATE", "closed").strip().lower()
        if mode not in {"fixture", "paper"}:
            raise ValueError(f"unsupported mode: {mode}")
        if gate != "closed":
            raise ValueError("REAL_DATA_GATE must remain closed")
        return cls(mode=mode, real_data_gate=gate)
