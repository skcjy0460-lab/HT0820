# -*- coding: utf-8 -*-
"""
이미지 리사이즈 유틸리티
- 크롭이 아니라 "이미지 전체 내용을 유지한 채" 크기만 줄이는 것이 목적.
- LANCZOS(고품질 다운샘플링 필터) 사용 + 다운스케일 후 선택적 언샤프 마스크로
  체감 화질(선명도) 손실을 최소화한다.
- EXIF 회전 정보를 반영해서 저장 시 이미지가 돌아가는 문제를 방지한다.
- JPEG 저장 시 품질/서브샘플링을 최적화해서 파일 용량 대비 화질을 확보한다.
"""

from __future__ import annotations
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, ImageFilter


@dataclass
class ResizeResult:
    image: Image.Image
    original_size: tuple[int, int]
    new_size: tuple[int, int]
    original_bytes: int
    new_bytes: int
    format: str


def _apply_light_unsharp(img: Image.Image, scale_ratio: float) -> Image.Image:
    """
    다운스케일 비율이 클수록(많이 줄일수록) 이미지가 뭉개져 보이기 쉬우므로
    아주 약한 언샤프 마스크를 적용해 윤곽선 선명도를 보정한다.
    scale_ratio: new_width / original_width (0~1)
    """
    if scale_ratio >= 0.9:
        return img  # 거의 안 줄었으면 보정 불필요
    # 많이 줄일수록 radius/percent를 살짝 키움 (과도한 샤프닝은 아티팩트 유발하므로 상한 설정)
    percent = min(60, int((1 - scale_ratio) * 80))
    return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=percent, threshold=2))


def resize_image(
    file_bytes: bytes,
    mode: str,
    target_width: int | None = None,
    target_height: int | None = None,
    percent: float | None = None,
    keep_aspect_ratio: bool = True,
    output_format: str = "auto",
    jpeg_quality: int = 92,
) -> ResizeResult:
    """
    mode: "pixel"(가로/세로 직접 입력) 또는 "percent"(비율 축소)
    output_format: "auto"(원본 포맷 유지) / "JPEG" / "PNG" / "WEBP"
    """
    original_bytes_len = len(file_bytes)
    img = Image.open(io.BytesIO(file_bytes))
    # 주의: ImageOps.exif_transpose()는 반환되는 이미지의 .format 속성을 None으로
    # 초기화시키므로, 반드시 exif_transpose 호출 "이전"에 원본 포맷을 읽어둬야 한다.
    original_format = (img.format or "PNG").upper()
    img = ImageOps.exif_transpose(img)  # EXIF 회전 정보 반영 후 EXIF 태그 자체는 제거
    original_size = img.size

    orig_w, orig_h = img.size

    if mode == "percent":
        if not percent or percent <= 0 or percent > 100:
            raise ValueError("percent 값은 1~100 사이여야 합니다.")
        new_w = max(1, round(orig_w * percent / 100))
        new_h = max(1, round(orig_h * percent / 100))
    else:
        if keep_aspect_ratio:
            if target_width and not target_height:
                new_w = target_width
                new_h = round(orig_h * (target_width / orig_w))
            elif target_height and not target_width:
                new_h = target_height
                new_w = round(orig_w * (target_height / orig_h))
            elif target_width and target_height:
                # 두 값 다 입력된 경우, 비율 유지를 위해 더 작은 축소율에 맞춤 (이미지가 잘리지 않도록)
                ratio = min(target_width / orig_w, target_height / orig_h)
                new_w = max(1, round(orig_w * ratio))
                new_h = max(1, round(orig_h * ratio))
            else:
                raise ValueError("가로 또는 세로 중 최소 1개 값을 입력해주세요.")
        else:
            if not (target_width and target_height):
                raise ValueError("비율 유지를 해제한 경우 가로/세로를 모두 입력해주세요.")
            new_w, new_h = target_width, target_height

    # 확대는 화질 손실이 크므로 이 기능의 목적(축소)에 맞게 제한
    if new_w >= orig_w and new_h >= orig_h:
        raise ValueError("이 기능은 이미지를 '축소'하는 용도입니다. 목표 크기가 원본보다 작아야 합니다.")

    scale_ratio = new_w / orig_w

    # RGBA -> JPEG 저장 시 오류 방지를 위해 모드 정리
    save_format = original_format if output_format == "auto" else output_format
    if save_format == "JPEG" and img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1])
        img = bg

    resized = img.resize((new_w, new_h), resample=Image.LANCZOS)
    resized = _apply_light_unsharp(resized, scale_ratio)

    buf = io.BytesIO()
    save_kwargs = {}
    if save_format in ("JPEG", "JPG"):
        save_format = "JPEG"
        save_kwargs = dict(quality=jpeg_quality, optimize=True, subsampling=0)
    elif save_format == "PNG":
        save_kwargs = dict(optimize=True)
    elif save_format == "WEBP":
        save_kwargs = dict(quality=jpeg_quality, method=6)

    resized.save(buf, format=save_format, **save_kwargs)
    new_bytes = buf.getvalue()

    return ResizeResult(
        image=resized,
        original_size=original_size,
        new_size=(new_w, new_h),
        original_bytes=original_bytes_len,
        new_bytes=len(new_bytes),
        format=save_format,
    )


def result_to_download_bytes(result: ResizeResult, jpeg_quality: int = 92) -> bytes:
    buf = io.BytesIO()
    fmt = result.format
    save_kwargs = {}
    if fmt == "JPEG":
        save_kwargs = dict(quality=jpeg_quality, optimize=True, subsampling=0)
    elif fmt == "PNG":
        save_kwargs = dict(optimize=True)
    elif fmt == "WEBP":
        save_kwargs = dict(quality=jpeg_quality, method=6)
    result.image.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


def human_readable_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"
