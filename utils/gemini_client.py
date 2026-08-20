# -*- coding: utf-8 -*-
"""
Gemini API 클라이언트 래퍼
- 텍스트 생성용 모델과 이미지 생성용 모델을 분리해서 관리합니다.
- 텍스트 생성: gemini-3.6-flash -> gemini-3.5-flash-lite -> gemini-2.5-flash-lite 순서로 폴백
- 이미지 생성: gemini-3.1-flash-image(나노바나나2) -> gemini-2.5-flash-image 순서로 폴백
  * 주의: 3.6-flash/3.5-flash-lite 계열은 "텍스트 전용" 모델이라 이미지 생성이 불가능합니다.
    이미지 생성은 반드시 별도의 "-image" 계열 모델을 사용해야 합니다.
"""

import io
import json
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# ------------------------------------------------------------------
# 모델 폴백 체인 (2026-08 기준, 필요 시 이 리스트만 수정하면 전체 반영됨)
# ------------------------------------------------------------------
TEXT_MODEL_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
]

IMAGE_MODEL_CHAIN = [
    "gemini-3.1-flash-image",   # 나노바나나2 (Nano Banana 2) - 최신, 빠르고 저렴
    "gemini-2.5-flash-image",   # 나노바나나 1세대 - 폴백용
]


def _get_api_key() -> str:
    """secrets.toml 또는 환경변수에서 API 키를 가져옵니다."""
    key = st.secrets.get("GEMINI_API_KEY", None)
    if not key:
        st.error(
            "GEMINI_API_KEY가 설정되지 않았습니다. "
            "`.streamlit/secrets.toml` 파일에 GEMINI_API_KEY를 추가해주세요."
        )
        st.stop()
    return key


@st.cache_resource(show_spinner=False)
def get_client() -> "genai.Client":
    """genai.Client는 매 요청마다 새로 만들 필요가 없으므로 캐싱합니다."""
    return genai.Client(api_key=_get_api_key())


def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    response_json: bool = False,
    temperature: float = 0.7,
) -> str:
    """
    텍스트 생성 (모델 자동 폴백 포함).
    response_json=True이면 모델에게 JSON만 출력하도록 강제합니다.
    """
    client = get_client()
    last_error = None

    config_kwargs = {"temperature": temperature}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if response_json:
        config_kwargs["response_mime_type"] = "application/json"

    for model_name in TEXT_MODEL_CHAIN:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("빈 응답")
            return text
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue

    raise RuntimeError(f"모든 텍스트 모델 호출 실패. 마지막 오류: {last_error}")


def generate_text_json(prompt: str, system_instruction: str | None = None) -> dict:
    """JSON 형식 응답을 강제하고 파싱까지 처리."""
    raw = generate_text(prompt, system_instruction=system_instruction, response_json=True)
    # 혹시 모델이 마크다운 코드펜스를 붙였을 경우 제거
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    reference_images: list[Image.Image] | None = None,
) -> Image.Image:
    """
    이미지 생성 (모델 자동 폴백 포함).
    aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4" 등
    reference_images: 이미지 편집/합성 시 참조 이미지 목록 (선택)
    """
    client = get_client()
    last_error = None

    contents = []
    if reference_images:
        for img in reference_images:
            contents.append(img)
    contents.append(prompt)

    for model_name in IMAGE_MODEL_CHAIN:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) is not None:
                    img_bytes = part.inline_data.data
                    return Image.open(io.BytesIO(img_bytes))
            raise ValueError("응답에 이미지 데이터가 없습니다.")
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue

    raise RuntimeError(f"모든 이미지 모델 호출 실패. 마지막 오류: {last_error}")
