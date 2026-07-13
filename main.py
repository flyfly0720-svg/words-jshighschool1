import streamlit as st
import parselmouth
import tempfile
import os
import io
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="음성 비교 & 음운변동 분석기", layout="wide")

@st.cache_data
def load_sound(audio_bytes):
    """오디오 바이트를 안전하게 Parselmouth Sound로 변환 (캐싱 적용)"""
    try:
        return parselmouth.Sound(io.BytesIO(audio_bytes))
    except:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        sound = parselmouth.Sound(tmp_path)
        os.unlink(tmp_path)
        return sound

st.title("🎤 Praat 기반 음성 비교 & 음운변동 분석기")
st.markdown("**파일 업로드 또는 실시간 녹음** 후 두 구간을 비교하고 음운변동을 분석합니다.")

# ====================== 사이드바 입력 ======================
st.sidebar.header("1. 음성 입력")

audio_source = st.sidebar.radio("입력 방식", ["파일 업로드", "마이크 녹음"], horizontal=True)

sound = None
audio_bytes = None

if audio_source == "파일 업로드":
    uploaded_file = st.sidebar.file_uploader("WAV 파일 선택", type=["wav"])
    if uploaded_file:
        audio_bytes = uploaded_file.read()
else:
    audio_input = st.sidebar.audio_input("🎤 마이크로 녹음하기")
    if audio_input:
        audio_bytes = audio_input.read()

if audio_bytes:
    with st.spinner("음성 파일 처리 중..."):
        sound = load_sound(audio_bytes)
    st.success(f"✅ 로드 완료 | 길이: {sound.xmax - sound.xmin:.2f}초")

if sound is None:
    st.info("👈 사이드바에서 파일을 업로드하거나 녹음해주세요.")
    st.stop()

# ====================== 전체 파형 ======================
st.subheader("📊 전체 파형")
fig = go.Figure()
fig.add_trace(go.Scatter(x=sound.xs(), y=sound.values[0], mode='lines', line=dict(color='royalblue')))
fig.update_layout(height=250, xaxis_title="시간 (초)", yaxis_title="진폭")
st.plotly_chart(fig, use_container_width=True)

# ====================== 구간 선택 ======================
st.subheader("2. 비교할 두 구간 선택")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**구간 1**")
    s1_start = st.number_input("시작 (초)", 0.0, float(sound.xmax), 0.0, 0.1, key="s1s")
    s1_end = st.number_input("끝 (초)", 0.0, float(sound.xmax), min(5.0, sound.xmax), 0.1, key="s1e")

with col2:
    st.markdown("**구간 2**")
    s2_start = st.number_input("시작 (초)", 0.0, float(sound.xmax), min(5.0, sound.xmax), 0.1, key="s2s")
    s2_end = st.number_input("끝 (초)", 0.0, float(sound.xmax), min(10.0, sound.xmax), 0.1, key="s2e")

if s1_end <= s1_start or s2_end <= s2_start:
    st.error("구간 끝 시간이 시작 시간보다 커야 합니다.")
    st.stop()

# ====================== 분석 버튼 ======================
if st.button("🔍 파형 비교 & 음운변동 분석 실행", type="primary", use_container_width=True):
    with st.spinner("분석 중..."):
        seg1 = sound.extract_part(s1_start, s1_end, preserve_times=True)
        seg2 = sound.extract_part(s2_start, s2_end, preserve_times=True)

        # 파형 비교
        st.subheader("📊 파형 비교 (정규화)")
        fig2 = make_subplots(rows=2, cols=1, subplot_titles=("구간 1", "구간 2"))
        fig2.add_trace(go.Scatter(x=seg1.xs(), y=seg1.values[0]/np.max(np.abs(seg1.values[0])), name="구간1"), row=1, col=1)
        fig2.add_trace(go.Scatter(x=seg2.xs(), y=seg2.values[0]/np.max(np.abs(seg2.values[0])), name="구간2"), row=2, col=1)
        fig2.update_layout(height=500)
        st.plotly_chart(fig2, use_container_width=True)

        # 특징 비교
        st.subheader("📈 음향 특징 비교")
        def get_features(s):
            pitch = s.to_pitch()
            intensity = s.to_intensity()
            pvals = pitch.selected_array['frequency']
            pvals = pvals[pvals > 0]
            return {
                "지속시간(초)": s.xmax - s.xmin,
                "평균 Pitch(Hz)": round(np.mean(pvals), 1) if len(pvals)>0 else 0,
                "Pitch 범위(Hz)": round(np.ptp(pvals), 1) if len(pvals)>0 else 0,
                "평균 Intensity(dB)": round(intensity.get_average(), 1)
            }

        f1 = get_features(seg1)
        f2 = get_features(seg2)
        df = pd.DataFrame([f1, f2], index=["구간 1", "구간 2"])
        st.dataframe(df, use_container_width=True)

        # 음운변동 판단
        st.subheader("🔍 음운변동 분석")
        if abs(f1["지속시간(초)"] - f2["지속시간(초)"]) > 0.3:
            st.warning("⚠️ 지속시간 차이가 큽니다 → 연음, 축약, 삭제 등의 음운변동 가능성")
        elif abs(f1["평균 Pitch(Hz)"] - f2["평균 Pitch(Hz)"]) > 25:
            st.warning("⚠️ 피치 차이가 큽니다 → 억양이나 강조 차이")
        else:
            st.success("✅ 두 구간이 비교적 유사합니다. 큰 음운변동은 감지되지 않았습니다.")

st.caption("Powered by Praat (Parselmouth) + Streamlit")
