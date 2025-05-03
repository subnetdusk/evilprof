# -*- coding: utf-8 -*-
# app.py 

import streamlit as st
from datetime import datetime
import os
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, EXAMPLE_IMAGE_PATH
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data, run_validation_test
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
# Toggle Button Lingua (con gap="small")
# ================================================================
# Usa colonne per posizionare a destra, e gap="small" per avvicinarli
col_spacer, col_lang_it, col_lang_en = st.columns(
    [0.85, 0.075, 0.075], # Riduci leggermente la larghezza delle colonne bottoni
    gap="small" # Imposta lo spazio tra le colonne a "small"
)

with col_lang_it:
    button_it_type = "primary" if st.session_state.lang == 'it' else "secondary"
    # Aggiungi use_container_width=True per farli riempire la piccola colonna
    if st.button("🇮🇹", key="lang_it_btn", type=button_it_type, help="Passa a Italiano / Switch to Italian", use_container_width=True):
        if st.session_state.lang != 'it':
            st.session_state.lang = 'it'
            st.rerun()

with col_lang_en:
    button_en_type = "primary" if st.session_state.lang == 'en' else "secondary"
    if st.button("🇬🇧", key="lang_en_btn", type=button_en_type, help="Passa a Inglese / Switch to English", use_container_width=True):
        if st.session_state.lang != 'en':
            st.session_state.lang = 'en'
            st.rerun()
# --- Fine Toggle Button ---

# ================================================================
# Titolo e Contenuto Principale
# ================================================================
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER"))

if not WEASYPRINT_AVAILABLE:
    st.error(T("WEASYPRINT_ERROR"))
    st.stop()

# ================================================================
# Istruzioni 
# ================================================================
with st.expander(T("INSTRUCTIONS_HEADER"), expanded=False):
    st.markdown(T("INTRO_TEXT"), unsafe_allow_html=True)
    try:
        # Assicurati di avere la chiave IMAGE_CAPTION in localization.py
        st.image(EXAMPLE_IMAGE_PATH, caption=T("IMAGE_CAPTION"), use_container_width=True)
    except FileNotFoundError:
        st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
    except Exception as e:
        st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))

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
validation_button = st.sidebar.button(T("VALIDATE_BUTTON_LABEL"), help=T("VALIDATE_BUTTON_HELP"), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader(T("SOURCE_CODE_HEADER"))
try:
    script_path = os.path.abspath(__file__)
    script_name = os.path.basename(script_path)
    with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    st.sidebar.download_button(label=T("DOWNLOAD_SOURCE_BUTTON_LABEL"), data=source_code, file_name=script_name, mime="text/x-python", use_container_width=True)
    st.sidebar.caption(T("DOWNLOAD_SOURCE_CAPTION"))
except Exception as e:
    st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error=e))

# ================================================================
# Area Output Principale e Gestione Messaggi
# ================================================================
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container()

# Funzione display_message (invariata)
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

# Callback per funzioni backend (invariato)
def status_callback(msg_type, msg_key, **kwargs):
     display_message(msg_type, msg_key, **kwargs)

# ================================================================
# Logica per il Test di Validazione
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
                validation_results = run_validation_test(all_questions_test, status_callback)
             display_message("info", "VALIDATION_RESULTS_HEADER")
             if not validation_results:
                 display_message("warning", "VALIDATION_NO_MESSAGES")
             else:
                 for msg_type, msg_key, msg_kwargs in validation_results:
                     display_message(msg_type, msg_key, **msg_kwargs)

# ================================================================
# Logica Principale per Generazione PDF
# ================================================================
if generate_button:
    output_placeholder.empty()
    display_message("info", "GENERATION_START")
    if uploaded_file is None:
        display_message("warning", "UPLOAD_FIRST_WARNING");
