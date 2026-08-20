# -*- coding: utf-8 -*-
"""
기능 1: 이미지 크기 편집
- 크롭이 아니라, 이미지 전체 구도를 유지한 채 "크기만" 줄이는 기능.
- 블로그/인스타/배너 등 업로드 규격에 맞춰 화질 손실을 최소화하며 축소.
"""

import streamlit as st
from utils.image_utils import resize_image, result_to_download_bytes, human_readable_size

PRESETS = {
    "직접 입력": None,
    "네이버 블로그 대표이미지 (966 x 604)": (966, 604),
    "인스타그램 정사각형 (1080 x 1080)": (1080, 1080),
    "인스타그램 스토리 (1080 x 1920)": (1080, 1920),
    "카카오톡 채널 배너 (800 x 400)": (800, 400),
    "홈페이지 배너 (1920 x 600)": (1920, 600),
}


def render():
    st.title("🖼️ 이미지 크기 편집")
    st.caption("이미지를 자르지 않고, 화질 손실을 최소화하면서 크기만 줄여드립니다.")

    uploaded = st.file_uploader(
        "이미지를 업로드하세요", type=["jpg", "jpeg", "png", "webp"], key="resize_uploader"
    )

    if not uploaded:
        st.info("좌측에서 이미지를 업로드하면 미리보기와 설정이 표시됩니다.")
        return

    file_bytes = uploaded.getvalue()

    col_preview, col_setting = st.columns([1, 1])

    with col_preview:
        st.subheader("원본 미리보기")
        st.image(file_bytes, use_container_width=True)
        st.caption(f"원본 용량: {human_readable_size(len(file_bytes))}")

    with col_setting:
        st.subheader("축소 설정")
        preset_name = st.selectbox("사이즈 프리셋", list(PRESETS.keys()))

        mode = st.radio("축소 방식", ["픽셀(가로/세로) 지정", "비율(%) 지정"], horizontal=True)

        keep_ratio = True
        target_w = target_h = None
        percent = None

        if mode == "픽셀(가로/세로) 지정":
            if PRESETS[preset_name]:
                default_w, default_h = PRESETS[preset_name]
            else:
                default_w, default_h = 0, 0

            keep_ratio = st.checkbox("가로세로 비율 유지", value=True)
            c1, c2 = st.columns(2)
            with c1:
                target_w = st.number_input("가로(px)", min_value=0, value=default_w, step=10)
            with c2:
                target_h = st.number_input("세로(px)", min_value=0, value=default_h, step=10,
                                            disabled=keep_ratio and bool(target_w))
            target_w = target_w or None
            target_h = target_h or None
        else:
            percent = st.slider("축소 비율(%)", min_value=10, max_value=95, value=70, step=5)

        output_format = st.selectbox("저장 포맷", ["원본 유지", "JPEG", "PNG", "WEBP"])
        fmt_map = {"원본 유지": "auto", "JPEG": "JPEG", "PNG": "PNG", "WEBP": "WEBP"}

        jpeg_quality = 92
        if fmt_map[output_format] in ("JPEG", "WEBP", "auto"):
            jpeg_quality = st.slider("화질(JPEG/WEBP 품질)", min_value=70, max_value=100, value=92,
                                      help="높을수록 화질은 좋아지지만 용량이 커집니다.")

        run = st.button("🔧 크기 조절 실행", type="primary", use_container_width=True)

    if run:
        try:
            with st.spinner("이미지를 처리하는 중입니다..."):
                result = resize_image(
                    file_bytes=file_bytes,
                    mode="percent" if mode == "비율(%) 지정" else "pixel",
                    target_width=int(target_w) if target_w else None,
                    target_height=int(target_h) if target_h else None,
                    percent=percent,
                    keep_aspect_ratio=keep_ratio,
                    output_format=fmt_map[output_format],
                    jpeg_quality=jpeg_quality,
                )
        except ValueError as e:
            st.error(str(e))
            return

        st.success("완료되었습니다!")
        r1, r2 = st.columns([1, 1])
        with r1:
            st.subheader("결과 미리보기")
            st.image(result.image, use_container_width=True)
        with r2:
            st.subheader("결과 정보")
            st.markdown(
                f"""
                | 항목 | 원본 | 변경 후 |
                |---|---|---|
                | 크기 | {result.original_size[0]} x {result.original_size[1]}px | **{result.new_size[0]} x {result.new_size[1]}px** |
                | 용량 | {human_readable_size(result.original_bytes)} | **{human_readable_size(result.new_bytes)}** |
                | 절감률 | - | **{(1 - result.new_bytes / result.original_bytes) * 100:.1f}% 감소** |
                """
            )
            download_bytes = result_to_download_bytes(result, jpeg_quality=jpeg_quality)
            ext = result.format.lower().replace("jpeg", "jpg")
            st.download_button(
                "⬇️ 결과 이미지 다운로드",
                data=download_bytes,
                file_name=f"resized_{result.new_size[0]}x{result.new_size[1]}.{ext}",
                mime=f"image/{result.format.lower()}",
                type="primary",
                use_container_width=True,
            )
