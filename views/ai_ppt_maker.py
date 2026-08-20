# -*- coding: utf-8 -*-
"""
기능 4: AI PPT 제작
- 주제/내용/페이지 수를 입력하면 Gemini 텍스트 모델이 슬라이드 구조(JSON)를 설계하고,
  python-pptx로 실제 PPT 파일을 조립한다.
- 표지 -> (선택)섹션 구분 -> 본문 슬라이드들 -> 마무리 슬라이드 구조로 자동 구성.
"""

import streamlit as st
from utils.gemini_client import generate_text_json
from utils.ppt_utils import (
    THEMES, new_presentation, add_title_slide, add_section_slide,
    add_bullet_slide, presentation_to_bytes,
)

AUDIENCE_OPTIONS = ["병원 원장/경영진", "병원 직원 교육용", "환자 대상 설명자료", "투자자/외부 파트너"]

SYSTEM_INSTRUCTION = """당신은 병원 경영 컨설팅 전문 프레젠테이션 기획자입니다.
주어진 주제와 내용을 바탕으로 논리적이고 설득력 있는 PPT 슬라이드 구조를 설계합니다.
반드시 JSON 형식으로만 응답하며, 다른 설명 텍스트는 절대 포함하지 않습니다.

JSON 스키마:
{
  "cover": {"eyebrow": "상단 소제목(영문 약어 가능, 없으면 빈 문자열)", "title": "표지 제목", "subtitle": "부제목"},
  "sections": [
    {
      "section_title": "섹션 제목 (없으면 null)",
      "slides": [
        {"title": "슬라이드 제목", "bullets": ["핵심 포인트1", "핵심 포인트2", "..."], "notes": "발표자 메모(간단히)"}
      ]
    }
  ]
}

규칙:
- bullets 각 항목은 한 줄로 읽기 좋게 15~40자 내외로 간결하게 작성 (완전한 문장이 아니어도 됨).
- 슬라이드 당 bullets는 3~5개를 넘지 않도록 한다.
- 실무에서 바로 쓸 수 있도록 구체적인 수치/예시/용어를 포함해 작성한다.
- 요청된 총 슬라이드 수(표지 제외)에 맞춰 sections/slides 개수를 배분한다.
"""


def _build_user_prompt(topic, content, audience, num_slides, tone):
    return f"""
주제: {topic}
청중: {audience}
톤/스타일: {tone}
목표 슬라이드 수(표지 제외): {num_slides}

포함되어야 할 핵심 내용:
{content}

위 내용을 바탕으로 PPT 슬라이드 구조를 JSON으로 설계해주세요.
"""


def render():
    st.title("📽️ AI PPT 제작")
    st.caption("주제와 내용을 입력하면 AI가 슬라이드 구조를 설계하고 PPT 파일을 완성해드립니다.")

    with st.form("ppt_gen_form"):
        topic = st.text_input("PPT 주제 (필수)", placeholder="예: 2026년 하반기 병원 마케팅 전략 보고")
        content = st.text_area(
            "포함할 핵심 내용 (필수)", height=160,
            placeholder="예:\n- 상반기 내원객 수 전년 대비 12% 증가\n- 블로그/인스타 채널 강화 필요\n"
                        "- 재방문율 개선을 위한 CRM 도입 검토\n- 3분기 목표: 월 신규 환자 15% 증가"
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            audience = st.selectbox("대상 청중", AUDIENCE_OPTIONS)
        with c2:
            num_slides = st.slider("본문 슬라이드 수", min_value=3, max_value=20, value=8)
        with c3:
            theme_key = st.selectbox("디자인 테마", list(THEMES.keys()), format_func=lambda k: THEMES[k].name)

        tone = st.selectbox("톤 & 스타일", ["전문적이고 신뢰감 있게", "친근하고 쉽게", "간결하고 임팩트 있게"])
        use_sections = st.checkbox("섹션 구분 슬라이드 사용 (내용이 길 때 권장)", value=(num_slides >= 8))

        submitted = st.form_submit_button("🪄 AI로 PPT 생성하기", type="primary", use_container_width=True)

    if not submitted:
        return

    if not topic.strip() or not content.strip():
        st.error("주제와 핵심 내용을 모두 입력해주세요.")
        return

    prompt = _build_user_prompt(topic, content, audience, num_slides, tone)

    with st.spinner("AI가 슬라이드 구조를 설계하는 중입니다..."):
        try:
            structure = generate_text_json(prompt, system_instruction=SYSTEM_INSTRUCTION)
        except Exception as e:  # noqa: BLE001
            st.error(f"AI 구조 설계에 실패했습니다: {e}")
            return

    with st.spinner("PPT 파일을 조립하는 중입니다..."):
        try:
            theme = THEMES[theme_key]
            prs = new_presentation()

            cover = structure.get("cover", {})
            add_title_slide(
                prs, theme,
                title=cover.get("title", topic),
                subtitle=cover.get("subtitle", ""),
                eyebrow=cover.get("eyebrow", ""),
            )

            sections = structure.get("sections", [])
            section_no = 1
            for section in sections:
                if use_sections and section.get("section_title"):
                    add_section_slide(prs, theme, f"{section_no:02d}", section["section_title"])
                    section_no += 1
                for slide_data in section.get("slides", []):
                    add_bullet_slide(
                        prs, theme,
                        title=slide_data.get("title", ""),
                        bullets=slide_data.get("bullets", []),
                        notes=slide_data.get("notes"),
                    )

            data = presentation_to_bytes(prs)
        except Exception as e:  # noqa: BLE001
            st.error(f"PPT 조립 중 오류가 발생했습니다: {e}")
            with st.expander("AI가 생성한 구조(디버그용)"):
                st.json(structure)
            return

    st.success("PPT가 완성되었습니다!")
    st.download_button(
        "⬇️ PPT 파일 다운로드", data=data,
        file_name=f"{topic.strip()[:20]}_AI생성.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary", use_container_width=True,
    )

    with st.expander("AI가 설계한 슬라이드 구조 미리보기"):
        st.json(structure)
