# -*- coding: utf-8 -*-
# app.py (Cleaned Indentation)

import streamlit as st
from datetime import datetime
import os
import pandas as pd

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, EXAMPLE_IMAGE_PATH
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
from test import run_all_tests
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Stato Sessione e Logica Lingua / Session State and Language Logic
# ================================================================
if 'lang' not in st.session_state: st.session_state.lang = 'it'
def T(key): return get_text(st.session_state.lang, key)
def F(key, **kwargs): kwargs = kwargs or {}; return format_text(st.session_state.lang, key, **kwargs)

# ================================================================
# Setup Pagina / Page Setup
# ================================================================
st.set_page_config(page_title=T("PAGE_TITLE"), layout="wide", initial_sidebar_state="expanded")

# ================================================================
# Toggle Button Lingua / Language Toggle Button
# ================================================================
col_spacer, col_lang_it, col_lang_en = st.columns([0.85, 0.075, 0.075], gap="small")
with col_lang_it:
    button_it_type = "primary" if st.session_state.lang == 'it' else "secondary"
    if st.button("🇮🇹", key="lang_it_btn", type=button_it_type, help="Passa a Italiano / Switch to Italian", use_container_width=True):
        if st.session_state.lang != 'it': st.session_state.lang = 'it'; st.rerun()
with col_lang_en:
    button_en_type = "primary" if st.session_state.lang == 'en' else "secondary"
    if st.button("🇬🇧", key="lang_en_btn", type=button_en_type, help="Passa a Inglese / Switch to English", use_container_width=True):
        if st.session_state.lang != 'en': st.session_state.lang = 'en'; st.rerun()

# ================================================================
# Titolo e Contenuto Principale / Title and Main Content
# ================================================================
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER"))
if not WEASYPRINT_AVAILABLE: st.error(T("WEASYPRINT_ERROR")); st.stop()

# ================================================================
# Istruzioni (Espandibili) / Instructions (Expandable)
# ================================================================
with st.expander(T("INSTRUCTIONS_HEADER"), expanded=False):
    st.markdown(T("INTRO_TEXT"), unsafe_allow_html=True)
    try: st.image(EXAMPLE_IMAGE_PATH, caption=T("IMAGE_CAPTION"), use_container_width=True)
    except FileNotFoundError: st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
    except Exception as e: st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))

# ================================================================
# Sidebar per Input Utente / Sidebar for User Input
# ================================================================
st.sidebar.header(T("GENERATION_PARAMS_HEADER"))
uploaded_file = st.sidebar.file_uploader(T("UPLOAD_LABEL"), type=['xlsx', 'xls'], help=T("UPLOAD_HELP"))
subject_name = st.sidebar.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
num_tests = st.sidebar.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))
num_mc_q = st.sidebar.number_input(T("NUM_MC_LABEL"), min_value=0, value=DEFAULT_NUM_MC, step=1, help=T("NUM_MC_HELP"))
num_open_q = st.sidebar.number_input(T("NUM_OPEN_LABEL"), min_value=0, value=DEFAULT_NUM_OPEN, step=1, help=T("NUM_OPEN_HELP"))
generate_button = st.sidebar.button(T("GENERATE_BUTTON_LABEL"), type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader(T("VALIDATION_TEST_HEADER"))
validation_button = st.sidebar.button(
    T("VALIDATE_BUTTON_LABEL"),
    help=T("VALIDATE_BUTTON_HELP_NEW"),
    use_container_width=True
)

st.sidebar.markdown("---")
st.sidebar.subheader(T("SOURCE_CODE_HEADER"))
try:
    script_path = os.path.abspath(__file__)
    script_name = os.path.basename(script_path)
    with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    st.sidebar.download_button(label=T("DOWNLOAD_SOURCE_BUTTON_LABEL"), data=source_code, file_name=script_name, mime="text/x-python", use_container_width=True)
    st.sidebar.caption(T("DOWNLOAD_SOURCE_CAPTION"))
except NameError: st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error="__file__ not defined"))
except FileNotFoundError: st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error="Could not find script file"))
except Exception as e: st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error=str(e)))

# ================================================================
# Area Output Principale e Gestione Messaggi / Main Output Area and Message Handling
# ================================================================
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container()
transient_status_placeholder = st.empty()

def display_critical_message(message_type, key_or_raw_text, **kwargs):
    """Mostra solo warning/error nel transient_status_placeholder."""
    if message_type not in ["warning", "error"]: return
    kwargs = kwargs or {}
    formatted_text = F(key_or_raw_text, **kwargs)
    if formatted_text == key_or_raw_text or formatted_text.startswith("MISSING_TEXT["):
        if kwargs:
            try: formatted_text = key_or_raw_text.format(**kwargs)
            except (KeyError, IndexError, ValueError, TypeError): formatted_text = key_or_raw_text
        else: formatted_text = key_or_raw_text
    if message_type == "warning": transient_status_placeholder.warning(formatted_text)
    elif message_type == "error": transient_status_placeholder.error(formatted_text)

def status_callback(msg_type, msg_key, **kwargs):
     display_critical_message(msg_type, msg_key, **kwargs)

