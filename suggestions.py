import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
from dotenv import load_dotenv

load_dotenv()

def get_llm(api_key):
    return ChatOpenAI(
        model_name="gpt-4o",
        openai_api_key=api_key,
        temperature=0.0,
        model_kwargs={"seed": 42}
    )

def extract_company_names(resume_text: str) -> List[str]:
    """
    Heuristically extracts company/role names based on date patterns.
    """
    import re
    
    # Normalize newlines
    clean_text = resume_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.strip() for l in clean_text.split('\n') if l.strip()] 
    
    # 1. Complex Date Pattern (Month Year - Present)
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\.,]?\s+\d{4}|\d{1,2}/\d{4}|(?:19|20)\d{2})\s*[-–to]+\s*(?:Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\.,]?\s+\d{4}|\d{1,2}/\d{4}|(?:19|20)\d{2})'
    
    candidates = []
    
    for i, line in enumerate(lines):
        match = re.search(date_pattern, line, re.IGNORECASE)
        if match:
            # Case A: Date is on the same line
            start_idx = match.start()
            if start_idx > 5:
                content_before = line[:start_idx].strip()
                content_clean = content_before.rstrip(" -–,")
                if len(content_clean) > 4:
                        candidates.append(content_clean)
            
            # Case B: Date is on next line, Role/Company is previous line
            elif i > 0:
                prev_line = lines[i-1].strip()
                if len(prev_line) > 3 and len(prev_line) < 60:
                    if "Employment" not in prev_line and "Experience" not in prev_line:
                        candidates.append(prev_line)
    
    # 2. Simple Year/Present Pattern (Broader Fallback)
    else:
        # Matches "2024 - Present", "2020 - 2023", "Oct 2022 - Present"
        year_pattern = r'.*\d{4}.*(?:Present|Current|Now|\d{4})'
        for i, line in enumerate(lines):
            # Exclude long paragraphs
            if len(line) < 100:
                match = re.search(year_pattern, line, re.IGNORECASE)
                if match:
                     print(f"DEBUG: Matched Date Line: '{line}'")
                     # Case A: Left side of line? "Company ... Date"
                     # Relaxed split: 2 spaces or tab
                     parts = re.split(r'\s{2,}|\t', line) 
                     if len(parts) > 1:
                         candidate = parts[0].strip()
                         # Check if candidate is likely a company (not just "Aug")
                         if len(candidate) > 3 and len(candidate) < 60 and not re.match(r'^[A-Za-z]{3}\s\d{4}$', candidate):
                             print(f"DEBUG: Extracted Candidate (Same Line): '{candidate}'")
                             candidates.append(candidate)
                     
                     # Case B: Prev line
                     elif i > 0:
                        prev_line = lines[i-1].strip()
                        print(f"DEBUG: Checking Prev Line: '{prev_line}'")
                        if len(prev_line) > 3 and len(prev_line) < 60:
                            if "Employment" not in prev_line and "Experience" not in prev_line and "Education" not in prev_line:
                                candidates.append(prev_line)

    # Dedup and limit
    unique_candidates = sorted(list(set(candidates)))[:6]
    print(f"DEBUG: Final Extracted Companies: {unique_candidates}")
    return unique_candidates

