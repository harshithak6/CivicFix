
import streamlit as st
import json
import os
import uuid
import re
import hashlib
import hmac
from datetime import datetime
from google import genai


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CivicFix | Smart Civic Management",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# 2. SESSION AND AUTHENTICATION
# =====================================================

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


def verify_admin_password(password):

    try:
        stored_hash = st.secrets["ADMIN_PASSWORD_HASH"]

        salt, expected_hash = stored_hash.split("$")

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            600000
        ).hex()

        return hmac.compare_digest(
            password_hash,
            expected_hash
        )

    except Exception:
        return False


# =====================================================
# 3. UI STYLING
# =====================================================

st.markdown("""
<style>

.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #F4F7FB !important;
}

.main .block-container {
    color: #172B4D !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #102A43 !important;
}

p, li, label {
    color: #172B4D;
}

/* SIDEBAR */

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #10243A !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #D5E2F0 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #456078 !important;
}

/* TITLES */

.main-title {
    font-size: 32px;
    font-weight: 800;
    color: #102A43 !important;
}

.subtitle {
    font-size: 16px;
    color: #34495E !important;
}

/* METRIC CARDS */

.metric-card {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #C8D5E3;
    min-height: 105px;
}

.metric-label {
    color: #34495E !important;
    font-size: 14px;
    font-weight: 600;
}

.metric-value {
    color: #102A43 !important;
    font-size: 30px;
    font-weight: 800;
}

/* BUTTONS */

div.stButton > button,
div.stFormSubmitButton > button {
    background-color: #1769AA !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

div.stButton > button *,
div.stFormSubmitButton > button * {
    color: #FFFFFF !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background-color: #0F4C81 !important;
}

/* INPUTS */

.stTextInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #172B4D !important;
    border: 1px solid #9BAFC4 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #65758B !important;
}

/* SELECT BOXES */

.stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    color: #172B4D !important;
}

.stSelectbox div[data-baseweb="select"] * {
    color: #172B4D !important;
}

[data-baseweb="popover"],
[data-baseweb="menu"] {
    background-color: #FFFFFF !important;
}

[data-baseweb="menu"] * {
    color: #172B4D !important;
}

/* ALERTS */

[data-testid="stAlert"] {
    background-color: #EAF2FF !important;
    border: 1px solid #B8D2F0 !important;
    border-radius: 10px !important;
}

[data-testid="stAlert"],
[data-testid="stAlert"] *,
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div,
[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
    color: #17324D !important;
}

[data-testid="stAlert"] svg {
    color: #1769AA !important;
    fill: none !important;
}

/* METRICS */

[data-testid="stMetricValue"] {
    color: #102A43 !important;
}

[data-testid="stMetricLabel"] {
    color: #34495E !important;
}

/* CAPTIONS */

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #34495E !important;
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #C8D5E3 !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: #172B4D !important;
}

/* PROGRESS */

.stProgress > div > div {
    background-color: #1769AA !important;
}

/* DIVIDERS */

hr {
    border-color: #C8D5E3 !important;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 4. DATABASE CONFIGURATION
# =====================================================

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "complaints.json"
)


def load_complaints():

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_complaints(complaints):

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(complaints, file, indent=4)


# =====================================================
# 5. DEPARTMENT MAPPING
# =====================================================

DEPARTMENT_MAPPING = {
    "Road Infrastructure": "Road Maintenance Department",
    "Sanitation": "Sanitation Department",
    "Street Lighting": "Electrical Maintenance Department",
    "Water and Drainage": "Water Supply and Drainage Department",
    "General Public Issue": "General Civic Administration"
}

VALID_CATEGORIES = list(DEPARTMENT_MAPPING.keys())

VALID_PRIORITIES = ["High", "Medium", "Low"]


# =====================================================
# 6. RULE-BASED CLASSIFICATION
# =====================================================

def classify_issue(issue, description):

    text = (issue + " " + description).lower()

    if "pothole" in text or "road" in text:
        return "Road Infrastructure", "Road Maintenance Department"

    elif "garbage" in text or "waste" in text:
        return "Sanitation", "Sanitation Department"

    elif (
        "streetlight" in text
        or "street light" in text
        or "light" in text
    ):
        return "Street Lighting", "Electrical Maintenance Department"

    elif (
        "water" in text
        or "leakage" in text
        or "drainage" in text
    ):
        return "Water and Drainage", "Water Supply and Drainage Department"

    return "General Public Issue", "General Civic Administration"


# =====================================================
# 7. RULE-BASED PRIORITY ASSESSMENT
# =====================================================

def assess_priority(description):

    text = description.lower()

    high_keywords = [
        "accident",
        "injured",
        "injury",
        "danger",
        "emergency",
        "exposed wire",
        "electric shock",
        "fire",
        "collapsed",
        "severe flooding"
    ]

    medium_keywords = [
        "not working",
        "overflow",
        "blocked",
        "damaged",
        "broken",
        "leaking"
    ]

    if any(word in text for word in high_keywords):
        return "High"

    elif any(word in text for word in medium_keywords):
        return "Medium"

    return "Low"


# =====================================================
# 8. GEMINI AI COMPLAINT ANALYSIS
# =====================================================

def analyze_complaint_with_ai(issue, description):

    fallback_category, fallback_department = classify_issue(
        issue, description
    )

    fallback_priority = assess_priority(description)

    try:

        api_key = st.secrets["GEMINI_API_KEY"]

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are CivicFix, an AI public complaint analysis agent.

Analyze this citizen complaint.

Selected issue: {issue}

Complaint description: {description}

Your tasks:
1. Identify the complaint category.
2. Assess the complaint priority.
3. Explain your decision briefly.

Choose ONLY one category:
- Road Infrastructure
- Sanitation
- Street Lighting
- Water and Drainage
- General Public Issue

Choose ONLY one priority:
- High
- Medium
- Low

Return ONLY valid JSON in this format:

{{
    "category": "Road Infrastructure",
    "priority": "High",
    "explanation": "Brief reason for the classification."
}}
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        response_text = response.text.strip()

        response_text = re.sub(
            r"```(?:json)?|```",
            "",
            response_text
        ).strip()

        result = json.loads(response_text)

        category = result.get("category", fallback_category)

        priority = result.get("priority", fallback_priority)

        explanation = result.get(
            "explanation",
            "Complaint analyzed by Gemini AI."
        )

        if category not in VALID_CATEGORIES:
            category = fallback_category

        if priority not in VALID_PRIORITIES:
            priority = fallback_priority

        department = DEPARTMENT_MAPPING[category]

        return {
            "category": category,
            "department": department,
            "priority": priority,
            "explanation": explanation,
            "analysis_source": "Gemini AI"
        }

    except Exception:

        return {
            "category": fallback_category,
            "department": fallback_department,
            "priority": fallback_priority,
            "explanation": (
                "Gemini AI was unavailable. "
                "The complaint was analyzed using Python-based rules."
            ),
            "analysis_source": "Rule-Based Fallback"
        }


# =====================================================
# 9. TICKET GENERATION
# =====================================================

def create_ticket():

    return "CF-" + str(uuid.uuid4())[:8].upper()


# =====================================================
# 10. SIDEBAR NAVIGATION
# =====================================================

with st.sidebar:

    st.markdown("# 🏙️ CivicFix")

    st.caption("SMART CIVIC MANAGEMENT")

    st.divider()

    if st.session_state.admin_authenticated:

        st.success("Admin Logged In")

        pages = [
            "Citizen Portal",
            "Dashboard",
            "All Complaints",
            "Agent Workflow",
            "Logout"
        ]

    else:

        pages = [
            "Citizen Portal",
            "Admin Login"
        ]

    page = st.radio(
        "NAVIGATION",
        pages,
        key="navigation"
    )

    st.divider()

    st.markdown("### About CivicFix")

    st.caption(
        "An intelligent public complaint management "
        "platform for better communities."
    )

    if st.session_state.admin_authenticated:

        st.caption("Administrator Access")

    else:

        st.caption("Citizen Access")

    st.caption("Version 4.1 | Hackathon Prototype")


# =====================================================
# 11. LOGOUT
# =====================================================

if page == "Logout":

    st.session_state.admin_authenticated = False

    st.success("You have been logged out successfully.")

    st.rerun()


# =====================================================
# 12. ADMIN PAGE PROTECTION
# =====================================================

ADMIN_PAGES = [
    "Dashboard",
    "All Complaints",
    "Agent Workflow"
]

if page in ADMIN_PAGES and not st.session_state.admin_authenticated:

    st.error("Access denied. Please log in as administrator.")

    st.stop()


# =====================================================
# 13. ADMIN LOGIN PAGE
# =====================================================

if page == "Admin Login":

    st.markdown(
        '<div class="main-title">Admin Login</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Sign in to access the CivicFix administration portal.'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    with st.container(border=True):

        st.subheader("🔐 Administrator Authentication")

        with st.form("admin_login_form"):

            username = st.text_input(
                "Username",
                placeholder="Enter admin username"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter admin password"
            )

            login = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if login:

            try:

                correct_username = st.secrets["ADMIN_USERNAME"]

                if (
                    hmac.compare_digest(
                        username.strip(),
                        correct_username
                    )
                    and verify_admin_password(password)
                ):

                    st.session_state.admin_authenticated = True

                    st.success("Admin login successful!")

                    st.rerun()

                else:

                    st.error("Invalid username or password.")

            except Exception as e:

                st.error(f"Admin configuration error: {e}")

    st.info(
        "This login is reserved for the authorized CivicFix administrator."
    )


# =====================================================
# 14. CITIZEN PORTAL
# =====================================================

elif page == "Citizen Portal":

    st.markdown(
        '<div class="main-title">Welcome to CivicFix</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Report public issues and help build better communities.'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    st.markdown("### 📝 Report a Public Issue")

    st.write(
        "Submit details about potholes, garbage, broken streetlights, "
        "water leakage and other civic problems."
    )

    with st.form("complaint_form"):

        name = st.text_input("Full Name")

        location = st.text_input("Issue Location")

        issue = st.selectbox(
            "Select Issue Category",
            [
                "Pothole",
                "Garbage",
                "Broken Streetlight",
                "Water Leakage",
                "Other"
            ]
        )

        description = st.text_area(
            "Describe the Issue",
            placeholder="Explain the problem in detail..."
        )

        submit = st.form_submit_button(
            "Submit Complaint",
            use_container_width=True
        )

    if submit:

        if (
            name.strip()
            and location.strip()
            and description.strip()
        ):

            with st.spinner(
                "CivicFix AI is analyzing your complaint..."
            ):

                analysis = analyze_complaint_with_ai(
                    issue,
                    description
                )

            ticket_id = create_ticket()

            complaint = {
                "ticket_id": ticket_id,
                "name": name.strip(),
                "location": location.strip(),
                "issue": issue,
                "description": description.strip(),
                "category": analysis["category"],
                "department": analysis["department"],
                "priority": analysis["priority"],
                "status": "Pending",
                "date": datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S"
                ),
                "ai_explanation": analysis["explanation"],
                "analysis_source": analysis["analysis_source"]
            }

            complaints = load_complaints()

            complaints.append(complaint)

            save_complaints(complaints)

            st.success("Complaint submitted successfully!")

            st.subheader("CivicFix Agent Analysis")

            col1, col2 = st.columns(2)

            with col1:

                st.write("**Ticket ID:**", ticket_id)

                st.write("**Category:**", analysis["category"])

                st.write("**Department:**", analysis["department"])

            with col2:

                st.write("**Priority:**", analysis["priority"])

                st.write("**Status:** Pending")

                st.write(
                    "**Analysis Method:**",
                    analysis["analysis_source"]
                )

            st.markdown("### AI Explanation")

            st.markdown(
                f"""
                <div style="
                    background-color: #EAF2FF;
                    color: #17324D;
                    padding: 18px;
                    border-radius: 10px;
                    border: 1px solid #B8D2F0;
                    font-size: 16px;
                    line-height: 1.6;
                ">
                    {analysis["explanation"]}
                </div>
                """,
                unsafe_allow_html=True
            )

            if analysis["analysis_source"] == "Gemini AI":

                st.success(
                    "Complaint analyzed successfully using Gemini AI."
                )

            else:

                st.warning(
                    "Gemini AI was unavailable. "
                    "Rule-based analysis was used instead."
                )

            st.markdown(
                """
                <div style="
                    background-color: #FFF4D6;
                    color: #594214;
                    padding: 16px;
                    border-radius: 10px;
                    border: 1px solid #E8D49A;
                    font-size: 15px;
                    line-height: 1.6;
                ">
                    <strong>Prototype Notice</strong><br>
                    This demonstration ticket has been saved locally.
                    It has not been sent to an actual government department.
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.warning("Please complete all required fields.")


# =====================================================
# 15. DASHBOARD PAGE - ADMIN ONLY
# =====================================================

elif page == "Dashboard":

    complaints = load_complaints()

    total = len(complaints)

    pending = sum(
        1 for c in complaints
        if c.get("status", "Pending") == "Pending"
    )

    in_progress = sum(
        1 for c in complaints
        if c.get("status", "Pending") == "In Progress"
    )

    resolved = sum(
        1 for c in complaints
        if c.get("status", "Pending") == "Resolved"
    )

    resolution_rate = (
        (resolved / total) * 100
        if total > 0 else 0
    )

    st.markdown(
        '<div class="main-title">Admin Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Monitor public complaints, department activity '
        'and resolution progress.'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        (col1, "TOTAL COMPLAINTS", total),
        (col2, "PENDING", pending),
        (col3, "IN PROGRESS", in_progress),
        (col4, "RESOLVED", resolved)
    ]

    for column, label, value in metrics:

        with column:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    st.divider()

    # RESOLUTION PERFORMANCE

    st.subheader("Resolution Performance")

    col1, col2 = st.columns([1, 2])

    with col1:

        st.metric(
            "Resolution Rate",
            f"{resolution_rate:.1f}%"
        )

    with col2:

        st.write("Complaint Resolution Progress")

        st.progress(resolution_rate / 100)

        st.caption(
            f"{resolved} of {total} complaints resolved"
        )

    st.divider()

    # HIGH PRIORITY ALERTS

    st.subheader("🚨 High-Priority Alerts")

    high_priority = [
        c for c in complaints
        if c.get("priority") == "High"
        and c.get("status", "Pending") != "Resolved"
    ]

    if high_priority:

        st.warning(
            f"{len(high_priority)} unresolved high-priority "
            "complaint(s) require attention."
        )

        for c in high_priority:

            with st.container(border=True):

                st.write(f"**{c.get('ticket_id', 'N/A')}**")

                st.write(f"Issue: {c.get('issue', 'N/A')}")

                st.write(f"Location: {c.get('location', 'N/A')}")

                st.write(f"Department: {c.get('department', 'N/A')}")

                st.write(f"Status: {c.get('status', 'Pending')}")

    else:

        st.success("No unresolved high-priority complaints.")

    st.divider()

    # DEPARTMENT ANALYSIS

    st.subheader("🏢 Department-wise Analysis")

    if complaints:

        department_counts = {}

        for c in complaints:

            department = c.get(
                "department",
                "General Civic Administration"
            )

            department_counts[department] = (
                department_counts.get(department, 0) + 1
            )

        for department, count in sorted(
            department_counts.items(),
            key=lambda item: item[1],
            reverse=True
        ):

            percentage = count / total

            st.write(f"**{department}** — {count} complaints")

            st.progress(percentage)

    else:

        st.info(
            "Department analysis will appear "
            "after complaints are submitted."
        )

    st.divider()

    # PRIORITY DISTRIBUTION

    st.subheader("Priority Distribution")

    priority_counts = {
        "High": 0,
        "Medium": 0,
        "Low": 0
    }

    for c in complaints:

        priority = c.get("priority", "Low")

        if priority in priority_counts:
            priority_counts[priority] += 1

    p1, p2, p3 = st.columns(3)

    p1.metric("🔴 High", priority_counts["High"])

    p2.metric("🟠 Medium", priority_counts["Medium"])

    p3.metric("🟢 Low", priority_counts["Low"])

    st.divider()

    # RECENT COMPLAINTS

    st.subheader("Recent Complaints")

    if complaints:

        for c in reversed(complaints[-5:]):

            with st.container(border=True):

                col1, col2 = st.columns([3, 1])

                with col1:

                    st.write(f"**{c.get('ticket_id', 'N/A')}**")

                    st.write(
                        f"{c.get('issue', 'N/A')} | "
                        f"{c.get('location', 'N/A')}"
                    )

                with col2:

                    st.write(f"**{c.get('status', 'Pending')}**")

    else:

        st.info(
            "No complaints available. Submit your first complaint."
        )


# =====================================================
# 16. ALL COMPLAINTS PAGE - ADMIN ONLY
# =====================================================

elif page == "All Complaints":

    st.markdown(
        '<div class="main-title">Complaint Management</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Search, filter and manage all citizen complaints.'
        '</div>',
        unsafe_allow_html=True
    )

    complaints = load_complaints()

    if complaints:

        st.write("")

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "Search complaints",
                placeholder="Ticket ID or location..."
            )

        with col2:

            priority_filter = st.selectbox(
                "Filter by Priority",
                ["All", "High", "Medium", "Low"]
            )

        with col3:

            status_filter = st.selectbox(
                "Filter by Status",
                [
                    "All",
                    "Pending",
                    "In Progress",
                    "Resolved"
                ]
            )

        filtered = []

        for c in complaints:

            searchable_text = (
                c.get("ticket_id", "") + " " +
                c.get("location", "") + " " +
                c.get("issue", "") + " " +
                c.get("name", "")
            ).lower()

            matches_search = search.lower() in searchable_text

            matches_priority = (
                priority_filter == "All"
                or c.get("priority", "Low") == priority_filter
            )

            matches_status = (
                status_filter == "All"
                or c.get("status", "Pending") == status_filter
            )

            if (
                matches_search
                and matches_priority
                and matches_status
            ):

                filtered.append(c)

        st.divider()

        st.write(
            f"Showing {len(filtered)} of {len(complaints)} complaints"
        )

        header = st.columns([1.5, 1.5, 1.5, 1.2, 1.3])

        header[0].markdown("**Ticket ID**")
        header[1].markdown("**Issue**")
        header[2].markdown("**Location**")
        header[3].markdown("**Priority**")
        header[4].markdown("**Status**")

        st.divider()

        for c in reversed(filtered):

            row = st.columns([1.5, 1.5, 1.5, 1.2, 1.3])

            row[0].write(c.get("ticket_id", "N/A"))
            row[1].write(c.get("issue", "N/A"))
            row[2].write(c.get("location", "N/A"))

            priority_icon = {
                "High": "🔴",
                "Medium": "🟠",
                "Low": "🟢"
            }

            row[3].write(
                priority_icon.get(
                    c.get("priority", "Low"), "⚪"
                ) + " " + c.get("priority", "Low")
            )

            status_icon = {
                "Pending": "🟡",
                "In Progress": "🔵",
                "Resolved": "🟢"
            }

            row[4].write(
                status_icon.get(
                    c.get("status", "Pending"), "⚪"
                ) + " " + c.get("status", "Pending")
            )

            with st.expander(
                "View / Update " + c.get("ticket_id", "Complaint")
            ):

                st.write("**Citizen:**", c.get("name", "N/A"))

                st.write("**Description:**", c.get("description", "N/A"))

                st.write("**Category:**", c.get("category", "N/A"))

                st.write("**Department:**", c.get("department", "N/A"))

                st.write("**Submitted:**", c.get("date", "N/A"))

                st.write(
                    "**Analysis Method:**",
                    c.get("analysis_source", "Rule-Based")
                )

                if c.get("ai_explanation"):

                    st.write(
                        "**AI Explanation:**",
                        c.get("ai_explanation")
                    )

                status_options = [
                    "Pending",
                    "In Progress",
                    "Resolved"
                ]

                current_status = c.get("status", "Pending")

                if current_status not in status_options:
                    current_status = "Pending"

                new_status = st.selectbox(
                    "Update Complaint Status",
                    status_options,
                    index=status_options.index(current_status),
                    key="status_" + c["ticket_id"]
                )

                if st.button(
                    "Save Changes",
                    key="save_" + c["ticket_id"]
                ):

                    updated = load_complaints()

                    for item in updated:

                        if item["ticket_id"] == c["ticket_id"]:
                            item["status"] = new_status

                    save_complaints(updated)

                    st.success("Complaint updated successfully!")

                    st.rerun()

    else:

        st.info("No complaints have been submitted yet.")


