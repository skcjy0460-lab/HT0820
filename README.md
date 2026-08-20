# 🏥 병원 마케팅 툴킷 (무료 버전)

병원 마케팅/원무 실무에 바로 쓸 수 있는 4가지 기능을 담은 Streamlit 앱입니다.

## 기능 구성

| 기능 | 설명 |
|---|---|
| 🖼️ 이미지 크기 편집 | 자르지 않고, 화질 손실을 최소화하며 이미지 크기(용량)만 축소. 블로그/인스타/배너 규격 프리셋 제공 |
| 🎨 AI 이미지 생성 | 주제·세부내용·용도(비율)·스타일을 입력하면 AI가 마케팅용 이미지 생성 |
| 📁 포트폴리오 만들기 | 이미지+설명(일반/Before-After)을 등록해 PPT 또는 PDF 포트폴리오로 즉시 내보내기 |
| 📽️ AI PPT 제작 | 주제·핵심내용·페이지 수·청중을 입력하면 AI가 슬라이드 구조를 설계하고 디자인까지 완성된 PPT 생성 |

## 중요: 사용 모델 안내 (2026년 8월 기준)

Gemini의 **텍스트 모델**과 **이미지 생성 모델**은 서로 다른 계열입니다.

- **텍스트 생성** (AI PPT의 슬라이드 구조 설계 등): `gemini-3.6-flash` → 실패 시 `gemini-3.5-flash-lite` → `gemini-2.5-flash-lite` 순으로 자동 폴백
- **이미지 생성**: `gemini-3.1-flash-image` (일명 "나노바나나2") → 실패 시 `gemini-2.5-flash-image` 순으로 자동 폴백
  - ⚠️ `3.6-flash`/`3.5-flash-lite`는 텍스트 전용이라 이미지를 생성하지 못합니다. 이미지 생성에는 반드시 `-image`가 붙은 별도 모델이 필요해서 위와 같이 분리했습니다.
- 모델명이 향후 변경/종료될 경우 `utils/gemini_client.py` 상단의 `TEXT_MODEL_CHAIN`, `IMAGE_MODEL_CHAIN` 리스트만 수정하면 전체에 반영됩니다.

## 로컬 실행 방법

```bash
pip install -r requirements.txt
cp .streamlit/secrets_example.toml .streamlit/secrets.toml
# secrets.toml 파일을 열어 GEMINI_API_KEY 값을 실제 발급받은 키로 교체
streamlit run app.py
```

API 키는 [Google AI Studio](https://aistudio.google.com/)에서 무료로 발급받을 수 있습니다.

## Streamlit Community Cloud 배포 방법

1. 이 폴더 전체를 GitHub 저장소에 업로드 (단, `.streamlit/secrets.toml` 실제 파일은 절대 올리지 말 것 — `.gitignore`에 이미 포함되어 있습니다)
2. [share.streamlit.io](https://share.streamlit.io) 접속 → New app → 저장소/브랜치/`app.py` 선택 후 Deploy
3. 배포된 앱의 **Settings → Secrets**에 들어가 아래 내용을 붙여넣기:
   ```toml
   GEMINI_API_KEY = "실제_발급받은_키"
   ```
4. 저장 후 앱이 자동 재시작되면 AI 기능(이미지 생성, AI PPT)까지 정상 작동합니다.
   - 이미지 크기 편집, 포트폴리오 만들기(PPT/PDF 내보내기)는 API 키 없이도 바로 사용 가능합니다.

## 폴더 구조

```
app.py                      # 메인 진입점 (네비게이션)
views/
  image_resize.py           # 기능 1
  image_generate.py         # 기능 2
  portfolio_maker.py        # 기능 3
  ai_ppt_maker.py           # 기능 4
utils/
  gemini_client.py          # Gemini API 래퍼 (텍스트/이미지 모델 폴백)
  image_utils.py            # 고품질 이미지 리사이즈 로직
  ppt_utils.py              # python-pptx 기반 슬라이드 빌더 (테마 3종 포함)
  pdf_utils.py              # reportlab 기반 PDF 빌더 (한글 폰트 내장)
requirements.txt
.streamlit/secrets_example.toml
```

## 설계 상 주의사항 (유지보수 시 참고)

- **PPT/PDF는 python-pptx / reportlab으로 직접 조립합니다.** Streamlit Community Cloud에는 LibreOffice가 없어 다른 포맷으로의 변환이 불가능하기 때문에, 각 포맷을 코드로 직접 그리는 방식을 택했습니다.
- **이미지 리사이즈는 크롭이 아니라 축소 전용입니다.** LANCZOS 리샘플링 + 축소 비율에 비례한 약한 언샤프 마스크로 체감 화질을 보정합니다. 목표 크기가 원본보다 크면 의도적으로 에러를 반환합니다(확대는 화질 저하가 크므로 이 도구의 목적과 맞지 않음).
- **디자인 테마 3종**(네이비&골드 / 민트 / 코랄)은 포트폴리오와 AI PPT 기능이 공유합니다. 새 테마 추가는 `ppt_utils.py`의 `THEMES` 딕셔너리에 한 줄만 추가하면 됩니다.
