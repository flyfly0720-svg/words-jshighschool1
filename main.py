import streamlit as st
import parselmouth
import tempfile
import os

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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        sound = parselmouth.Sound(tmp_path)
        os.unlink(tmp_path)  # 사용 후 임시파일 삭제

else:  # 마이크 녹음
    audio_input = st.sidebar.audio_input("마이크로 녹음하기")
    if audio_input:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_input.read())
            tmp_path = tmp.name
        sound = parselmouth.Sound(tmp_path)
        os.unlink(tmp_path)

if sound is None:
    st.info("왼쪽 사이드바에서 음성 파일을 업로드하거나 녹음해주세요.")
    st.stop()
