import html

import streamlit as st
from utils.ai_context import BASE_SYSTEM_PROMPT, build_context_system_message

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    OpenAI = None


SHOW_KEY = "show_ai"
MESSAGES_KEY = "messages"
ERROR_KEY = "weather_assistant_error"
DRAFT_KEY = "weather_assistant_draft"
DRAFT_CLEAR_KEY = "weather_assistant_clear_draft"
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def _init_assistant_state() -> None:
    st.session_state.setdefault(SHOW_KEY, False)
    if MESSAGES_KEY not in st.session_state:
        st.session_state[MESSAGES_KEY] = []
    st.session_state.setdefault(ERROR_KEY, "")
    if st.session_state.get(DRAFT_CLEAR_KEY, False):
        st.session_state[DRAFT_KEY] = ""
        st.session_state[DRAFT_CLEAR_KEY] = False
    st.session_state.setdefault(DRAFT_KEY, "")


@st.cache_resource(show_spinner=False)
def _get_openai_client(api_key: str):
    if OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def _inject_launcher_css() -> None:
    st.markdown(
        """
        <style>
        .assistant-launcher-anchor {
            display: none;
        }

        .assistant-launcher-meta {
            margin-top: 0.42rem;
            text-align: center;
            font-size: 0.69rem;
            line-height: 1.3;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(212, 198, 188, 0.62);
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
        div[role="dialog"]:has(.assistant-panel-anchor),
        div[role="dialog"]:has(.assistant-panel-anchor) *,
        div[role="dialog"]:has(.assistant-panel-anchor) *::before,
        div[role="dialog"]:has(.assistant-panel-anchor) *::after {
            box-sizing: border-box;
        }

        .assistant-panel-anchor,
        .assistant-footer-anchor,
        .assistant-close-anchor,
        .assistant-draft-anchor,
        .assistant-send-anchor,
        .assistant-tools-anchor,
        .assistant-mic-anchor {
            display: none;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) {
            width: min(400px, 92vw) !important;
            max-width: min(400px, 92vw) !important;
            margin: clamp(0.75rem, 3vh, 1.25rem) auto !important;
            z-index: 999999 !important;
            animation: assistant-dialog-fade 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        div[role="dialog"]:has(.assistant-panel-anchor) > div:first-child {
            padding: 0 !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [aria-label="dialog"] {
            --assistant-surface: rgba(14, 12, 12, 0.72);
            --assistant-surface-strong: rgba(22, 18, 18, 0.9);
            --assistant-border: rgba(255, 255, 255, 0.11);
            --assistant-border-soft: rgba(255, 255, 255, 0.06);
            --assistant-text: rgba(247, 241, 236, 0.96);
            --assistant-muted: rgba(201, 188, 181, 0.66);
            --assistant-glow: rgba(223, 90, 44, 0.32);
            --assistant-shadow: 0 24px 58px rgba(0, 0, 0, 0.48);
            display: flex;
            flex-direction: column;
            width: min(400px, 92vw) !important;
            height: min(72vh, 700px) !important;
            max-height: min(72vh, 700px) !important;
            margin: 0 auto;
            padding: 0 !important;
            border-radius: 24px !important;
            border: 1px solid var(--assistant-border) !important;
            background:
                radial-gradient(circle at 18% 88%, rgba(255, 118, 54, 0.12), transparent 30%),
                radial-gradient(circle at 70% 10%, rgba(135, 64, 40, 0.08), transparent 28%),
                linear-gradient(180deg, rgba(20, 17, 18, 0.82), rgba(10, 9, 10, 0.92)) !important;
            background-color: var(--assistant-surface) !important;
            box-shadow:
                var(--assistant-shadow),
                inset 0 1px 0 rgba(255, 255, 255, 0.09),
                inset 0 -1px 0 rgba(255, 255, 255, 0.03),
                0 0 0 1px rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(30px) saturate(125%);
            -webkit-backdrop-filter: blur(30px) saturate(125%);
            overflow: hidden;
            isolation: isolate;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [aria-label="dialog"] > div:first-child {
            display: none !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) h1,
        div[role="dialog"]:has(.assistant-panel-anchor) h2:not(.assistant-empty-title) {
            display: none !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0 !important;
        }

        div[role="dialog"]:has(.assistant-panel-anchor) [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        .assistant-shell {
            display: flex;
            flex-direction: column;
            height: 100%;
            min-height: 0;
            overflow: hidden;
        }

        .assistant-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 14px 16px 12px 16px;
            flex-shrink: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0));
            white-space: nowrap;
        }

        .assistant-topbar-copy {
            min-width: 0;
            overflow: hidden;
        }

        .assistant-topbar-title {
            margin: 0;
            color: rgba(248, 240, 234, 0.97);
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1.2;
            letter-spacing: 0.01em;
            white-space: nowrap;
        }

        .assistant-topbar-subtitle {
            margin: 0.18rem 0 0;
            color: rgba(201, 188, 181, 0.62);
            font-size: 0.71rem;
            line-height: 1.35;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .assistant-topbar-actions {
            display: inline-flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.34rem;
            flex-direction: row;
            flex-wrap: nowrap;
            white-space: nowrap;
        }

        .assistant-utility-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.72rem;
            height: 1.72rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.07);
            background: rgba(255, 255, 255, 0.025);
            color: rgba(236, 225, 218, 0.72);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            flex-shrink: 0;
        }

        .assistant-utility-icon svg {
            width: 0.76rem;
            height: 0.76rem;
            stroke: currentColor;
            fill: none;
            stroke-width: 1.7;
            stroke-linecap: round;
            stroke-linejoin: round;
        }

        div[data-testid="stHorizontalBlock"]:has(.assistant-close-anchor) {
            align-items: center !important;
            flex-wrap: nowrap !important;
            gap: 0.75rem !important;
        }

        div[data-testid="column"]:has(.assistant-close-anchor),
        div[data-testid="column"]:has(.assistant-topbar-title),
        div[data-testid="column"]:has(.assistant-utility-icon) {
            display: flex;
            align-items: center;
            min-width: 0;
        }

        div[data-testid="column"]:has(.assistant-close-anchor) > div,
        div[data-testid="column"]:has(.assistant-topbar-title) > div,
        div[data-testid="column"]:has(.assistant-utility-icon) > div {
            width: 100%;
            min-width: 0;
        }

        .assistant-body {
            display: flex;
            flex-direction: column;
            flex: 1 1 auto;
            min-height: 0;
            overflow: hidden;
        }

        .assistant-messages {
            flex: 1 1 auto;
            min-height: 0;
            overflow-y: auto;
            padding: 18px 18px 16px 18px;
            scroll-behavior: smooth;
        }

        .assistant-error {
            margin: 0 0 1rem;
            color: rgba(255, 201, 193, 0.88);
            font-size: 0.76rem;
            line-height: 1.45;
        }

        .assistant-message-list {
            display: flex;
            flex-direction: column;
            gap: 0.95rem;
            min-height: 100%;
            padding-bottom: 0.65rem;
        }

        .assistant-message-row {
            display: flex;
            width: 100%;
        }

        .assistant-message-row.user {
            justify-content: flex-end;
        }

        .assistant-message-row.assistant {
            justify-content: flex-start;
        }

        .assistant-message-bubble {
            max-width: min(76%, 260px);
            padding: 0.78rem 0.88rem;
            border-radius: 18px;
            color: rgba(240, 234, 229, 0.94);
            font-size: 0.82rem;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
            border: 1px solid rgba(255, 255, 255, 0.07);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.03),
                0 12px 22px rgba(0, 0, 0, 0.1);
        }

        .message-bubble-assistant {
            background: linear-gradient(180deg, rgba(35, 29, 28, 0.72), rgba(19, 16, 17, 0.74));
            border-top-left-radius: 12px;
        }

        .message-bubble-user {
            background: linear-gradient(180deg, rgba(58, 47, 41, 0.78), rgba(34, 28, 28, 0.78));
            border-color: rgba(255, 210, 190, 0.11);
            border-top-right-radius: 12px;
        }

        .assistant-role {
            display: block;
            margin-bottom: 0.32rem;
            color: rgba(190, 175, 167, 0.58);
            font-size: 0.62rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .assistant-empty-state {
            display: grid;
            place-items: center;
            flex: 1 1 auto;
            min-height: 100%;
            padding: clamp(3rem, 14vh, 7rem) 0 1rem;
        }

        .assistant-empty-copy {
            width: min(100%, 280px);
            text-align: center;
        }

        .assistant-empty-kicker {
            margin: 0 0 0.8rem;
            color: rgba(214, 198, 188, 0.48);
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }

        .assistant-empty-title {
            margin: 0 0 0.65rem;
            color: var(--assistant-text);
            font-size: clamp(1.28rem, 1.12rem + 0.62vw, 1.7rem);
            font-weight: 600;
            line-height: 1.08;
            letter-spacing: -0.03em;
        }

        .assistant-empty-text {
            margin: 0;
            color: var(--assistant-muted);
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .assistant-composer {
            flex-shrink: 0;
            padding: 14px 14px 16px 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            background:
                linear-gradient(180deg, rgba(18, 14, 15, 0.9), rgba(12, 10, 11, 0.96));
            overflow: visible;
        }

        .assistant-composer-card {
            width: 100%;
            padding: 0.55rem 0.6rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.09);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.03)),
                rgba(31, 26, 26, 0.62);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.04),
                inset 0 -1px 0 rgba(255, 255, 255, 0.02),
                0 18px 30px rgba(0, 0, 0, 0.18);
            backdrop-filter: blur(22px) saturate(118%);
            -webkit-backdrop-filter: blur(22px) saturate(118%);
            overflow: visible;
        }

        div[data-testid="stForm"]:has(.assistant-footer-anchor) {
            margin: 0;
            overflow: visible !important;
        }

        div[data-testid="stForm"] form:has(.assistant-footer-anchor) {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            overflow: visible !important;
        }

        div[data-testid="stForm"] form:has(.assistant-footer-anchor) > div:first-child,
        div[data-testid="stForm"]:has(.assistant-footer-anchor) [data-testid="stVerticalBlock"] {
            min-width: 0 !important;
            overflow: visible !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.assistant-draft-anchor) {
            align-items: center;
            gap: 0.55rem;
            background: transparent;
            min-width: 0;
            flex-wrap: nowrap !important;
            min-height: 48px;
        }

        div[data-testid="column"]:has(.assistant-send-anchor),
        div[data-testid="column"]:has(.assistant-tools-anchor),
        div[data-testid="column"]:has(.assistant-draft-anchor) {
            display: flex;
            align-items: center;
            min-width: 0;
        }

        div[data-testid="column"]:has(.assistant-send-anchor) > div,
        div[data-testid="column"]:has(.assistant-tools-anchor) > div,
        div[data-testid="column"]:has(.assistant-draft-anchor) > div {
            width: 100%;
            min-width: 0;
        }

        .assistant-tools-row {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            padding-left: 0.08rem;
            flex-direction: row;
            flex-wrap: nowrap;
        }

        .assistant-tool,
        .assistant-mic-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.15rem;
            height: 2.15rem;
            border-radius: 999px;
            color: rgba(228, 215, 207, 0.62);
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            flex-shrink: 0;
        }

        .assistant-tool svg,
        .assistant-mic-icon svg {
            width: 0.88rem;
            height: 0.88rem;
            stroke: currentColor;
            fill: none;
            stroke-width: 1.7;
            stroke-linecap: round;
            stroke-linejoin: round;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) label {
            display: none;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) {
            min-width: 0 !important;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) > div {
            min-width: 0 !important;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) [data-baseweb="base-input"] {
            min-height: 50px !important;
            align-items: center !important;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) input {
            min-height: 50px !important;
            height: 50px !important;
            border-radius: 16px !important;
            border: none !important;
            background: transparent !important;
            color: rgba(246, 239, 234, 0.98) !important;
            box-shadow: none !important;
            padding: 0 0.6rem !important;
            font-size: 0.89rem !important;
            line-height: 1.25 !important;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) input::placeholder {
            color: rgba(193, 178, 169, 0.58) !important;
            -webkit-text-fill-color: rgba(193, 178, 169, 0.58) !important;
            opacity: 1 !important;
        }

        div[data-testid="stTextInput"]:has(.assistant-draft-anchor) input:focus {
            box-shadow: none !important;
        }

        div.stButton > button:has(+ .assistant-send-anchor),
        div.stButton > button:has(+ .assistant-close-anchor) {
            white-space: nowrap !important;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        div.stButton > button:has(+ .assistant-send-anchor) {
            min-height: 2.7rem;
            width: 2.7rem;
            min-width: 2.7rem;
            padding: 0;
            border-radius: 999px !important;
            border: 1px solid rgba(255, 206, 187, 0.13) !important;
            background:
                radial-gradient(circle at 30% 30%, rgba(255, 173, 128, 0.18), transparent 55%),
                linear-gradient(180deg, rgba(66, 49, 43, 0.94), rgba(37, 29, 29, 0.96)) !important;
            color: rgba(252, 243, 236, 0.92) !important;
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.08),
                0 10px 18px rgba(0, 0, 0, 0.2),
                0 0 20px rgba(195, 73, 34, 0.1) !important;
        }

        div.stButton > button:has(+ .assistant-send-anchor):hover {
            border-color: rgba(255, 214, 193, 0.22) !important;
            background:
                radial-gradient(circle at 30% 30%, rgba(255, 192, 138, 0.22), transparent 55%),
                linear-gradient(180deg, rgba(79, 58, 48, 0.98), rgba(48, 37, 35, 0.98)) !important;
        }

        div.stButton > button:has(+ .assistant-close-anchor) {
            width: 2rem;
            min-width: 2rem;
            min-height: 2rem;
            padding: 0;
            border-radius: 999px;
            border: 1px solid rgba(255, 221, 210, 0.18) !important;
            background:
                radial-gradient(circle at 34% 34%, rgba(255, 186, 148, 0.88), rgba(145, 55, 34, 0.88)) !important;
            color: rgba(255, 246, 240, 0.96) !important;
            box-shadow:
                0 0 0 4px rgba(255, 255, 255, 0.02),
                0 8px 18px rgba(0, 0, 0, 0.18),
                0 0 20px rgba(202, 86, 47, 0.12) !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            line-height: 1 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            white-space: nowrap !important;
        }

        div.stButton > button:has(+ .assistant-close-anchor):hover {
            filter: brightness(1.05);
            transform: scale(1.03);
        }

        @keyframes assistant-dialog-fade {
            from {
                opacity: 0;
                transform: translateY(10px) scale(0.985);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @media (max-width: 900px) {
            div[role="dialog"]:has(.assistant-panel-anchor) {
                width: min(400px, 92vw) !important;
            }

            div[role="dialog"]:has(.assistant-panel-anchor) [aria-label="dialog"] {
                width: min(400px, 92vw) !important;
                height: min(72vh, 700px) !important;
                max-height: min(72vh, 700px) !important;
                border-radius: 22px !important;
            }

            .assistant-header {
                padding: 13px 14px 11px 14px;
            }

            .assistant-messages {
                padding: 16px 15px 14px 15px;
            }

            .assistant-composer {
                padding: 13px 12px 14px 12px;
            }

            .assistant-composer-card {
                padding: 0.5rem 0.55rem;
            }

            div[data-testid="stHorizontalBlock"]:has(.assistant-draft-anchor) {
                gap: 0.45rem;
            }

            .assistant-tools-row {
                gap: 0.22rem;
            }

            .assistant-tool,
            .assistant-mic-icon {
                width: 2.05rem;
                height: 2.05rem;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            div[role="dialog"]:has(.assistant-panel-anchor) {
                animation: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_api_messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        build_context_system_message(),
        *st.session_state[MESSAGES_KEY],
    ]


def _fetch_assistant_reply() -> None:
    st.session_state[ERROR_KEY] = ""

    if OpenAI is None:
        st.session_state[ERROR_KEY] = "Error connecting to AI service. Please try again."
        return

    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = _get_openai_client(api_key)
        if client is None:
            raise RuntimeError("OpenAI client unavailable")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=_build_api_messages(),
        )
        reply = response.choices[0].message.content or "I couldn't generate a response."
        st.session_state[MESSAGES_KEY].append({"role": "assistant", "content": reply})
    except Exception:
        st.session_state[ERROR_KEY] = "Error connecting to AI service. Please try again."


def _render_message_history() -> None:
    messages = st.session_state[MESSAGES_KEY]
    st.markdown('<div class="assistant-message-list">', unsafe_allow_html=True)
    if not messages:
        st.markdown(
            (
                '<div class="assistant-empty-state">'
                '<div class="assistant-empty-copy">'
                '<p class="assistant-empty-kicker">Weather Assistant</p>'
                '<h2 class="assistant-empty-title">Ask anything</h2>'
                '<p class="assistant-empty-text">Forecasts, hazards, local setup, and quick severe weather context are ready whenever you are.</p>'
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for idx, message in enumerate(messages):
        role_label = "You" if message["role"] == "user" else "Assistant"
        content = html.escape(message["content"])
        role_class = "user" if message["role"] == "user" else "assistant"
        bubble_class = "message-bubble-user" if message["role"] == "user" else "message-bubble-assistant"
        st.markdown(
            (
                f'<div class="assistant-message-row {role_class}" id="assistant-message-{idx}">'
                f'<div class="assistant-message-bubble {bubble_class}">'
                f'<span class="assistant-role">{role_label}</span>'
                f"{content}"
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_assistant_launcher() -> None:
    _init_assistant_state()
    _inject_launcher_css()

    if st.button("AI Weather Assistant", key="weather_assistant_launcher", use_container_width=True):
        st.session_state[SHOW_KEY] = True
        st.rerun()

    st.markdown(
        '<div class="assistant-launcher-meta">Beta disclaimer: experimental assistant output may be inaccurate.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="assistant-launcher-anchor"></div>', unsafe_allow_html=True)


dialog_api = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

if dialog_api is not None:
    try:
        _assistant_dialog_decorator = dialog_api("AI Weather Assistant", width="small")
    except TypeError:
        _assistant_dialog_decorator = dialog_api("AI Weather Assistant")

    @_assistant_dialog_decorator
    def _render_assistant_dialog() -> None:
        _init_assistant_state()
        _inject_dialog_css()
        st.markdown('<div class="assistant-panel-anchor"></div>', unsafe_allow_html=True)
        st.markdown('<div class="assistant-shell">', unsafe_allow_html=True)
        st.markdown('<div class="assistant-header">', unsafe_allow_html=True)

        topbar_left, topbar_center, topbar_right = st.columns([1, 6.8, 2.2], gap="small")
        with topbar_left:
            if st.button("×", key="weather_assistant_close_button"):
                st.session_state[SHOW_KEY] = False
                st.rerun()
            st.markdown('<div class="assistant-close-anchor"></div>', unsafe_allow_html=True)

        with topbar_center:
            st.markdown(
                (
                    '<div class="assistant-topbar-copy">'
                    '<p class="assistant-topbar-title">Weather Assistant</p>'
                    '<p class="assistant-topbar-subtitle">Live dashboard context, forecasts, hazards, and local weather questions.</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        with topbar_right:
            st.markdown(
                (
                    '<div class="assistant-topbar-actions" aria-hidden="true">'
                    '<span class="assistant-utility-icon">'
                    '<svg viewBox="0 0 24 24"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>'
                    "</span>"
                    '<span class="assistant-utility-icon">'
                    '<svg viewBox="0 0 24 24"><path d="M7 12h10"></path><path d="M12 7v10"></path></svg>'
                    "</span>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="assistant-body">', unsafe_allow_html=True)
        st.markdown('<div class="assistant-messages">', unsafe_allow_html=True)

        if st.session_state[ERROR_KEY]:
            st.markdown(
                f'<p class="assistant-error">{st.session_state[ERROR_KEY]}</p>',
                unsafe_allow_html=True,
            )

        _render_message_history()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        prompt = None
        st.markdown('<div class="assistant-composer">', unsafe_allow_html=True)
        st.markdown('<div class="assistant-composer-card">', unsafe_allow_html=True)

        with st.form(key="weather_assistant_form", clear_on_submit=False, border=False):
            tools_col, input_col, send_col = st.columns([1.25, 6.35, 0.9], gap="small")

            with tools_col:
                st.markdown(
                    (
                        '<div class="assistant-tools-row" aria-hidden="true">'
                        '<span class="assistant-tool">'
                        '<svg viewBox="0 0 24 24"><path d="M12 5v14"></path><path d="M5 12h14"></path></svg>'
                        "</span>"
                        '<span class="assistant-tool">'
                        '<svg viewBox="0 0 24 24"><path d="M7 12h10"></path><path d="M12 7v10"></path></svg>'
                        "</span>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="assistant-tools-anchor"></div>', unsafe_allow_html=True)

            with input_col:
                st.text_input(
                    "Message",
                    key=DRAFT_KEY,
                    placeholder="Ask anything",
                    label_visibility="collapsed",
                )
                st.markdown('<div class="assistant-draft-anchor"></div>', unsafe_allow_html=True)

            with send_col:
                submitted = st.form_submit_button("↑", use_container_width=True)
                st.markdown('<div class="assistant-send-anchor"></div>', unsafe_allow_html=True)

            st.markdown('<div class="assistant-footer-anchor"></div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            prompt = st.session_state.get(DRAFT_KEY, "").strip()
        if prompt:
            st.session_state[MESSAGES_KEY].append({"role": "user", "content": prompt})
            st.session_state[DRAFT_CLEAR_KEY] = True
            with st.spinner("Thinking..."):
                _fetch_assistant_reply()
            st.rerun()
else:
    def _render_assistant_dialog() -> None:
        return


def render_assistant_modal() -> None:
    _init_assistant_state()
    if st.session_state[SHOW_KEY]:
        _render_assistant_dialog()