def analyze_role_length(resume_text: str) -> List[Dict]:
    """
    Parses resume text to find roles with > 6 bullets.
    Returns list of {'id': int, 'header': str, 'bullet_count': int, 'full_text': str}
    """
    import re
    
    # 1. Split into chunks by Companies (Heuristic)
    # Looking for lines that look like Headers (Short, no bullets, usually followed by date or bullets)
    lines = resume_text.split('\n')
    roles = []
    
    current_role = {"header": "Unknown", "bullets": [], "start_idx": 0}
    
    # Simple parser: A header is a line without a bullet that precedes lines with bullets
    # This is tricky on raw text, so we rely on the bullet character '•' or '-'
    
    for i, line in enumerate(lines):
        clean_line = line.strip()
        # More robust bullet detection
        is_bullet = clean_line.startswith('•') or clean_line.startswith('- ') or clean_line.startswith('* ')
        
        if is_bullet:
            current_role["bullets"].append(line)
        else:
            # Possible Header?
            # If previous role had bullets, close it
            if len(current_role["bullets"]) > 0:
                print(f"DEBUG: Found Role '{current_role['header']}' with {len(current_role['bullets'])} bullets")
                # Save previous
                if len(current_role["bullets"]) > 5: # Changed to > 5 to be more inclusive
                    roles.append({
                        "id": len(roles),
                        "header": current_role["header"],
                        "bullet_count": len(current_role["bullets"]),
                        "full_text": "\n".join([current_role["header"]] + current_role["bullets"])
                    })
                
                # Start new
                # IGNORE SECTION HEADERS
                is_section_header = any(keyword in clean_line.upper() for keyword in ["EDUCATION", "SKILLS", "SUMMARY", "PROFESSIONAL EXPERIENCE", "WORK HISTORY", "EXPERIENCE"])
                
                if len(clean_line) > 3 and not is_section_header:
                    current_role = {"header": clean_line, "bullets": [], "start_idx": i}
            
            elif len(clean_line) > 3:
                 # Update header if we haven't started collecting bullets yet
                 # But avoid overwriting a valid header with a Section Header
                 is_section_header = any(keyword in clean_line.upper() for keyword in ["EDUCATION", "SKILLS", "SUMMARY", "PROFESSIONAL EXPERIENCE", "WORK HISTORY", "EXPERIENCE"])
                 
                 if not current_role["bullets"] and not is_section_header:
                    current_role["header"] = clean_line

    # Flush last
    if len(current_role["bullets"]) > 0:
        print(f"DEBUG: Found Role '{current_role['header']}' with {len(current_role['bullets'])} bullets")
        if len(current_role["bullets"]) > 5:
            roles.append({
                "id": len(roles),
                "header": current_role["header"],
                "bullet_count": len(current_role["bullets"]),
                "full_text": "\n".join([current_role["header"]] + current_role["bullets"])
            })
        
    return roles

def condense_role_content(role_text: str, api_key: str) -> str:
    """
    Rewrites a role description to be exactly 5-6 bullets.
    """
    llm = get_llm(api_key)
    
    prompt = """
    You are a Resume Editor.
    
    TASK: Condense the following role description into EXACTLY 5-6 high-impact bullets.
    
    RULES:
    1. Merge similar points.
    2. Preserve ALL metrics (%, $).
    3. Preserve ALL specific technologies (Java, AWS, etc).
    4. Output ONLY the lines starting with "•".
    5. No intro/outro.
    
    INPUT ROLE:
    {role_text}
    """
    
    from langchain_core.prompts import PromptTemplate
    chain = PromptTemplate.from_template(prompt) | llm
    
    res = chain.invoke({"role_text": role_text})
    content = res.content if hasattr(res, 'content') else str(res)
    
    # Cleanup
    lines = [l for l in content.split('\n') if "•" in l or "-" in l]
    return "\n".join(lines)


