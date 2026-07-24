#!/usr/bin/env python3
"""Genera el pack de sonidos del juego (WAV 22050 Hz mono, síntesis pura).

Sin dependencias: onda + envolvente + mezcla con la stdlib. Los archivos son
cortos y livianos (disco al límite). Se re-generan con: python3 este-script.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

RATE = 22050
ROOT = Path(__file__).resolve().parents[2] / "assets" / "audio"
random.seed(42)  # sonidos reproducibles


def _env(i: int, n: int, attack: float = 0.01, release: float = 0.3) -> float:
    t = i / n
    a = min(1.0, t / attack) if attack > 0 else 1.0
    r = min(1.0, (1.0 - t) / release) if release > 0 else 1.0
    return a * r


def tone(freq: float, seconds: float, *, kind: str = "triangle", vol: float = 0.6,
         release: float = 0.35) -> list[float]:
    n = int(RATE * seconds)
    out = []
    for i in range(n):
        t = i / RATE
        ph = (t * freq) % 1.0
        if kind == "sine":
            v = math.sin(2 * math.pi * freq * t)
        elif kind == "square":
            v = 1.0 if ph < 0.5 else -1.0
        elif kind == "saw":
            v = 2.0 * ph - 1.0
        else:  # triangle
            v = 4.0 * abs(ph - 0.5) - 1.0
        # segundo armónico suave para que no suene a beep pelado
        v += 0.25 * math.sin(4 * math.pi * freq * t)
        out.append(v * vol * _env(i, n, release=release))
    return out


def noise(seconds: float, *, vol: float = 0.5, lowpass: float = 0.3,
          release: float = 0.5) -> list[float]:
    n = int(RATE * seconds)
    out, prev = [], 0.0
    for i in range(n):
        prev = prev * (1 - lowpass) + random.uniform(-1, 1) * lowpass
        out.append(prev * vol * _env(i, n, release=release))
    return out


def silence(seconds: float) -> list[float]:
    return [0.0] * int(RATE * seconds)


def concat(*parts: list[float]) -> list[float]:
    out: list[float] = []
    for p in parts:
        out.extend(p)
    return out


def mix(*parts: list[float]) -> list[float]:
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p):
            out[i] += v
    peak = max(1.0, max(abs(v) for v in out))
    return [v / peak for v in out]


def write(path: str, samples: list[float]) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(full), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32000)) for s in samples
        )
        w.writeframes(frames)
    print(f"  {path} ({full.stat().st_size // 1024} KB)")


def main() -> None:
    print("🎧 Generando pack de sonidos…")

    # dados: traqueteo de cubilete (ráfagas de ruido) + golpe al caer
    rattle = concat(*[
        mix(noise(0.05, vol=0.7, lowpass=0.6, release=0.9), silence(0.02))
        for _ in range(5)
    ])
    drop = mix(tone(90, 0.18, kind="sine", vol=0.9, release=0.9),
               noise(0.1, vol=0.4, lowpass=0.8, release=0.9))
    write("dice/sound-dice-roll-001.wav", concat(rattle, drop))

    # combate: choque metálico + tambor grave
    clash = mix(
        noise(0.25, vol=0.8, lowpass=0.9, release=0.7),
        tone(140, 0.3, kind="saw", vol=0.5, release=0.8),
        tone(70, 0.35, kind="sine", vol=0.9, release=0.6),
    )
    write("battles/sound-battle-clash-001.wav", clash)

    # conquista: arpegio mayor ascendente triunfal
    win = concat(
        tone(262, 0.14, vol=0.5), tone(330, 0.14, vol=0.55),
        tone(392, 0.14, vol=0.6), tone(523, 0.4, vol=0.7, release=0.5),
    )
    write("battles/sound-battle-win-001.wav", win)

    # perdiste un país: dos notas descendentes con peso
    lose = concat(tone(330, 0.2, kind="sine", vol=0.6),
                  tone(220, 0.45, kind="sine", vol=0.7, release=0.5))
    write("battles/sound-battle-lose-001.wav", lose)

    # eliminación: caída cromática lúgubre
    elim = concat(
        tone(392, 0.22, kind="sine", vol=0.6), tone(311, 0.22, kind="sine", vol=0.65),
        tone(233, 0.6, kind="sine", vol=0.75, release=0.55),
    )
    write("alerts/sound-player-eliminated-001.wav", elim)

    # traición: puñalada dramática (segunda menor repetida)
    stab = mix(tone(466, 0.16, kind="saw", vol=0.7, release=0.9),
               tone(494, 0.16, kind="saw", vol=0.7, release=0.9))
    write("alerts/sound-alert-traitor-001.wav",
          concat(stab, silence(0.07), stab, silence(0.05),
                 tone(155, 0.5, kind="saw", vol=0.6, release=0.5)))

    # victoria: fanfarria
    fan = concat(
        tone(392, 0.16, vol=0.6), tone(392, 0.12, vol=0.6), tone(392, 0.12, vol=0.6),
        tone(523, 0.5, vol=0.75, release=0.4), silence(0.05),
        mix(tone(523, 0.7, vol=0.5, release=0.5), tone(659, 0.7, vol=0.5, release=0.5),
            tone(784, 0.7, vol=0.5, release=0.5)),
    )
    write("victory/sound-victory-fanfare-001.wav", fan)

    # derrota propia (te eliminaron): trombón triste
    sad = concat(tone(294, 0.3, kind="saw", vol=0.5), tone(277, 0.3, kind="saw", vol=0.5),
                 tone(262, 0.3, kind="saw", vol=0.5), tone(196, 0.8, kind="saw", vol=0.6, release=0.6))
    write("victory/sound-defeat-sad-001.wav", sad)

    # click UI: tick corto
    write("ui/sound-ui-click-001.wav", tone(1200, 0.03, kind="sine", vol=0.4, release=0.9))

    # notificación (chat/pacto propuesto): ping doble
    write("ui/sound-notify-001.wav",
          concat(tone(880, 0.09, kind="sine", vol=0.45), silence(0.04),
                 tone(1175, 0.16, kind="sine", vol=0.5, release=0.6)))

    # refuerzo colocado: pop suave
    write("ui/sound-reinforce-001.wav",
          mix(tone(520, 0.09, kind="sine", vol=0.5, release=0.8),
              tone(780, 0.07, kind="sine", vol=0.3, release=0.9)))

    print("✅ pack completo en assets/audio/")


if __name__ == "__main__":
    main()
