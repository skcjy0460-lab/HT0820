# -*- coding: utf-8 -*-
"""
reportlab 기반 PDF 빌더.
Streamlit Community Cloud에는 LibreOffice가 없어 pptx->pdf 변환이 불가능하므로,
포트폴리오 PDF는 reportlab으로 "직접" 그린다 (레이아웃은 ppt_utils와 톤을 맞춤).

한글 폰트: reportlab 기본 폰트는 한글을 지원하지 않으므로 나눔고딕(TTF)을
런타임에 폰트가 있으면 등록하고, 없으면 시스템에 내장된 CID 폰트로 폴백한다.
"""

from __future__ import annotations
import io
import os

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

PAGE_W, PAGE_H = landscape((13.333 * inch, 7.5 * inch))

_FONT_NAME = "HYSMyeongJo-Medium"  # reportlab 내장 CID 한글 폰트 (별도 파일 불필요)


def _ensure_font():
    """내장 CID 한글 폰트를 등록한다. (파일 설치 없이 바로 사용 가능)"""
    if _FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT_NAME))
    return _FONT_NAME


class PortfolioPDFBuilder:
    def __init__(self, primary_hex: str = "0F2A47", secondary_hex: str = "C9A24B"):
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=(PAGE_W, PAGE_H))
        self.primary = HexColor(f"#{primary_hex}")
        self.secondary = HexColor(f"#{secondary_hex}")
        self.font = _ensure_font()

    def add_title_page(self, title: str, subtitle: str = "", eyebrow: str = ""):
        c = self.c
        c.setFillColor(self.primary)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(self.secondary)
        c.circle(PAGE_W - 1.6 * inch, 1.6 * inch, 2.4 * inch, fill=1, stroke=0)
        c.setFillColor(white)
        if eyebrow:
            c.setFont(self.font, 13)
            c.drawString(0.9 * inch, PAGE_H - 1.9 * inch, eyebrow)
        c.setFont(self.font, 30)
        c.drawString(0.9 * inch, PAGE_H - 2.7 * inch, title)
        if subtitle:
            c.setFont(self.font, 15)
            c.drawString(0.9 * inch, PAGE_H - 3.4 * inch, subtitle)
        c.showPage()

    def add_image_page(self, title: str, image_bytes: bytes, caption: str = ""):
        c = self.c
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(self.primary)
        c.rect(0, PAGE_H - 0.9 * inch, PAGE_W, 0.9 * inch, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(self.font, 18)
        c.drawString(0.6 * inch, PAGE_H - 0.6 * inch, title)

        img = PILImage.open(io.BytesIO(image_bytes))
        iw, ih = img.size
        max_w, max_h = PAGE_W - 1.6 * inch, PAGE_H - 2.2 * inch
        ratio = min(max_w / iw, max_h / ih)
        dw, dh = iw * ratio, ih * ratio
        x = (PAGE_W - dw) / 2
        y = (PAGE_H - 1.1 * inch - dh) / 2 + 0.3 * inch

        img_reader = io.BytesIO(image_bytes)
        c.drawImage(img_reader, x, y, width=dw, height=dh, preserveAspectRatio=True, mask='auto')

        if caption:
            c.setFillColor(HexColor("#6B6B6B"))
            c.setFont(self.font, 11)
            c.drawCentredString(PAGE_W / 2, 0.4 * inch, caption)
        c.showPage()

    def add_text_page(self, title: str, paragraphs: list[str]):
        c = self.c
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(self.primary)
        c.rect(0, PAGE_H - 0.9 * inch, PAGE_W, 0.9 * inch, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(self.font, 18)
        c.drawString(0.6 * inch, PAGE_H - 0.6 * inch, title)

        c.setFillColor(HexColor("#1A1A1A"))
        c.setFont(self.font, 13)
        y = PAGE_H - 1.6 * inch
        for para in paragraphs:
            for line in _wrap_text(para, 70):
                c.drawString(0.9 * inch, y, line)
                y -= 0.32 * inch
            y -= 0.15 * inch
        c.showPage()

    def finish(self) -> bytes:
        self.c.save()
        return self.buf.getvalue()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """아주 단순한 문자 수 기준 줄바꿈 (한글 CJK 폭 근사치)."""
    lines = []
    current = ""
    for ch in text:
        current += ch
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines or [""]
