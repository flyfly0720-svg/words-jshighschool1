if st.button("🔍 분석 실행", type="primary", use_container_width=True):
    try:
        seg1 = sound.extract_part(start1, end1)
        seg2 = sound.extract_part(start2, end2)

        st.subheader("📊 파형 비교")
        fig2 = make_subplots(rows=2, cols=1, subplot_titles=("구간 1", "구간 2"))
        fig2.add_trace(go.Scatter(x=seg1.xs(), y=seg1.values[0]), row=1, col=1)
        fig2.add_trace(go.Scatter(x=seg2.xs(), y=seg2.values[0]), row=2, col=1)
        st.plotly_chart(fig2, use_container_width=True)

        # ====================== 특징 비교 ======================
        st.subheader("📈 음향 특징 비교")
        
        def get_features(s):
            pitch = s.to_pitch()
            intensity = s.to_intensity()
            pvals = pitch.selected_array['frequency']
            pvals = pvals[pvals > 0]
            return {
                "지속시간(초)": round(s.xmax - s.xmin, 2),
                "평균 Pitch(Hz)": round(np.mean(pvals), 1) if len(pvals) > 0 else 0,
                "Pitch 범위(Hz)": round(np.ptp(pvals), 1) if len(pvals) > 0 else 0,
                "평균 Intensity(dB)": round(intensity.get_average(), 1)
            }

        f1 = get_features(seg1)
        f2 = get_features(seg2)
        df = pd.DataFrame([f1, f2], index=["구간 1", "구간 2"])
        st.dataframe(df, use_container_width=True)

        # ====================== 음운변동 분석 설명 ======================
        st.subheader("🔍 음운변동 분석 결과")
        
        duration_diff = abs(f1["지속시간(초)"] - f2["지속시간(초)"])
        pitch_diff = abs(f1["평균 Pitch(Hz)"] - f2["평균 Pitch(Hz)"])
        
        if duration_diff > 0.3:
            st.warning(f"⚠️ **지속시간 차이 {duration_diff:.2f}초** → 연음, 음절 축약, 또는 자음 삭제 등의 음운변동이 있을 수 있습니다.")
        elif pitch_diff > 25:
            st.warning(f"⚠️ **평균 피치 차이 {pitch_diff:.1f}Hz** → 억양이나 강조의 차이가 큽니다.")
        else:
            st.success("✅ 두 구간의 음향 특징이 비교적 유사합니다. 큰 음운변동은 관찰되지 않았습니다.")

        # 간단 설명
        with st.expander("📝 분석 설명 보기"):
            st.markdown("""
            - **지속시간**: 길이가 많이 다르면 음운변동(연음, 축약 등)이 발생했을 가능성이 높습니다.
            - **Pitch (높이)**: 평균 피치 차이가 크면 억양이나 감정 표현의 차이일 수 있습니다.
            - **Intensity (세기)**: 소리의 크기 차이로 발음 강세를 비교할 수 있습니다.
            """)

    except Exception as e:
        st.error(f"분석 중 오류: {e}")
