# -*- coding: utf-8 -*-
# app.py (UI e testo aggiornati)

import streamlit as st
from datetime import datetime
import os
# import pandas as pd # Non direttamente usato qui, ma file_handler lo usa

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, EXAMPLE_IMAGE_PATH, ANALYSIS_IMAGE_PATH # EXAMPLE_IMAGE_PATH e ANALYSIS_IMAGE_PATH non sono più usati in app.py
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
from test import run_all_tests # Per il test funzionale
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Stato Sessione e Logica Lingua / Session State and Language Logic
# ================================================================
if 'lang' not in st.session_state: st.session_state.lang = 'it'
if 'blocks_summary' not in st.session_state: st.session_state.blocks_summary = None
if 'all_questions' not in st.session_state: st.session_state.all_questions = None
if 'block_requests' not in st.session_state: st.session_state.block_requests = {}
if 'action_performed' not in st.session_state: st.session_state.action_performed = False
if 'processed_filename' not in st.session_state: st.session_state.processed_filename = None

def T(key): return get_text(st.session_state.lang, key)
def F(key, **kwargs): kwargs = kwargs or {}; return format_text(st.session_state.lang, key, **kwargs)

# ================================================================
# Setup Pagina / Page Setup
# ================================================================
st.set_page_config(page_title=T("PAGE_TITLE"), layout="centered", initial_sidebar_state="collapsed")

# ================================================================
# Toggle Button Lingua / Language Toggle Button
# ================================================================
cols_lang = st.columns([0.85, 0.075, 0.075])
with cols_lang[1]:
    button_it_type = "primary" if st.session_state.lang == 'it' else "secondary"
    if st.button("🇮🇹", key="lang_it_btn", type=button_it_type, help="Passa a Italiano / Switch to Italian", use_container_width=True):
        if st.session_state.lang != 'it': st.session_state.lang = 'it'; st.rerun()
with cols_lang[2]:
    button_en_type = "primary" if st.session_state.lang == 'en' else "secondary"
    if st.button("🇬🇧", key="lang_en_btn", type=button_en_type, help="Passa a Inglese / Switch to English", use_container_width=True):
        if st.session_state.lang != 'en': st.session_state.lang = 'en'; st.rerun()

# ================================================================
# Titolo e Contenuto Principale / Title and Main Content
# ================================================================
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER_NEW"))
if not WEASYPRINT_AVAILABLE:
    st.error(T("WEASYPRINT_ERROR"))
    st.stop()

# ================================================================
# Sidebar per Istruzioni / Sidebar for Instructions
# ================================================================
with st.sidebar:
    st.header(T("INSTRUCTIONS_HEADER"))

    # Link al README su GitHub
    readme_url = T("README_LINK_URL_EN") if st.session_state.lang == 'en' else T("README_LINK_URL_IT")
    st.markdown(f"[{T('README_LINK_TEXT')}]({readme_url})")
    st.markdown("---")

    # Mostra il testo delle istruzioni (versione snellita)
    st.markdown(T("INTRO_TEXT_NEW"), unsafe_allow_html=True)
    # Le immagini di esempio e la sezione dettagliata sull'analisi statistica sono state rimosse dalla sidebar
    # e sono accessibili tramite il README.md linkato sopra.

# ================================================================
# Corpo Principale / Main Body
# ================================================================
main_upload_status_placeholder = st.empty()

def main_upload_status_callback(msg_type, msg_key, **kwargs):
     if msg_type not in ["warning", "error"]: return
     formatted_text = F(msg_key, **kwargs)
     if formatted_text.startswith("MISSING_TEXT["): formatted_text = f"{msg_key}: {kwargs}"
     if msg_type == "warning": main_upload_status_placeholder.warning(formatted_text)
     elif msg_type == "error": main_upload_status_placeholder.error(formatted_text)

st.header(T("UPLOAD_LABEL"))
uploaded_file = st.file_uploader(
    label="‎",
    type=['xlsx', 'xls', 'csv'],
    help=T("UPLOAD_HELP"),
    key="file_uploader_main",
    label_visibility="collapsed"
)

if uploaded_file is not None:
    if st.session_state.processed_filename != uploaded_file.name:
        main_upload_status_placeholder.empty()
        with st.spinner(T("LOADING_DATA_SPINNER")):
            all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, main_upload_status_callback)
        if error_k:
            st.session_state.all_questions = None; st.session_state.blocks_summary = None
            st.session_state.block_requests = {}; st.session_state.processed_filename = None
        else:
            st.session_state.all_questions = all_q; st.session_state.blocks_summary = blocks_sum
            st.session_state.block_requests = {b['block_id']: 0 for b in blocks_sum}
            st.session_state.processed_filename = uploaded_file.name
elif st.session_state.processed_filename is not None and uploaded_file is None:
     st.session_state.all_questions = None; st.session_state.blocks_summary = None
     st.session_state.block_requests = {}; st.session_state.processed_filename = None
     main_upload_status_placeholder.empty()

st.markdown("---")
st.header(T("GENERATION_PARAMS_HEADER"))