# =====================================================
# 17. AGENT WORKFLOW PAGE - ADMIN ONLY
# =====================================================

elif page == "Agent Workflow":

    st.markdown(
        '<div class="main-title">AI Agent Workflow</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Understand how CivicFix processes public complaints.'
        '</div>',
        unsafe_allow_html=True
    )

    steps = [
        (
            "01",
            "Complaint Input",
            "The citizen submits a public issue."
        ),
        (
            "02",
            "AI Issue Understanding",
            "Gemini AI analyzes the complaint and identifies its category."
        ),
        (
            "03",
            "Priority Assessment",
            "The system assigns High, Medium or Low priority."
        ),
        (
            "04",
            "Department Selection",
            "The system selects the responsible department."
        ),
        (
            "05",
            "Ticket Generation",
            "A unique complaint identification number is created."
        ),
        (
            "06",
            "Database Storage",
            "The complaint is saved in the local JSON database."
        ),
        (
            "07",
            "Status Tracking",
            "The administrator updates the complaint status."
        ),
        (
            "08",
            "Dashboard Analytics",
            "The dashboard displays complaint statistics and progress."
        )
    ]

    for number, title, description in steps:

        with st.container(border=True):

            col1, col2 = st.columns([1, 8])

            with col1:

                st.markdown(f"## {number}")

            with col2:

                st.markdown(f"### {title}")

                st.write(description)

    st.divider()

    st.subheader("Current Agent Capabilities")

    st.write("- AI-powered complaint understanding using Gemini")
    st.write("- Automatic issue classification")
    st.write("- Priority assessment")
    st.write("- Department assignment")
    st.write("- Automatic ticket generation")
    st.write("- Complaint storage and tracking")
    st.write("- Dashboard analytics")

    st.info(
        "CivicFix is a hackathon prototype. "
        "Complaints are stored locally and are not automatically "
        "forwarded to real government departments."
    )


# =====================================================
# 18. FOOTER
# =====================================================

st.divider()

st.caption(
    "CivicFix | Smart Communities, Better Cities | Version 4.1"
)
