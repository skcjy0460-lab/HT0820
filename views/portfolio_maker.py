# -*- coding: utf-8 -*-
"""
기능 3: 포트폴리오 만들기
- 여러 장의 이미지(시술 전/후, 시설 사진, 케이스 사진 등)와 설명을 입력받아
  PPT 또는 PDF 형식의 포트폴리오로 즉시 내보낸다.
- Before/After 비교 슬라이드를 지원해 시술 결과 포트폴리오에 바로 활용 가능.
"""

import streamlit as st
from utils.ppt_utils import (
    THEMES, new_presentation, add_title_slide, add_section_slide,
    add_image_slide, add_before_after_slide, presentation_to_bytes,
)
from utils.pdf_utils import PortfolioPDFBuilder

ITEM_TYPES = ["일반 이미지", "Before/After 비교"]


def _init_state():
    if "portfolio_items" not in st.session_state:
        st.session_state.portfolio_items = []  # list of dict


def render():
    _init_state()
    st.title("📁 포트폴리오 만들기")
    st.caption("이미지와 설명을 등록하면 PPT 또는 PDF 포트폴리오로 바로 내보낼 수 있습니다.")

    with st.expander("① 표지 정보 입력", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            cover_title = st.text_input("포트폴리오 제목", placeholder="예: OO의원 2026 시술 케이스 포트폴리오")
            eyebrow = st.text_input("상단 소제목 (선택)", placeholder="예: PATIENT CASE PORTFOLIO")
        with c2:
            cover_subtitle = st.text_input("부제목/설명 (선택)", placeholder="예: 2026년 상반기 대표 케이스 모음")
            theme_key = st.selectbox("디자인 테마", list(THEMES.keys()),
                                      format_func=lambda k: THEMES[k].name)

    st.divider()
    st.subheader("② 포트폴리오 항목 추가")

    with st.form("add_item_form", clear_on_submit=True):
        item_type = st.radio("항목 유형", ITEM_TYPES, horizontal=True)
        item_title = st.text_input("슬라이드 제목", placeholder="예: 리프팅 시술 케이스 A")

        if item_type == "일반 이미지":
            img_file = st.file_uploader("이미지 업로드", type=["jpg", "jpeg", "png", "webp"], key="single_img")
            caption = st.text_input("캡션(선택)", placeholder="예: 시술 3주 후 경과")
        else:
            col_b, col_a = st.columns(2)
            with col_b:
                before_file = st.file_uploader("Before 이미지", type=["jpg", "jpeg", "png", "webp"], key="before_img")
                before_label = st.text_input("Before 라벨", value="Before")
            with col_a:
                after_file = st.file_uploader("After 이미지", type=["jpg", "jpeg", "png", "webp"], key="after_img")
                after_label = st.text_input("After 라벨", value="After")

        add_clicked = st.form_submit_button("➕ 이 항목 추가하기", use_container_width=True)

    if add_clicked:
        if not item_title.strip():
            st.error("슬라이드 제목을 입력해주세요.")
        elif item_type == "일반 이미지":
            if not img_file:
                st.error("이미지를 업로드해주세요.")
            else:
                st.session_state.portfolio_items.append({
                    "type": "image", "title": item_title, "image": img_file.getvalue(),
                    "caption": caption,
                })
                st.success(f"'{item_title}' 항목이 추가되었습니다.")
        else:
            if not (before_file and after_file):
                st.error("Before/After 이미지를 모두 업로드해주세요.")
            else:
                st.session_state.portfolio_items.append({
                    "type": "before_after", "title": item_title,
                    "before": before_file.getvalue(), "after": after_file.getvalue(),
                    "before_label": before_label, "after_label": after_label,
                })
                st.success(f"'{item_title}' 항목이 추가되었습니다.")

    st.divider()
    st.subheader(f"③ 현재 등록된 항목 ({len(st.session_state.portfolio_items)}개)")

    if not st.session_state.portfolio_items:
        st.info("아직 등록된 항목이 없습니다. 위에서 항목을 추가해주세요.")
    else:
        for idx, item in enumerate(st.session_state.portfolio_items):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1:
                    thumb = item["image"] if item["type"] == "image" else item["after"]
                    st.image(thumb, use_container_width=True)
                with c2:
                    st.markdown(f"**{item['title']}**")
                    st.caption("일반 이미지" if item["type"] == "image" else "Before/After 비교")
                with c3:
                    if st.button("삭제", key=f"del_{idx}", use_container_width=True):
                        st.session_state.portfolio_items.pop(idx)
                        st.rerun()

    st.divider()
    st.subheader("④ 내보내기")

    if not st.session_state.portfolio_items:
        st.warning("항목을 1개 이상 등록해야 내보낼 수 있습니다.")
        return

    if not cover_title.strip():
        st.warning("표지 제목을 입력해주세요.")
        return

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        if st.button("📊 PPT로 내보내기", type="primary", use_container_width=True):
            theme = THEMES[theme_key]
            prs = new_presentation()
            add_title_slide(prs, theme, cover_title, cover_subtitle, eyebrow)
            for i, item in enumerate(st.session_state.portfolio_items, start=1):
                if item["type"] == "image":
                    add_image_slide(prs, theme, item["title"], item["image"], item.get("caption", ""))
                else:
                    add_before_after_slide(
                        prs, theme, item["title"], item["before"], item["after"],
                        item["before_label"], item["after_label"],
                    )
            data = presentation_to_bytes(prs)
            st.download_button(
                "⬇️ PPT 파일 다운로드", data=data,
                file_name=f"{cover_title[:20]}_포트폴리오.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )

    with exp_col2:
        if st.button("📄 PDF로 내보내기", type="primary", use_container_width=True):
            theme = THEMES[theme_key]
            builder = PortfolioPDFBuilder(primary_hex=theme.primary, secondary_hex=theme.secondary)
            builder.add_title_page(cover_title, cover_subtitle, eyebrow)
            for item in st.session_state.portfolio_items:
                if item["type"] == "image":
                    builder.add_image_page(item["title"], item["image"], item.get("caption", ""))
                else:
                    builder.add_image_page(f"{item['title']} - {item['before_label']}", item["before"])
                    builder.add_image_page(f"{item['title']} - {item['after_label']}", item["after"])
            data = builder.finish()
            st.download_button(
                "⬇️ PDF 파일 다운로드", data=data,
                file_name=f"{cover_title[:20]}_포트폴리오.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