def generate_tailoring_suggestions(
    resume_text: str,
    basic_gaps: List[Dict],
    preferred_gaps: List[Dict],
    role_alignment_data: Dict,
    api_key: str
) -> List[Dict]:
    """
    Generates a list of specific proposed edits to fix the identified gaps.
    """
    llm = get_llm(api_key)

    # PRE-CALCULATE KNOWN COMPANIES
    known_companies = extract_company_names(resume_text)
    known_companies_str = ", ".join(known_companies) if known_companies else "None detected (Please Scan Resume Text Manually)"

    # Prepare gap text
    basic_gap_text = "\n".join([f"- {item['requirement']} (Notes: {item.get('notes', '')})" for item in basic_gaps if item['match_status'] != 'Full' or "Missing" in item.get('notes', '')])
    preferred_gap_text = "\n".join([f"- {item['requirement']} (Notes: {item.get('notes', '')})" for item in preferred_gaps if item['match_status'] != 'Full' or "Missing" in item.get('notes', '')])

    
    # ITERATIVE GENERATION LOOP
    MAX_RETRIES = 3
    feedback = ""
    
    for attempt in range(MAX_RETRIES):
        print(f"DEBUG: Generation Attempt {attempt + 1}/{MAX_RETRIES}")
        
        full_template = """
        You are a Resume Optimization Planner with Auditor-Level Safety Constraints.

        GOAL:
        Analyze the resume and gaps to produce a safe optimization plan.
        
        MISSING SKILLS:
        {basic_gap_text}
        
        PREFERRED SKILLS:
        {preferred_gap_text}

        RESUME CONTENT:
        {resume_text}

        KNOWN COMPANIES (FROM PARSER):
        [{known_companies_str}]

        You MUST NOT directly propose resume edits for HIGH-RISK gaps.
        Your task is to PRODUCE ONE OF TWO OUTPUT TYPES for each gap:

        ====================
        TYPE A: USER DECISION REQUIRED
        ====================
        Return this if the gap requires re-framing experience.

        Criteria:
        • The skill is NOT explicitly present in the resume
        • The skill changes execution context (cloud, framework, platform)
        • Adding it would imply hands-on production experience

        INSTRUCTION FOR ELIGIBLE ROLES:
        - **STEP 1**: Check the 'KNOWN COMPANIES' list above. Use those if valid.
        - **STEP 2 (FALLBACK)**: If 'KNOWN COMPANIES' is empty/insufficient, SCAN THE RESUME TEXT for Company Names.
        - You MUST return the COMPANY NAME (e.g. "Google", "Amazon"). 
        - DO NOT return generic titles like "Senior Engineer" without the Company Name.
        - Format as "Company Name (Role)".
        - Select 2-3 specific assignments where this skill fits.

        Output format (JSON):
        {{
          "action": "USER_DECISION_REQUIRED",
          "gap": "<Skill name>",
          "risk_reason": "Why auto-inserting this would be misleading",
          "eligible_roles": [
              {{"company": "Company Name (Role)", "why_eligible": "High relevance to skill"}},
              {{"company": "Other Company (Role)", "why_eligible": "Duration/Seniority fit"}}
          ],
          "user_prompt": "Which role (if any) should be re-focused to align with this requirement?"
        }}

        ====================
        TYPE B: SAFE EDIT PROPOSAL
        ====================
        Only allowed if ALL are true:
        • Skill is already present OR
        • Change is purely wording / emphasis OR
        • Change does NOT imply new production experience

        Output format (JSON):
        {{
          "action": "SAFE_PROPOSAL",
          "type": "rewrite_bullet" | "add_skill",
          "target_section": "Name of Company/Role or 'Skills Section'",
          "proposal": "The text of the change",
          "reason": "1-line ATS or JD alignment reason",
          "placement_rationale": "Why this specific section?",
          "is_recommended": true,
          "suitability_reason": "Safe to add / Verify experience"
        }}

        ====================
        ABSOLUTE RULES
        ====================
        • Never auto-add a cloud provider if it is absent from resume history
        • Never change company names
        • Never change primary skills (Java, Spring Boot, etc.)
        • Never invent migrations or certifications
        • If unsure, default to TYPE A.

        CRITICAL OUTPUT INSTRUCTION:
        Return a JSON LIST containing a mix of Type A and Type B objects.
        """
        
        feedback_section = ""
        if feedback:
            feedback_section = f"PREVIOUS ATTEMPT REJECTED. FEEDBACK:\n{feedback}\n\nCORRECT THESE ISSUES."

        chain = PromptTemplate(
            input_variables=["resume_text", "basic_gap_text", "preferred_gap_text", "role_mismatch_status", "role_mismatch_reason", "feedback_section", "known_companies_str"],
            template=full_template
        ) | llm
        
        response = chain.invoke({
            "resume_text": resume_text, 
            "basic_gap_text": basic_gap_text, 
            "preferred_gap_text": preferred_gap_text,
            "role_mismatch_status": role_alignment_data.get("match_status", "Aligned"),
            "role_mismatch_reason": role_alignment_data.get("reason", "N/A"),
            "feedback_section": feedback_section,
            "known_companies_str": known_companies_str
        })
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            raw_plan = json.loads(content)
            plan = []

            # ADAPTER: Normalize LLM output to UI schema
            for item in raw_plan:
                action = item.get("action", "SAFE_PROPOSAL")
                
                if action == "USER_DECISION_REQUIRED" or "High Risk" in item.get("reason", "") or "High Risk" in item.get("risk_reason", "") or item.get("eligible_roles"):
                    # Format eligible roles for display
                    roles = item.get("eligible_roles", [])
                    
                    # --- CRITICAL FIX: ALWAYS MERGE HEURISTIC ROLES ---
                    # Don't rely on 'len(roles) < 2'. Force merge known companies.
                    known_companies = extract_company_names(resume_text)
                    existing_names = [str(r.get('company', '')) if isinstance(r, dict) else str(r) for r in roles]
                    
                    for c in known_companies:
                        # Append if not already roughly present - basic fuzzy match
                        is_present = False
                        for name in existing_names:
                            if c in name or name in c:
                                is_present = True
                                break
                        
                        if not is_present:
                             roles.append({"company": c, "why_eligible": "Detected from Resume Timeline"})
                                
                    role_str = ""
                    if roles:
                        role_str = "<br><br><b>SUGGESTED OPTIONS:</b>"
                        for r in roles:
                            if isinstance(r, dict):
                                company = r.get('company', 'Unknown Role')
                                reason = r.get('why_eligible', '')
                                role_str += f"<br>• {company} <i>({reason})</i>"
                            else:
                                role_str += f"<br>• {str(r)}"

                    # Convert to a UI-friendly warning card
                    plan.append({
                        "type": "decision_required", # Special type we can style or handle
                        "target_section": "Manual Decision",
                        "proposal": f"ACTION REQUIRED: {item.get('user_prompt')}{role_str}",
                        "reason": f"High Risk Gap: {item.get('gap')}",
                        "gap": item.get('gap'), # Explicitly pass gap for the resolver
                        "eligible_roles": roles, # Explicitly pass roles for the selector
                        "placement_rationale": "AI Safety Protocol triggered.",
                        "is_recommended": False,
                        "suitability_reason": f"⚠️ {item.get('risk_reason')}"
                    })
                else:
                    # Standard Proposal (clean up keys if needed)
                    plan.append({
                        "type": item.get("type", "rewrite_bullet"),
                        "target_section": item.get("target_section", "Experience"),
                        "proposal": item.get("proposal", ""),
                        "reason": item.get("reason", "Optimization"),
                        "placement_rationale": item.get("placement_rationale", ""),
                        "is_recommended": item.get("is_recommended", True),
                        "suitability_reason": item.get("suitability_reason", "Verified")
                    })

            # --- FORCE ROLE CORRECTION IF IGNORED ---
            if "Mismatch" in role_alignment_data.get("match_status", "") or "Partial" in role_alignment_data.get("match_status", ""):
                has_rewrite = any(
                    "Professional Summary" in item.get('reason', '') or 
                    "Title" in item.get('reason', '') or 
                    "rewrite_bullet" in item.get('type', '') 
                    for item in plan
                )
                
                if not has_rewrite:
                    print("DEBUG: Injecting Mandatory Title Rewrite.")
                    plan.insert(0, {
                        "type": "rewrite_bullet",
                        "section": "Professional Summary",
                        "proposal": f"Rewrite Header/Summary to align with '{role_alignment_data.get('reason', 'Target Role')}'. Focus on transferrable skills.",
                        "reason": f"CRITICAL ROLE MISMATCH: {role_alignment_data.get('reason', 'Title mismatch')}",
                        "is_recommended": True,
                        "suitability_reason": "Essential to pass the ATS Role Filter."
                    })
            
            # --- VERIFICATION STEP ---
            print("DEBUG: Running Verifier...")
            verification = verify_suggestions_relevance(plan, resume_text, basic_gap_text + "\n" + preferred_gap_text, api_key)
            
            if verification.get("status") == "VALID":
                print("DEBUG: Plan Verified.")
                return plan
            else:
                feedback = verification.get("feedback", "Invalid plan.")
                print(f"DEBUG: Plan Rejected. Feedback: {feedback}")
                
        except Exception as e:
            print(f"ERROR processing generation: {e}")
            feedback = f"JSON Parsing Error or System Error: {str(e)}"

    print("WARNING: Max retries reached. Returning last attempt.")
    # Return the last generated plan (if it exists) rather than empty string, 
    # so the user sees *something* even if the verifier wasn't fully satisfied.
    if 'plan' in locals() and plan:
        return plan
    return []

