# -*- coding: utf-8 -*-
# app.py 

import streamlit as st
from datetime import datetime
import os

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, EXAMPLE_IMAGE_PATH
)
from file_handler import load_questions_from_excel
# Importa la funzione di generazione principale da core_logic
from core_logic import generate_all_tests_data
# Importa la funzione di validazione dal NUOVO file test.py
from test import run_validation_test # <<< MODIFICATO QUI
# Assicurati che pdf_generator esporti WEASYPRINT_AVAILABLE
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Stato Sessione e Logica Lingua
# ================================================================
if 'lang' not in st.session_state:
    st.session_state.lang = 'it'

def T(key): return get_text(st.session_state.lang, key)
def F(key, **kwargs): kwargs = kwargs or {}; return format_text(st.session_state.lang, key, **kwargs)

# ================================================================
# Setup Pagina
# ================================================================
st.set_page_config(page_title=T("PAGE_TITLE"), layout="wide", initial_sidebar_state="expanded")

# ================================================================
# Toggle Button Lingua
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
# Titolo e Contenuto Principale
# ================================================================
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER"))
if not WEASYPRINT_AVAILABLE: st.error(T("WEASYPRINT_ERROR")); st.stop()

# ================================================================
# Istruzioni (Espandibili)
# ================================================================
with st.expander(T("INSTRUCTIONS_HEADER"), expanded=False):
    st.markdown(T("INTRO_TEXT"), unsafe_allow_html=True)
    try: st.image(EXAMPLE_IMAGE_PATH, caption=T("IMAGE_CAPTION"), use_container_width=True)
    except FileNotFoundError: st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
    except Exception as e: st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))

# ================================================================
# Sidebar per Input Utente
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
# Ora run_validation_test viene importato da test.py
validation_button = st.sidebar.button(T("VALIDATE_BUTTON_LABEL"), help=T("VALIDATE_BUTTON_HELP"), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader(T("SOURCE_CODE_HEADER"))
try:
    # Tenta di ottenere il path dello script corrente
    # Questo potrebbe non funzionare in tutti gli ambienti di deployment Streamlit
    script_path = os.path.abspath(__file__)
    script_name = os.path.basename(script_path)
    with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    st.sidebar.download_button(label=T("DOWNLOAD_SOURCE_BUTTON_LABEL"), data=source_code, file_name=script_name, mime="text/x-python", use_container_width=True)
    st.sidebar.caption(T("DOWNLOAD_SOURCE_CAPTION"))
except NameError:
    # __file__ non è definito (comune in alcuni ambienti Streamlit o REPL)
    st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error="__file__ not defined"))
except FileNotFoundError:
     st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error="Could not find script file"))
except Exception as e:
    st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error=str(e)))


# ================================================================
# Area Output Principale e Gestione Messaggi
# ================================================================
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container()

def display_message(message_type, key_or_raw_text, **kwargs):
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
# Logica per il Test di Validazione (Usa funzione importata da test.py)
# ================================================================
if validation_button:
    output_placeholder.empty()
    display_message("info", "VALIDATION_START")
    if uploaded_file is None:
        display_message("warning", "VALIDATION_UPLOAD_FIRST")
    else:
        with st.spinner(T("LOADING_DATA_VALIDATION_SPINNER")):
            all_questions_test, error_key_load = load_questions_from_excel(uploaded_file, status_callback)
        if error_key_load:
             display_message("error", error_key_load)
        elif not all_questions_test:
             display_message("error", "NO_VALID_QUESTIONS_VALIDATION")
        else:
             with st.spinner(T("VALIDATION_LOGIC_SPINNER")):
                # Chiama la funzione importata da test.py
                validation_results = run_validation_test(all_questions_test, status_callback)
             display_message("info", "VALIDATION_RESULTS_HEADER")
             if not validation_results:
                 display_message("warning", "VALIDATION_NO_MESSAGES")
             else:
                 for msg_type, msg_key, msg_kwargs in validation_results:
                     display_message(msg_type, msg_key, **msg_kwargs)

# ================================================================
# Logica Principale per Generazione PDF (invariata)
# ================================================================
if generate_button:
    output_placeholder.empty()
    display_message("info", "GENERATION_START")
    if uploaded_file is None:
        display_message("warning", "UPLOAD_FIRST_WARNING"); st.stop()

    with st.spinner(T("LOADING_DATA_SPINNER")):
         all_questions, error_key_load = load_questions_from_excel(uploaded_file, status_callback)
    if error_key_load:
         display_message("error", error_key_load); st.stop()
    if not all_questions:
         display_message("error", "NO_VALID_QUESTIONS_ERROR"); st.stop()

    num_q_per_test = num_mc_q + num_open_q
    if num_q_per_test <= 0:
         display_message("error", "TOTAL_QUESTIONS_ZERO_ERROR"); st.stop()

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions); total_open = len(open_questions)
    error_found_main = False

    if total_mc == 0 and num_mc_q > 0: display_message("error", "MC_ZERO_ERROR", num_mc_q=num_mc_q); error_found_main = True
    if total_open == 0 and num_open_q > 0: display_message("error", "OPEN_ZERO_ERROR", num_open_q=num_open_q); error_found_main = True
    if total_mc < num_mc_q: display_message("error", "MC_INSUFFICIENT_ERROR", total_mc=total_mc, num_mc_q=num_mc_q); error_found_main = True
    if total_open < num_open_q: display_message("error", "OPEN_INSUFFICIENT_ERROR", total_open=total_open, num_open_q=num_open_q); error_found_main = True

    if error_found_main:
        display_message("error", "CORRECT_ERRORS_ERROR"); st.stop()

    display_message("info", "PARAMS_OK_INFO", num_tests=num_tests, subject_name=subject_name, num_mc_q=num_mc_q, num_open_q=num_open_q, num_q_per_test=num_q_per_test)

    with st.spinner(F("GENERATING_DATA_SPINNER", num_tests=num_tests)):
        # Chiama la funzione importata da core_logic.py
        all_tests_data, generation_messages = generate_all_tests_data(
            mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback
        )

    if generation_messages:
         display_message("info", "GENERATION_MESSAGES_HEADER")
         for msg_type, msg_key, msg_kwargs in generation_messages:
             display_message(msg_type, msg_key, **msg_kwargs)

    if all_tests_data is None:
        if not any(m[0]=='error' for m in generation_messages):
            display_message("error", "GENERATION_FAILED_ERROR")
        st.stop()

    pdf_strings = {
        "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
        "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
        "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")
    }

    display_message("info", "DATA_READY_PDF_INFO", num_tests=len(all_tests_data))
    with st.spinner(T("PDF_CREATION_SPINNER")):
         # Chiama la funzione importata da pdf_generator.py
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
        # Tenta di mostrare errore specifico da callback, altrimenti generico
        if not any(m[0]=='error' for m in generation_messages): # Controlla se callback ha già segnalato errore PDF
             display_message("error", "PDF_GENERATION_ERROR")

# ================================================================
# Messaggio Iniziale
# ================================================================
# Traccia se un'azione è stata eseguita per nascondere il msg iniziale
if 'action_performed' not in st.session_state: st.session_state.action_performed = False
# Imposta a True quando i bottoni principali vengono premuti
if validation_button: st.session_state.action_performed = True
if generate_button: st.session_state.action_performed = True
# Mostra il messaggio solo se nessuna azione è stata fatta
if not st.session_state.action_performed: output_placeholder.info(T("INITIAL_INFO"))

# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
