"""Draw a ticket's barcode as a PNG, on the device, without network (S015)."""

from __future__ import annotations

import io
from collections.abc import Sequence

import aztec_code_generator
import barcode as python_barcode
import pdf417gen
import segno
from barcode.writer import ImageWriter
from PIL import Image

from escale_core.tickets import Barcode

MODULE_PX = 8
"""Size of one module (dot) of a 2D code, in pixels."""


def matrix_png(rows: Sequence[Sequence[int]], quiet: int, scale: int = MODULE_PX) -> bytes:
    """A black-on-white PNG of a module matrix, with a quiet zone of ``quiet`` modules."""
    size_y, size_x = len(rows), len(rows[0])
    image = Image.new("1", ((size_x + 2 * quiet) * scale, (size_y + 2 * quiet) * scale), 1)
    pixels = image.load()
    assert pixels is not None
    for y, row in enumerate(rows):
        for x, dark in enumerate(row):
            if dark:
                for dy in range(scale):
                    for dx in range(scale):
                        pixels[(x + quiet) * scale + dx, (y + quiet) * scale + dy] = 0
    return _png(image)


def _png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def png(code: Barcode) -> bytes | None:
    """The barcode as a PNG; ``None`` for a kind Escale cannot draw (Data Matrix)."""
    if code.kind == "qr":
        return matrix_png(segno.make(code.data, micro=False, error="m").matrix, quiet=4)
    if code.kind == "aztec":
        return matrix_png(aztec_code_generator.AztecCode(code.data).matrix, quiet=2)
    if code.kind == "pdf417":
        codes = pdf417gen.encode(code.data, columns=6, security_level=2)
        return _png(pdf417gen.render_image(codes, scale=3, ratio=3, padding=12))
    if code.kind == "code128":
        drawn = python_barcode.get(
            "code128", code.data.decode("latin-1"), writer=ImageWriter()
        ).render({"write_text": False, "module_height": 18.0, "quiet_zone": 4.0})
        return _png(drawn)
    return None
