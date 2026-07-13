import streamlit as st
import parselmouth
import soundfile as sf
import io
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="음성 분석기", layout="wide")

st.title("🎤 Praat 음성 비교 분석기")
st.caption("Streamlit Cloud 안정 버전")

# ====================== 입력 ======================
st.sidebar.header("음성 입력")
mode = st.sidebar.radio("입력 방식", ["파일 업로드", "마이크 녹음"], horizontal=True)

sound = None

if mode == "파일 업로드":
    uploaded = st.sidebar.file_uploader("WAV 파일", type=["wav"])
    if uploaded:
        audio_bytes = uploaded.read()
else:
    rec = st.sidebar.audio_input("🎤 마이크 녹음")
    if rec:
        audio_bytes = rec.read()

if 'audio_bytes' in locals() and audio_bytes:
    try:
        with st.spinner("로드 중..."):
            data, sr = sf.read(io.BytesIO(audio_bytes))
            sound = parselmouth.Sound(values=data.T if data.ndim > 1 else data.reshape(1, -1), 
                                     sampling_frequency=sr)
        st.success(f"✅ 로드 성공 | 길이: {sound.xmax - sound.xmin:.2f}초")
    except Exception as e:
        st.error(f"로드 실패: {e}")

if sound is None:
    st.info("👈 사이드바에서 음성을 입력하세요.")
    st.stop()

# ====================== 파형 ======================
st.subheader("전체 파형")
fig = go.Figure(go.Scatter(x=sound.xs(), y=sound.values[0], mode='lines'))
fig.update_layout(height=300, xaxis_title="시간 (초)")
st.plotly_chart(fig, use_container_width=True)

# ====================== 구간 선택 (길이 안전하게) ======================
st.subheader("두 구간 선택")
c1, c2 = st.columns(2)

duration = sound.xmax - sound.xmin

with c1:
    st.write("**구간 1**")
    start1 = st.number_input("시작 (초)", 0.0, duration, 0.0, 0.1, key="s1")
    end1 = st.number_input("끝 (초)", start1, duration, min(5.0, duration), 0.1, key="e1")

with c2:
    st.write("**구간 2**")
    start2 = st.number_input("시작 (초)", 0.0, duration, min(5.0, duration), 0.1, key="s2")
    end2 = st.number_input("끝 (초)", start2, duration, min(10.0, duration), 0.1, key="e2")

if st.button("🔍 분석 실행", type="primary", use_container_width=True):
    try:
        seg1 = sound.extract_part(start1, end1)
        seg2 = sound.extract_part(start2, end2)

        st.subheader("파형 비교")
        fig2 = make_subplots(rows=2, cols=1)
        fig2.add_trace(go.Scatter(x=seg1.xs(), y=seg1.values[0]), row=1, col=1)
        fig2.add_trace(go.Scatter(x=seg2.xs(), y=seg2.values[0]), row=2, col=1)
        st.plotly_chart(fig2, use_container_width=True)

        st.success("✅ 분석 완료!")
    except Exception as e:
        st.error(f"분석 오류: {e}")

st.caption("Powered by Praat (Parselmouth)")
