"""Pickle-compat shim — kept after the coordframe graduation.

The 730-LOC `CoordFrame` / `PointCloud` / `Quat` implementation that
lived here through 2026-05-14 was graduated to the standalone
``coordframe`` package (PyPI ``coordframe``, version >=1.0.0). This
namespace now re-exports everything from ``coordframe`` so that:

1. Existing call sites (``from bpn import trf``) keep working
   unchanged until the per-feature retirement pass flips them to
   ``import coordframe``.
2. Any future on-disk pickles that encode ``bpn.trf.CoordFrame`` /
   ``bpn.trf.PointCloud`` / ``bpn.trf.Quat`` as the class
   ``__module__`` continue to load.

As of 2026-05-14 the ``C:/data/_cache/`` scan was clean (0 hits for
``CoordFrame|PointCloud`` and ``bpn.trf``), so this shim is
preemptive rather than load-bearing for the cache. See
``pn-specs/plans/20260514_coordframe_extraction.md`` and the
``feedback_pickle_compat_graduation`` memory.
"""
from coordframe import *  # noqa: F401, F403
