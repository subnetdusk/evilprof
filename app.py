# -*- coding: utf-8 -*-
# app.py (Default Domande Suggerite)

import streamlit as st
from datetime import datetime
import os
import math # Importato math

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
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

st.markdown(
    f"""
    <style>
        section[data-testid="stSidebar"] {{
            border-right: 2px solid #e0e0e0; 
            box-shadow: 2px 0px 5px rgba(0,0,0,0.1); 
        }}
        button[title="Collapse sidebar"] svg, button[title="Expand sidebar"] svg {{
            fill: #333 !important; 
        }}
         button[title="Collapse sidebar"], button[title="Expand sidebar"] {{
            background-color: rgba(240, 242, 246, 0.5) !important; 
            border: 1px solid #cccccc !important; 
            border-radius: 50% !important;
            width: 36px !important; 
            height: 36px !important;
            box-shadow: 0px 1px 3px rgba(0,0,0,0.2) !important; 
        }}
        button[title="Collapse sidebar"]:hover, button[title="Expand sidebar"]:hover {{
            background-color: rgba(230, 230, 230, 0.7) !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================================================================
# Toggle Button Lingua / Language Toggle Button
# ================================================================
cols_lang_title = st.columns([0.85, 0.075, 0.075])
with cols_lang_title[1]:
    button_it_type = "primary" if st.session_state.lang == 'it' else "secondary"
    if st.button("🇮🇹", key="lang_it_btn_main", type=button_it_type, help="Passa a Italiano / Switch to Italian", use_container_width=True):
        if st.session_state.lang != 'it':
            st.session_state.lang = 'it'
            st.rerun()
with cols_lang_title[2]:
    button_en_type = "primary" if st.session_state.lang == 'en' else "secondary"
    if st.button("🇬🇧", key="lang_en_btn_main", type=button_en_type, help="Passa a Inglese / Switch to English", use_container_width=True):
        if st.session_state.lang != 'en':
            st.session_state.lang = 'en'
            st.rerun()

# ================================================================
# Titolo e Contenuto Principale / Title and Main Content
# ================================================================
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER_NEW"))
if not WEASYPRINT_AVAILABLE:
    st.error(T("WEASYPRINT_ERROR"))
    st.stop()

# ================================================================
# Sidebar
# ================================================================
with st.sidebar:
    st.header(T("INSTRUCTIONS_HEADER"))
    readme_url = T("README_LINK_URL_EN") if st.session_state.lang == 'en' else T("README_LINK_URL_IT")
    st.markdown(f"[{T('README_LINK_TEXT')}]({readme_url})")
    st.markdown("---")
    st.markdown(T("INTRO_TEXT_NEW"), unsafe_allow_html=True)
    st.markdown("---")

# ================================================================
# Corpo Principale / Main Body
# ================================================================
main_upload_status_placeholder = st.empty()
output_placeholder = st.container() 
transient_status_placeholder = st.empty() 

def main_upload_status_callback(msg_type, msg_key, **kwargs):
     if msg_type not in ["warning", "error"]: return
     formatted_text = F(msg_key, **kwargs)
     if formatted_text.startswith("MISSING_TEXT["): formatted_text = f"{msg_key}: {kwargs}"
     if msg_type == "warning": main_upload_status_placeholder.warning(formatted_text)
     elif msg_type == "error": main_upload_status_placeholder.error(formatted_text)

def status_callback(msg_type, msg_key, **kwargs):
     if msg_type not in ["warning", "error"]: return
     raw_template = get_text(st.session_state.lang, msg_key)
     if raw_template == f"MISSING_TEXT[{msg_key}]":
         formatted_text = f"{msg_key}: {kwargs}" if kwargs else msg_key
     else:
        try:
            formatted_text = raw_template.format(**kwargs)
        except KeyError: 
            formatted_text = f"{raw_template} (Params: {kwargs})"
        except Exception: 
            formatted_text = f"{raw_template} (Params: {kwargs})"
     if msg_type == "warning": transient_status_placeholder.warning(formatted_text)
     elif msg_type == "error": transient_status_placeholder.error(formatted_text)

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
        output_placeholder.empty() 
        transient_status_placeholder.empty() 
        with st.spinner(T("LOADING_DATA_SPINNER")):
            all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, main_upload_status_callback)
        if error_k:
            st.session_state.all_questions = None; st.session_state.blocks_summary = None
            st.session_state.block_requests = {}; st.session_state.processed_filename = None
        else:
            st.session_state.all_questions = all_q; st.session_state.blocks_summary = blocks_sum
            st.session_state.processed_filename = uploaded_file.name
            # Inizializza block_requests con il valore suggerito (ceil(n/3))
            temp_block_requests = {}
            for block_info in blocks_sum:
                block_id = block_info['block_id']
                available_count = block_info['count']
                # Calcola il valore suggerito, assicurandosi che sia almeno 1 se ci sono domande, e non superi il massimo
                suggested_value = 0
                if available_count > 0:
                    suggested_value = min(math.ceil(available_count / 3), available_count)
                temp_block_requests[block_id] = suggested_value
            st.session_state.block_requests = temp_block_requests

            # Resetta i valori dei widget number_input nel form (se il form esiste già)
            for key_widget in list(st.session_state.keys()):
                if key_widget.startswith("form_block_input_"):
                    # Estrai block_id dalla chiave del widget
                    try:
                        block_id_from_key = int(key_widget.split("_")[-1])
                        if block_id_from_key in st.session_state.block_requests:
                             st.session_state[key_widget] = st.session_state.block_requests[block_id_from_key]
                        else:
                             st.session_state[key_widget] = 0 # Fallback se block_id non trovato
                    except ValueError:
                         st.session_state[key_widget] = 0 # Fallback in caso di errore parsing chiave


elif st.session_state.processed_filename is not None and uploaded_file is None: 
     st.session_state.all_questions = None; st.session_state.blocks_summary = None
     st.session_state.block_requests = {}; st.session_state.processed_filename = None
     main_upload_status_placeholder.empty()
     output_placeholder.empty()
     transient_status_placeholder.empty()

st.markdown("---")
st.header(T("GENERATION_PARAMS_HEADER"))

with st.form(key="generation_form"):
    subject_name = st.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
    num_tests_input = st.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))

    total_questions_requested_form = 0
    if st.session_state.blocks_summary:
        st.subheader(T("BLOCK_REQUESTS_HEADER"))
        st.caption(T("BLOCK_REQUEST_SUGGESTION_INFO_TEXT")) # Testo di suggerimento aggiunto qui
        
        if not isinstance(st.session_state.block_requests, dict): # Safety check
            st.session_state.block_requests = {}

        for block_info in st.session_state.blocks_summary:
            block_id = block_info['block_id']
            block_type_str = block_info['type']
            available_count = block_info['count']
            label = F("BLOCK_REQUEST_LABEL", block_id=block_id, type=block_type_str, n=available_count)
            
            # Prendi il valore predefinito da st.session_state.block_requests, che ora ha il suggerimento
            default_value_for_block = st.session_state.block_requests.get(block_id, 0)
            # Assicura che il default non superi il massimo disponibile
            value_to_set_in_form = min(default_value_for_block, available_count)
            if available_count == 0 : value_to_set_in_form = 0 # Se il blocco è vuoto, il default è 0
            
            num_input_key = f"form_block_input_{block_id}"
            user_input_for_block = st.number_input(
                label=label, min_value=0, max_value=available_count,
                value=value_to_set_in_form, # Usa il valore precalcolato
                step=1, key=num_input_key
            )
            # Aggiorna st.session_state.block_requests con l'input effettivo dell'utente nel form
            # Questo è cruciale perché il form non aggiorna st.session_state.block_requests direttamente
            # ma aggiorna st.session_state[num_input_key]
            st.session_state.block_requests[block_id] = user_input_for_block 
            total_questions_requested_form += user_input_for_block

        st.markdown(f"**{T('TOTAL_QUESTIONS_SELECTED')}: {total_questions_requested_form}**")
    else:
        if uploaded_file is not None and not st.session_state.blocks_summary :
             pass 
        elif uploaded_file is None: 
            if st.session_state.processed_filename is None:
                st.info(T("UPLOAD_FIRST_WARNING"))

    generate_button_form = st.form_submit_button(
        T("GENERATE_BUTTON_LABEL"),
        type="primary",
        use_container_width=True,
        disabled=(uploaded_file is None or not st.session_state.blocks_summary)
    )

st.markdown("---") 
st.subheader(T("OUTPUT_AREA_HEADER"))

if generate_button_form:
    output_placeholder.empty(); transient_status_placeholder.empty() 
    main_upload_status_placeholder.empty() 
    st.session_state.action_performed = True

    # Usa i valori da st.session_state.block_requests che sono stati aggiornati nel ciclo del form
    active_block_requests = {bid: k for bid, k in st.session_state.block_requests.items() if k > 0}
    total_requested_final = sum(active_block_requests.values())

    if uploaded_file is None and st.session_state.processed_filename is None: 
        with output_placeholder: st.warning(T("UPLOAD_FIRST_WARNING")); st.stop()
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         with output_placeholder: st.error(F("LOAD_ERROR", error_msg="Dati blocchi non caricati. Ricarica il file.")); st.stop()
    if total_requested_final <= 0:
        with output_placeholder: st.error(T("TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS")); st.stop()

    pdf_generated = False; pdf_data = None; final_generation_messages = []
    with st.spinner(T("GENERATING_DATA_SPINNER")):
        try:
            all_tests_data, generation_messages_core = generate_all_tests_data(
                st.session_state.all_questions, active_block_requests, num_tests_input, status_callback 
            )
            final_generation_messages.extend(generation_messages_core)
            if all_tests_data is None or any(msg[0] == 'error' for msg in generation_messages_core):
                pass 

            if all_tests_data: 
                pdf_strings = { "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
                                "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
                                "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")}
                pdf_data = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)
                if pdf_data is not None:
                    pdf_generated = True
            
        except Exception as e: 
             if not any(m[0] == 'error' for m in final_generation_messages): 
                final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": str(e)}))
                status_callback("error", "GENERATION_FAILED_ERROR", error=str(e))


    with output_placeholder: 
        permanent_messages_to_show = [fm for fm in final_generation_messages if fm[0] not in ['warning', 'error']]
        if permanent_messages_to_show:
             st.markdown(f"**{T('GENERATION_MESSAGES_HEADER')}**")
             for msg_type, msg_key, msg_kwargs in permanent_messages_to_show:
                 final_formatted_text = F(msg_key, **msg_kwargs)
                 if msg_type == "info": st.info(final_formatted_text)

        if pdf_generated and pdf_data:
            st.success(T("PDF_SUCCESS"))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
            pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests_input}tests_{timestamp}.pdf"
            st.download_button( label=T("PDF_DOWNLOAD_BUTTON_LABEL"), data=pdf_data, file_name=pdf_filename,
                                mime="application/pdf", help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=pdf_filename),
                                use_container_width=True, type="primary")
        elif not pdf_generated and not transient_status_placeholder.empty(): 
            pass
        elif not pdf_generated: 
            if not any(msg[0] == 'error' for msg in final_generation_messages) and transient_status_placeholder.empty():
                 st.error(T("PDF_GENERATION_ERROR"))


if not st.session_state.action_performed and not uploaded_file and st.session_state.processed_filename is None:
    with output_placeholder: 
        st.info(T("INITIAL_INFO_NEW"))

st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