with st.form(key="generation_form"):
    subject_name = st.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
    num_tests_input = st.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))

    total_questions_requested_form = 0
    if st.session_state.blocks_summary:
        st.subheader(T("BLOCK_REQUESTS_HEADER"))
        if not isinstance(st.session_state.block_requests, dict):
            st.session_state.block_requests = {b['block_id']: 0 for b in st.session_state.blocks_summary}

        for block_info in st.session_state.blocks_summary:
            block_id = block_info['block_id']
            block_type_str = block_info['type']
            available_count = block_info['count']
            label = F("BLOCK_REQUEST_LABEL", block_id=block_id, type=block_type_str, n=available_count)
            current_value_for_block = st.session_state.block_requests.get(block_id, 0)
            value_to_set_in_form = min(current_value_for_block, available_count)
            st.session_state.block_requests[block_id] = st.number_input(
                label=label, min_value=0, max_value=available_count,
                value=value_to_set_in_form, step=1, key=f"form_block_input_{block_id}"
            )
            total_questions_requested_form += st.session_state.block_requests[block_id]
        st.markdown(f"**{T('TOTAL_QUESTIONS_SELECTED')}: {total_questions_requested_form}**")
    else:
        if uploaded_file is not None and not st.session_state.blocks_summary :
             pass
        elif uploaded_file is None:
            st.info(T("UPLOAD_FIRST_WARNING"))

    generate_button_form = st.form_submit_button(
        T("GENERATE_BUTTON_LABEL"),
        type="primary",
        use_container_width=True,
        disabled=(uploaded_file is None or not st.session_state.blocks_summary)
    )

st.markdown("---")
st.header(T("VALIDATION_TEST_HEADER"))
validation_button = st.button(
    T("VALIDATE_BUTTON_LABEL"),
    help=T("VALIDATE_BUTTON_HELP_NEW"),
    use_container_width=True
)

st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container()
transient_status_placeholder = st.empty()

def display_critical_message(message_type, key_or_raw_text, **kwargs):
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

if validation_button:
    output_placeholder.empty()
    transient_status_placeholder.empty()
    excel_file_created = None
    test_results_messages = []
    st.session_state.action_performed = True
    with st.spinner(T("VALIDATION_LOGIC_SPINNER")):
        try:
            test_results_messages, excel_file_created = run_all_tests(status_callback)
        except Exception as e:
             with output_placeholder: st.error(F("CL_VALIDATION_UNEXPECTED_ERROR", error=str(e)))
             test_results_messages = None
    with output_placeholder:
        if test_results_messages is not None:
            st.markdown(f"**{T('VALIDATION_RESULTS_HEADER')}**")
            if not test_results_messages and not excel_file_created:
                st.warning(T("VALIDATION_NO_MESSAGES"))
            elif test_results_messages:
                for msg_type, msg_key, msg_kwargs in test_results_messages:
                    final_formatted_text = F(msg_key, **msg_kwargs)
                    if msg_type == "info": st.info(final_formatted_text)
                    elif msg_type == "warning": st.warning(final_formatted_text)
                    elif msg_type == "error": st.error(final_formatted_text)
                    elif msg_type == "success": st.success(final_formatted_text)
                    else: st.write(f"[{msg_type.upper()}] {final_formatted_text}")
            if excel_file_created and os.path.exists(excel_file_created):
                try:
                    with open(excel_file_created, "rb") as fp: excel_bytes = fp.read()
                    st.download_button(label=T("DOWNLOAD_STATS_EXCEL_LABEL"), data=excel_bytes,
                                       file_name=os.path.basename(excel_file_created),
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       help=T("DOWNLOAD_STATS_EXCEL_HELP"))
                except Exception as e: st.error(f"Errore lettura file Excel per download: {e}")

if generate_button_form:
    output_placeholder.empty(); transient_status_placeholder.empty()
    st.session_state.action_performed = True
    current_block_requests_from_form = st.session_state.get('block_requests', {})
    active_block_requests = {bid: k for bid, k in current_block_requests_from_form.items() if k > 0}
    total_requested_final = sum(active_block_requests.values())

    if uploaded_file is None and st.session_state.processed_filename is None:
        output_placeholder.warning(T("UPLOAD_FIRST_WARNING")); st.stop()
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         output_placeholder.error(F("LOAD_ERROR", error_msg="Dati blocchi non caricati correttamente. Ricarica il file.")); st.stop()
    if total_requested_final <= 0:
        output_placeholder.error(T("TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS")); st.stop()

    pdf_generated = False; pdf_data = None; final_generation_messages = []
    with st.spinner(T("GENERATING_DATA_SPINNER")):
        try:
            all_tests_data, generation_messages_core = generate_all_tests_data(
                st.session_state.all_questions, active_block_requests, num_tests_input, status_callback
            )
            final_generation_messages.extend(generation_messages_core)
            if all_tests_data is None or any(msg[0] == 'error' for msg in generation_messages_core):
                raise ValueError("Test data generation failed due to errors in core logic.")

            pdf_strings = { "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
                            "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
                            "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")}
            pdf_data = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)
            if pdf_data is None:
                if not any(msg[0] == 'error' for msg in final_generation_messages):
                    final_generation_messages.append(("error", "PDF_GENERATION_ERROR", {}))
            else:
                pdf_generated = True
        except ValueError as ve:
            if not any(m[0] == 'error' for m in final_generation_messages):
                 final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": str(ve)}))
        except Exception as e:
             if not any(m[0] == 'error' for m in final_generation_messages):
                final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": str(e)}))

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
            pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests_input}tests_{timestamp}.pdf"
            st.download_button( label=T("PDF_DOWNLOAD_BUTTON_LABEL"), data=pdf_data, file_name=pdf_filename,
                                mime="application/pdf", help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=pdf_filename),
                                use_container_width=True, type="primary")
        elif not any(msg[0] == 'error' for msg in final_generation_messages) and not pdf_generated :
            st.error(T("PDF_GENERATION_ERROR"))

if not st.session_state.action_performed and not uploaded_file:
    output_placeholder.info(T("INITIAL_INFO_NEW"))

st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
