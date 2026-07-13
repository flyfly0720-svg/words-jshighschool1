import streamlit as st
import parselmouth
import tempfile
import os
import io

# ====================== 오디오 입력 ======================
st.sidebar.header("1. 음성 파일 입력")

audio_source = st.sidebar.radio(
    "입력 방식 선택", 
    ["파일 업로드", "마이크 녹음"], 
    horizontal=True
)

sound = None

if audio_source == "파일 업로드":
    uploaded_file = st.sidebar.file_uploader("WAV 파일 업로드", type=["wav"])
    if uploaded_file:
        audio_bytes = uploaded_file.read()
        # BytesIO 방식 (가장 안정적)
        try:
            sound = parselmouth.Sound(io.BytesIO(audio_bytes))
        except:
            # BytesIO 실패 시 tempfile fallback
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            sound = parselmouth.Sound(tmp_path)
            os.unlink(tmp_path)

else:  # 마이크 녹음
    audio_input = st.sidebar.audio_input("🎤 마이크로 녹음하기 (최대 1분 권장)")
    if audio_input is not None:
        audio_bytes = audio_input.read()
        st.success(f"녹음 완료: {len(audio_bytes)/1024:.1f} KB")
        
        try:
            # 1순위: BytesIO
            sound = parselmouth.Sound(io.BytesIO(audio_bytes))
        except Exception as e:
            st.warning("BytesIO 실패 → tempfile 사용")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            sound = parselmouth.Sound(tmp_path)
            os.unlink(tmp_path)

if sound is None:
    st.info("왼쪽 사이드바에서 음성 파일을 업로드하거나 녹음해주세요.")
    st.stop()

# ====================== 나머지 코드는 그대로 ======================
duration = sound.xmax - sound.xmin
st.success(f"✅ 오디오 로드 완료 | 길이: {duration:.2f}초 | 샘플링 주파수: {sound.sampling_frequency} Hz")
