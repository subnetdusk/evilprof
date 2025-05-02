# -*- coding: utf-8 -*-

# ================================================================
# EvilProf 😈 - Test Generator from Excel - v1.1
# ================================================================
# v1.1 Changes:
# - Implemented Weighted Random Sampling Without Replacement (WRSwOR).
# - Removed "Ensure different tests" checkbox.
# - Updated instructions.
# - Added validation test button.
# - Added banner.svg reference.
# ================================================================
# v1.1.1 (Internal): Translated all user-facing strings and comments to English.
# ================================================================


import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io
import os
import math

# Import and check for WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# ================================================================
# Introduction Text and Instructions (English)
# ================================================================
INTRO_TEXT = """
EvilProf is a web application built with Streamlit that allows you to quickly generate PDF files containing customized tests.

Key features include:

- **Input from Excel:** Easily upload your questions from an `.xlsx` or `.xls` file.
- **Question Types:** Supports both multiple-choice questions (with randomized answers) and open-ended questions.
- **Customization:** Choose the number of tests to generate, the number of questions per type (multiple/open) for each test, and the subject name.
- **Advanced Randomization:** Questions in each test are randomly selected from the pool available in the Excel file. The order of multiple-choice answers is also randomized.
- **Enhanced Diversity (with Fallback):** The application attempts to use a **Weighted Random Sampling Without Replacement (WRSwOR)** technique based on Algorithm A by Efraimidis and Spirakis (described in [this paper](https://ethz.ch/content/dam/ethz/special-interest/baug/ivt/ivt-dam/vpl/reports/1101-1200/ab1141.pdf)) to select questions. This method:
    - Attempts to **guarantee** that questions used in one test are not repeated in the *immediately following* test. This requires the total number of questions of a certain type (`n`) to be strictly greater than the number of questions of that type required per test (`k`), i.e., `n > k`.
    - Attempts to **statistically favor** the selection of questions that haven't been used for a longer time. For good rotation and long-term diversity, it is **strongly recommended** to have a total number of questions at least **three times higher** (`n >= 3k`) than those required per single test. The app will show a warning if `n < 3k` (and if there are no more critical errors or active fallbacks).
    - **Fallback:** If there are not enough unique questions available to guarantee diversity compared to the previous test (`n <= k`), the application will **switch to simple random sampling** from *all* available questions of that type, **losing the diversity guarantee** between adjacent tests. A prominent red warning will be displayed in this case.
- **PDF Output:** Generates a single PDF file ready for printing, with each test starting on a new page and a header for name, date, and class.

**Excel File Structure**

For the application to work correctly, the Excel file must adhere to the following structure **without column headers**:

- **Column A:** Contains the full text of the question.
- **Columns B, C, D, ...:** Contain the different answer options *only* for multiple-choice questions. There must be at least two answer options for the question to be considered multiple-choice.
- **Open-Ended Questions:** For an open-ended question, simply leave the cells in columns B, C, D, ... blank.
- *See example image below.*

---
"""

# ================================================================
# Helper Function for WRSwOR (Unchanged)
# ================================================================
def weighted_random_sample_without_replacement(population, weights, k):
    """Selects k unique items from population without replacement, respecting weights."""
    if k > len(population): raise ValueError(f"k ({k}) > len(population) ({len(population)})")
    if len(population) != len(weights): raise ValueError("len(population) != len(weights)")
    if k == 0: return []
    if k == len(population): result = list(population); random.shuffle(result); return result
    valid_indices = [i for i, w in enumerate(weights) if w > 0]
    if not valid_indices: raise ValueError("No items with positive weight available for sampling.")
    filtered_population = [population[i] for i in valid_indices]
    filtered_weights = [weights[i] for i in valid_indices]
    if k > len(filtered_population): raise ValueError(f"Not enough items with positive weight ({len(filtered_population)}) to sample k={k}.")
    keys = []
    for w in filtered_weights:
        u = random.uniform(0, 1); epsilon = 1e-9
        if u < epsilon: u = epsilon
        try: key = u**(1.0 / (w + epsilon))
        except OverflowError: key = 0.0
        keys.append(key)
    indexed_keys = list(zip(keys, range(len(filtered_population)))); indexed_keys.sort(key=lambda x: x[0], reverse=True)
    sampled_indices = [index for key, index in indexed_keys[:k]]
    return [filtered_population[i] for i in sampled_indices]

