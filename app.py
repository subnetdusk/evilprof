# -*- coding: utf-8 -*-
# app.py (Corretto NameError nello spinner)

import streamlit as st
from datetime import datetime
import os
import pandas as pd

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, EXAMPLE_IMAGE_PATH # Rimosso DEFAULT_NUM_MC, DEFAULT_NUM_OPEN non usati qui
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
from test import run_all_tests
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Stato Sessione e Logica Lingua / Session State and Language Logic
# ================================================================
if 'lang' not in st.session_state: st.session_state.lang = 'it'
if 'blocks_summary' not in st.session_state: st.session_state.blocks_summary = None
if 'all_questions' not in st.session_state: st.session_state.all_questions = None
if 'block_requests' not in st.session_state: st.session_state.block_requests = {}
if 'action_performed' not in st.session_state: st.session_state.action_performed = False

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
st.subheader(T("SUBHEADER_NEW"))
if not WEASYPRINT_AVAILABLE: st.error(T("WEASYPRINT_ERROR")); st.stop()

# ================================================================
# Istruzioni (Espandibili) / Instructions (Expandable)
# ================================================================
with st.expander(T("INSTRUCTIONS_HEADER"), expanded=False):
    st.markdown(T("INTRO_TEXT_NEW"), unsafe_allow_html=True)
    try: st.image(EXAMPLE_IMAGE_PATH, caption=T("IMAGE_CAPTION"), use_container_width=True)
    except FileNotFoundError: st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
    except Exception as e: st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))

# ================================================================
# Sidebar per Input Utente / Sidebar for User Input
# ================================================================
st.sidebar.header(T("GENERATION_PARAMS_HEADER"))

# --- 1. Caricamento File ---
uploaded_file = st.sidebar.file_uploader(
    T("UPLOAD_LABEL"),
    type=['xlsx', 'xls'],
    help=T("UPLOAD_HELP"),
    key="file_uploader"
)

# --- Placeholder per messaggi critici durante caricamento/analisi ---
sidebar_status_placeholder = st.sidebar.empty()

# --- Funzione Callback per Sidebar ---
def sidebar_status_callback(msg_type, msg_key, **kwargs):
     """Mostra solo warning/error nella sidebar."""
     if msg_type not in ["warning", "error"]: return
     formatted_text = F(msg_key, **kwargs)
     if formatted_text.startswith("MISSING_TEXT["): formatted_text = f"{msg_key}: {kwargs}"
     if msg_type == "warning": sidebar_status_placeholder.warning(formatted_text)
     elif msg_type == "error": sidebar_status_placeholder.error(formatted_text)

# --- 2. Logica di Caricamento e Creazione Input Dinamici ---
if uploaded_file is not None:
    if 'processed_filename' not in st.session_state or st.session_state.processed_filename != uploaded_file.name:
        sidebar_status_placeholder.info(F("FH_READING_EXCEL", file_name=uploaded_file.name))
        all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, sidebar_status_callback)
        if error_k:
            st.session_state.all_questions = None
            st.session_state.blocks_summary = None
            st.session_state.block_requests = {}
            st.session_state.processed_filename = None
        else:
            st.session_state.all_questions = all_q
            st.session_state.blocks_summary = blocks_sum
            st.session_state.block_requests = {b['block_id']: 0 for b in blocks_sum}
            st.session_state.processed_filename = uploaded_file.name
            sidebar_status_placeholder.success(F("FH_LOAD_COMPLETE_BLOCKS", count=len(all_q), num_blocks=len(blocks_sum)))

# --- 3. Mostra Input Dinamici se Blocchi sono stati Identificati ---
total_questions_requested = 0 # Calcola sempre, sarà 0 se non ci sono blocchi
if st.session_state.blocks_summary:
    st.sidebar.markdown("---")
    st.sidebar.subheader(T("BLOCK_REQUESTS_HEADER"))
    for block_info in st.session_state.blocks_summary:
        block_id = block_info['block_id']
        block_type_str = block_info['type']
        available_count = block_info['count']
        label = F("BLOCK_REQUEST_LABEL", block_id=block_id, type=block_type_str, n=available_count)
        st.session_state.block_requests[block_id] = st.sidebar.number_input(
            label=label, min_value=0, max_value=available_count,
            value=st.session_state.block_requests.get(block_id, 0),
            step=1, key=f"block_input_{block_id}"
        )
        total_questions_requested += st.session_state.block_requests[block_id]
    st.sidebar.markdown(f"**{T('TOTAL_QUESTIONS_SELECTED')}: {total_questions_requested}**")
else:
    st.session_state.block_requests = {}

# --- 4. Input Generali Rimasti ---
st.sidebar.markdown("---")
subject_name = st.sidebar.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
# Usa la variabile corretta qui / Use the correct variable here
num_tests_input = st.sidebar.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))

# --- 5. Bottone Generazione ---
generate_button = st.sidebar.button(T("GENERATE_BUTTON_LABEL"), type="primary", use_container_width=True)

# --- 6. Test Funzionale ---
st.sidebar.markdown("---")
st.sidebar.subheader(T("VALIDATION_TEST_HEADER"))
validation_button = st.sidebar.button(
    T("VALIDATE_BUTTON_LABEL"),
    help=T("VALIDATE_BUTTON_HELP_NEW"),
    use_container_width=True,
    disabled=True # Mantenuto disabilitato / Kept disabled
)

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

    # 1. Recupera richieste utente dai widget dinamici
    current_block_requests = st.session_state.get('block_requests', {})
    active_block_requests = {bid: k for bid, k in current_block_requests.items() if k > 0}
    total_requested = sum(active_block_requests.values())

    # 2. Validazione Input
    if uploaded_file is None:
        output_placeholder.warning(T("UPLOAD_FIRST_WARNING")); st.stop()
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         output_placeholder.error(T("LOAD_ERROR", error_msg="Dati blocchi non caricati correttamente. Ricarica il file.")); st.stop()
    if total_requested <= 0:
        output_placeholder.error(T("TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS")); st.stop()

    # 3. Esecuzione Generazione
    pdf_generated = False
    pdf_data = None
    final_generation_messages = []

    # --- CORREZIONE QUI ---
    # Usa num_tests_input invece di num_tests_to_generate (che non esiste)
    # Use num_tests_input instead of num_tests_to_generate (which doesn't exist)
    with st.spinner(T("GENERATING_DATA_SPINNER")): # Rimosso argomento non necessario / Removed unnecessary argument
    # --- FINE CORREZIONE ---
        try:
            # Logica interna rimane uguale, ma usa num_tests_input per la chiamata
            all_tests_data, generation_messages = generate_all_tests_data(
                st.session_state.all_questions,
                active_block_requests,
                num_tests_input, # <<< USA LA VARIABILE CORRETTA / USE THE CORRECT VARIABLE
                status_callback
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

    # 4. Mostra Risultati Finali
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
            # Aggiorna nome file per usare num_tests_input / Update filename to use num_tests_input
            pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests_input}tests_{timestamp}.pdf"
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
    output_placeholder.info(T("INITIAL_INFO_NEW"))

# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
