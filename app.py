import streamlit as st
import os
import json
import time
import re
from dotenv import load_dotenv
import textwrap

from utils import (
    parse_pdf,
    parse_docx,
    analyze_resume,
    rewrite_resume,
    create_docx,
    verify_optimization,
    verify_analysis_integrity
)
from suggestions import generate_tailoring_suggestions


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------


load_dotenv()

st.set_page_config(
    page_title="ATS Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Main Layout */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1E293B;
    }
    
    /* Gradient Header */
    .main-header {
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    /* Cards */
    .stCard {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
    }
    
    /* Score Metric */
    .score-card {
        text-align: center;
        padding: 20px;
        border-radius: 15px;
        background: #F8FAFC;
        border: 2px solid #E2E8F0;
    }
    .score-value {
        font-size: 3.5rem;
        font-weight: 800;
        color: #4F46E5;
    }
    .score-label {
        font-size: 1rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    
    /* Badges / Chips */
    .badge-full {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
    }
    .badge-partial {
        background-color: #FEF9C3;
        color: #854D0E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .badge-missing {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Optimization Items (Results List) */
    .opt-item {
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        margin-bottom: 8px;
        transition: transform 0.2s;
    }
    .opt-item:hover {
        transform: translateX(4px);
        border-color: #CBD5E1;
    }

    /* Keyword Cloud */
    .keyword-cloud {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .keyword-tag {
        background-color: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">AI Resume Analyzer & ATS Optimizer</div>', unsafe_allow_html=True)
st.markdown("**Realistic ATS feedback mimicking Workday, Greenhouse & iCIMS logic.**")

# ---------------------------------------------------------
# API KEY
# ---------------------------------------------------------

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.warning("Please enter your OpenAI API Key to proceed.")

# ---------------------------------------------------------
# INPUTS
# ---------------------------------------------------------

col1, col2 = st.columns(2)

resume_text = ""
jd_text = ""

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF or DOCX)",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            resume_text = parse_pdf(uploaded_file)
        else:
            resume_text = parse_docx(uploaded_file)

        st.success("Resume parsed successfully")
        with st.expander("View extracted resume text"):
            st.text_area("Resume Text", resume_text, height=250)

with col2:
    st.subheader("2. Job Description")
    jd_text = st.text_area("Paste Job Description", height=350)

# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------

if st.button("Analyze Resume", type="primary"):
    if not api_key:
        st.error("OpenAI API key missing")
    elif not resume_text:
        st.error("Please upload a resume")
    elif not jd_text:
        st.error("Please paste a Job Description")
    else:
        # Improved Progress Visuals
        with st.status("🚀 Running Deep ATS Analysis...", expanded=True) as status:
            st.write("🔍 Scanning resume against job description...")
            raw_analysis = analyze_resume(resume_text, jd_text, api_key)
            
            st.write("🤖 Audit Agent verifying findings and checking for hallucinations...")
            verified_analysis = verify_analysis_integrity(raw_analysis, resume_text, jd_text, api_key)
            
            st.session_state["analysis"] = verified_analysis
            st.session_state["resume_text"] = resume_text
            st.session_state["jd_text"] = jd_text
            
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
        st.rerun()

# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

if "analysis" in st.session_state:
    analysis = st.session_state["analysis"]

    st.divider()
    st.subheader("📊 ATS Relevance Assessment")

    # ---- SCORE DASHBOARD ----
    score_col, summary_col = st.columns([1, 2])

    with score_col:
        # Custom HTML Score Card
        score_val = analysis.get("overall_relevance_score", 0)
        band = analysis.get("ats_ranking_band", "Low")
        
        score_color = "#4F46E5" # Default Indigo
        if score_val >= 90: score_color = "#16A34A" # Green
        elif score_val < 60: score_color = "#DC2626" # Red
        elif score_val < 75: score_color = "#D97706" # Orange

        st.markdown(f"""
        <div class="score-card" style="border-color: {score_color};">
            <div class="score-value" style="color: {score_color};">{score_val}</div>
            <div class="score-label">{band} Match</div>
        </div>
        """, unsafe_allow_html=True)

    with summary_col:
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; height: 100%;">
            <h4 style="margin-top: 0; color: #475569;">Recruiter Summary</h4>
            <p style="color: #334155; line-height: 1.6;">{analysis.get("recruiter_summary", "No summary available.")}</p>
        </div>
        """, unsafe_allow_html=True)

    # ---- ELIGIBILITY ----
    eligibility = analysis.get("eligibility_check", {"meets_minimum_requirements": False, "blocking_issues": ["Analysis failed to check eligibility."]})
    if eligibility.get("meets_minimum_requirements"):
        st.success("✅ **Meets Minimum Requirements**")
    else:
        st.error("❌ **Does Not Meet Minimum Requirements**")
        for issue in eligibility.get("blocking_issues", []):
            st.write(f"- {issue}")

    # ---- DETAILED MATCHING ----
    with st.expander("Detailed Requirement Breakdown", expanded=True):
        st.subheader("📋 Basic Qualifications")
        
        for item in analysis.get("basic_qualification_match", []):
            status = item.get("match_status", "Missing")
            
            badge_class = "badge-missing"
            if status == "Full": badge_class = "badge-full"
            elif status == "Partial": badge_class = "badge-partial"
            
            st.markdown(
                f"""
                <div class="opt-item">
                    <span class="{badge_class}">{status.upper()}</span>
                    <span style="font-weight: 600; color: #1E293B;">{item.get('requirement', 'Unknown')}</span>
                    <div style="margin-top: 8px; font-size: 0.9rem; color: #64748B;">
                        {item.get('notes', '')}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🌟 Preferred Qualifications")
        
        for item in analysis.get("preferred_qualification_match", []):
            status = item.get("match_status", "Missing")
            
            badge_class = "badge-missing"
            if status == "Full": badge_class = "badge-full"
            elif status == "Partial": badge_class = "badge-partial"
            
            st.markdown(
                f"""
                <div class="opt-item" style="border-left: 3px solid #E2E8F0;">
                    <span class="{badge_class}">{status.upper()}</span>
                    <span style="color: #334155;">{item.get('requirement', 'Unknown Preference')}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )

    # ---- BREAKDOWN ----
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 🎯 Required Skills Detected")
        skill_signals = analysis.get("required_skill_signals", {"primary": [], "secondary": []})
        st.write("**Primary**")
        for s in skill_signals.get("primary", []):
            st.write(f"- {s}")

        st.write("**Secondary**")
        for s in skill_signals.get("secondary", []):
            st.write(f"- {s}")

    with c2:
        st.markdown("### ⚠️ Risk Signals")
        risks = analysis.get("noise_or_dilution_signals", [])
        if not risks:
            st.success("No critical risks found.")
        else:
            for risk in risks:
                st.warning(f"{risk}", icon="⚠️")

    with c3:
        st.markdown("### 🔍 Missing Keywords")
        gap_analysis = analysis.get("keyword_gap_analysis", {"missing_jd_keywords": [], "concept_mismatches": []})
        
        st.caption("**Missing Exact Keywords** (High Priority)")
        missing_kws = gap_analysis.get("missing_jd_keywords", [])
        
        if not missing_kws:
            st.success("All keywords matched!")
        else:
            # Generate Cloud HTML
            tags_html = "".join([f'<div class="keyword-tag">⚠️ {kw}</div>' for kw in missing_kws])
            
            st.markdown(f"""
            <div class="keyword-cloud">
                {tags_html}
            </div>
            """, unsafe_allow_html=True)

        if gap_analysis.get("concept_mismatches", []):
            st.caption("**Concept Mismatches**")
            for k in gap_analysis.get("concept_mismatches", []):
                st.info(f"{k}", icon="ℹ️")

    # ---- PENALTIES ----
    # (Removed by user request)

    # ---------------------------------------------------------
    # REWRITE
    # ---------------------------------------------------------

    st.divider()
    st.markdown("### 🛠️ Resume Optimization Plan")
    st.info("Review the proposed changes below. Uncheck any you do not want to apply.")

    # Initialize plan in session state if not present
    if "optimization_plan" not in st.session_state:
        st.session_state["optimization_plan"] = None

    trigger_gen = False
    
    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        if st.button("Generate Optimization Plan", key="btn_gen_main"):
            trigger_gen = True
    with c2:
        if st.session_state.get("optimization_plan") and st.button("🔄 Regenerate Plan", key="btn_regen_main"):
            trigger_gen = True
            
    if trigger_gen:
        # Debugging: Check if we have gaps to process
        basic_gaps = analysis.get("basic_qualification_match", [])
        preferred_gaps = analysis.get("preferred_qualification_match", [])
        
        print(f"DEBUG: Generating Plan. Basic Gaps: {len(basic_gaps)}, Preferred Gaps: {len(preferred_gaps)}")
        
        with st.spinner("✨ Drafting tailored optimization plan..."):
            plan = generate_tailoring_suggestions(
                st.session_state["resume_text"],
                basic_gaps,
                preferred_gaps,
                analysis.get("role_alignment", {}),
                api_key
            )
            st.session_state["optimization_plan"] = plan
            st.rerun()


    # Display Plan
    if st.session_state["optimization_plan"] is not None:
        if not st.session_state["optimization_plan"]:
            st.warning("No suggestions generated. The AI might not have found any gaps to fix.")
        
    if st.session_state["optimization_plan"]:
        approved_changes = []
        
        # We need to iterate by index to allow updates
        plan = st.session_state["optimization_plan"]
        
        for i in range(len(plan)):
            item = plan[i]
            
            # Determine display attributes
            # Determine display attributes
            raw_proposal = item.get('proposal') or item.get('proposed_text') or "Unknown Change"
            
            # Robust Text Formatting (Handle List vs String)
            if isinstance(raw_proposal, list):
                # It's a list of bullets (e.g. FULL_ROLE_REWRITE)
                display_text = "• " + "<br>• ".join([str(p) for p in raw_proposal])
            else:
                # It's a string, just handle newlines
                display_text = str(raw_proposal).replace('\n', '<br>')
                
            item_type = item.get('type', 'Change').replace('_', ' ').title()
            reason = item.get('reason', 'Optimization')
            
            # Context Attributes
            target_section = item.get('target_section', 'General')
            placement_rationale = item.get('placement_rationale', '')
            
            is_recommended = item.get('is_recommended', True)
            suitability_reason = item.get('suitability_reason', "No specific risk found.")
            
            # Badge Color
            badge_color = "#DBEAFE" # Blue for additions
            badge_text_color = "#1E40AF"
            if "Rewrite" in item_type:
                badge_color = "#FCE7F3" # Pink/Purple for rewrites
                badge_text_color = "#9D174D"
            if not is_recommended:
                badge_color = "#FEE2E2" # Red for risky
                badge_text_color = "#991B1B"
            
            # Layout: [Checkbox (0.05)] [Card Content (0.85)] [Regenerate (0.10)]
            c_check, c_content, c_regen = st.columns([0.05, 0.85, 0.10])
            
            with c_check:
                # Vertical alignment hack or just simple checkbox
                st.write("") # Spacer
                is_checked = st.checkbox(
                    "",
                    value=is_recommended, 
                    key=f"plan_item_{i}_{display_text[:10]}",
                    label_visibility="collapsed"
                )
            
            with c_content:
                # ------------------------------------------------------------------
                # SPECIAL HANDLING FOR DECISION CARDS
                # ------------------------------------------------------------------
                if item.get("type") == "decision_required":
                    # WRAP IN CONTAINER FOR VISUAL COHESION
                    with st.container(border=True):
                        # Safeguard against None values (from restore state or bad generation)
                        safe_gap = item.get("gap") or "Detected Gap"
                        safe_reason = reason if reason and reason != "None" else f"High Risk Gap: {safe_gap}"
                        
                        prop_text = item.get('proposal', 'Action Required')
                        action_text = ""
                        if prop_text:
                            action_text = prop_text.replace('ACTION REQUIRED: ', '').split('<br>')[0]

                        # Custom HTML Decision Header
                        st.markdown(f"""
                        <div style="background-color: #FEFCE8; border-bottom: 1px solid #FDE047; padding-bottom: 12px; margin-bottom: 12px;">
                            <div style="font-weight: 700; color: #854D0E; font-size: 1rem; margin-bottom: 8px;">
                                ⚠️ {safe_reason}
                            </div>
                            <div style="color: #713F12; font-size: 0.9rem;">
                                <strong>Guidance:</strong> {action_text}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Widget Area (Visually connected by proximity)
                        
                        # Extract options (safely handle dicts or strings)
                        options = []
                        label_map = {}
                        reason_map = {}
                        seen_options = set()
                        
                        raw_roles = item.get("eligible_roles", [])
                        for r in raw_roles:
                            opt_str = ""
                            short_label = ""
                            why_text = ""
                            
                            if isinstance(r, dict):
                                company = r.get('company', 'Unknown')
                                why = r.get('why_eligible', '')
                                
                                # IMMEDIATE UI FILTER: partial match for headers
                                if any(bad in company.upper() for bad in ["PROFESSIONAL EXPERIENCE", "WORK HISTORY", "EXPERIENCE", "SUMMARY", "SKILLS", "EDUCATION"]):
                                    continue
                                
                                opt_str = f"{company} ({why})"
                                
                                # Hybrid Label logic
                                short_why = (why[:45] + '..') if len(why) > 45 else why
                                if short_why:
                                    short_label = f"📍 {company} — {short_why}"
                                else:
                                    short_label = f"📍 {company}"
                                    
                                why_text = why
                            else:
                                opt_str = str(r)
                                short_label = f"📍 {str(r)[:30]}..." if len(str(r)) > 30 else f"📍 {str(r)}"
                                why_text = "General placement"
                            
                            # Normalize for deduplication
                            norm_key = opt_str.strip()
                            
                            if norm_key not in seen_options:
                                options.append(norm_key)
                                label_map[norm_key] = short_label
                                reason_map[norm_key] = why_text
                                seen_options.add(norm_key)
                        
                        other_opt = "Other (Reason in notes)"
                        options.append(other_opt)
                        label_map[other_opt] = "✏️ Other / Custom"
                        reason_map[other_opt] = "Specify reason in notes or mental prompt"
                        
                        selected_option = st.selectbox(
                            "Select a role to re-focus:",
                            options,
                            format_func=lambda x: label_map.get(x, x),
                            key=f"decision_select_{i}"
                        )
                        
                        # Show extended context ONLY if truncated in dropdown (cutoff was 45 chars)
                        if selected_option in reason_map:
                             full_reason = reason_map[selected_option]
                             # If reason is long, show it fully here. If short, it's already in the dropdown label.
                             if len(full_reason) > 40:
                                 st.caption(f"**Detailed Context:** {full_reason}")
                        
                        strategy_choice = st.radio(
                            "Optimization Strategy:",
                            ["🔄 Pivot Context (Reframe Role)", "➕ Add Specific Bullets"],
                            key=f"strategy_{i}",
                            help="Pivot: Rewrites the role to feature this skill (Good for Platforms). Add: Inserts 1-2 new bullets (Good for Tools)."
                        )
                        
                        if st.button("✨ Apply Fix & Generate Rewrite", key=f"fix_btn_{i}"):
                            with st.spinner(f"Applying {strategy_choice} for {item.get('gap')}..."):
                                from suggestions import regenerate_single_suggestion
                                # Create a synthetic 'rejected' item that guides the regeneration
                                context_item = item.copy()
                                context_item["type"] = "rewrite_bullet"
                                context_item["proposal"] = "USER_DECISION_CONTEXT"
                                
                                # Map Selection to Strategy Code
                                context_item["optimization_strategy"] = "PIVOT" if "Pivot" in strategy_choice else "ADD_BULLETS"
                                
                                # ROBUST REASON EXTRACTION:
                                # If 'gap' is missing (e.g. from a restored state), try to parse it from 'reason' text.
                                raw_gap = item.get("gap")
                                if not raw_gap:
                                    raw_reason = str(item.get("reason", ""))
                                    if "High Risk Gap:" in raw_reason:
                                        raw_gap = raw_reason.replace("High Risk Gap:", "").strip()
                                    else:
                                        raw_gap = raw_reason # fallback to full reason text
                                
                                context_item["reason"] = raw_gap or "Missing Skill"
                                
                                # Pass user selection as specific instruction
                                context_item["user_selection"] = selected_option
                                
                                new_item = regenerate_single_suggestion(
                                    context_item, 
                                    st.session_state["resume_text"], 
                                    analysis.get("role_alignment", {}),
                                    api_key
                                )
                                # PERSIST DROPDOWN DATA: Ensure we don't lose the options if we switch back
                                new_item["eligible_roles"] = item.get("eligible_roles", [])
                                
                                # SAVE RESTORE STATE (Crucial for Undo)
                                # We save the FULL original item so we can revert exactly
                                new_item["_restore_state"] = item
                                
                                # Replace the Decision Card with the new Safe Proposal
                                st.session_state["optimization_plan"][i] = new_item
                                st.rerun()

                # ------------------------------------------------------------------
                # STANDARD CARDS
                # ------------------------------------------------------------------
                else:
                    # Custom HTML Card
                    warning_icon = "⚠️" if not is_recommended else ""
                    
                    # Context Line (Why here?)
                    context_html = ""
                    if placement_rationale:
                        context_html = f'<div style="font-size: 0.85rem; color: #475569; margin-top: 6px; font-style: italic;">Reference: {placement_rationale}</div>'

                    st.markdown(
                        textwrap.dedent(f"""
                        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="background: {badge_color}; color: {badge_text_color}; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">{item_type.upper()}</span>
                                    <span style="font-size: 0.75rem; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 2px 8px; border-radius: 4px;">📍 {target_section}</span>
                                </div>
                                <span style="color: #F59E0B;">{warning_icon}</span>
                            </div>
                            
                            <div style="font-size: 0.875rem; color: #334155; margin-bottom: 4px;"><strong>Gap:</strong> {reason}</div>
                            <div style="font-size: 1rem; font-weight: 500; color: #1E293B;">
                                {display_text}
                            </div>
                            {context_html}
                            {f'<div style="font-size: 0.8rem; color: #B45309; margin-top: 4px;">Note: {suitability_reason}</div>' if not is_recommended else ''}
                        </div>
                        """).replace("\n", ""),
                        unsafe_allow_html=True
                    )
            
            with c_regen:
                st.write("") # Spacer
                # Only show regen for normal items or the "Switch Role" for resolved decisions
                
                # Check if this was a user-resolved decision
                if item.get("user_selection") or item.get("_restore_state"):
                     # Stack buttons vertically in this narrow column (0.10 width)
                     # Using columns inside 0.10 width is bad.
                     
                     if st.button("↩️", key=f"reset_{i}", help="Undo Choice: Switch Role"):
                        # RESTORE ORIGINAL STATE
                        if item.get("_restore_state"):
                            st.session_state["optimization_plan"][i] = item["_restore_state"]
                        else:
                            # Fallback for older items (Partial Reset)
                            st.session_state["optimization_plan"][i]["type"] = "decision_required"
                            if "user_selection" in st.session_state["optimization_plan"][i]:
                                del st.session_state["optimization_plan"][i]["user_selection"]
                            if "proposal" in st.session_state["optimization_plan"][i]:
                                del st.session_state["optimization_plan"][i]["proposal"]
                                
                        st.rerun()
                     
                     if st.button("🔄", key=f"reroll_{i}", help="Re-Roll Bullets (Keep Strategy)"):
                         with st.spinner(".."):
                             from suggestions import regenerate_single_suggestion
                             new_item = regenerate_single_suggestion(
                                 item, 
                                 st.session_state["resume_text"], 
                                 analysis.get("role_alignment", {}),
                                 api_key
                             )
                             st.session_state["optimization_plan"][i] = new_item
                             st.rerun()
                    
                elif item.get("type") != "decision_required": # Standard Regen for non-decision items
                         if st.button("🔄", key=f"regen_item_{i}", help="Get a different suggestion for this gap"):
                            with st.spinner("Thinking..."):
                                from suggestions import regenerate_single_suggestion
                                new_item = regenerate_single_suggestion(
                                    item, 
                                    st.session_state["resume_text"], 
                                    analysis.get("role_alignment", {}),
                                    api_key
                                )
                                st.session_state["optimization_plan"][i] = new_item
                                st.rerun()
            
            # Only check if it's NOT a decision card (or we just allow checking normal items)
            if item_type != "decision_required" and is_checked:
                 approved_changes.append(item)
        
        st.write(f"selected {len(approved_changes)} changes.")

        if st.button("🚀 Apply Approved Changes & Generate Resume"):
            current_resume = st.session_state["resume_text"]
            remaining_changes = approved_changes
            final_report = []
            
            # MODERN PROGRESS UI
            with st.status("🏗️ Building your optimized resume...", expanded=True) as status:
                progress_bar = st.progress(0)
                
                # MULTI-PASS AGENT LOOP
                MAX_RETRIES = 2
                for attempt in range(MAX_RETRIES + 1):
                    pass_num = attempt + 1
                    status.write(f"**Pass {pass_num}/{MAX_RETRIES + 1}**: Applying {len(remaining_changes)} improvements via LLM...")
                    progress_bar.progress((attempt) / (MAX_RETRIES + 1) * 0.8) # Up to 80% is generation
                    
                    # 1. Apply Changes
                    optimized_resume = rewrite_resume(
                        resume_text=current_resume,
                        jd_text=st.session_state["jd_text"],
                        optimization_plan=remaining_changes,
                        role_intent=analysis.get("role_intent_alignment", "Medium"),
                        seniority_penalty=analysis.get("seniority_normalization_penalty", 0),
                        api_key=api_key
                    )
                    
                    # 2. Verify Result
                    status.write(f"🕵️ **Auditor Agent**: Verifying changes in Pass {pass_num}...")
                    report = verify_optimization(
                        st.session_state["resume_text"], 
                        optimized_resume, 
                        approved_changes, # Check FULL plan every time to ensure no regressions
                        api_key
                    )
                    
                    # 3. Analyze Failures
                    failed_items = []
                    for item in approved_changes:
                        # Find matching report item
                        report_item = next((r for r in report if r['proposal'] == (item.get('proposal') or item.get('proposed_text'))), None)
                        
                        if not report_item or report_item['status'] == 'FAILED':
                            retry_item = item.copy()
                            retry_item['type'] = "FORCE_INSERTION"
                            
                            # Clean the text: Extract just the content to insert
                            raw_proposal = item.get('proposal') or item.get('proposed_text')
                            if isinstance(raw_proposal, list):
                                clean_content = raw_proposal # Lists are presumed clean
                            else:
                                 clean_content = str(raw_proposal).replace("Rewrite bullet to include", "").replace("Rewrite bullet", "").strip(" '\"")
                            
                            retry_item['proposal'] = clean_content
                            failed_items.append(retry_item)
    
                    current_resume = optimized_resume
                    final_report = report
                    
                    if not failed_items:
                        status.write(f"✅ Pass {pass_num}: All changes applied and verified!")
                        break
                        
                    status.write(f"⚠️ Pass {pass_num}: Found {len(failed_items)} missing items. Retrying with forceful insertion strategy...")
                    remaining_changes = failed_items # Retry only what failed
                
                # FINAL STEP: DOCX GENERATION
                status.write("📄 Compiling Final DOCX document...")
                progress_bar.progress(0.9)
                time.sleep(0.5) # Fake delay for visual satisfaction
                
                progress_bar.progress(1.0)
                status.update(label="✅ Resume Optimized & Built!", state="complete", expanded=False)
                
            st.session_state["optimized_resume"] = current_resume
            st.session_state["verification_report"] = final_report
            st.rerun()

    # ---- PERSISTENT RESULTS ----
    if "optimized_resume" in st.session_state:
        optimized_resume = st.session_state["optimized_resume"]

    # ---- PERSISTENT RESULTS ----
    if "optimized_resume" in st.session_state:
        optimized_resume = st.session_state["optimized_resume"]

        st.markdown("### 📄 Optimized Resume Result")
        
        tab_preview, tab_raw = st.tabs(["👁️ Visual Preview", "📝 Copy Raw Text"])
        
        with tab_preview:
            # CSS for Resume Paper
            st.markdown("""
            <style>
            .resume-paper {
                background-color: white;
                color: black;
                padding: 40px;
                font-family: 'Times New Roman', Times, serif;
                font-size: 16px;
                line-height: 1.4;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-radius: 4px;
                max-width: 800px;
                margin: 0 auto;
            }
            .resume-name {
                text-align: center;
                font-weight: bold;
                font-size: 24px;
                text-transform: uppercase;
                margin-bottom: 5px;
            }
            .resume-contact {
                text-align: center;
                font-size: 14px;
                margin-bottom: 20px;
            }
            .resume-section {
                text-transform: uppercase;
                font-weight: bold;
                border-bottom: 2px solid #333;
                margin-top: 20px;
                margin-bottom: 10px;
                padding-bottom: 2px;
                font-size: 16px;
            }
            .resume-role-row {
                display: flex;
                justify-content: space-between;
                font-weight: bold;
                margin-top: 10px;
            }
            .resume-company { font-weight: bold; }
            .resume-date { font-weight: bold; text-align: right; }
            .resume-role-title {
                font-style: italic;
                margin-bottom: 5px;
            }
            .resume-ul {
                margin: 5px 0;
                padding-left: 20px;
            }
            .resume-li {
                margin-bottom: 3px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # PARSER LOGIC
            def render_resume_to_html(text):
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                html = '<div class="resume-paper">'
                
                if not lines:
                    return html + "</div>"

                # 1. Name & Contact (Heuristic: First 2 lines)
                html += f'<div class="resume-name">{lines[0]}</div>'
                if len(lines) > 1:
                    html += f'<div class="resume-contact">{lines[1]}</div>'
                
                # Regex for Date Detection (Month Year or Year - Present)
                # Matches: "Aug 2024 - Present", "May 2021 - Jul 2023", "Jun 2019 - May 2021"
                # Regex for Date Detection (Month Year or Year - Present)
                # Should match Hyphen, En-dash, Em-dash
                date_pattern = re.compile(r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})\s*[-–—]\s*(Present|Now|Current|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})', re.IGNORECASE)
                
                heading_pattern = re.compile(r'^(PROFESSIONAL|WORK|EDUCATION|SKILLS|TECHNICAL|PROJECTS|CERTIFICATIONS|SUMMARY)', re.IGNORECASE)

                in_ul = False
                in_experience = False # Track if we are in bullet-heavy section
                i = 2
                
                while i < len(lines):
                    line = lines[i]
                    
                    # Check for Section Header (ALL CAPS or known keywords, no bullets)
                    is_bullet = line.startswith('•') or line.startswith('-') or line.startswith('*')
                    is_all_caps = line.isupper() and len(line) > 3 and not is_bullet
                    is_known_header = heading_pattern.match(line) and not is_bullet
                    
                    if in_ul and not is_bullet:
                        html += '</ul>'
                        in_ul = False
                    
                    if is_all_caps or is_known_header:
                        html += f'<div class="resume-section">{line}</div>'
                        
                        # Update Section Context
                        upper_line = line.upper()
                        if any(k in upper_line for k in ["EXPERIENCE", "WORK", "PROJECTS", "SKILLS"]):
                            in_experience = True
                        elif any(k in upper_line for k in ["SUMMARY", "PROFILE", "EDUCATION", "CERTIFICATION"]):
                            in_experience = False
                            
                        i += 1
                        continue
                        
                    # Clean potential bullets from start of line for detection purposes
                    clean_line_check = line.lstrip('•-* ').strip()
                    
                    # Role / Company Detection
                    # Check if THIS line (cleaned) has a date
                    date_match = date_pattern.search(clean_line_check)
                    
                    # Check if NEXT line has a date parsing
                    next_line_date = None
                    if i + 1 < len(lines):
                         clean_next = lines[i+1].lstrip('•-* ').strip()
                         next_line_date = date_pattern.search(clean_next)
                    
                    if date_match and len(line) < 100:
                        # Single line: "Company   Date"
                        span = date_match.span()
                        
                        # Use clean text for the split to avoid bullet issues
                        date_str = clean_line_check[span[0]:]
                        company_str = clean_line_check[:span[0]].strip()
                        
                        html += f'''
                        <div class="resume-role-row">
                            <span class="resume-company">{company_str}</span>
                            <span class="resume-date">{date_str}</span>
                        </div>
                        '''
                        i += 1
                        # Check for Title on next line
                        if i < len(lines):
                             # Clean potential bullet from title too
                             clean_title = lines[i].lstrip('•-* ').strip()
                             # Heuristic: If it's short and not all caps, it's likely a title
                             if not clean_title.isupper() and len(clean_title) < 80:
                                  html += f'<div class="resume-role-title">{clean_title}</div>'
                                  i += 1
                             
                    elif next_line_date and not is_bullet:
                        # Multi-line: "Company" (line i) \n "Date" (line i+1)
                        # NOTE: matches if current line is NOT bullet, but next IS date (bulleted or not)
                        company_str = line
                        # Use clean next line for date
                        date_str = lines[i+1].lstrip('•-* ').strip()
                        
                        html += f'''
                        <div class="resume-role-row">
                            <span class="resume-company">{company_str}</span>
                            <span class="resume-date">{date_str}</span>
                        </div>
                        '''
                        i += 2 # Consumed both lines
                        
                        # Check for Title on next line (i)
                        if i < len(lines):
                             clean_title = lines[i].lstrip('•-* ').strip()
                             if not clean_title.isupper() and len(clean_title) < 80:
                                  html += f'<div class="resume-role-title">{clean_title}</div>'
                                  i += 1
                    
                    elif is_bullet:
                        if not in_ul:
                            html += '<ul class="resume-ul">'
                            in_ul = True
                        clean_text = line.lstrip('•-* ').strip()
                        # BOLD logic: **text** -> <strong>text</strong>
                        clean_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', clean_text)
                        html += f'<li class="resume-li">{clean_text}</li>'
                        i += 1
                        continue
                    else:
                        # Just a paragraph
                        # HEURISTIC: If text is long (>60 chars) AND we are in Experience/Projects, force bullet.
                        # ELSE (Summary, Education), keep as paragraph.
                        if len(line) > 60 and in_experience:
                             if not in_ul:
                                html += '<ul class="resume-ul">'
                                in_ul = True
                             clean_text = line.lstrip('•-* ').strip()
                             clean_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', clean_text)
                             html += f'<li class="resume-li">{clean_text}</li>'
                        else:
                             # Short text -> Title or Heading or Info OR Summary Paragraph
                             clean_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                             html += f'<div>{clean_text}</div>'
                        i += 1
                
                if in_ul:
                    html += '</ul>'
                
                html += '</div>'
                return html

            preview_html = render_resume_to_html(optimized_resume)
            st.markdown(preview_html, unsafe_allow_html=True)

        with tab_raw:
            st.text_area(
                "Copy Raw Text",
                optimized_resume,
                height=600,
                label_visibility="collapsed"
            )

        # Verification Report
        if "verification_report" in st.session_state:
            with st.expander("🕵️ Change Verification Report", expanded=True):
                for v in st.session_state["verification_report"]:
                    status = v.get("status", "UNKNOWN")
                    icon = "✅" if status == "VERIFIED" else "❌"
                    color = "green" if status == "VERIFIED" else "red"
                    
                    st.markdown(f":{color}[{icon} **{v.get('proposal')}**]")
                    if status != "VERIFIED":
                         st.caption(f"Reason: {v.get('notes', 'No evidence found')}")
                    else:
                         st.caption(f"Evidence: {v.get('evidence', 'Confirmed')}")

        # Create Downloadable DOCX
        docx_file = "Optimized_Resume.docx"
        create_docx(optimized_resume, docx_file)
        
        st.success("✅ DOCX Generated Successfully!")
        with open(docx_file, "rb") as f:
            st.download_button(
                label="📄 Download Optimized Resume (DOCX)",
                data=f,
                file_name="Optimized_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )
        
        st.write("") # Spacer

        # ---- LENGTH REFINER (POST-PROCESSING) ----
        # Check for bloated roles
        from suggestions import analyze_role_length, condense_role_content
        bloated_roles = analyze_role_length(optimized_resume)
        
        if bloated_roles:
            st.divider()
            st.markdown("### 📏 Resume Length Refiner")
            st.info(f"Found {len(bloated_roles)} roles with more than 6 bullets. You can condense them automatically.")
            
            with st.expander("Select Roles to Condense", expanded=True):
                selected_ids = []
                for r in bloated_roles:
                    # User requested format: "HCA Healthcare x bullets->target 6"
                    clean_header = r['header'].replace('*', '').strip()
                    label = f"{clean_header} {r['bullet_count']} bullets -> target 6"
                    
                    if st.checkbox(label, key=f"condense_{r['id']}"):
                        selected_ids.append(r)
                
                if selected_ids and st.button("✨ Condense Selected & Update Resume"):
                    progress_bar = st.progress(0)
                    updated_text = optimized_resume
                    
                    for i, r in enumerate(selected_ids):
                        with st.spinner(f"Condensing {r['header']}..."):
                            collapsed_bullets = condense_role_content(r['full_text'], api_key)
                            
                            # Replace in text (Find full block match)
                            # We construct a replacement block
                            # Header + New Bullets
                            new_block = r['header'] + "\n" + collapsed_bullets
                            
                            # Strict Replace? Text might have changed slightly if there are duplicates...
                            # We try to replace the captured 'full_text'
                            updated_text = updated_text.replace(r['full_text'], new_block)
                            
                            progress_bar.progress((i + 1) / len(selected_ids))
                            
                    st.session_state["optimized_resume"] = updated_text
                    st.success("Resume updated! Review the preview above.")
                    st.rerun()

        # COVER LETTER GENERATOR UI
        st.divider()
        if st.button("📝 Generate Tailored Cover Letter"):
            with st.spinner("Writing a professional cover letter based on your resume and this JD..."):
                from utils import generate_cover_letter_content, create_cover_letter_docx
                # Force reload of utils to get new function if cached
                import utils
                import importlib
                importlib.reload(utils)
                
                cl_content = utils.generate_cover_letter_content(
                    st.session_state["resume_text"], 
                    st.session_state["jd_text"], 
                    api_key
                )
                
                st.session_state["cover_letter_content"] = cl_content
        
        if "cover_letter_content" in st.session_state:
            import utils # Ensure module is available for docx creation
            st.subheader("📝 Cover Letter Preview")
            cl_edited = st.text_area("Edit Cover Letter:", st.session_state["cover_letter_content"], height=300)
            
            # Create DOCX
            cl_file = "Cover_Letter.docx"
            utils.create_cover_letter_docx(cl_edited, cl_file)
            
            with open(cl_file, "rb") as f:
                st.download_button(
                    label="📄 Download Cover Letter (DOCX)",
                    data=f,
                    file_name="Cover_Letter.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
        # ---- RE-ANALYSIS ----
        if st.button("📊 Analyze Optimized Resume vs JD", type="secondary"):
            with st.spinner("Re-analyzing new resume..."):
                raw_new_analysis = analyze_resume(optimized_resume, st.session_state["jd_text"], api_key)
                # Apply the same Verification + Scoring logic as the initial analysis
                new_analysis = verify_analysis_integrity(raw_new_analysis, optimized_resume, st.session_state["jd_text"], api_key)
                
                # Display Score
                relevance_score = new_analysis.get("overall_relevance_score", 0)
        
                # Check Role Alignment
                role_alignment = new_analysis.get("role_alignment", {"match_status": "Aligned", "reason": ""})
                if role_alignment.get("match_status") in ["Mismatch", "Partial"]:
                    st.error(f"⚠️ **ROLE MISMATCH DETECTED**: {role_alignment.get('reason')}")
                    # Visual penalty indication
                    st.caption(f"Status: {role_alignment.get('match_status')}")

                # Score Card
                score_val = new_analysis.get("overall_relevance_score", 0)
                band = new_analysis.get("ats_ranking_band", "Low")
                
                score_color = "#4F46E5"
                if score_val >= 90: score_color = "#16A34A"
                elif score_val < 60: score_color = "#DC2626"
                elif score_val < 75: score_color = "#D97706"

                st.markdown(f"""
                <div class="score-card" style="border-color: {score_color}; margin-bottom: 20px;">
                    <div class="score-value" style="color: {score_color};">{score_val}</div>
                    <div class="score-label">{band} Match (Optimized)</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Basic Quals
                st.subheader("✅ Qualification Alignment Check (Optimized)")
                
                for item in new_analysis.get("basic_qualification_match", []):
                    status = item.get("match_status", "Missing")
                    badge_class = "badge-missing"
                    if status == "Full": badge_class = "badge-full"
                    elif status == "Partial": badge_class = "badge-partial"
                    
                    st.markdown(
                        f"""
                        <div class="opt-item">
                            <span class="{badge_class}">{status.upper()}</span>
                            <span style="font-weight: 600; color: #1E293B;">{item.get('requirement', 'Unknown')}</span>
                            <div style="margin-top: 8px; font-size: 0.9rem; color: #64748B;">
                                {item.get('notes', '')}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Preferred Quals
                st.subheader("🌟 Preferred / Bonus Qualifications (Optimized)")
                
                for item in new_analysis.get("preferred_qualification_match", []):
                    status = item.get("match_status", "Missing")
                    badge_class = "badge-missing"
                    if status == "Full": badge_class = "badge-full"
                    elif status == "Partial": badge_class = "badge-partial"
                    
                    st.markdown(
                        f"""
                        <div class="opt-item" style="border-left: 3px solid #E2E8F0;">
                            <span class="{badge_class}">{status.upper()}</span>
                            <span style="color: #334155;">{item.get('requirement', 'Unknown Preference')}</span>
                            <div style="margin-top: 4px; font-size: 0.85rem; color: #64748B;">
                                {item.get('notes', '')}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