# ================================================================
# Function to Load Questions from Excel (English Status Messages)
# ================================================================
def load_questions_from_excel(uploaded_file, status_placeholder=None):
    """Loads questions/answers from Excel file (UploadedFile). Uses status_placeholder."""
    if uploaded_file is None: return None
    def update_status(message):
        if status_placeholder: status_placeholder.info(message)
        else: st.info(message) # Fallback if no placeholder provided
    try:
        if 'loaded_file_name' not in st.session_state or st.session_state.loaded_file_name != uploaded_file.name:
             update_status(f"⏳ Reading Excel file: {uploaded_file.name}...")
             st.session_state.loaded_file_name = uploaded_file.name
             st.session_state.excel_df = pd.read_excel(uploaded_file, header=None)
        else: update_status(f"ℹ️ Using already loaded data for: {uploaded_file.name}")
        df = st.session_state.excel_df
        questions_data = []; mc_count_temp = 0; oe_count_temp = 0; warnings = []
        for index, row in df.iterrows():
            row_list = [str(item) if pd.notna(item) else "" for item in row]; question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
            if question_text:
                if len(answers) >= 2: question_type = 'multiple_choice'; mc_count_temp += 1; questions_data.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': question_type})
                else: question_type = 'open_ended'; oe_count_temp += 1; questions_data.append({'question': question_text, 'answers': [], 'original_index': index, 'type': question_type})
                if len(answers) == 1: warnings.append(f"Warning: Question '{question_text[:50]}...' on row {index+1} has only 1 answer, treated as open-ended.")
            elif any(answers): warnings.append(f"Warning: Row {index+1} has answers but is missing the question and will be ignored.")
        for warning in warnings: st.warning(warning) # Display accumulated warnings
        if not questions_data: st.error(f"Error: No valid questions found in the file."); return None
        update_status(f"✅ Data loaded: {len(questions_data)} questions ({mc_count_temp} multiple-choice, {oe_count_temp} open-ended). Validating parameters...")
        return questions_data
    except Exception as e: st.error(f"Unexpected error reading Excel file: {e}"); return None

