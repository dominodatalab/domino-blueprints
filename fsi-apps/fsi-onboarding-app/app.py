"""
FSI Domino Onboarding Application
Streamlit app with Domino theming for personalized onboarding pathways
"""

import streamlit as st
import os
from config.onboarding_data import (
    ORGANIZATIONS,
    ROLE_DEFINITIONS,
    COMMON_DOCS,
    LEARNING_PATHS,
    FSI_USE_CASES,
    BEST_PRACTICES,
    SUPPORT_INFO,
    ROLE_TECH_STACK
)

# Page configuration
st.set_page_config(
    page_title="Domino FSI Onboarding",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Domino Design System Theme
DOMINO_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* ========== DOMINO DESIGN SYSTEM ========== */
    /* Base typography - Inter font family */
    * {
        font-family: 'Inter', 'Lato', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }

    /* Color tokens from Domino Design System */
    :root {
        --domino-primary: #543FDE;
        --domino-primary-hover: #3B23D1;
        --domino-primary-active: #311EAE;
        --domino-text: #2E2E38;
        --domino-text-secondary: #65657B;
        --domino-text-tertiary: #8F8FA3;
        --domino-success: #28A464;
        --domino-warning: #CCB718;
        --domino-error: #C20A29;
        --domino-info: #0070CC;
        --domino-bg: #FFFFFF;
        --domino-bg-layout: #FAFAFA;
        --domino-border: #E0E0E0;
        --domino-border-hover: #C0C0C0;
        --domino-radius: 4px;
        --domino-radius-lg: 8px;
    }

    /* ========== SIDEBAR STYLING ========== */
    /* Dark header matching Domino nav bar (44px height, #2E2E38 background) */
    .sidebar-header {
        background: #2E2E38;
        padding: 11px 16px;
        margin: -1rem -1rem 1.5rem -1rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        display: flex;
        align-items: center;
        gap: 12px;
        min-height: 44px;
    }
    .sidebar-logo-img {
        height: 32px;
        width: auto;
    }
    .sidebar-logo {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 700;
        display: block;
        letter-spacing: 0.01em;
        line-height: 1.2;
    }
    .sidebar-subtitle {
        color: #8F8FA3;
        font-size: 12px;
        display: block;
        margin-top: 2px;
    }

    /* ========== CARD COMPONENTS ========== */
    .card {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .card:hover {
        border-color: #C0C0C0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #2E2E38;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .card-subtitle {
        font-size: 14px;
        color: #65657B;
        margin-bottom: 12px;
        line-height: 1.6;
    }
    .card p {
        font-size: 13px;
        color: #65657B;
        margin: 6px 0;
    }
    .card strong {
        color: #2E2E38;
        font-weight: 600;
    }

    /* ========== BADGE COMPONENTS ========== */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
        line-height: 1.2;
    }
    /* Difficulty level badges */
    .badge-beginner      { background: #E8F5EE; color: #28A464; border: 1px solid #C8E8DA; }
    .badge-intermediate  { background: #FFF9E6; color: #A08C00; border: 1px solid #F5EDCC; }
    .badge-advanced      { background: #FDECEA; color: #C20A29; border: 1px solid #F5D4D0; }

    /* Content type badges */
    .badge-lab           { background: #EEEBFB; color: #543FDE; border: 1px solid #DBD5F5; }
    .badge-documentation { background: #E6F3FC; color: #0070CC; border: 1px solid #CCE5F5; }
    .badge-video         { background: #FDE8F3; color: #C21B7C; border: 1px solid #F5D4E8; }
    .badge-workshop      { background: #E8F5EE; color: #28A464; border: 1px solid #C8E8DA; }

    /* ========== STREAMLIT COMPONENT OVERRIDES ========== */
    /* Better button styling */
    .stButton > button {
        border-radius: 4px !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        box-shadow: 0 2px 4px rgba(84, 63, 222, 0.15) !important;
    }

    /* Info/Success/Warning/Error boxes */
    .stAlert {
        border-radius: 4px !important;
        border-left-width: 4px !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500 !important;
        border-radius: 4px !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 600 !important;
        color: #2E2E38 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #65657B !important;
        font-weight: 500 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        border-radius: 4px 4px 0 0;
    }

    /* Radio buttons */
    .stRadio > label {
        font-weight: 500 !important;
        color: #2E2E38 !important;
    }

    /* ========== TYPOGRAPHY IMPROVEMENTS ========== */
    h1, h2, h3, h4, h5, h6 {
        color: #2E2E38 !important;
        font-weight: 600 !important;
    }

    h1 { font-size: 32px !important; margin-bottom: 16px !important; }
    h2 { font-size: 24px !important; margin-bottom: 12px !important; }
    h3 { font-size: 18px !important; margin-bottom: 10px !important; }

    p, li {
        color: #2E2E38 !important;
        line-height: 1.6 !important;
    }

    /* Footer styling */
    .footer {
        text-align: center;
        color: #8F8FA3;
        font-size: 13px;
        padding: 20px 0;
        border-top: 1px solid #E0E0E0;
        margin-top: 40px;
    }
</style>
"""

# Get user information from Domino environment
def get_user_name():
    """Get user's name from Domino environment variables or default"""
    # Try to get from Domino environment variable
    domino_user = os.environ.get('DOMINO_STARTING_USERNAME', '')
    if domino_user:
        # Format username nicely (e.g., "john_doe" -> "John Doe")
        return ' '.join(word.capitalize() for word in domino_user.replace('_', ' ').replace('.', ' ').split())
    # Fallback to generic greeting
    return None

st.markdown(DOMINO_CSS, unsafe_allow_html=True)

# Initialize session state
if 'selected_org' not in st.session_state:
    st.session_state.selected_org = None
if 'selected_role' not in st.session_state:
    st.session_state.selected_role = None
if 'onboarding_step' not in st.session_state:
    st.session_state.onboarding_step = 1
if 'user_name' not in st.session_state:
    st.session_state.user_name = get_user_name()

# Sidebar Navigation
with st.sidebar:
    # SVG logo as data URI for better performance
    logo_svg = """<svg width="90" height="40" viewBox="0 0 90 40" fill="none" xmlns="http://www.w3.org/2000/svg"><g clip-path="url(#clip0_3120_3604)"><path d="M14.5295 16.3142C14.593 16.5028 14.7259 16.6568 14.903 16.7454C15.0088 16.7973 15.1224 16.8243 15.236 16.8243C15.3149 16.8243 15.3958 16.8108 15.4728 16.7858L18.9783 15.6173C19.3691 15.4883 19.5789 15.0648 19.4499 14.6741C19.3209 14.2833 18.8955 14.0734 18.5066 14.2024L15.0011 15.3709C14.6123 15.4999 14.4005 15.9234 14.5295 16.3142Z" fill="white"/><path d="M15.4128 24.2335C15.5014 24.0546 15.5168 23.8543 15.4532 23.6637C15.3243 23.2749 14.9008 23.0631 14.51 23.1921L11.0045 24.3606C10.8158 24.4242 10.6618 24.5569 10.5733 24.7341C10.4847 24.9112 10.4693 25.1133 10.5329 25.3038C10.6368 25.6157 10.9275 25.814 11.2394 25.814C11.3183 25.814 11.3972 25.8025 11.4742 25.7756L14.9797 24.607C15.1683 24.5435 15.3223 24.4107 15.4109 24.2335H15.4128Z" fill="white"/><path d="M12.0651 17.7176C12.171 17.7715 12.2846 17.7965 12.3962 17.7965C12.6696 17.7965 12.9333 17.6464 13.0642 17.3846L14.7159 14.0793C14.8044 13.9022 14.8198 13.7001 14.7563 13.5095C14.6928 13.3208 14.56 13.1668 14.3829 13.0783C14.0152 12.8954 13.5667 13.0436 13.3838 13.4113L11.7321 16.7166C11.5492 17.0843 11.6975 17.5328 12.0651 17.7157V17.7176Z" fill="white"/><path d="M17.9155 22.2603C17.7383 22.1718 17.5343 22.1564 17.3456 22.2199C17.157 22.2834 17.003 22.4162 16.9144 22.5933L15.2628 25.8986C15.1742 26.0757 15.1588 26.2778 15.2223 26.4684C15.2859 26.659 15.4187 26.8111 15.5958 26.8996C15.7017 26.9516 15.8133 26.9785 15.9288 26.9785C16.0077 26.9785 16.0886 26.965 16.1656 26.94C16.3542 26.8765 16.5082 26.7437 16.5968 26.5665L18.2485 23.2613C18.337 23.0842 18.3524 22.8821 18.2889 22.6915C18.2254 22.5029 18.0925 22.3489 17.9155 22.2603Z" fill="white"/><path d="M10.3733 19.9796C10.4772 20.2915 10.7679 20.4898 11.0817 20.4898C11.1587 20.4898 11.2395 20.4782 11.3166 20.4513C11.7054 20.3223 11.9172 19.8988 11.7882 19.508L10.6197 16.0026C10.4907 15.6137 10.0672 15.4 9.67643 15.5309C9.28757 15.6599 9.07582 16.0834 9.2048 16.4742L10.3733 19.9796Z" fill="white"/><path d="M19.6075 19.9987C19.4785 19.6079 19.0549 19.3981 18.6641 19.5271C18.4755 19.5906 18.3215 19.7234 18.233 19.9005C18.1444 20.0776 18.129 20.2797 18.1926 20.4703L19.361 23.9758C19.465 24.2877 19.7557 24.486 20.0675 24.486C20.1465 24.486 20.2254 24.4744 20.3024 24.4474C20.6912 24.3184 20.903 23.8949 20.774 23.5042L19.6055 19.9987H19.6075Z" fill="white"/><path d="M12.052 23.3272C12.1309 23.3272 12.2117 23.3137 12.2887 23.2886C12.4774 23.2251 12.6314 23.0923 12.72 22.9152C12.8085 22.7381 12.8239 22.5359 12.7604 22.3454C12.6969 22.1567 12.564 22.0027 12.3869 21.9142L9.08166 20.2625C8.71398 20.0796 8.26545 20.2278 8.08258 20.5955C7.99403 20.7745 7.97863 20.9747 8.04215 21.1653C8.10568 21.354 8.2385 21.508 8.41561 21.5965L11.7209 23.2482C11.8267 23.3002 11.9403 23.3272 12.0539 23.3272H12.052Z" fill="white"/><path d="M21.9405 18.8151C21.8771 18.6265 21.7443 18.4725 21.5671 18.3839L18.2618 16.7323C17.8942 16.5494 17.4456 16.6976 17.2627 17.0653C17.1742 17.2443 17.1588 17.4445 17.2223 17.6351C17.2858 17.8238 17.4187 17.9778 17.5958 18.0663L20.901 19.718C21.007 19.7719 21.1205 19.7969 21.2321 19.7969C21.5055 19.7969 21.7693 19.6468 21.9001 19.385C21.9887 19.2079 22.0041 19.0057 21.9405 18.8151Z" fill="white"/><path d="M31.9852 25.7413H28.5029L28.3374 25.5757V14.297L28.5029 14.1315H31.9852C36.1317 14.1315 37.4601 16.4531 37.4601 19.9373C37.4601 23.4216 36.1336 25.7432 31.9852 25.7432V25.7413ZM31.8197 15.6234H30.1603L29.9948 15.7889V24.082L30.1603 24.2475H31.8197C34.9711 24.2475 35.8006 22.7556 35.8006 19.9354C35.8006 17.1152 34.9711 15.6234 31.8197 15.6234Z" fill="white"/><path d="M42.602 17.2824C45.0891 17.2824 46.5829 18.9418 46.5829 21.5945C46.5829 24.2472 45.0891 25.9065 42.602 25.9065C40.1147 25.9065 38.6211 24.2472 38.6211 21.5945C38.6211 18.9418 40.113 17.2824 42.602 17.2824ZM42.602 24.4146C44.0939 24.4146 44.9234 23.4194 44.9234 21.5945C44.9234 19.7696 44.0939 18.7743 42.602 18.7743C41.1101 18.7743 40.2803 19.7696 40.2803 21.5945C40.2803 23.4194 41.1101 24.4146 42.602 24.4146Z" fill="white"/><path d="M59.5211 25.741H58.1946L58.0292 25.5754V20.5992C58.0292 19.604 57.8635 18.7743 56.5373 18.7743C55.3764 18.7743 54.7124 19.604 54.7124 20.9303V25.5754L54.5469 25.741H53.2204L53.055 25.5754V20.5992C53.055 19.604 52.8893 18.7743 51.5631 18.7743C50.7333 18.7743 49.7382 19.271 49.7382 20.9303V25.5754L49.5725 25.741H48.2462L48.0806 25.5754V17.6135L48.2462 17.448H49.4071L49.5725 17.6135L49.7382 18.2776H49.9036C50.2347 17.781 50.8988 17.2824 52.0596 17.2824C53.3861 17.2824 53.8847 17.9465 54.2158 18.4432H54.3813C54.878 17.7791 55.7075 17.2824 56.8684 17.2824C59.19 17.2824 59.6887 18.7762 59.6887 20.5992V25.5754L59.523 25.741H59.5211Z" fill="white"/><path d="M63.0032 16.122H61.6769L61.5112 15.9564V14.6301L61.6769 14.4645H63.0032L63.1688 14.6301V15.9564L63.0032 16.122ZM63.0032 25.7432H61.6769L61.5112 25.5777V17.6139L61.6769 17.4483H63.0032L63.1688 17.6139V25.5758L63.0032 25.7413V25.7432Z" fill="white"/><path d="M72.1259 25.741H70.7994L70.634 25.5754V20.7648C70.634 19.9197 70.4683 18.7743 68.9747 18.7743C67.4807 18.7743 66.8185 19.5867 66.8185 21.5945V25.5754L66.6531 25.741H65.3266L65.1611 25.5754V17.6135L65.3266 17.448H66.4874L66.6531 17.6135L66.8185 18.2776H66.9842C67.4653 17.6482 68.2603 17.2824 69.1402 17.2824C71.4616 17.2824 72.2913 18.7762 72.2913 20.7667V25.5774L72.1259 25.7429V25.741Z" fill="white"/><path d="M77.601 17.2824C80.0881 17.2824 81.5819 18.9418 81.5819 21.5945C81.5819 24.2472 80.0881 25.9065 77.601 25.9065C75.1139 25.9065 73.6201 24.2472 73.6201 21.5945C73.6201 18.9418 75.112 17.2824 77.601 17.2824ZM77.601 24.4146C79.0929 24.4146 79.9224 23.4194 79.9224 21.5945C79.9224 19.7696 79.0929 18.7743 77.601 18.7743C76.1091 18.7743 75.2793 19.7696 75.2793 21.5945C75.2793 23.4194 76.1091 24.4146 77.601 24.4146Z" fill="white"/></g><defs><clipPath id="clip0_3120_3604"><rect width="74" height="14" fill="white" transform="translate(8 13)"/></clipPath></defs></svg>"""

    st.markdown(f"""
    <div class="sidebar-header">
        {logo_svg}
        <div>
            <span class="sidebar-subtitle">FSI Onboarding</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.title("Navigation")

    page = st.radio(
        "Select Page",
        ["🏠 Welcome", "🎯 Role Selection", "📚 Learning Path", "🔗 Resources", "💡 Use Cases", "🛠️ Tools & Languages", "🆘 Support", "✅ Best Practices"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Display current selection
    if st.session_state.selected_org:
        st.markdown("### Your Profile")
        st.info(f"**Organization:** {st.session_state.selected_org}")
        if st.session_state.selected_role:
            st.info(f"**Role:** {st.session_state.selected_role}")
            role_info = ROLE_DEFINITIONS[st.session_state.selected_role]
            st.success(f"**Domino Role:** {role_info['domino_role']}")

        if st.button("Reset Selection"):
            st.session_state.selected_org = None
            st.session_state.selected_role = None

# Main Content Area
if page == "🏠 Welcome":
    # Personalized greeting
    if st.session_state.user_name:
        st.title(f"Welcome, {st.session_state.user_name}")
        st.markdown("### We're glad to have you on the Domino Platform")
    else:
        st.title("Welcome to Domino FSI Onboarding")
        st.markdown("### Your Personalized Path to Mastering Domino Data Lab")

    # Personalized welcome message
    if not st.session_state.selected_org or not st.session_state.selected_role:
        st.info("**Let's get started.** Select your organization and role to begin your personalized onboarding journey.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        This onboarding application will guide you through your journey on the Domino platform,
        tailored specifically to your organization and role within our Financial Services Institution.

        **What you'll learn:**
        - Essential Domino capabilities for your role
        - Organization-specific use cases and examples
        - Best practices for model governance and compliance
        - Hands-on labs and code samples
        - Links to critical documentation and policies
        """)

        st.markdown("---")

        st.markdown("### 🚀 Getting Started")
        st.markdown("""
        1. **Select Your Organization** - Identify your business unit
        2. **Choose Your Role** - Pick the role that best describes your responsibilities
        3. **Explore Your Learning Path** - Access curated labs and resources
        4. **Review Use Cases** - See real-world applications from your organization
        5. **Follow Best Practices** - Learn Domino standards and governance requirements
        """)

        if not st.session_state.selected_org:
            st.info("👈 Start by selecting your organization in the **Role Selection** page")

    with col2:
        st.markdown("### Platform overview")

        st.metric("Organizations", len(ORGANIZATIONS))
        st.metric("Role Types", len(ROLE_DEFINITIONS))
        st.metric("Learning Modules", sum(len(paths['beginner']) + len(paths['intermediate']) + len(paths['advanced']) for paths in LEARNING_PATHS.values()))

        st.markdown("---")

        st.markdown("### Governance & compliance")
        st.markdown("""
        All content follows:
        - SR 11-7 Requirements
        - NIST AI RMF Framework
        - Enterprise AI Policy
        - Model Risk Management
        """)

elif page == "🎯 Role Selection":
    st.title("Select Your Organization and Role")

    # Organization Selection
    st.markdown("### Step 1: Choose your organization")

    org_cols = st.columns(3)

    for idx, (org_name, org_info) in enumerate(ORGANIZATIONS.items()):
        with org_cols[idx % 3]:
            is_selected = st.session_state.selected_org == org_name

            st.markdown(f"""
            <div class="card" style="{'border: 2px solid #543FDE;' if is_selected else ''}">
                <div class="card-title">{org_name}</div>
                <div class="card-subtitle">{org_info['description']}</div>
                <p><strong>Roles:</strong> {len(org_info['roles'])}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Select {org_name}", key=f"org_{org_name}", use_container_width=True):
                st.session_state.selected_org = org_name
                st.session_state.selected_role = None

    # Role Selection (only show if org is selected)
    if st.session_state.selected_org:
        st.markdown("---")
        st.markdown("### Step 2: Choose your role")

        selected_org_info = ORGANIZATIONS[st.session_state.selected_org]
        available_roles = selected_org_info['roles']

        role_cols = st.columns(2)

        for idx, role_name in enumerate(available_roles):
            with role_cols[idx % 2]:
                role_info = ROLE_DEFINITIONS[role_name]
                is_selected = st.session_state.selected_role == role_name

                st.markdown(f"""
                <div class="card" style="{'border: 2px solid #543FDE;' if is_selected else ''}">
                    <div class="card-title">{role_name}</div>
                    <div class="card-subtitle">{role_info['description']}</div>
                    <p><strong>Domino Role:</strong> {role_info['domino_role']}</p>
                    <p><strong>Project Access:</strong> {role_info['project_access']}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Select {role_name}", key=f"role_{role_name}", use_container_width=True):
                    st.session_state.selected_role = role_name

        # Show role details if selected
        if st.session_state.selected_role:
            st.markdown("---")
            st.success(f"✅ You've selected: **{st.session_state.selected_role}** in **{st.session_state.selected_org}**")

            role_info = ROLE_DEFINITIONS[st.session_state.selected_role]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Key capabilities")
                for capability in role_info['key_capabilities']:
                    st.markdown(f"- {capability}")

            with col2:
                st.markdown("### Typical tools")
                for tool in role_info['typical_tools']:
                    st.markdown(f"- {tool}")

            st.info("Navigate to **Learning path** to see your personalized training modules.")

elif page == "📚 Learning Path":
    st.title("Your Personalized Learning Path")

    if not st.session_state.selected_role:
        st.warning("Please select your organization and role first in the **Role Selection** page.")
    else:
        role_name = st.session_state.selected_role
        org_name = st.session_state.selected_org

        st.markdown(f"### Learning Path for {role_name} in {org_name}")

        role_learning = LEARNING_PATHS.get(role_name, {})

        if not role_learning:
            st.error("No learning path available for this role yet.")
        else:
            # Progress overview
            total_modules = len(role_learning.get('beginner', [])) + len(role_learning.get('intermediate', [])) + len(role_learning.get('advanced', []))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Beginner Modules", len(role_learning.get('beginner', [])))
            with col2:
                st.metric("Intermediate Modules", len(role_learning.get('intermediate', [])))
            with col3:
                st.metric("Advanced Modules", len(role_learning.get('advanced', [])))

            st.markdown("---")

            # Tabs for difficulty levels
            tabs = st.tabs(["🟢 Beginner", "🟡 Intermediate", "🔴 Advanced"])

            # Beginner Tab
            with tabs[0]:
                st.markdown("### Beginner level")
                st.markdown("Start here if you're new to Domino or this role.")

                for idx, module in enumerate(role_learning.get('beginner', [])):
                    with st.expander(f"**{idx + 1}. {module['title']}** ({module['duration']})"):
                        st.markdown(f"**Type:** {module['type'].title()}")
                        st.markdown(f"**Description:** {module['description']}")
                        st.markdown(f"**Topics:** {', '.join(module['topics'])}")

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f'<span class="badge badge-beginner">Beginner</span>', unsafe_allow_html=True)
                            st.markdown(f'<span class="badge badge-{module["type"]}\">{module["type"].title()}</span>', unsafe_allow_html=True)
                        with col2:
                            st.button("Start Module", key=f"begin_{idx}", use_container_width=True)

            # Intermediate Tab
            with tabs[1]:
                st.markdown("### Intermediate level")
                st.markdown("Build on foundational knowledge with more complex topics.")

                for idx, module in enumerate(role_learning.get('intermediate', [])):
                    with st.expander(f"**{idx + 1}. {module['title']}** ({module['duration']})"):
                        st.markdown(f"**Type:** {module['type'].title()}")
                        st.markdown(f"**Description:** {module['description']}")
                        st.markdown(f"**Topics:** {', '.join(module['topics'])}")

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f'<span class="badge badge-intermediate">Intermediate</span>', unsafe_allow_html=True)
                            st.markdown(f'<span class="badge badge-{module["type"]}\">{module["type"].title()}</span>', unsafe_allow_html=True)
                        with col2:
                            st.button("Start Module", key=f"inter_{idx}", use_container_width=True)

            # Advanced Tab
            with tabs[2]:
                st.markdown("### Advanced level")
                st.markdown("Master advanced capabilities and production-ready practices.")

                for idx, module in enumerate(role_learning.get('advanced', [])):
                    with st.expander(f"**{idx + 1}. {module['title']}** ({module['duration']})"):
                        st.markdown(f"**Type:** {module['type'].title()}")
                        st.markdown(f"**Description:** {module['description']}")
                        st.markdown(f"**Topics:** {', '.join(module['topics'])}")

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f'<span class="badge badge-advanced">Advanced</span>', unsafe_allow_html=True)
                            st.markdown(f'<span class="badge badge-{module["type"]}\">{module["type"].title()}</span>', unsafe_allow_html=True)
                        with col2:
                            st.button("Start Module", key=f"adv_{idx}", use_container_width=True)

elif page == "🔗 Resources":
    st.title("Documentation & Resources")

    st.markdown("### Essential documentation")
    st.markdown("Access critical governance, policy, and standards documentation.")

    # Common Documentation
    st.markdown("#### Enterprise-wide resources")

    for doc_name, doc_info in COMMON_DOCS.items():
        with st.expander(f"📄 {doc_name}"):
            st.markdown(f"**Description:** {doc_info['description']}")
            st.markdown(f"**Key Topics:** {', '.join(doc_info['topics'])}")
            st.markdown(f"**Link:** [{doc_info['url']}]({doc_info['url']})")
            st.button(f"Open {doc_name}", key=f"doc_{doc_name}", use_container_width=True)

    st.markdown("---")

    # Organization-Specific Resources
    if st.session_state.selected_org:
        org_info = ORGANIZATIONS[st.session_state.selected_org]

        st.markdown(f"#### {st.session_state.selected_org} Specific Resources")

        with st.expander(f"📁 {st.session_state.selected_org} Use Cases & Examples"):
            st.markdown(f"**Description:** Organization-specific use cases, templates, and code examples")
            st.markdown(f"**Link:** [{org_info['use_case_url']}]({org_info['use_case_url']})")
            st.button(f"Open {st.session_state.selected_org} SharePoint", key="org_sharepoint", use_container_width=True)
    else:
        st.info("Select your organization in the **Role Selection** page to see organization-specific resources.")

    st.markdown("---")

    # Quick Links
    st.markdown("### Quick links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Domino Platform")
        st.markdown("- [Domino Documentation](https://docs.dominodatalab.com)")
        st.markdown("- [Domino Community](https://community.dominodatalab.com)")
        st.markdown("- [API Reference](https://docs.dominodatalab.com/api)")

    with col2:
        st.markdown("#### Support")
        st.markdown("- [Submit Support Ticket](#)")
        st.markdown("- [Internal Slack Channel](#)")
        st.markdown("- [Office Hours](#)")

    with col3:
        st.markdown("#### Training")
        st.markdown("- [Video Tutorials](#)")
        st.markdown("- [Live Webinars](#)")
        st.markdown("- [Certification Program](#)")

elif page == "💡 Use Cases":
    st.title("FSI Use Cases & Examples")

    if not st.session_state.selected_org:
        st.warning("Please select your organization in the **Role Selection** page to see relevant use cases.")
    else:
        org_name = st.session_state.selected_org
        org_use_cases = FSI_USE_CASES.get(org_name, [])

        st.markdown(f"### Use Cases for {org_name}")
        st.markdown(f"Explore real-world applications and examples specific to your organization.")

        # Filter by role if selected
        if st.session_state.selected_role:
            show_all = st.checkbox("Show all use cases", value=False)
            if not show_all:
                org_use_cases = [uc for uc in org_use_cases if st.session_state.selected_role in uc['relevant_roles']]
                st.info(f"Showing use cases relevant to **{st.session_state.selected_role}**. Check the box above to see all.")

        # Group by complexity
        beginner_uc = [uc for uc in org_use_cases if uc['complexity'] == 'Beginner']
        intermediate_uc = [uc for uc in org_use_cases if uc['complexity'] == 'Intermediate']
        advanced_uc = [uc for uc in org_use_cases if uc['complexity'] == 'Advanced']

        tabs = st.tabs([f"🟢 Beginner ({len(beginner_uc)})", f"🟡 Intermediate ({len(intermediate_uc)})", f"🔴 Advanced ({len(advanced_uc)})"])

        # Beginner Use Cases
        with tabs[0]:
            if not beginner_uc:
                st.info("No beginner use cases available for your selection.")
            else:
                for uc in beginner_uc:
                    with st.expander(f"**{uc['title']}**"):
                        st.markdown(f"**Description:** {uc['description']}")
                        st.markdown(f"**Relevant Roles:** {', '.join(uc['relevant_roles'])}")
                        st.markdown(f"**Complexity:** {uc['complexity']}")
                        if uc['governance_required']:
                            st.warning("⚠️ **Governance Required:** This use case requires model governance and compliance documentation.")
                        else:
                            st.success("✅ No special governance requirements")

                        col1, col2 = st.columns([3, 1])
                        with col2:
                            st.button("View Example", key=f"uc_begin_{uc['title']}", use_container_width=True)

        # Intermediate Use Cases
        with tabs[1]:
            if not intermediate_uc:
                st.info("No intermediate use cases available for your selection.")
            else:
                for uc in intermediate_uc:
                    with st.expander(f"**{uc['title']}**"):
                        st.markdown(f"**Description:** {uc['description']}")
                        st.markdown(f"**Relevant Roles:** {', '.join(uc['relevant_roles'])}")
                        st.markdown(f"**Complexity:** {uc['complexity']}")
                        if uc['governance_required']:
                            st.warning("⚠️ **Governance Required:** This use case requires model governance and compliance documentation.")
                        else:
                            st.success("✅ No special governance requirements")

                        col1, col2 = st.columns([3, 1])
                        with col2:
                            st.button("View Example", key=f"uc_inter_{uc['title']}", use_container_width=True)

        # Advanced Use Cases
        with tabs[2]:
            if not advanced_uc:
                st.info("No advanced use cases available for your selection.")
            else:
                for uc in advanced_uc:
                    with st.expander(f"**{uc['title']}**"):
                        st.markdown(f"**Description:** {uc['description']}")
                        st.markdown(f"**Relevant Roles:** {', '.join(uc['relevant_roles'])}")
                        st.markdown(f"**Complexity:** {uc['complexity']}")
                        if uc['governance_required']:
                            st.warning("⚠️ **Governance Required:** This use case requires model governance and compliance documentation.")
                        else:
                            st.success("✅ No special governance requirements")

                        col1, col2 = st.columns([3, 1])
                        with col2:
                            st.button("View Example", key=f"uc_adv_{uc['title']}", use_container_width=True)

elif page == "🛠️ Tools & Languages":
    st.title("Tools & Programming Languages")

    if not st.session_state.selected_role:
        st.warning("Please select your organization and role first to see role-specific tools and languages.")
    else:
        role_name = st.session_state.selected_role
        tech_stack = ROLE_TECH_STACK.get(role_name, {})

        st.markdown(f"### Technology Stack for {role_name}")
        st.markdown(f"Essential programming languages, tools, and Domino capabilities for your role.")

        st.markdown("---")

        # Primary Languages
        if tech_stack.get('primary_languages'):
            st.markdown("## Primary programming languages")

            for lang in tech_stack['primary_languages']:
                with st.expander(f"**{lang['name']} {lang.get('version', '')}**", expanded=True):
                    st.markdown(f"**Use Cases:** {lang['use_cases']}")

                    if lang['key_libraries'] and lang['key_libraries'][0] != 'N/A':
                        st.markdown(f"**Key Libraries:** {', '.join(lang['key_libraries'])}")

                    st.markdown("**Learning Resources:**")
                    for resource in lang.get('learning_resources', []):
                        st.markdown(f"- {resource}")

        st.markdown("---")

        # Key Tools
        if tech_stack.get('key_tools'):
            st.markdown("## Essential tools")

            col1, col2 = st.columns(2)
            tools = tech_stack['key_tools']
            mid_point = (len(tools) + 1) // 2

            with col1:
                for tool in tools[:mid_point]:
                    st.markdown(f"- {tool}")

            with col2:
                for tool in tools[mid_point:]:
                    st.markdown(f"- {tool}")

        st.markdown("---")

        # Domino-Specific Capabilities
        if tech_stack.get('domino_specific'):
            st.markdown("## Domino Platform capabilities")
            st.markdown("Features and services you'll use most in Domino:")

            for capability in tech_stack['domino_specific']:
                st.markdown(f"- {capability}")

        st.markdown("---")

        # Quick Start Tips
        st.markdown("## Quick start tips")

        if role_name == "Data Scientist":
            st.success("""
            **Getting Started:**
            1. Start with a Domino Standard Environment (Python 3.9 or R 4.2)
            2. Launch a Jupyter workspace to explore the platform
            3. Try running your first job with a simple Python/R script
            4. Experiment with MLflow for tracking your first model experiment
            """)
        elif role_name == "Quant Analyst":
            st.success("""
            **Getting Started:**
            1. Choose high-performance compute tiers for complex calculations
            2. Start with Jupyter or RStudio for prototyping
            3. Use scheduled jobs for recurring model runs
            4. Leverage Spark or Ray for large-scale backtesting
            """)
        elif role_name == "Model Validator":
            st.success("""
            **Getting Started:**
            1. Get read access to models under validation
            2. Create a separate validation project for independence
            3. Use MLflow to review model training history
            4. Start building your validation test suite with pytest or testthat
            """)
        elif role_name == "ML Engineer":
            st.success("""
            **Getting Started:**
            1. Learn to build custom Domino Environments with Docker
            2. Deploy your first model API with a simple Flask/FastAPI app
            3. Set up monitoring with Grafana dashboards
            4. Explore Domino Flows for pipeline orchestration
            """)
        elif role_name == "Business Manager":
            st.success("""
            **Getting Started:**
            1. Explore published Domino Apps in your organization
            2. Try using a Launcher to run a pre-configured analysis
            3. If you're a Practitioner, launch a Jupyter workspace to explore
            4. Connect with your technical team to understand available data products
            """)

elif page == "🆘 Support":
    st.title("Support & Help")
    st.markdown("Get help when you need it - here's how to access support for Domino platform issues.")

    st.markdown("---")

    # Incident System
    st.markdown("## Submit a support ticket")

    system_info = SUPPORT_INFO['incident_system']
    st.markdown(f"""
    **{system_info['name']}**

    {system_info['description']}

    **Portal:** [{system_info['url']}]({system_info['url']})
    """)

    if st.button("Open Service Desk Portal", use_container_width=True):
        st.markdown(f"[Click here to open the portal]({system_info['url']})")

    st.markdown("---")

    # Best Practices for Ticket Creation
    st.markdown("## Best practices for creating effective tickets")
    st.markdown("Follow these guidelines to get faster, more effective support:")

    for practice in SUPPORT_INFO['best_practices']:
        with st.expander(f"**{practice['title']}**", expanded=False):
            for guideline in practice['guidelines']:
                st.markdown(f"- {guideline}")

    st.markdown("---")

    # Contact Channels
    st.markdown("## Support channels")
    st.markdown("Choose the right channel based on your needs:")

    for channel in SUPPORT_INFO['contact_channels']:
        with st.expander(f"**{channel['channel']}**"):
            st.markdown(f"**Best For:** {channel['use_for']}")
            st.markdown(f"**SLA:** {channel['sla']}")
            st.markdown(f"**Link:** [{channel['url']}]({channel['url']})")

    st.markdown("---")

    # Quick Tips
    st.markdown("## Quick troubleshooting tips")

    st.markdown("""
    Before submitting a ticket, try these common solutions:

    **Workspace Issues:**
    - Restart your workspace session
    - Check if you selected the correct environment
    - Verify hardware tier is sufficient for your workload

    **Job Failures:**
    - Review the job logs for error messages
    - Check if all required files are in the project
    - Verify environment has necessary packages installed

    **App Not Loading:**
    - Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)
    - Check if the app is running in Domino
    - Try accessing from a different browser

    **Package Installation Errors:**
    - Check package name spelling and version
    - Look for conflicting dependencies
    - Consider creating a custom environment
    """)

    st.info("Join the #domino-support Slack channel for community help and to learn from others' questions.")

elif page == "✅ Best Practices":
    st.title("Domino Best Practices")

    st.markdown("""
    Follow these best practices to ensure successful, compliant, and efficient use of the Domino platform.
    These guidelines align with our enterprise standards and governance requirements.
    """)

    st.markdown("---")

    # Display best practices by category
    for category, practices in BEST_PRACTICES.items():
        with st.expander(f"📋 {category}", expanded=False):
            for practice in practices:
                st.markdown(f"- {practice}")

    st.markdown("---")

    # Role-specific recommendations
    if st.session_state.selected_role:
        st.markdown(f"### Recommendations for {st.session_state.selected_role}")

        role_name = st.session_state.selected_role

        if role_name == "Data Scientist":
            st.info("""
            **Key Focus Areas:**
            - Set up experiment tracking from day one
            - Use Git for version control
            - Document data sources and assumptions
            - Follow governance requirements for regulated models
            """)

        elif role_name == "Quant Analyst":
            st.info("""
            **Key Focus Areas:**
            - Version all pricing and risk models
            - Document model assumptions and calibration
            - Use high-performance compute efficiently
            - Maintain audit trail for regulatory compliance
            """)

        elif role_name == "Model Validator":
            st.info("""
            **Key Focus Areas:**
            - Create comprehensive governance bundles
            - Document all validation steps and findings
            - Ensure independent replication of results
            - Maintain clear separation from development teams
            """)

        elif role_name == "ML Engineer":
            st.info("""
            **Key Focus Areas:**
            - Build robust CI/CD pipelines
            - Implement comprehensive monitoring
            - Optimize resource utilization
            - Document infrastructure decisions
            """)

        elif role_name == "Business Manager":
            st.info("""
            **Key Focus Areas:**
            - Understand governance requirements for your use cases
            - Communicate business requirements clearly
            - Use Launchers and Apps for self-service
            - Provide timely feedback to technical teams
            """)

    st.markdown("---")

    st.markdown("### Additional resources")
    st.markdown(f"For detailed standards and guidelines, visit the [Domino Standards Documentation]({COMMON_DOCS['Domino Standards']['url']})")

# Footer
st.markdown("""
<div class="footer">
    <p style="margin: 0 0 8px 0;">Domino FSI Onboarding Application</p>
    <p style="margin: 0;">For support, contact your Domino Administrator or visit the Internal Support Portal</p>
</div>
""", unsafe_allow_html=True)