def verify_suggestions_relevance(plan: List[Dict], resume_text: str, gaps: str, api_key: str) -> Dict:
    """
    Audits the proposed plan for hallucination and relevance.
    """
    llm = get_llm(api_key)
    
    plan_text = json.dumps(plan, indent=2)
    
    prompt = """
    You are a Strict Resume Auditor.
    
    Review this Optimization Plan.
    
    GAPS TO FILL:
    {gaps}
    
    PROPOSED PLAN:
    {plan_text}
    
    RESUME CONTEXT:
    {resume_text}
    
    CHECKLIST:
    1. Do the proposals actually address the Gaps?
    2. Are the "rewrite_bullet" suggestions FACTUALLY PLAUSIBLE based on the resume?
       - Bad: Suggesting "Built AI models" for a pure Frontadmin role.
       - Good: Suggesting "Collaborated with AI teams" for the same role.
    3. Are "is_recommended" flags correctly set? (False for high-risk changes).
    
    OUTPUT JSON:
    {{
        "status": "VALID" | "INVALID",
        "feedback": "If INVALID, explain specifically what is wrong so the generator can fix it."
    }}
    """
    
    chain = PromptTemplate(input_variables=["plan_text", "resume_text", "gaps"], template=prompt) | llm
    
    try:
        res = chain.invoke({"plan_text": plan_text, "resume_text": resume_text, "gaps": gaps})
        content = res.content if hasattr(res, 'content') else str(res)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        print(f"Verification Error: {e}")
        return {"status": "VALID"} # Fail open if verifier crashes

