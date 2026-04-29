# ======================
# FLASHCARDS PRO v8.8 ANKI STYLE
# ======================
if mode == "Flashcards":
    st.markdown("## 🧠 Flashcards PRO")

    df = load_words()

    if len(df) == 0:
        st.warning("No words loaded")

    else:
        today_str = str(date.today())

        # ----------------------
        # STUDY MODE
        # ----------------------
        study_mode = st.radio(
            "Study Mode",
            ["Serial", "Random", "Due Today", "Hard", "Smart Mix"],
            horizontal=True
        )

        df_filtered = df.copy()

        if study_mode == "Due Today":
            df_filtered = df[df["next_review"].astype(str) <= today_str]

        elif study_mode == "Hard":
            df_filtered = df[df["difficulty"].astype(str).str.lower() == "hard"]

        elif study_mode == "Random":
            df_filtered = df.sample(frac=1).reset_index(drop=True)

        elif study_mode == "Smart Mix":
            due = df[df["next_review"].astype(str) <= today_str]
            hard = df[df["difficulty"].astype(str).str.lower() == "hard"]
            rand = df.sample(min(5, len(df)))
            df_filtered = pd.concat([due, hard, rand]).drop_duplicates()
            df_filtered = df_filtered.sample(frac=1).reset_index(drop=True)

        else:
            df_filtered = df.reset_index(drop=True)

        if len(df_filtered) == 0:
            st.warning("No cards available in this mode")

        else:
            if "i" not in st.session_state or st.session_state.i >= len(df_filtered):
                st.session_state.i = 0

            i = st.session_state.i
            row = df_filtered.iloc[i]

            # ----------------------
            # PROGRESS
            # ----------------------
            st.caption(f"Card {i+1} / {len(df_filtered)}")
            progress = (i + 1) / len(df_filtered)
            st.progress(progress)

            # ----------------------
            # WORD CARD UI
            # ----------------------
            st.markdown(f"""
            <div style="
            padding:20px;
            border-radius:15px;
            background: linear-gradient(135deg,#4facfe,#00f2fe);
            text-align:center;
            color:white;
            font-size:34px;
            font-weight:bold;
            margin-bottom:10px;">
            {row['word']}
            </div>
            """, unsafe_allow_html=True)

            # difficulty badge
            difficulty = str(row["difficulty"]).lower()
            if difficulty == "hard":
                badge = "🔴 Hard"
            elif difficulty == "easy":
                badge = "🟢 Easy"
            else:
                badge = "🟡 Medium"

            st.markdown(f"**Difficulty:** {badge}")

            # ----------------------
            # SHOW ANSWER
            # ----------------------
            if st.button("👀 Show Answer"):
                st.success(row["translation"])
                st.write(f"**Lemma:** {row['lemma']}")
                st.write(f"**POS:** {row['pos']}")
                st.info(row["sentence"])

            # ----------------------
            # BUTTONS
            # ----------------------
            col1, col2, col3, col4, col5 = st.columns(5)

            def save_updated(updated):
                full = load_words()
                idx = full.index[full["word"] == row["word"]][0]
                for k in updated.index:
                    full.at[idx, k] = updated[k]
                save_words(full)

            # AGAIN
            if col1.button("❌ Again"):
                updated = row.copy()
                updated["interval"] = 1
                updated["ease"] = max(1.3, float(row["ease"]) - 0.2)
                updated["repetitions"] = 0
                updated["next_review"] = str(date.today() + timedelta(days=1))
                updated["difficulty"] = "hard"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            # HARD
            if col2.button("😬 Hard"):
                updated = row.copy()
                updated["interval"] = max(1, int(float(row["interval"])) + 1)
                updated["ease"] = max(1.3, float(row["ease"]) - 0.05)
                updated["repetitions"] = int(row["repetitions"]) + 1
                updated["next_review"] = str(date.today() + timedelta(days=int(updated["interval"])))
                updated["difficulty"] = "hard"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            # GOOD
            if col3.button("🙂 Good"):
                updated = row.copy()
                updated["interval"] = max(1, int(float(row["interval"]) * float(row["ease"])))
                updated["repetitions"] = int(row["repetitions"]) + 1
                updated["next_review"] = str(date.today() + timedelta(days=int(updated["interval"])))
                updated["difficulty"] = "medium"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            # EASY
            if col4.button("😎 Easy"):
                updated = row.copy()
                updated["ease"] = float(row["ease"]) + 0.15
                updated["interval"] = max(1, int(float(row["interval"]) * float(updated["ease"])))
                updated["repetitions"] = int(row["repetitions"]) + 1
                updated["next_review"] = str(date.today() + timedelta(days=int(updated["interval"])))
                updated["difficulty"] = "easy"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            # HARD TOGGLE
            if col5.button("🔥 Toggle"):
                full = load_words()
                idx = full.index[full["word"] == row["word"]][0]
                current = str(full.at[idx, "difficulty"]).lower()
                if current == "hard":
                    full.at[idx, "difficulty"] = "medium"
                    st.toast("Removed Hard")
                else:
                    full.at[idx, "difficulty"] = "hard"
                    st.toast("Marked Hard")
                save_words(full)
                st.rerun()
