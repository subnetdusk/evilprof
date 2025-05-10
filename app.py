# -*- coding: utf-8 -*-
# app.py (Larghezza 1200px e Test in Sidebar)

import streamlit as st
from datetime import datetime
import os
# import pandas as pd # Non direttamente usato qui, ma file_handler lo usa

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text # Assicurati che localization.py sia la versione corretta
from config import (
    DEFAULT_NUM_TESTS
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
from test import run_all_tests # Per il test funzionale/statistico
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
if 'show_test_results_in_sidebar' not in st.session_state: st.session_state.show_test_results_in_sidebar = False
if 'sidebar_test_messages' not in st.session_state: st.session_state.sidebar_test_messages = []
if 'sidebar_excel_file' not in st.session_state: st.session_state.sidebar_excel_file = None


def T(key): return get_text(st.session_state.lang, key)
def F(key, **kwargs): kwargs = kwargs or {}; return format_text(st.session_state.lang, key, **kwargs)

# ================================================================
# Setup Pagina / Page Setup
# ================================================================
st.set_page_config(page_title=T("PAGE_TITLE"), layout="wide", initial_sidebar_state="collapsed")

# CSS per impostare la larghezza massima del contenuto principale
# Il selettore [data-testid="stAppViewContainer"] punta al contenitore principale dell'app
# e [data-testid="stBlock"] ai blocchi di contenuto al suo interno.
# Applichiamo max-width al primo stBlock diretto figlio del main per centrare il contenuto.
max_width_px = 1200  # Aggiornato a 1200px
st.markdown(
    f"""
    <style>
        /* Contenitore principale dell'applicazione Streamlit */
        .main [data-testid="stAppViewContainer"] > .block-container {{
            max-width: {max_width_px}px;
            padding-left: 1rem; 
            padding-right: 1rem;
            margin-left: auto !important; /* Forza il margine per centrare */
            margin-right: auto !important; /* Forza il margine per centrare */
        }}
        /* Stile per i messaggi di output del test nella sidebar */
        .sidebar .stAlert {{
            font-size: 0.85rem; 
        }}
         .sidebar .stDownloadButton button {{
            width: 100%; 
            font-size: 0.9rem;
        }}
        /* Rende il bordo della sidebar più visibile */
        section[data-testid="stSidebar"] {{
            border-right: 2px solid #e0e0e0; 
            box-shadow: 2px 0px 5px rgba(0,0,0,0.1); 
        }}
        /* Stile per il bottone di espansione/collasso della sidebar */
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
# Per mantenere i bottoni lingua all'interno della larghezza definita,
# li mettiamo in una colonna che sarà influenzata dal CSS sopra.
# Questo è un workaround; idealmente Streamlit offrirebbe più controllo sul layout header.
# Dato che il CSS ora agisce su .main [data-testid="stAppViewContainer"] > .block-container,
# i bottoni lingua, se messi direttamente, sarebbero a larghezza piena.
# Li collochiamo quindi all'inizio del contenuto principale.

# Titolo e Sottotitolo Principale
st.title(T("MAIN_TITLE"))

# Bottoni lingua posizionati sotto il titolo ma prima del contenuto principale "stretto"
cols_lang_title = st.columns([0.85, 0.075, 0.075])
with cols_lang_title[1]:
    button_it_type = "primary" if st.session_state.lang == 'it' else "secondary"
    if st.button("🇮🇹", key="lang_it_btn_main", type=button_it_type, help="Passa a Italiano / Switch to Italian", use_container_width=True):
        if st.session_state.lang != 'it':
            st.session_state.lang = 'it'
            st.session_state.show_test_results_in_sidebar = False 
            st.rerun()
with cols_lang_title[2]:
    button_en_type = "primary" if st.session_state.lang == 'en' else "secondary"
    if st.button("🇬🇧", key="lang_en_btn_main", type=button_en_type, help="Passa a Inglese / Switch to English", use_container_width=True):
        if st.session_state.lang != 'en':
            st.session_state.lang = 'en'
            st.session_state.show_test_results_in_sidebar = False 
            st.rerun()

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

    # --- Sezione Test Statistico-Funzionale (NELLA SIDEBAR) ---
    st.header(T("STAT_FUNCTIONAL_TEST_HEADER"))
    validation_button_sidebar = st.button(
        T("STAT_FUNCTIONAL_VALIDATE_BUTTON_LABEL"), 
        help=T("VALIDATE_BUTTON_HELP_NEW"),
        use_container_width=True,
        key="validation_button_sidebar" 
    )

    sidebar_test_output_placeholder = st.container() 

    if validation_button_sidebar:
        st.session_state.action_performed = True 
        st.session_state.show_test_results_in_sidebar = True 
        st.session_state.sidebar_test_messages = [] 
        st.session_state.sidebar_excel_file = None  
        
        main_upload_status_placeholder.empty() 
        output_placeholder.empty() 
        transient_status_placeholder.empty()

        with st.spinner(T("VALIDATION_LOGIC_SPINNER")): 
            try:
                test_results_messages, excel_file_created = run_all_tests(status_callback)
                st.session_state.sidebar_test_messages = test_results_messages
                st.session_state.sidebar_excel_file = excel_file_created
            except Exception as e:
                 st.session_state.sidebar_test_messages = [("error", "CL_VALIDATION_UNEXPECTED_ERROR", {"error": str(e)})]
        st.rerun() 

    if st.session_state.show_test_results_in_sidebar:
        with sidebar_test_output_placeholder:
            st.markdown(f"**{T('VALIDATION_RESULTS_HEADER')}**") 
            if not st.session_state.sidebar_test_messages and not st.session_state.sidebar_excel_file:
                st.warning(T("VALIDATION_NO_MESSAGES")) 
            elif st.session_state.sidebar_test_messages:
                for msg_type, msg_key, msg_kwargs in st.session_state.sidebar_test_messages:
                    final_formatted_text = F(msg_key, **msg_kwargs)
                    if msg_type == "info": st.info(final_formatted_text)
                    elif msg_type == "warning": st.warning(final_formatted_text)
                    elif msg_type == "error": st.error(final_formatted_text)
                    elif msg_type == "success": st.success(final_formatted_text)
                    else: st.write(f"[{msg_type.upper()}] {final_formatted_text}")
            if st.session_state.sidebar_excel_file and os.path.exists(st.session_state.sidebar_excel_file):
                try:
                    with open(st.session_state.sidebar_excel_file, "rb") as fp: excel_bytes = fp.read()
                    st.download_button(
                        label=T("DOWNLOAD_STATS_EXCEL_LABEL"),
                        data=excel_bytes,
                        file_name=os.path.basename(st.session_state.sidebar_excel_file),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help=T("DOWNLOAD_STATS_EXCEL_HELP"),
                        use_container_width=True 
                    )
                except Exception as e: st.error(f"Errore lettura file Excel per download: {e}")
            if st.button("Nascondi Risultati Test", key="hide_sidebar_test_results", use_container_width=True):
                st.session_state.show_test_results_in_sidebar = False
                st.rerun()

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
        st.session_state.show_test_results_in_sidebar = False 
        with st.spinner(T("LOADING_DATA_SPINNER")):
            all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, main_upload_status_callback)
        if error_k:
            st.session_state.all_questions = None; st.session_state.blocks_summary = None
            st.session_state.block_requests = {}; st.session_state.processed_filename = None
        else:
            st.session_state.all_questions = all_q; st.session_state.blocks_summary = blocks_sum
            st.session_state.block_requests = {b['block_id']: 0 for b in blocks_sum} # Resetta a 0 per il nuovo file
            st.session_state.processed_filename = uploaded_file.name
            # Resetta i valori dei number_input nel form se un nuovo file viene caricato
            for key_widget in list(st.session_state.keys()):
                if key_widget.startswith("form_block_input_"):
                    st.session_state[key_widget] = 0


elif st.session_state.processed_filename is not None and uploaded_file is None: 
     st.session_state.all_questions = None; st.session_state.blocks_summary = None
     st.session_state.block_requests = {}; st.session_state.processed_filename = None
     main_upload_status_placeholder.empty()
     st.session_state.show_test_results_in_sidebar = False 

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
            
            num_input_key = f"form_block_input_{block_id}"
            user_input_for_block = st.number_input(
                label=label, min_value=0, max_value=available_count,
                value=value_to_set_in_form, step=1, key=num_input_key
            )
            st.session_state.block_requests[block_id] = user_input_for_block 
            total_questions_requested_form += user_input_for_block

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
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container() 
transient_status_placeholder = st.empty() 

def display_critical_message_main(message_type, key_or_raw_text, **kwargs):
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
     display_critical_message_main(msg_type, msg_key, **kwargs)


if generate_button_form:
    output_placeholder.empty(); transient_status_placeholder.empty()
    st.session_state.action_performed = True
    st.session_state.show_test_results_in_sidebar = False 

    active_block_requests = {bid: k for bid, k in st.session_state.block_requests.items() if k > 0}
    total_requested_final = sum(active_block_requests.values())

    if uploaded_file is None and st.session_state.processed_filename is None:
        output_placeholder.warning(T("UPLOAD_FIRST_WARNING")); st.stop()
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         output_placeholder.error(F("LOAD_ERROR", error_msg="Dati blocchi non caricati. Ricarica il file.")); st.stop()
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

if not st.session_state.action_performed and not uploaded_file and st.session_state.processed_filename is None:
    with output_placeholder: 
        st.info(T("INITIAL_INFO_NEW"))

st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
