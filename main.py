
import streamlit as st
import parselmouth
from parselmouth import praat
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import librosa
import pandas as pd

st.set_page_config(page_title="음성 비교 & 음운변동 분석기", layout="wide")
st.title("🎤 음성 비교 및 음운변동 분석 웹앱")
st.markdown("Praat(Parselmouth) 기반으로 **파형 비교**와 **음운변동 현상**을 분석합니다.")

# ====================== 오디오 입력 ======================
st.sidebar.header("1. 음성 파일 입력")

audio_source = st.sidebar.radio(
    "입력 방식 선택", 
    ["파일 업로드", "마이크 녹음"], 
    horizontal=True
)

sound = None
audio_bytes = None

if audio_source == "파일 업로드":
    uploaded_file = st.sidebar.file_uploader("WAV 파일 업로드", type=["wav"])
    if uploaded_file:
        audio_bytes = uploaded_file.read()
        sound = parselmouth.Sound(audio_bytes)
else:
    audio_input = st.sidebar.audio_input("마이크로 녹음하기")
    if audio_input:
        audio_bytes = audio_input.read()
        sound = parselmouth.Sound(audio_bytes)

if sound is None:
    st.info("왼쪽 사이드바에서 음성 파일을 업로드하거나 녹음해주세요.")
    st.stop()

# 기본 정보 표시
duration = sound.xmax - sound.xmin
st.success(f"오디오 로드 완료 | 길이: {duration:.2f}초 | 샘플링 주파수: {sound.sampling_frequency} Hz")

# ====================== 파형 시각화 ======================
st.subheader("전체 파형")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=sound.xs(), 
    y=sound.values[0], 
    mode='lines', 
    name='Waveform',
    line=dict(color='royalblue', width=1)
))
fig.update_layout(
    height=300,
    xaxis_title="Time (s)",
    yaxis_title="Amplitude",
    margin=dict(l=20, r=20, t=30, b=20)
)
st.plotly_chart(fig, use_container_width=True)

# ====================== 구간 선택 ======================
st.subheader("2. 비교할 두 구간 선택")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**구간 1**")
    seg1_start = st.number_input("시작 시간 (초)", min_value=0.0, max_value=duration, value=0.0, step=0.1, key="seg1_start")
    seg1_end = st.number_input("끝 시간 (초)", min_value=0.0, max_value=duration, value=min(5.0, duration), step=0.1, key="seg1_end")

with col2:
    st.markdown("**구간 2**")
    seg2_start = st.number_input("시작 시간 (초)", min_value=0.0, max_value=duration, value=min(5.0, duration), step=0.1, key="seg2_start")
    seg2_end = st.number_input("끝 시간 (초)", min_value=0.0, max_value=duration, value=min(10.0, duration), step=0.1, key="seg2_end")

if seg1_end <= seg1_start or seg2_end <= seg2_start:
    st.error("구간 끝 시간이 시작 시간보다 커야 합니다.")
    st.stop()

# ====================== 분석 실행 ======================
if st.button("🔍 파형 비교 및 음운변동 분석 실행", type="primary", use_container_width=True):
    
    # 구간 추출
    sound1 = sound.extract_part(seg1_start, seg1_end, preserve_times=True)
    sound2 = sound.extract_part(seg2_start, seg2_end, preserve_times=True)
    
    # ====================== 파형 비교 ======================
    st.subheader("📊 파형 비교 결과")
    
    # 정규화된 파형 비교
    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                         subplot_titles=("구간 1 파형 (정규화)", "구간 2 파형 (정규화)"))
    
    # 정규화
    norm1 = sound1.values[0] / np.max(np.abs(sound1.values[0]))
    norm2 = sound2.values[0] / np.max(np.abs(sound2.values[0]))
    
    fig2.add_trace(go.Scatter(x=sound1.xs(), y=norm1, name="구간 1", line=dict(color="#1f77b4")), row=1, col=1)
    fig2.add_trace(go.Scatter(x=sound2.xs(), y=norm2, name="구간 2", line=dict(color="#ff7f0e")), row=2, col=1)
    
    fig2.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig2, use_container_width=True)
    
    # ====================== 음향 특징 비교 ======================
    st.subheader("📈 음향 특징 비교 (음운변동 분석)")
    
    def get_acoustic_features(snd):
        pitch = snd.to_pitch()
        intensity = snd.to_intensity()
        
        # Pitch
        pitch_values = pitch.selected_array['frequency']
        pitch_values = pitch_values[pitch_values > 0]  # 무성음 제거
        
        return {
            "지속시간 (초)": snd.xmax - snd.xmin,
            "평균 Pitch (Hz)": np.mean(pitch_values) if len(pitch_values) > 0 else 0,
            "Pitch 범위 (Hz)": np.ptp(pitch_values) if len(pitch_values) > 0 else 0,
            "평균 Intensity (dB)": intensity.get_average(),
        }
    
    feat1 = get_acoustic_features(sound1)
    feat2 = get_acoustic_features(sound2)
    
    df = pd.DataFrame([feat1, feat2], index=["구간 1", "구간 2"])
    st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
    
    # ====================== 음운변동 판단 ======================
    st.subheader("🔍 음운변동 현상 분석 결과")
    
    duration_diff = abs(feat1["지속시간 (초)"] - feat2["지속시간 (초)"])
    pitch_diff = abs(feat1["평균 Pitch (Hz)"] - feat2["평균 Pitch (Hz)"])
    
    analysis_result = []
    
    if duration_diff > 0.3:
        analysis_result.append("⚠️ **지속시간 차이 큼** → 연음(linking) 또는 음절 축약/삭제 가능성")
    if pitch_diff > 30:
        analysis_result.append("⚠️ **평균 피치 차이 큼** → 억양 변동 또는 강조 차이")
    if feat1["지속시간 (초)"] < feat2["지속시간 (초)"] * 0.7:
        analysis_result.append("⚠️ **구간 1이 현저히 짧음** → 자음동화 또는 모음 축약 의심")
    
    if analysis_result:
        for msg in analysis_result:
            st.warning(msg)
    else:
        st.success("✅ 두 구간의 음향 특징이 비교적 유사합니다. 큰 음운변동은 감지되지 않았습니다.")
    
    # 상세 해석
    with st.expander("상세 분석 설명 보기"):
        st.markdown("""
        - **지속시간 차이**: 한국어에서 연음, 자음동화, 모음 탈락 등이 발생하면 길이가 크게 달라집니다.
        - **Pitch 차이**: 억양, 강조, 의문/평서문 차이에서 나타납니다.
        - 실제 음운변동 판단은 **문맥 + 청취**와 함께 보는 것이 가장 정확합니다.
        """)

st.caption("Powered by Parselmouth (Praat) + Streamlit | 개발자: 재원님을 위해 제작")