# ================================================================
# Logica per il Test Funzionale / Logic for Functional Test
# ================================================================
if validation_button:
    output_placeholder.empty()
    transient_status_placeholder.empty()
    excel_file_created = None
    test_results = []
    with st.spinner(T("VALIDATION_LOGIC_SPINNER")):
        try:
            test_results, excel_file_created = run_all_tests(status_callback)
        except Exception as e:
             with output_placeholder:
                 st.error(F("CL_VALIDATION_UNEXPECTED_ERROR", error=str(e)))
    with output_placeholder:
        st.markdown(f"**{T('VALIDATION_RESULTS_HEADER')}**")
        if not test_results and not excel_file_created:
             st.warning(T("VALIDATION_NO_MESSAGES"))
        elif test_results:
            for msg_type, msg_key, msg_kwargs in test_results:
                final_formatted_text = F(msg_key, **msg_kwargs)
                if msg_type == "info": st.info(final_formatted_text)
                elif msg_type == "warning": st.warning(final_formatted_text)
                elif msg_type == "error": st.error(final_formatted_text)
                elif msg_type == "success": st.success(final_formatted_text)
                else: st.write(f"[{msg_type.upper()}] {final_formatted_text}")
        if excel_file_created and os.path.exists(excel_file_created):
            try:
                with open(excel_file_created, "rb") as fp: excel_bytes = fp.read()
                st.download_button(
                    label=T("DOWNLOAD_STATS_EXCEL_LABEL"), data=excel_bytes,
                    file_name=excel_file_created,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help=T("DOWNLOAD_STATS_EXCEL_HELP")
                )
            except Exception as e: st.error(f"Errore lettura file Excel per download: {e}")

# ================================================================
# Logica Principale per Generazione PDF / Main Logic for PDF Generation
# ================================================================
if generate_button:
    output_placeholder.empty()
    transient_status_placeholder.empty()
    if uploaded_file is None:
        output_placeholder.warning(T("UPLOAD_FIRST_WARNING")); st.stop()
    pdf_generated = False
    pdf_data = None
    final_generation_messages = []
    with st.spinner(T("GENERATING_DATA_SPINNER")):
        try:
            all_questions, error_key_load = load_questions_from_excel(uploaded_file, status_callback)
            if error_key_load: raise ValueError(error_key_load)
            if not all_questions: raise ValueError("NO_VALID_QUESTIONS_ERROR")
            num_q_per_test = num_mc_q + num_open_q
            if num_q_per_test <= 0: raise ValueError("TOTAL_QUESTIONS_ZERO_ERROR")
            mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
            open_questions = [q for q in all_questions if q['type'] == 'open_ended']
            total_mc = len(mc_questions); total_open = len(open_questions)
            error_found_main = False
            if total_mc == 0 and num_mc_q > 0: final_generation_messages.append(("error", "MC_ZERO_ERROR", {"num_mc_q": num_mc_q})); error_found_main = True
            if total_open == 0 and num_open_q > 0: final_generation_messages.append(("error", "OPEN_ZERO_ERROR", {"num_open_q": num_open_q})); error_found_main = True
            if total_mc < num_mc_q: final_generation_messages.append(("error", "MC_INSUFFICIENT_ERROR", {"total_mc": total_mc, "num_mc_q": num_mc_q})); error_found_main = True
            if total_open < num_open_q: final_generation_messages.append(("error", "OPEN_INSUFFICIENT_ERROR", {"total_open": total_open, "num_open_q": num_open_q})); error_found_main = True
            if error_found_main: raise ValueError("Input parameter errors found.")
            all_tests_data, generation_messages = generate_all_tests_data(
                mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback
            )
            final_generation_messages.extend(generation_messages)
            if all_tests_data is None: raise ValueError("Test data generation failed.")
            pdf_strings = {
                "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
                "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
                "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")
            }
            pdf_data = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)
            if pdf_data is None: raise ValueError("PDF generation failed.")
            pdf_generated = True
        except ValueError as ve:
            msg_key = str(ve)
            if msg_key in TEXTS['it'] or msg_key in TEXTS['en']:
                 if not any(m[1] == msg_key for m in final_generation_messages): final_generation_messages.append(("error", msg_key, {}))
            else:
                 if not any(m[1] == "GENERATION_FAILED_ERROR" for m in final_generation_messages): final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": msg_key}))
        except Exception as e:
             if not any(m[1] == "GENERATION_FAILED_ERROR" for m in final_generation_messages): final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": str(e)}))
    with output_placeholder:
        if final_generation_messages:
             st.markdown(f"**{T('GENERATION_MESSAGES_HEADER')}**")
             for msg_type, msg_key, msg_kwargs in final_generation_messages:
                 final_formatted_text = F(msg_key, **msg_kwargs)
                 if msg_type == "warning": st.warning(final_formatted_text)
                 elif msg_type == "error": st.error(final_formatted_text)
        if pdf_generated and pdf_data:
            st.success(T("PDF_SUCCESS"))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
            pdf_filename = f"Tests_{safe_filename_subject}_{num_tests}x{num_q_per_test}q_{timestamp}.pdf"
            st.download_button(
                label=T("PDF_DOWNLOAD_BUTTON_LABEL"), data=pdf_data, file_name=pdf_filename, mime="application/pdf",
                help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=pdf_filename),
                use_container_width=True, type="primary"
            )
        elif not final_generation_messages:
             st.error(T("PDF_GENERATION_ERROR"))

# ================================================================
# Messaggio Iniziale / Initial Message
# ================================================================
if 'action_performed' not in st.session_state: st.session_state.action_performed = False
if validation_button: st.session_state.action_performed = True
if generate_button: st.session_state.action_performed = True
if not st.session_state.action_performed:
    output_placeholder.info(T("INITIAL_INFO"))

# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
