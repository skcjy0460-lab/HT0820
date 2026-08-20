# -*- coding: utf-8 -*-
"""
기능 2: AI 이미지 생성
- 주제/내용/크기(비율)를 입력하면 Gemini 이미지 모델(나노바나나2)로 이미지를 생성.
- 병원 마케팅에 바로 쓸 수 있도록 "용도" 프리셋(블로그 썸네일, 배너, SNS 카드뉴스 등)을 함께 제공.
"""

import io
import streamlit as st
from utils.gemini_client import generate_image

ASPECT_PRESETS = {
    "정사각형 (1:1) - 인스타 피드": "1:1",
    "가로 와이드 (16:9) - 블로그 썸네일/유튜브": "16:9",
    "세로 스토리 (9:16) - 인스타/카카오 스토리": "9:16",
    "가로 표준 (4:3) - 배너": "4:3",
    "세로 표준 (3:4) - 카드뉴스": "3:4",
}

STYLE_PRESETS = {
    "선택 안함": "",
    "깔끔한 사진 스타일 (실사풍)": "photorealistic, soft natural lighting, clean composition",
    "따뜻한 일러스트 스타일": "warm flat illustration style, soft pastel colors",
    "미니멀 인포그래픽 스타일": "minimal infographic style, clean icons, lots of white space",
    "고급스러운 메디컬 브랜딩": "premium medical branding style, navy and gold accents, elegant",
}


def render():
    st.title("🎨 AI 이미지 생성")
    st.caption("주제와 내용을 입력하면 AI가 병원 마케팅용 이미지를 생성해드립니다.")

    with st.form("image_gen_form"):
        topic = st.text_input(
            "주제 (필수)", placeholder="예: 소아과 예방접종 안내 배너"
        )
        detail = st.text_area(
            "세부 내용 / 원하는 분위기 (선택)",
            placeholder="예: 밝고 따뜻한 느낌, 아이와 부모가 함께 있는 모습, 병원 로고 넣지 않음",
            height=100,
        )
        col1, col2 = st.columns(2)
        with col1:
            aspect_label = st.selectbox("이미지 크기(용도)", list(ASPECT_PRESETS.keys()))
        with col2:
            style_label = st.selectbox("스타일", list(STYLE_PRESETS.keys()))

        avoid_text = st.checkbox(
            "이미지 안에 텍스트/글자가 들어가지 않게 하기", value=True,
            help="AI 이미지 생성 모델은 글자를 어색하게 그리는 경우가 많아 기본적으로 체크를 권장합니다."
        )

        submitted = st.form_submit_button("✨ 이미지 생성하기", type="primary", use_container_width=True)

    if not submitted:
        if "generated_image" in st.session_state:
            st.image(st.session_state["generated_image"], use_container_width=True)
        return

    if not topic.strip():
        st.error("주제를 입력해주세요.")
        return

    prompt_parts = [f"주제: {topic.strip()}"]
    if detail.strip():
        prompt_parts.append(f"세부 내용: {detail.strip()}")
    if STYLE_PRESETS[style_label]:
        prompt_parts.append(f"스타일: {STYLE_PRESETS[style_label]}")
    if avoid_text:
        prompt_parts.append("이미지 안에 어떠한 글자, 문구, 캡션도 넣지 마세요 (no text, no letters, no captions).")
    prompt_parts.append("병원/의료 마케팅에 바로 사용할 수 있는 전문적이고 신뢰감 있는 퀄리티로 생성해주세요.")

    full_prompt = "\n".join(prompt_parts)

    with st.spinner("AI가 이미지를 생성하는 중입니다... (최대 30초 정도 소요될 수 있습니다)"):
        try:
            image = generate_image(full_prompt, aspect_ratio=ASPECT_PRESETS[aspect_label])
        except Exception as e:  # noqa: BLE001
            st.error(f"이미지 생성에 실패했습니다: {e}")
            return

    st.session_state["generated_image"] = image
    st.success("이미지가 생성되었습니다!")
    st.image(image, use_container_width=True)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    st.download_button(
        "⬇️ 이미지 다운로드 (PNG)",
        data=buf.getvalue(),
        file_name=f"{topic.strip()[:20] or 'generated'}.png",
        mime="image/png",
        type="primary",
        use_container_width=True,
    )

    with st.expander("실제 사용된 프롬프트 보기"):
        st.code(full_prompt)
