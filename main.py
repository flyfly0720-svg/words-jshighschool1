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
st.caption("파일 첨부 오류 해결 버전")

# 세션 상태 초기화
if "sound" not in st.session_state:
    st.session_state.sound = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# ====================== 입력 (form 사용으로 안정화) ======================
with st.form("audio_form"):
    st.subheader("음성 입력")
    mode = st.radio("입력 방식", ["파일 업로드", "마이크 녹음"], horizontal=True, key="mode")
    
    if mode == "파일 업로드":
        uploaded = st.file_uploader("WAV 파일", type=["wav"], key="uploader")
        submitted = st.form_submit_button("업로드")
        if submitted and uploaded:
            st.session_state.audio_bytes = uploaded.read()
            st.success("파일 업로드 완료")
    else:
        rec = st.audio_input("🎤 마이크 녹음", key="recorder")
        submitted = st.form_submit_button("녹음 완료")
        if submitted and rec:
            st.session_state.audio_bytes = rec.read()
            st.success("녹음 완료")

# ====================== 로드 ======================
if st.session_state.audio_bytes and st.session_state.sound is None:
    try:
        with st.spinner("로드 중..."):
            data, sr = sf.read(io.BytesIO(st.session_state.audio_bytes))
            st.session_state.sound = parselmouth.Sound(
                values=data.T if data.ndim > 1 else data.reshape(1, -1),
                sampling_frequency=sr
            )
        st.success(f"✅ 로드 성공 | 길이: {st.session_state.sound.xmax - st.session_state.sound.xmin:.2f}초")
    except Exception as e:
        st.error(f"로드 실패: {e}")

sound = st.session_state.sound

if sound is None:
    st.info("👈 위 폼에서 음성을 입력하세요.")
    st.stop()

# ====================== 파형 ======================
st.subheader("전체 파형")
fig = go.Figure(go.Scatter(x=sound.xs(), y=sound.values[0], mode='lines'))
fig.update_layout(height=300, xaxis_title="시간 (초)")
st.plotly_chart(fig, use_container_width=True, key="main_wave")

# ====================== 구간 선택 ======================
st.subheader("두 구간 선택")
c1, c2 = st.columns(2)
with c1:
    st.write("**구간 1**")
    start1 = st.number_input("시작 (초)", 0.0, float(sound.xmax), 0.0, 0.1, key="start1")
    end1 = st.number_input("끝 (초)", start1, float(sound.xmax), min(5.0, sound.xmax), 0.1, key="end1")
with c2:
    st.write("**구간 2**")
    start2 = st.number_input("시작 (초)", 0.0, float(sound.xmax), min(5.0, sound.xmax), 0.1, key="start2")
    end2 = st.number_input("끝 (초)", start2, float(sound.xmax), min(10.0, sound.xmax), 0.1, key="end2")

# ====================== 분석 ======================
if st.button("🔍 분석 실행", type="primary", use_container_width=True):
    try:
        seg1 = sound.extract_part(start1, end1)
        seg2 = sound.extract_part(start2, end2)

        st.subheader("📊 파형 비교")
        fig2 = make_subplots(rows=2, cols=1, subplot_titles=("구간 1", "구간 2"))
        fig2.add_trace(go.Scatter(x=seg1.xs(), y=seg1.values[0]), row=1, col=1)
        fig2.add_trace(go.Scatter(x=seg2.xs(), y=seg2.values[0]), row=2, col=1)
        st.plotly_chart(fig2, use_container_width=True)

        st.success("✅ 분석 완료!")
    except Exception as e:
        st.error(f"분석 오류: {e}")

st.caption("Powered by Praat (Parselmouth)")
