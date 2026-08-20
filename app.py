# -*- coding: utf-8 -*-
"""
병원 마케팅 툴킷 - 메인 진입점
st.navigation을 사용한 멀티페이지 구조. 각 기능은 views/ 폴더의 개별 모듈이 담당한다.
"""

import streamlit as st
from utils.gemini_client import check_api_key_configured

st.set_page_config(
    page_title="병원 마케팅 툴킷",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 사이드바 공통 영역
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏥 병원 마케팅 툴킷")
    st.caption("무료 실무 지원 도구 모음")

    if check_api_key_configured():
        st.success("AI API 연결됨", icon="✅")
    else:
        st.error("AI API 키 미설정", icon="⚠️")
        st.caption(
            "AI 이미지 생성 / AI PPT 제작 기능을 쓰려면 "
            "`.streamlit/secrets.toml`에 GEMINI_API_KEY를 등록해주세요."
        )

    st.divider()


def _image_resize():
    from views import image_resize
    image_resize.render()


def _image_generate():
    from views import image_generate
    image_generate.render()


def _portfolio_maker():
    from views import portfolio_maker
    portfolio_maker.render()


def _ai_ppt_maker():
    from views import ai_ppt_maker
    ai_ppt_maker.render()


pages = [
    st.Page(_image_resize, title="이미지 크기 편집", icon="🖼️", url_path="image-resize", default=True),
    st.Page(_image_generate, title="AI 이미지 생성", icon="🎨", url_path="image-generate"),
    st.Page(_portfolio_maker, title="포트폴리오 만들기", icon="📁", url_path="portfolio-maker"),
    st.Page(_ai_ppt_maker, title="AI PPT 제작", icon="📽️", url_path="ai-ppt-maker"),
]

nav = st.navigation(pages, position="sidebar")
nav.run()

with st.sidebar:
    st.divider()
    st.caption("© 병원 마케팅 툴킷 · 내부 무료 배포용")
