import streamlit as st


DRAFT_KEY = "weather_assistant_dialog_draft"
SUGGESTION_KEY = "weather_assistant_dialog_suggestion"

SUGGESTED_PROMPTS = [
    "What are today's main hazards?",
    "Explain the SPC outlook for my location",
    "How confident is the forecast?",
    "What setup should I watch this evening?",
]


def _inject_launcher_css() -> None:
    st.markdown(
        """
        <style>
        .assistant-launcher-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.assistant-launcher-anchor) > [data-testid="element-container"] {
            margin-bottom: 0;
        }

        div.stButton > button:has(+ .assistant-launcher-anchor) {
            min-height: 3rem;
            width: 100%;
            padding: 0.74rem 0.95rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.09) !important;
            background:
                linear-gradient(180deg, rgba(19, 24, 32, 0.78), rgba(12, 16, 23, 0.72)) !important;
            color: rgba(247, 249, 252, 0.96) !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.05),
                0 14px 28px rgba(0, 0, 0, 0.18),
                0 0 0 1px rgba(120, 143, 169, 0.04) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
        }

        div.stButton > button:has(+ .assistant-launcher-anchor):hover {
            transform: translateY(-1px);
            border-color: rgba(255, 255, 255, 0.14) !important;
            background:
                linear-gradient(180deg, rgba(22, 28, 37, 0.84), rgba(14, 18, 26, 0.78)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.07),
                0 18px 34px rgba(0, 0, 0, 0.22),
                0 0 24px rgba(112, 146, 186, 0.08) !important;
        }

        div.stButton > button:has(+ .assistant-launcher-anchor) p {
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            color: inherit !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_dialog_css() -> None:
    st.markdown(
        """
        <style>
        .assistant-panel-anchor {
            display: none;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) {
            width: min(95vw, 680px) !important;
            max-width: 680px !important;
            margin: clamp(1.25rem, 4vh, 2.75rem) auto !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) > div:first-child {
            padding: 0 !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [aria-label="dialog"] {
            display: flex;
            flex-direction: column;
            width: min(95vw, 680px) !important;
            min-height: 420px;
            max-height: 75vh;
            margin: 0 auto;
            padding: 14px 18px 14px !important;
            border-radius: 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background: linear-gradient(180deg, rgba(15, 19, 26, 0.96), rgba(10, 13, 18, 0.94)) !important;
            box-shadow: 0 28px 60px rgba(0, 0, 0, 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            overflow: hidden;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [aria-label="dialog"] > div:first-child {
            display: none !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) h1,
        div[role="dialog"]:has(.assistant-panel-anchor) h2:not(.assistant-title) {
            display: none !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0 !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        @keyframes assistantFadeIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .assistant-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            min-height: 46px;
            padding: 0 0 10px;
            flex-shrink: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .assistant-heading-wrap {
            min-width: 0;
        }

        .assistant-title-row {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            margin-bottom: 0.18rem;
        }

        .assistant-weather-glyph {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background:
                radial-gradient(circle at 32% 28%, rgba(228, 236, 245, 0.9), rgba(125, 154, 187, 0.22) 42%, rgba(21, 28, 39, 0.18) 100%);
            color: rgba(248, 250, 252, 0.92);
            font-size: 0.82rem;
        }

        .assistant-title {
            margin: 0;
            color: rgba(247, 249, 252, 0.98);
            font-size: clamp(1.02rem, 0.96rem + 0.35vw, 1.2rem);
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: -0.01em;
        }

        .assistant-subtitle {
            margin: 0;
            color: rgba(191, 201, 213, 0.82);
            font-size: 0.82rem;
            line-height: 1.35;
        }

        .assistant-close-note {
            color: rgba(150, 161, 174, 0.64);
            font-size: 0.72rem;
            line-height: 1.2;
            text-align: right;
            white-space: nowrap;
        }

        .assistant-conversation-shell {
            flex: 1 1 auto;
            min-height: 0;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            overflow: hidden;
        }

        .assistant-conversation-scroll {
            flex: 1 1 auto;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 0;
            overflow-y: auto;
            padding: 14px 2px 10px 0;
        }

        .assistant-conversation-scroll::-webkit-scrollbar {
            width: 8px;
        }

        .assistant-conversation-scroll::-webkit-scrollbar-track {
            background: transparent;
        }

        .assistant-conversation-scroll::-webkit-scrollbar-thumb {
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
        }

        .assistant-message-stack {
            display: flex;
            flex-direction: column;
            gap: 0.72rem;
        }

        .assistant-message {
            max-width: 84%;
            padding: 0.8rem 0.9rem;
            border-radius: 16px;
            font-size: 0.9rem;
            line-height: 1.45;
            color: rgba(242, 246, 249, 0.92);
        }

        .assistant-message.assistant {
            border: 1px solid rgba(255, 255, 255, 0.05);
            background:
                linear-gradient(180deg, rgba(27, 33, 42, 0.8), rgba(20, 25, 33, 0.74));
        }

        .assistant-message.user {
            margin-left: auto;
            border: 1px solid rgba(132, 155, 180, 0.09);
            background:
                linear-gradient(180deg, rgba(33, 41, 53, 0.78), rgba(25, 31, 41, 0.74));
            color: rgba(229, 238, 247, 0.9);
        }

        .assistant-suggestion-label {
            margin: 0 0 0.45rem;
            color: rgba(152, 163, 176, 0.72);
            font-size: 0.74rem;
            line-height: 1.2;
        }

        .assistant-composer-shell {
            flex-shrink: 0;
            padding-top: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        .assistant-composer-row {
            display: flex;
            align-items: flex-end;
            gap: 0.65rem;
            margin-top: 0.55rem;
        }

        .assistant-suggestions-shell {
            margin-top: 12px;
        }

        .assistant-composer-input-anchor,
        .assistant-chip-anchor,
        .assistant-send-anchor,
        .assistant-close-anchor {
            display: none;
        }

        div[data-testid="stHorizontalBlock"]:has(.assistant-chip-anchor) {
            gap: 0.4rem;
            align-items: stretch;
            flex-wrap: wrap;
        }

        div[data-testid="column"]:has(.assistant-chip-anchor) {
            flex: 0 0 auto;
            width: auto !important;
            min-width: 0 !important;
        }

        div.stButton > button:has(+ .assistant-chip-anchor) {
            min-height: 2rem;
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background: rgba(255, 255, 255, 0.04) !important;
            color: rgba(228, 236, 245, 0.84) !important;
            font-size: 0.74rem;
            font-weight: 500;
            box-shadow: none !important;
            transition: border-color 0.16s ease, background 0.16s ease, transform 0.16s ease;
        }

        div.stButton > button:has(+ .assistant-chip-anchor):hover {
            transform: translateY(-1px);
            border-color: rgba(255, 255, 255, 0.14) !important;
            background: rgba(255, 255, 255, 0.065) !important;
        }

        div[data-testid="stTextInput"]:has(.assistant-composer-input-anchor) input {
            min-height: 2.85rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.07);
            background: rgba(10, 14, 20, 0.82);
            color: rgba(244, 247, 250, 0.94);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }

        div[data-testid="stTextInput"]:has(.assistant-composer-input-anchor) label {
            display: none;
        }

        div[data-testid="stTextInput"]:has(.assistant-composer-input-anchor) input::placeholder {
            color: rgba(156, 167, 179, 0.62);
        }

        div.stButton > button:has(+ .assistant-send-anchor) {
            min-height: 2.85rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background:
                linear-gradient(180deg, rgba(49, 61, 77, 0.9), rgba(34, 43, 55, 0.88)) !important;
            color: rgba(244, 247, 250, 0.45) !important;
            font-weight: 600;
            box-shadow: none !important;
        }

        div.stButton > button:has(+ .assistant-close-anchor) {
            width: 2rem;
            min-width: 2rem;
            min-height: 2rem;
            padding: 0;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            background: rgba(255, 255, 255, 0.04) !important;
            color: rgba(214, 224, 236, 0.84) !important;
            box-shadow: none !important;
            transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
        }

        div.stButton > button:has(+ .assistant-close-anchor):hover {
            transform: translateY(-1px);
            border-color: rgba(255, 255, 255, 0.12) !important;
            background: rgba(255, 255, 255, 0.07) !important;
        }

        .assistant-composer-note {
            margin: 0.35rem 0 0;
            color: rgba(144, 155, 167, 0.64);
            font-size: 0.72rem;
            line-height: 1.3;
        }

        @media (max-width: 900px) {
            div[role="dialog"]:has(.assistant-panel-anchor) {
                width: 94vw !important;
            }

            div[role="dialog"]:has(.assistant-panel-anchor) [aria-label="dialog"] {
                width: 94vw !important;
                padding: 14px 16px !important;
            }

            .assistant-header {
                min-height: 44px;
            }

            .assistant-message {
                max-width: 94%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _apply_suggestion(prompt: str) -> None:
    st.session_state[DRAFT_KEY] = prompt
    st.session_state[SUGGESTION_KEY] = prompt


def _show_assistant_dialog() -> None:
    dialog_api = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog_api is None:
        return

    try:
        decorator = dialog_api("AI Weather Assistant", width="small")
    except TypeError:
        decorator = dialog_api("AI Weather Assistant")

    @decorator
    def _render_dialog() -> None:
        _inject_dialog_css()
        st.session_state.setdefault(DRAFT_KEY, "")
        st.session_state.setdefault(SUGGESTION_KEY, SUGGESTED_PROMPTS[0])
        st.markdown('<div class="assistant-panel-anchor"></div>', unsafe_allow_html=True)

        header_col, close_col = st.columns([7.2, 1], gap="small")
        with header_col:
            st.markdown(
                (
                    '<div class="assistant-header">'
                    '<div class="assistant-heading-wrap">'
                    '<div class="assistant-title-row">'
                    '<div class="assistant-weather-glyph">◌</div>'
                    '<h2 class="assistant-title">AI Weather Assistant</h2>'
                    '</div>'
                    '<p class="assistant-subtitle">Forecast help, setup guidance, and severe weather Q&amp;A</p>'
                    '</div>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )
        with close_col:
            if st.button("×", key="weather_assistant_dialog_close", help="Close"):
                st.rerun()
            st.markdown('<div class="assistant-close-anchor"></div>', unsafe_allow_html=True)

        st.markdown(
            (
                '<div class="assistant-conversation-shell">'
                '<div class="assistant-conversation-scroll">'
                '<div class="assistant-message-stack">'
                '<div class="assistant-message assistant">'
                'Ask about the forecast, severe setup, or what the latest outlook means for your location. '
                'This polished preview is ready for the AI backend when we wire it in.'
                '</div>'
                '<div class="assistant-message user">'
                'What are the main hazards I should pay attention to this evening?'
                '</div>'
                '<div class="assistant-message assistant">'
                'Once connected, this space will return a concise weather-focused answer with hazard context, '
                'forecast confidence, and setup guidance tailored to the dashboard state.'
                '</div>'
                '</div>'
                '</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="assistant-composer-shell">', unsafe_allow_html=True)
        st.markdown('<div class="assistant-suggestions-shell"><p class="assistant-suggestion-label">Try a prompt</p></div>', unsafe_allow_html=True)

        chip_cols = st.columns(len(SUGGESTED_PROMPTS), gap="small")
        for col, prompt in zip(chip_cols, SUGGESTED_PROMPTS):
            with col:
                st.button(
                    prompt,
                    key=f"assistant_suggestion_{prompt}",
                    use_container_width=True,
                    on_click=_apply_suggestion,
                    args=(prompt,),
                )
                st.markdown('<div class="assistant-chip-anchor"></div>', unsafe_allow_html=True)

        composer_col, send_col = st.columns([6.2, 1.15], gap="small")
        with composer_col:
            st.text_input(
                "Message",
                key=DRAFT_KEY,
                placeholder="Ask about the forecast, hazards, or what today means...",
            )
            st.markdown('<div class="assistant-composer-input-anchor"></div>', unsafe_allow_html=True)
        with send_col:
            st.button("Send", disabled=True, use_container_width=True, key="weather_assistant_dialog_send")
            st.markdown('<div class="assistant-send-anchor"></div>', unsafe_allow_html=True)

        st.markdown(
            '<p class="assistant-composer-note">Sending is disabled for now while the assistant backend is still being built.</p>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    _render_dialog()


def render_assistant() -> None:
    _inject_launcher_css()

    if st.button("AI Weather Assistant", key="weather_assistant_launcher", use_container_width=True):
        _show_assistant_dialog()
    st.markdown('<div class="assistant-launcher-anchor"></div>', unsafe_allow_html=True)
