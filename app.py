# -*- coding: utf-8 -*-
# app.py 

import streamlit as st
from datetime import datetime
import os
import pandas as pd # Import pandas per leggere l'Excel per il download / Import pandas to read Excel for download

# Importa funzioni e costanti dai moduli separati
# Import functions and constants from separate modules
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, EXAMPLE_IMAGE_PATH
)
from file_handler import load_questions_from_excel
# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data
# Importa la NUOVA funzione di test statistico dal file test.py
# Import the NEW statistical test function from test.py
from test import run_all_tests 
# Assicurati che pdf_generator esporti WEASYPRINT_AVAILABLE
# Ensure pdf_generator exports WEASYPRINT_AVAILABLE
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
# Bottone test funzionale (chiama run_statistical_similarity_test)
# Functional test button (calls run_statistical_similarity_test)
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

def display_message(message_type, key_or_raw_text, **kwargs):
    # ... (funzione display_message invariata) ...
    kwargs = kwargs or {}
    formatted_text = F(key_or_raw_text, **kwargs)
    if formatted_text == key_or_raw_text or formatted_text.startswith("MISSING_TEXT["):
        if kwargs:
            try: formatted_text = key_or_raw_text.format(**kwargs)
            except (KeyError, IndexError, ValueError, TypeError):
                 print(f"WARN: Could not format raw text '{key_or_raw_text}' with args {kwargs}")
                 formatted_text = key_or_raw_text
        else: formatted_text = key_or_raw_text
    if message_type == "info": output_placeholder.info(formatted_text)
    elif message_type == "warning": output_placeholder.warning(formatted_text)
    elif message_type == "error": output_placeholder.error(formatted_text)
    elif message_type == "success": output_placeholder.success(formatted_text)
    else: output_placeholder.write(f"[{message_type.upper()}] {formatted_text}")

def status_callback(msg_type, msg_key, **kwargs):
     display_message(msg_type, msg_key, **kwargs)

# ================================================================
# Logica per il Test Funzionale / Logic for Functional Test
# ================================================================
if validation_button:
    output_placeholder.empty()
    display_message("info", "VALIDATION_START")

    excel_file_created = None # Variabile per memorizzare il nome del file Excel / Variable to store Excel filename
    with st.spinner(T("VALIDATION_LOGIC_SPINNER")):
        # Chiama la funzione da test.py, che ora ritorna (risultati, nome_file_excel_o_None)
        # Call function from test.py, which now returns (results, excel_filename_or_None)
        test_results, excel_file_created = run_all_tests(status_callback)

    # Mostra i risultati sommari / Display summary results
    display_message("info", "VALIDATION_RESULTS_HEADER")
    if not test_results:
        display_message("warning", "VALIDATION_NO_MESSAGES")
    else:
        for msg_type, msg_key, msg_kwargs in test_results:
            display_message(msg_type, msg_key, **msg_kwargs)

    # Aggiungi bottone download se l'Excel è stato creato / Add download button if Excel was created
    if excel_file_created and os.path.exists(excel_file_created):
        try:
            with open(excel_file_created, "rb") as fp:
                excel_bytes = fp.read()
            output_placeholder.download_button(
                label=T("DOWNLOAD_STATS_EXCEL_LABEL"), # <-- Nuova chiave / New key
                data=excel_bytes,
                file_name=excel_file_created,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=T("DOWNLOAD_STATS_EXCEL_HELP") # <-- Nuova chiave / New key
            )
        except Exception as e:
            output_placeholder.error(f"Errore lettura file Excel per download: {e}")

# ================================================================
# Logica Principale per Generazione PDF / Main Logic for PDF Generation
# ================================================================
if generate_button:
    # ... (questa sezione rimane uguale) ...
    output_placeholder.empty()
    display_message("info", "GENERATION_START")
    if uploaded_file is None: display_message("warning", "UPLOAD_FIRST_WARNING"); st.stop()
    with st.spinner(T("LOADING_DATA_SPINNER")):
         all_questions, error_key_load = load_questions_from_excel(uploaded_file, status_callback)
    if error_key_load: display_message("error", error_key_load); st.stop()
    if not all_questions: display_message("error", "NO_VALID_QUESTIONS_ERROR"); st.stop()
    num_q_per_test = num_mc_q + num_open_q
    if num_q_per_test <= 0: display_message("error", "TOTAL_QUESTIONS_ZERO_ERROR"); st.stop()
    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions); total_open = len(open_questions)
    error_found_main = False
    if total_mc == 0 and num_mc_q > 0: display_message("error", "MC_ZERO_ERROR", num_mc_q=num_mc_q); error_found_main = True
    if total_open == 0 and num_open_q > 0: display_message("error", "OPEN_ZERO_ERROR", num_open_q=num_open_q); error_found_main = True
    if total_mc < num_mc_q: display_message("error", "MC_INSUFFICIENT_ERROR", total_mc=total_mc, num_mc_q=num_mc_q); error_found_main = True
    if total_open < num_open_q: display_message("error", "OPEN_INSUFFICIENT_ERROR", total_open=total_open, num_open_q=num_open_q); error_found_main = True
    if error_found_main: display_message("error", "CORRECT_ERRORS_ERROR"); st.stop()
    display_message("info", "PARAMS_OK_INFO", num_tests=num_tests, subject_name=subject_name, num_mc_q=num_mc_q, num_open_q=num_open_q, num_q_per_test=num_q_per_test)
    with st.spinner(F("GENERATING_DATA_SPINNER", num_tests=num_tests)):
        all_tests_data, generation_messages = generate_all_tests_data(
            mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback
        )
    if generation_messages:
         display_message("info", "GENERATION_MESSAGES_HEADER")
         for msg_type, msg_key, msg_kwargs in generation_messages:
             display_message(msg_type, msg_key, **msg_kwargs)
    if all_tests_data is None:
        if not any(m[0]=='error' for m in generation_messages): display_message("error", "GENERATION_FAILED_ERROR")
        st.stop()
    pdf_strings = {
        "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
        "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
        "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")
    }
    display_message("info", "DATA_READY_PDF_INFO", num_tests=len(all_tests_data))
    with st.spinner(T("PDF_CREATION_SPINNER")):
         pdf_data = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)
    if pdf_data:
        display_message("success", "PDF_SUCCESS")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
        pdf_filename = f"Tests_{safe_filename_subject}_{num_tests}x{num_q_per_test}q_{timestamp}.pdf"
        st.download_button(
            label=T("PDF_DOWNLOAD_BUTTON_LABEL"), data=pdf_data, file_name=pdf_filename, mime="application/pdf",
            help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=pdf_filename),
            use_container_width=True, type="primary"
        )
    else:
        if not any(m[0]=='error' for m in generation_messages): display_message("error", "PDF_GENERATION_ERROR")

# ================================================================
# Messaggio Iniziale / Initial Message
# ================================================================
if 'action_performed' not in st.session_state: st.session_state.action_performed = False
if validation_button: st.session_state.action_performed = True
if generate_button: st.session_state.action_performed = True
if not st.session_state.action_performed: output_placeholder.info(T("INITIAL_INFO"))

# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
