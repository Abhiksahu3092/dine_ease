"""
Streamlit UI for Restaurant Reservation AI Agent
"""

import streamlit as st
from agent.agent import RestaurantAgent
from llm.client import LLMClient


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Restaurant Reservation AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# Custom CSS Styling
# ============================================================================


def render_message(content: str):
    """Render message with special formatting for booking confirmations"""
    # Check if this is a booking confirmation
    if "BOOKING CONFIRMED" in content and "Booking ID:" in content:
        # Display as success box
        st.success("✅ Booking Confirmed!", icon="🎉")
        st.markdown(content)
    else:
        # Normal markdown rendering
        st.markdown(content)


def load_custom_css():
    """Load custom CSS for better UI."""
    st.markdown(
        """
        <style>
        /* Dark mode theme */
        :root {
            --bg-primary: #0e1117;
            --bg-secondary: #1a1d29;
            --bg-tertiary: #262730;
            --text-primary: #fafafa;
            --text-secondary: #b0b3b8;
            --accent-primary: #667eea;
            --accent-secondary: #764ba2;
            --border-color: #2d3139;
        }
        
        /* Force dark mode */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }
        
        /* Main container */
        .main {
            padding: 2rem;
            background-color: var(--bg-primary);
        }
        
        /* Header styling - Dark mode gradient */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .main-header p {
            font-size: 1.1rem;
            opacity: 0.95;
        }
        
        /* Chat message styling - Dark theme */
        .stChatMessage {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
        }
        
        /* Sidebar styling - Dark gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1d29 0%, #0e1117 100%);
            border-right: 1px solid var(--border-color);
        }
        
        [data-testid="stSidebar"] .element-container {
            color: var(--text-primary);
        }
        
        /* Button styling - Dark mode */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
        }
        
        /* Quick action chips */
        .quick-chip {
            display: inline-block;
            padding: 0.5rem 1rem;
            margin: 0.25rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .quick-chip:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
        }
        
        /* Stats cards - Dark theme */
        .stat-card {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            text-align: center;
            margin-bottom: 1rem;
            border: 1px solid var(--border-color);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }
        
        /* Feature cards - Dark theme */
        .feature-card {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--accent-primary);
        }
        
        .feature-card h4 {
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .feature-card p {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        /* Input styling - Dark mode */
        .stChatInput {
            border-radius: 10px;
        }
        
        .stChatInput textarea {
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        /* Markdown text in dark mode */
        .element-container {
            color: var(--text-primary);
        }
        
        /* Headers in dark mode */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
        }
        
        /* Booking confirmation box */
        .booking-confirmation {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
            border: 2px solid #34d399;
        }
        
        .booking-confirmation h3 {
            color: white !important;
            margin-bottom: 1rem;
        }
        
        .booking-confirmation code {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            color: white;
            font-weight: 600;
        }
        
        /* Lists in dark mode */
        ul, li, p {
            color: var(--text-secondary);
        }
        
        /* Divider in dark mode */
        hr {
            border-color: var(--border-color);
        }
        
        /* Warning/Info box - Dark mode */
        .warning-box {
            background: linear-gradient(135deg, #2d2416 0%, #1a1610 100%);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            color: var(--text-secondary);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        /* Chat avatars enhancement */
        .stChatMessage [data-testid="chatAvatarIcon"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Scrollbar styling for dark mode */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--bg-tertiary);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #667eea;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Session State Initialization
# ============================================================================


def initialize_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        # Create LLM client and agent
        llm_client = LLMClient()
        st.session_state.agent = RestaurantAgent(llm_client=llm_client)

    if "messages" not in st.session_state:
        # Initialize with agent's greeting
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": st.session_state.agent.get_initial_greeting(),
            }
        ]

    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = True

    if "total_suggestions" not in st.session_state:
        st.session_state.total_suggestions = 0

    if "total_searches" not in st.session_state:
        st.session_state.total_searches = 0


# ============================================================================
# Helper Functions
# ============================================================================


# ============================================================================
# Main UI
# ============================================================================


def main():
    """Main application UI."""

    # Load custom CSS
    load_custom_css()

    # Initialize session state
    initialize_session_state()

    # Header with gradient
    st.markdown(
        """
        <div class="main-header">
            <h1>🍽️ Restaurant Reservation AI</h1>
            <p>Your intelligent assistant for discovering and booking the best restaurants</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar with info and controls
    with st.sidebar:
        st.markdown("### 🎯 What I Can Do")

        # Feature cards
        st.markdown(
            """
            <div class="feature-card">
                <h4>🔍 Smart Search</h4>
                <p>Find restaurants by city, cuisine, price range, and more</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <h4>⭐ Personalized Recommendations</h4>
                <p>Get suggestions tailored to your preferences and occasions</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <h4>📅 Availability Check</h4>
                <p>Verify booking slots in real-time</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <h4>✅ Easy Reservations</h4>
                <p>Book your table with just a few messages</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Stats section
        st.markdown("### 📊 Session Stats")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">{st.session_state.agent.get_conversation_length()}</div>
                    <div class="stat-label">Messages</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">100</div>
                    <div class="stat-label">Restaurants</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.divider()

        # Controls
        st.markdown("### ⚙️ Controls")

        if st.button("🔄 Reset Chat", use_container_width=True, type="primary"):
            st.session_state.agent.reset_conversation()
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": st.session_state.agent.get_initial_greeting(),
                }
            ]
            st.session_state.total_suggestions = 0
            st.session_state.total_searches = 0
            st.rerun()

        st.divider()

        # Disclaimer
        st.markdown(
            """
            <div class="warning-box">
                <small><b>📌 Note:</b> Restaurant data is static and for demonstration purposes only.</small>
            </div>
        """,
            unsafe_allow_html=True,
        )

    # Main content area with two columns
    col_chat, col_help = st.columns([2, 1])

    with col_help:
        st.markdown("### 🎨 Features")
        st.markdown(
            """
        - 🤖 **AI-Powered** conversations
        - 🔍 **Smart** search filters
        - 📊 **Curated** restaurant database
        - ⚡ **Real-time** responses
        - 🎯 **Personalized** suggestions
        - 📅 **Easy** booking process
        """
        )

    with col_chat:
        # Chat container
        st.markdown("### 💬 Chat")

        # Display chat messages (filter out tool-related messages)
        for message in st.session_state.messages:
            # Only show user and assistant messages with actual content
            # Skip tool calls and tool results
            if message["role"] in ["user", "assistant"]:
                # Skip assistant messages that only contain tool calls
                if message["role"] == "assistant" and "tool_calls" in message:
                    continue
                # Skip empty messages
                if not message.get("content"):
                    continue

                with st.chat_message(
                    message["role"],
                    avatar="🤖" if message["role"] == "assistant" else "👤",
                ):
                    render_message(message["content"])

        # Chat input
        if prompt := st.chat_input("💭 Type your message here..."):
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            # Get agent response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        response = st.session_state.agent.process_message(prompt)
                    except Exception as e:
                        response = f"❌ Oops! Something went wrong: {str(e)}\n\nPlease try again or rephrase your question."
                render_message(response)

            # Add assistant response to chat
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Rerun to update the chat
            st.rerun()


# ============================================================================
# Run App
# ============================================================================

if __name__ == "__main__":
    main()
