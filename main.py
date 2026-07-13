import streamlit as st
import parselmouth
import io
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="음성 분석기", layout="wide")

st.title("🎤 Praat 음성 비교 분석기 (Streamlit Cloud 버전)")
st.caption("파일 업로드 또는 녹음 후 두 구간을 선택하세요")

# ====================== 입력 ======================
st.sidebar.header("음성 입력")
mode = st.sidebar.radio("입력 방식", ["파일 업로드", "마이크 녹음"], horizontal=True)

sound = None

if mode == "파일 업로드":
    file = st.sidebar.file_uploader("WAV 파일", type=["wav"])
    if file:
        audio_bytes = file.read()
else:
    rec = st.sidebar.audio_input("🎤 마이크 녹음")
    if rec:
        audio_bytes = rec.read()

if 'audio_bytes' in locals() and audio_bytes:
    try:
        with st.spinner("로드 중... (Cloud 최적화)"):
            sound = parselmouth.Sound(io.BytesIO(audio_bytes))
        st.success(f"✅ 성공 | 길이: {sound.xmax-sound.xmin:.2f}초")
    except Exception as e:
        st.error(f"로드 실패: {e}")
        st.info("파일을 다시 업로드하거나 짧게 녹음해보세요 (15초 이하 권장)")

if sound is None:
    st.info("👈 사이드바에서 음성을 입력하세요.")
    st.stop()

# ====================== 파형 ======================
st.subheader("전체 파형")
fig = go.Figure(go.Scatter(x=sound.xs(), y=sound.values[0], mode='lines'))
fig.update_layout(height=300, xaxis_title="시간 (초)")
st.plotly_chart(fig, use_container_width=True)

# ====================== 구간 선택 ======================
st.subheader("두 구간 선택")
c1, c2 = st.columns(2)
with c1:
    st.write("**구간 1**")
    start1 = st.number_input("시작", 0.0, float(sound.xmax), 0.0, 0.1, key="st1")
    end1 = st.number_input("끝", 0.0, float(sound.xmax), 5.0, 0.1, key="et1")
with c2:
    st.write("**구간 2**")
    start2 = st.number_input("시작", 0.0, float(sound.xmax), 5.0, 0.1, key="st2")
    end2 = st.number_input("끝", 0.0, float(sound.xmax), 10.0, 0.1, key="et2")

if st.button("🔍 분석 실행", type="primary", use_container_width=True):
    if end1 <= start1 or end2 <= start2:
        st.error("끝 시간이 시작 시간보다 커야 합니다.")
    else:
        try:
            seg1 = sound.extract_part(start1, end1)
            seg2 = sound.extract_part(start2, end2)

            st.subheader("파형 비교")
            fig2 = make_subplots(rows=2, cols=1)
            fig2.add_trace(go.Scatter(x=seg1.xs(), y=seg1.values[0]), row=1, col=1)
            fig2.add_trace(go.Scatter(x=seg2.xs(), y=seg2.values[0]), row=2, col=1)
            st.plotly_chart(fig2, use_container_width=True)

            st.success("분석 완료!")
        except Exception as e:
            st.error(f"분석 오류: {e}")

st.caption("Streamlit Cloud 최적화 버전 | 오류 시 정확한 메시지 알려주세요")