def regenerate_single_suggestion(
    item: Dict, 
    resume_text: str, 
    role_alignment_data: Dict, 
    api_key: str
) -> Dict:
    """
    Regenerates a SINGLE suggestion that was rejected by the user.
    """
    llm = get_llm(api_key)
    
    prompt = """
    You are a Senior Resume Consultant.
    
    TASK: RESUME ROLE REWRITE (FULL CONTEXT).
    
    CONTEXT:
    The user wants to address this gap: "{reason}"
    
    CURRENT STATUS:
    {user_instruction}
    
    RESUME CONTEXT:
    {resume_text}
    
    ROLE MISMATCH STATUS: {role_mismatch_status}
    
    INSTRUCTIONS:
    1. If "USER DECISION" context is present:
       - **STRATEGY CLARIFICATION**:
         - **CASE A: CORE PLATFORM CHANGE (GCP, Azure, AWS)**: 
           - **ACTION**: PERFROM A HARD PIVOT. You are re-writing history to match the target stack.
           - **REPLACE, DO NOT MIX**: If pivoting to '{reason}' (e.g. GCP), you MUST REMOVE mentions of the conflicting platform (e.g. AWS, Azure).
           
         - **CASE B: SPECIFIC TOOL ADDITION (Bedrock, Kafka)**: 
           - **ACTION**: SMART INTEGRATION. Only insert the tool into the 1-2 most relevant bullets.
           
         - **CASE C: ADD_BULLETS STRATEGY (User Requested)**:
           - **ACTION**: PRESERVE + APPEND. Keep the existing bullets exactly as they are.
           - **GENERATE**: Create 1-2 NEW, dense bullets focusing purely on '{reason}'.
           - **OUTPUT**: The combined list (Old Bullets + New Bullets).

       - **CRITICAL RULES**:
         - **NO KEYWORD SPAMMING**: Do NOT insert '{reason}' into every single bullet.
         - **Pivot vs Append**: Case A = REPLACE old tech. Case B = INSERT new tech.

       - Output the COMPLETE list of bullets for this role.

    2. If generic (User Rejected):
       - Just propose a single bullet alternative.

    OUTPUT JSON (Single Object):
    {{
        "type": "FULL_ROLE_REWRITE" | "rewrite_bullet",
        "target_section": "Name of Role/Company",
        "proposal": ["Bullet 1", "Bullet 2", "Bullet 3"] (IF Full Rewrite) OR "Single string" (IF single bullet),
        "reason": "{reason}",
        "is_recommended": true,
        "suitability_reason": "Contextually pivoted to highlight {reason}"
    }}
    """
    
    # Check if this is a Decision Resolution (User selected a role)
    if item.get("proposal") == "USER_DECISION_CONTEXT" or item.get("user_selection"):
        user_choice = item.get("user_selection", "Unknown")
        strategy = item.get("optimization_strategy", "PIVOT")
        
        if strategy == "PIVOT":
            action_prompt = (
                f"ACTION: PERFORM A HARD CONTEXT PIVOT (Reframe Role).\n"
                f"GOAL: Rewrite ALL bullets to make '{item.get('reason')}' the PRIMARY technology. \n"
                f"RULES: REPLACE conflicting tech (e.g. AWS->GCP). Do not just append.\n"
                f"OUTPUT MODE: FULL_ROLE_REWRITE (Return Old + New merged list)."
            )
            output_type = "FULL_ROLE_REWRITE"
            warning = "WARNING: Return the FULL list (Old + New) so the final result is complete."
        else: # ADD_BULLETS
            action_prompt = (
                f"ACTION: APPEND NEW BULLETS (Preserve Context).\n"
                f"GOAL: Keep existing bullets AS IS. Generate 1-2 NEW, high-quality bullets specifically for '{item.get('reason')}'.\n"
                f"RULES: Focus purely on the add-on. Do NOT touch the original text.\n"
                f"OUTPUT MODE: APPEND_BULLETS (Return ONLY the new bullets)."
            )
            output_type = "APPEND_BULLETS"
            warning = "WARNING: Return ONLY the new bullets. Do not repeat the old ones."
            
        user_instruction = (
            f"USER DECISION: The user explicitly selected '{user_choice}' to address the gap '{item.get('reason')}'.\n"
            f"{action_prompt}\n"
            f"{warning}"
        )
    else:
        # Standard Regeneration (Rejection)
        prev_proposal = item.get("proposal") or item.get("proposed_text")
        user_instruction = f"USER REJECTED: '{prev_proposal}'. \nREASON: User wants a better alternative."
        output_type = "rewrite_bullet"

    chain = PromptTemplate(
        input_variables=["user_instruction", "reason", "resume_text", "role_mismatch_status"],
        template=prompt
    ) | llm
    
    try:
        res = chain.invoke({
            "user_instruction": user_instruction,
            "reason": item.get("reason", "Gap filling"),
            "resume_text": resume_text,
            "role_mismatch_status": role_alignment_data.get("match_status", "Aligned")
        })
        
        content = res.content if hasattr(res, 'content') else str(res)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        
        result_item = json.loads(content)
        
        # Override Type if Strategy Dictated it
        if item.get("proposal") == "USER_DECISION_CONTEXT" or item.get("user_selection"):
             if output_type == "APPEND_BULLETS":
                 result_item["type"] = "APPEND_BULLETS"
        
        # PERSIST CONTEXT: If this was a user decision, carry over the metadata
        if item.get("proposal") == "USER_DECISION_CONTEXT" or item.get("user_selection"):
            result_item["user_selection"] = item.get("user_selection")
            result_item["optimization_strategy"] = item.get("optimization_strategy")
            
        return result_item
        
    except Exception as e:
        print(f"Regeneration Error: {e}")
        return item