# ================================================================
# Function to Generate PDF (English Status Messages)
# ================================================================
# ================================================================
# PDF Generation Function (English Version)
# ================================================================
def generate_pdf_data(tests_data_lists, timestamp, subject_name, status_placeholder=None):
    """Generates the binary data of the PDF, without extra space for open questions and with reduced margin."""
    # Check if WeasyPrint is available
    if not WEASYPRINT_AVAILABLE:
        st.error("ERROR: WeasyPrint library not found/functional.")
        return None

    # Helper function to update status via placeholder or st.info
    def update_status(message):
        if status_placeholder:
            status_placeholder.info(message)
        else:
            st.info(message) # Fallback if no placeholder is provided

    update_status("⚙️ Starting PDF generation...")

    # CSS Updated: Reduced margin-bottom for .question
    css_style = """
         @page {
             size: A4;
             margin: 2cm;
         }
         body { font-family: Verdana, sans-serif; font-size: 11pt; line-height: 1.4; }
         .test-container { }
         .page-break { page-break-before: always; }
         h2 { margin-bottom: 0.8em; font-size: 1.6em; color: #000; font-weight: bold; }
         .pdf-header-info { margin-bottom: 2.5em; font-size: 1em; font-weight: normal; line-height: 1.6; }
         .header-line { display: flex; align-items: baseline; width: 100%; margin-bottom: 0.6em; }
         .header-label { white-space: nowrap; margin-right: 0.5em; flex-shrink: 0; }
         .header-underline { flex-grow: 1; border-bottom: 1px solid black; position: relative; top: -2px; min-width: 40px; }
         .class-label { margin-left: 2.5em; }
         .question {
             margin-top: 1.8em;
             margin-bottom: 0.4em; /* Reduced from 0.8em */
             font-weight: bold;
         }
         .answer { display: flex; align-items: baseline; margin-left: 2.5em; margin-top: 0.1em; margin-bottom: 0.3em; padding-left: 0; text-indent: 0; }
         .checkbox { flex-shrink: 0; margin-right: 0.6em; }
         .answer-text { }
         /* .open-answer-space { ... } Removed */
    """

    update_status("⚙️ Building HTML document...")
    html_parts = []
    checkbox_char = "☐"
    # Sanitize subject name for HTML
    safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;')

    # Iterate through each test's data
    for index, single_test_data in enumerate(tests_data_lists):
        # Changed "Test for" instead of "Verifica di"
        test_html = f"<h2>Test for {safe_subject_name}</h2>\n";
        # Header with Name, Date, Class (English labels)
        test_html += '<div class="pdf-header-info">\n <div class="header-line">\n <span class="header-label">Name:</span><span class="header-underline"></span>\n </div>\n <div class="header-line">\n <span class="header-label">Date:</span><span class="header-underline date-line"></span><span class="header-label class-label">Class:</span><span class="header-underline class-line"></span>\n </div>\n</div>\n'

        q_counter = 1
        # Iterate through questions in the current test
        for question_data in single_test_data:
            # Sanitize question text
            q_text = question_data['question'].strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
            q_type = question_data['type']
            nbsp = "&nbsp;"
            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'

            # Handle multiple-choice questions
            if q_type == 'multiple_choice':
                answers = question_data['answers'].copy()
                random.shuffle(answers) # Shuffle answer options
                for answer in answers:
                    # Sanitize answer text
                    ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
                    test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'
            # Handle open-ended questions
            elif q_type == 'open_ended':
                # No extra div is added anymore
                pass # Does nothing, just leaves the question paragraph

            q_counter += 1

        # Add page break before the next test (except for the first one)
        page_break_class = " page-break" if index > 0 else ""
        html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')

    # Assemble the final HTML content
    final_html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Generated Tests</title><style>{css_style}</style></head><body>{''.join(html_parts)}</body></html>"""

    update_status("⚙️ Converting HTML to PDF with WeasyPrint (this may take time)...")
    try:
        # Convert HTML string to PDF bytes
        html_doc = HTML(string=final_html_content)
        pdf_bytes = html_doc.write_pdf()
        update_status("⚙️ PDF conversion complete.")
        return pdf_bytes
    except FileNotFoundError as e:
        # Handle missing GTK dependencies error
        st.error(f"ERROR WeasyPrint: Missing dependencies (GTK+?) {e}")
        return None
    except Exception as e:
        # Handle other WeasyPrint errors
        st.error(f"ERROR WeasyPrint: {e}")
        return None


# ================================================================
# Streamlit User Interface (English)
# ================================================================

st.set_page_config(page_title="EvilProf 😈", layout="wide", initial_sidebar_state="expanded")
st.title("EvilProf 😈")
# Changed subheader to English
st.subheader("Random and Diverse Test Generator from Excel to PDF")

# --- Banner SVG ---
banner_path = "banner.svg"
try:
    with open(banner_path, "r", encoding="utf-8") as f: svg_content = f.read()
    st.markdown(svg_content, unsafe_allow_html=True)
except FileNotFoundError: pass
except Exception as e: st.error(f"Error loading banner '{banner_path}': {e}")
# --- End Banner ---

if not WEASYPRINT_AVAILABLE:
    # Changed error message to English
    st.error("🚨 **Attention:** WeasyPrint library not available or not functional. PDF generation is disabled.")
    st.stop()

# Changed expander label to English
with st.expander("ℹ️ Instructions and Excel File Preparation", expanded=False):
    st.markdown(INTRO_TEXT, unsafe_allow_html=True) # Use updated INTRO_TEXT
    image_path = "excel_example.jpg"
    try:
        # Changed image caption to English
        st.image(image_path, caption="Example of a valid Excel file structure", use_container_width=True)
    except FileNotFoundError: st.warning(f"Note: Example image '{image_path}' not found.")
    except Exception as e: st.error(f"Error loading image '{image_path}': {e}")

# Changed sidebar header to English
st.sidebar.header("Generation Parameters")
# Changed widget labels and help text to English
uploaded_file = st.sidebar.file_uploader("1. Excel File (.xlsx, .xls)", type=['xlsx', 'xls'], help="Drag and drop or click to select the Excel file.")
subject_name = st.sidebar.text_input("2. Subject Name", value="Computer Science", help="Will appear in the title of each test.")
num_tests = st.sidebar.number_input("3. Number of Tests", min_value=1, value=30, step=1, help="How many different test versions to create?")
num_mc_q = st.sidebar.number_input("4. No. Multiple-Choice Qs / Test", min_value=0, value=8, step=1)
num_open_q = st.sidebar.number_input("5. No. Open-Ended Qs / Test", min_value=0, value=2, step=1)
generate_button = st.sidebar.button("🚀 Generate Test PDFs", type="primary")

# --- Validation Test Section (English) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Functional Test")
validation_button = st.sidebar.button(
    "🧪 Run Validation Test",
    help="Generates 2 tests with few questions to check the basic logic (requires an uploaded file)."
)

# --- Source Code Download Section (English) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Source Code")
try:
    script_name = "evilprof_app.py" # Default
    if '__file__' in locals() and os.path.exists(__file__):
         script_name = os.path.basename(__file__)
         script_path = os.path.abspath(__file__)
         with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    else:
         source_code = "# Source code could not be read automatically in this environment."
         st.sidebar.warning("Source code download unavailable in this environment.")
    if '__file__' in locals() and os.path.exists(__file__):
        st.sidebar.download_button(label="📥 Download App Code (.py)", data=source_code, file_name=script_name, mime="text/x-python")
except Exception as e: st.sidebar.warning(f"Could not read source code: {e}")
# --- End Sidebar ---

# Changed header to English
st.subheader("Generation Output")

# --- Validation Test Logic (English Status Messages) ---
if validation_button:
    st.markdown("---")
    st.subheader("Validation Test Result")
    if uploaded_file is None: st.warning("⚠️ Please upload an Excel file to run the test.")
    else:
        test_status_placeholder = st.empty(); test_status_placeholder.info("Starting test...")
        if 'excel_df' not in st.session_state:
             test_status_placeholder.warning("Excel data not yet loaded in session. Reloading for test..."); temp_questions = load_questions_from_excel(uploaded_file, test_status_placeholder)
             if not temp_questions: st.error("Error loading data for test."); st.stop()
        else:
            test_status_placeholder.info("Using current Excel data from session for the test.")
            df_test = st.session_state.excel_df; temp_questions = []; mc_test_count = 0; oe_test_count = 0
            for index, row in df_test.iterrows():
                row_list = [str(item) if pd.notna(item) else "" for item in row]; question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
                if question_text:
                    if len(answers) >= 2: temp_questions.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': 'multiple_choice'}); mc_test_count += 1
                    else: temp_questions.append({'question': question_text, 'answers': [], 'original_index': index, 'type': 'open_ended'}); oe_test_count += 1
        if temp_questions:
            with st.spinner("⏳ Running test..."):
                test_num_tests = 2; test_num_mc = 2; test_num_open = 1
                test_status_placeholder.write(f"Test configuration: {test_num_tests} tests, {test_num_mc} multiple-choice, {test_num_open} Open-Ended.")
                temp_mc = [q for q in temp_questions if q['type'] == 'multiple_choice']; temp_oe = [q for q in temp_questions if q['type'] == 'open_ended']
                temp_total_mc = len(temp_mc); temp_total_oe = len(temp_oe); test_error = False
                if temp_total_mc < test_num_mc: st.error(f"Not enough multiple-choice questions ({temp_total_mc}) for test ({test_num_mc})."); test_error = True
                if temp_total_oe < test_num_open: st.error(f"Not enough Open-Ended questions ({temp_total_oe}) for test ({test_num_open})."); test_error = True
                if test_num_mc > 0 and temp_total_mc <= test_num_mc: st.error(f"Need >{test_num_mc} total multiple-choice questions to test non-repetition."); test_error = True
                if test_num_open > 0 and temp_total_oe <= test_num_open: st.error(f"Need >{test_num_open} total Open-Ended questions to test non-repetition."); test_error = True
                if not test_error:
                    try:
                        mc_by_idx = {q['original_index']: q for q in temp_mc}; oe_by_idx = {q['original_index']: q for q in temp_oe}
                        last_used_mc_test = {idx: 0 for idx in mc_by_idx.keys()}; last_used_oe_test = {idx: 0 for idx in oe_by_idx.keys()}
                        test_results_data = []; prev_mc_idx_test = set(); prev_oe_idx_test = set(); test_passed_overall = True
                        for i_test in range(1, test_num_tests + 1):
                            test_status_placeholder.write(f"Generating test data {i_test}/{test_num_tests}...")
                            current_test_unshuffled = []; selected_mc_current = set(); selected_oe_current = set()
                            if test_num_mc > 0:
                                candidates = list(mc_by_idx.keys() - prev_mc_idx_test); weights = [i_test - last_used_mc_test[idx] + 1 for idx in candidates]
                                if len(candidates) < test_num_mc:
                                     st.warning(f"[Test] Fallback active for Multiple-Choice test {i_test}: sampling from all.")
                                     sampled_mc = random.sample(list(mc_by_idx.keys()), test_num_mc)
                                else: sampled_mc = weighted_random_sample_without_replacement(candidates, weights, test_num_mc)
                                selected_mc_current = set(sampled_mc)
                                for idx in selected_mc_current: current_test_unshuffled.append(mc_by_idx[idx]); last_used_mc_test[idx] = i_test
                            if test_num_open > 0:
                                candidates = list(oe_by_idx.keys() - prev_oe_idx_test); weights = [i_test - last_used_oe_test[idx] + 1 for idx in candidates]
                                if len(candidates) < test_num_open:
                                     st.warning(f"[Test] Fallback active for Open-Ended test {i_test}: sampling from all.")
                                     sampled_oe = random.sample(list(oe_by_idx.keys()), test_num_open)
                                else: sampled_oe = weighted_random_sample_without_replacement(candidates, weights, test_num_open)
                                selected_oe_current = set(sampled_oe)
                                for idx in selected_oe_current: current_test_unshuffled.append(oe_by_idx[idx]); last_used_oe_test[idx] = i_test
                            random.shuffle(current_test_unshuffled); test_results_data.append(current_test_unshuffled)
                            prev_mc_idx_test = selected_mc_current; prev_oe_idx_test = selected_oe_current
                        test_status_placeholder.write(f"Validating {len(test_results_data)} generated tests...")
                        if len(test_results_data) == test_num_tests:
                            for i_val, test_data in enumerate(test_results_data):
                                expected_total = test_num_mc + test_num_open
                                if len(test_data) != expected_total: st.error(f"❌ Validation Failed: Test {i_val+1} has {len(test_data)} questions instead of {expected_total}."); test_passed_overall = False
                            q_set_test1 = set(q['original_index'] for q in test_results_data[0]); q_set_test2 = set(q['original_index'] for q in test_results_data[1])
                            intersection = q_set_test1.intersection(q_set_test2)
                            if not intersection: st.success("✅ Validation Passed: Test 1 and Test 2 have no common questions.")
                            else: st.warning(f"⚠️ Validation: Test 1 and Test 2 have common questions (indices: {intersection}). Expected if fallback was activated.")
                        else: st.error("❌ Validation Failed: Incorrect number of tests generated."); test_passed_overall = False
                        if test_passed_overall: test_status_placeholder.success("🎉 Validation test completed successfully!")
                        else: test_status_placeholder.error("⚠️ Validation test failed or had warnings. Check messages.")
                    except ValueError as e_val: st.error(f"❌ Error during validation test execution (ValueError): {e_val}")
                    except Exception as e_val: st.error(f"❌ Unexpected error during validation test execution: {e_val}")
                else: st.error("❌ Cannot run test due to prerequisite errors.")
        else: st.error("❌ Error loading/processing data for test.")
    #st.markdown("---")

# ================================================================
# Main Generation Logic (Actual PDF - English Status Messages)
# ================================================================
if generate_button:
    status_placeholder = st.empty()
    if 'fallback_warning_shown' in st.session_state: del st.session_state['fallback_warning_shown']

    if uploaded_file is None: st.warning("⚠️ Please upload an Excel file first.")
    else:
        # Load or use session data, updating placeholder
        if 'excel_df' not in st.session_state or st.session_state.loaded_file_name != uploaded_file.name:
             with st.spinner("⏳ Loading Excel data..."):
                 all_questions = load_questions_from_excel(uploaded_file, status_placeholder)
        else:
             status_placeholder.info("ℹ️ Using Excel data from current session.")
             df_main = st.session_state.excel_df; all_questions = []; mc_main_count = 0; oe_main_count = 0
             for index, row in df_main.iterrows():
                 row_list = [str(item) if pd.notna(item) else "" for item in row]; question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
                 if question_text:
                     if len(answers) >= 2: all_questions.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': 'multiple_choice'}); mc_main_count += 1
                     else: all_questions.append({'question': question_text, 'answers': [], 'original_index': index, 'type': 'open_ended'}); oe_main_count += 1
             status_placeholder.info(f"✅ Data ready: {len(all_questions)} questions ({mc_main_count} multiple-choice, {oe_main_count} open-ended). Validating parameters...")

        if not all_questions: st.error("❌ Error loading/processing data. Cannot generate.")
        else:
             num_q_per_test = num_mc_q + num_open_q
             if num_q_per_test <= 0: st.error("ERROR: Total number of questions per test must be > 0.")
             else:
                 # Display main parameters (not in placeholder)
                 st.info(f"PDF Generation Parameters: {num_tests} tests, '{subject_name}', {num_mc_q} Multiple-Choice + {num_open_q} Open-Ended = {num_q_per_test} Qs/Test")

                 mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']; open_questions = [q for q in all_questions if q['type'] == 'open_ended']
                 total_mc = len(mc_questions); total_open = len(open_questions); error_found_main = False

                 # --- Feasibility Checks and Warnings (English) ---
                 if total_mc == 0 and num_mc_q > 0: st.error(f"ERROR: {num_mc_q} multiple-choice questions requested, 0 found."); error_found_main = True
                 if total_open == 0 and num_open_q > 0: st.error(f"ERROR: {num_open_q} open-ended questions requested, 0 found."); error_found_main = True
                 if total_mc < num_mc_q: st.error(f"CRITICAL ERROR: Not enough multiple-choice questions ({total_mc}) for {num_mc_q} requested per test."); error_found_main = True
                 if total_open < num_open_q: st.error(f"CRITICAL ERROR: Not enough open-ended questions ({total_open}) for {num_open_q} requested per test."); error_found_main = True

                 # Store whether to show low diversity warnings (only if no critical errors)
                 if not error_found_main:
                     st.session_state['show_mc_low_diversity_warning'] = (num_mc_q > 0 and total_mc < 3 * num_mc_q)
                     st.session_state['show_oe_low_diversity_warning'] = (num_open_q > 0 and total_open < 3 * num_open_q)
                 else: # Ensure flags are false if critical errors exist
                      st.session_state['show_mc_low_diversity_warning'] = False
                      st.session_state['show_oe_low_diversity_warning'] = False
                 # --- End Checks ---

                 if not error_found_main:
                     with st.spinner("⏳ Generating tests..."): # Generic spinner text
                         status_placeholder.info("⚙️ Preparing test data...")
                         mc_by_index = {q['original_index']: q for q in mc_questions}; open_by_index = {q['original_index']: q for q in open_questions}
                         last_used_mc = {idx: 0 for idx in mc_by_index.keys()}; last_used_oe = {idx: 0 for idx in open_by_index.keys()}
                         all_tests_question_data = []; prev_mc_indices = set(); prev_open_indices = set()

                         for i in range(1, num_tests + 1):
                             status_placeholder.info(f"⚙️ Generating data for test {i}/{num_tests}...")
                             current_test_data_unshuffled = []; selected_mc_indices_current = set(); selected_open_indices_current = set()
                             fallback_active_mc = False; fallback_active_oe = False

                             # --- Multiple-Choice Selection with Fallback ---
                             if num_mc_q > 0:
                                 candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
                                 if len(candidate_mc_indices) < num_mc_q:
                                     fallback_active_mc = True
                                     if 'fallback_warning_shown' not in st.session_state:
                                         st.error(f"‼️ ATTENTION: Insufficient unique questions to guarantee test {i} differs from the previous one for multiple-choice questions. Proceeding with simple random sampling from ALL available questions. Subsequent tests might contain repetitions.")
                                         st.session_state.fallback_warning_shown = True
                                     try: sampled_mc_indices = random.sample(list(mc_by_index.keys()), num_mc_q)
                                     except ValueError: st.error(f"Unexpected Error: Cannot sample {num_mc_q} from {total_mc} total questions."); break
                                 else:
                                     weights_mc = [i - last_used_mc[idx] + 1 for idx in candidate_mc_indices]
                                     try: sampled_mc_indices = weighted_random_sample_without_replacement(candidate_mc_indices, weights_mc, num_mc_q)
                                     except ValueError as e: st.error(f"Weighted sampling error for Multiple-Choice test {i}: {e}"); break
                                 selected_mc_indices_current = set(sampled_mc_indices)
                                 for idx in selected_mc_indices_current: current_test_data_unshuffled.append(mc_by_index[idx]); last_used_mc[idx] = i

                             # --- Open-Ended Selection with Fallback ---
                             if num_open_q > 0:
                                 candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
                                 if len(candidate_oe_indices) < num_open_q:
                                     fallback_active_oe = True
                                     if 'fallback_warning_shown' not in st.session_state:
                                         st.error(f"‼️ ATTENTION: Insufficient unique questions to guarantee test {i} differs from the previous one for open-ended questions. Proceeding with simple random sampling from ALL available questions. Subsequent tests might contain repetitions.")
                                         st.session_state.fallback_warning_shown = True
                                     try: sampled_oe_indices = random.sample(list(open_by_index.keys()), num_open_q)
                                     except ValueError: st.error(f"Unexpected Error: Cannot sample {num_open_q} from {total_open} total questions."); break
                                 else:
                                     weights_oe = [i - last_used_oe[idx] + 1 for idx in candidate_oe_indices]
                                     try: sampled_oe_indices = weighted_random_sample_without_replacement(candidate_oe_indices, weights_oe, num_open_q)
                                     except ValueError as e: st.error(f"Weighted sampling error for Open-Ended test {i}: {e}"); break
                                 selected_open_indices_current = set(sampled_oe_indices)
                                 for idx in selected_open_indices_current: current_test_data_unshuffled.append(open_by_index[idx]); last_used_oe[idx] = i

                             prev_mc_indices = selected_mc_indices_current; prev_open_indices = selected_open_indices_current
                             random.shuffle(current_test_data_unshuffled); all_tests_question_data.append(current_test_data_unshuffled)
                         # --- End Test Generation Loop ---

                         # --- Show Low Diversity Warning ONLY if Fallback did NOT occur ---
                         if 'fallback_warning_shown' not in st.session_state:
                             if st.session_state.get('show_mc_low_diversity_warning', False):
                                 st.warning(f"⚠️ Warning: The total number of multiple-choice questions ({total_mc}) is less than triple ({3*num_mc_q}) the number requested per test ({num_mc_q}). Diversity between tests over time might be limited.")
                             if st.session_state.get('show_oe_low_diversity_warning', False):
                                 st.warning(f"⚠️ Warning: The total number of open-ended questions ({total_open}) is less than triple ({3*num_open_q}) the number requested per test ({num_open_q}). Diversity between tests over time might be limited.")

                         # Final status message before PDF generation
                         if 'fallback_warning_shown' not in st.session_state:
                              status_placeholder.info(f"✅ Data prepared for {len(all_tests_question_data)} tests (diversity guaranteed). Starting PDF conversion...")
                         else:
                              status_placeholder.warning(f"✅ Data prepared for {len(all_tests_question_data)} tests (WARNING: diversity not guaranteed for all tests). Starting PDF conversion...")

                     # --- PDF Generation ---
                     with st.spinner("⏳ Converting to PDF..."):
                         pdf_data = generate_pdf_data(all_tests_question_data, datetime.now().strftime("%Y%m%d_%H%M%S"), subject_name, status_placeholder)

                     if pdf_data:
                         status_placeholder.empty() # Clear status placeholder
                         st.success("✅ PDF Generation Complete!")
                         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                         safe_filename_subject = subject_name.replace(' ','_').replace('/','-').replace('\\','-')
                         # Changed PDF filename prefix
                         pdf_filename = f"Tests_{safe_filename_subject}_{timestamp}.pdf"
                         st.download_button(label="📥 Download Generated PDF", data=pdf_data, file_name=pdf_filename, mime="application/pdf", help=f"Click to download '{pdf_filename}'")
                     else:
                         status_placeholder.empty()
                         st.error("❌ Error during PDF creation.")

# --- Footer ---
st.markdown("---")
# Kept version 1.1 as requested previously
st.markdown("EvilProf v1.1 - [GitHub](https://github.com/subnetdusk/evilprof) - Streamlit")
# --- End Application ---
