# -*- coding: utf-8 -*-
# app.py

import streamlit as st
from datetime import datetime
import os
import pandas as pd
import math # Importato math per math.floor

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS, EXAMPLE_IMAGE_PATH, ANALYSIS_IMAGE_PATH
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
if 'processed_filename' not in st.session_state: st.session_state.processed_filename = None

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
    img_col1, img_col2, img_col3 = st.columns([0.15, 0.7, 0.15])
    with img_col2:
        try:
            st.image(EXAMPLE_IMAGE_PATH, caption=T("IMAGE_CAPTION"), use_container_width=True)
        except FileNotFoundError:
            st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
        except Exception as e:
            st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))
        st.markdown("---")
        try:
            st.image(ANALYSIS_IMAGE_PATH, caption=T("ANALYSIS_IMAGE_CAPTION"), use_container_width=True)
        except FileNotFoundError:
            st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=ANALYSIS_IMAGE_PATH))
        except Exception as e:
            st.error(F("IMAGE_LOAD_ERROR", image_path=ANALYSIS_IMAGE_PATH, error=e))

# ================================================================
# Sidebar per Input Utente / Sidebar for User Input
# ================================================================
st.sidebar.header(T("GENERATION_PARAMS_HEADER"))
uploaded_file = st.sidebar.file_uploader(
    T("UPLOAD_LABEL"), type=['xlsx', 'xls', 'csv'],
    help=T("UPLOAD_HELP"), key="file_uploader"
)
sidebar_status_placeholder = st.sidebar.empty()
def sidebar_status_callback(msg_type, msg_key, **kwargs):
     if msg_type not in ["warning", "error"]: return
     formatted_text = F(msg_key, **kwargs)
     if formatted_text.startswith("MISSING_TEXT["): formatted_text = f"{msg_key}: {kwargs}"
     if msg_type == "warning": sidebar_status_placeholder.warning(formatted_text)
     elif msg_type == "error": sidebar_status_placeholder.error(formatted_text)

if uploaded_file is not None:
    if st.session_state.processed_filename != uploaded_file.name:
        all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, sidebar_status_callback)
        if error_k:
            st.session_state.all_questions = None; st.session_state.blocks_summary = None
            st.session_state.block_requests = {}; st.session_state.processed_filename = None
        else:
            st.session_state.all_questions = all_q; st.session_state.blocks_summary = blocks_sum
            # MODIFICA 1: Imposta il valore predefinito a floor(n/3)
            st.session_state.block_requests = {
                b['block_id']: math.floor(b['count'] / 3) if b['count'] > 0 else 0
                for b in blocks_sum
            }
            st.session_state.processed_filename = uploaded_file.name
elif st.session_state.processed_filename is not None:
     st.session_state.all_questions = None; st.session_state.blocks_summary = None
     st.session_state.block_requests = {}; st.session_state.processed_filename = None
     sidebar_status_placeholder.empty()

total_questions_requested = 0
sampling_warnings = [] # Lista per raccogliere i warning sul campionamento

if st.session_state.blocks_summary:
    st.sidebar.markdown("---")
    st.sidebar.subheader(T("BLOCK_REQUESTS_HEADER"))
    if not isinstance(st.session_state.block_requests, dict):
        # Fallback nel caso block_requests non sia un dizionario (dovrebbe esserlo)
        st.session_state.block_requests = {
            b['block_id']: math.floor(b['count'] / 3) if b['count'] > 0 else 0
            for b in st.session_state.blocks_summary
        }

    for block_info in st.session_state.blocks_summary:
        block_id = block_info['block_id']
        block_type_str = block_info['type']
        available_count = block_info['count']
        label = F("BLOCK_REQUEST_LABEL", block_id=block_id, type=block_type_str, n=available_count)
        
        # Assicura che il valore corrente in session_state sia valido e non superi available_count
        # Questo è importante perché il default potrebbe cambiare se il file viene ricaricato
        # o se l'utente aveva precedentemente inserito un valore che ora non è più valido
        # a causa di un cambio di file o di logica.
        current_value_from_session = st.session_state.block_requests.get(block_id, 0)
        
        # Se available_count è 0, il valore deve essere 0.
        # Altrimenti, usa il valore dalla sessione, ma non più di available_count.
        # Il default (floor(n/3)) è già stato impostato quando il file è stato caricato.
        value_to_set = 0
        if available_count > 0:
            value_to_set = min(current_value_from_session, available_count)
        else: # Se available_count è 0, forza a 0
            st.session_state.block_requests[block_id] = 0


        # Crea il number_input
        # Il valore 'value' qui prende il valore precalcolato (o modificato dall'utente)
        # dalla session_state.
        k_selected_for_block = st.sidebar.number_input(
            label=label, min_value=0, max_value=available_count,
            value=st.session_state.block_requests.get(block_id,0), # Usa il valore già in sessione
            step=1, key=f"block_input_{block_id}"
        )
        # Aggiorna il valore in session_state con quello del widget (se l'utente lo cambia)
        st.session_state.block_requests[block_id] = k_selected_for_block
        total_questions_requested += k_selected_for_block

        # MODIFICA 2: Controlla e aggiungi warning per campionamento semplice
        # La condizione è k_selected * 2 >= available_count (equivalente a k_selected >= available_count / 2)
        # E k_selected > 0 per evitare warning su blocchi non usati.
        if available_count > 0 and k_selected_for_block > 0 and (k_selected_for_block * 2 >= available_count) :
            warn_msg = F("BLOCK_SWITCH_TO_SIMPLE_SAMPLING_WARNING",
                         block_id=block_id,
                         k_selected=k_selected_for_block,
                         n_available=available_count)
            sampling_warnings.append(warn_msg)

    # Mostra i warning raccolti nella sidebar
    if sampling_warnings:
        for warning_message in sampling_warnings:
            st.sidebar.warning(warning_message)
            
    st.sidebar.markdown(f"**{T('TOTAL_QUESTIONS_SELECTED')}: {total_questions_requested}**")


st.sidebar.markdown("---")
subject_name = st.sidebar.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
num_tests_input = st.sidebar.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))
generate_button = st.sidebar.button(T("GENERATE_BUTTON_LABEL"), type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader(T("VALIDATION_TEST_HEADER"))
validation_button = st.sidebar.button(
    T("VALIDATE_BUTTON_LABEL"),
    help=T("VALIDATE_BUTTON_HELP_NEW"),
    use_container_width=True
)

# ================================================================
# Area Output Principale e Gestione Messaggi / Main Output Area and Message Handling
# ================================================================
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container()
transient_status_placeholder = st.empty() # Per messaggi di errore/warning temporanei dalla generazione

def display_critical_message(message_type, key_or_raw_text, **kwargs):
    """Mostra solo warning/error nel transient_status_placeholder."""
    if message_type not in ["warning", "error"]: return # Mostra solo warning/error
    kwargs = kwargs or {}
    # Prova a formattare usando la funzione di localizzazione F
    formatted_text = F(key_or_raw_text, **kwargs)
    # Se la formattazione non ha funzionato (es. chiave non trovata), usa il testo grezzo
    if formatted_text == key_or_raw_text or formatted_text.startswith("MISSING_TEXT["):
        if kwargs: # Se ci sono kwargs, prova a formattare il testo grezzo direttamente
            try:
                formatted_text = key_or_raw_text.format(**kwargs)
            except (KeyError, IndexError, ValueError, TypeError): # In caso di errore di formattazione
                formatted_text = key_or_raw_text # Torna al testo grezzo
        else: # Se non ci sono kwargs, il testo grezzo è il messaggio
            formatted_text = key_or_raw_text

    if message_type == "warning":
        transient_status_placeholder.warning(formatted_text)
    elif message_type == "error":
        transient_status_placeholder.error(formatted_text)


def status_callback(msg_type, msg_key, **kwargs):
     # Questa callback è usata da core_logic e pdf_generator
     # Mostra i messaggi (solo warning/error) nel transient_status_placeholder
     display_critical_message(msg_type, msg_key, **kwargs)


# ================================================================
# Logica per il Test Funzionale / Logic for Functional Test
# ================================================================
if validation_button:
    output_placeholder.empty() # Pulisce output precedente
    transient_status_placeholder.empty() # Pulisce messaggi temporanei precedenti
    excel_file_created = None
    test_results = []
    st.session_state.action_performed = True # Indica che un'azione è stata eseguita

    with st.spinner(T("VALIDATION_LOGIC_SPINNER")):
        try:
            # La status_callback per run_all_tests ora usa display_critical_message
            # per mostrare errori critici del test nel transient_status_placeholder
            test_results, excel_file_created = run_all_tests(status_callback)
        except Exception as e:
             # Errore imprevisto nell'esecuzione di run_all_tests
             with output_placeholder: # Mostra errore nell'area principale
                 st.error(F("CL_VALIDATION_UNEXPECTED_ERROR", error=str(e)))
             test_results = None # Assicura che non si tenti di processare risultati nulli

    # Visualizza i risultati del test nell'area principale
    with output_placeholder:
        if test_results is not None: # Solo se test_results è stato popolato
            st.markdown(f"**{T('VALIDATION_RESULTS_HEADER')}**")
            if not test_results and not excel_file_created: # Nessun messaggio o file
                st.warning(T("VALIDATION_NO_MESSAGES"))
            elif test_results: # Ci sono messaggi da visualizzare
                for msg_type, msg_key, msg_kwargs in test_results:
                    final_formatted_text = F(msg_key, **msg_kwargs)
                    if msg_type == "info": st.info(final_formatted_text)
                    elif msg_type == "warning": st.warning(final_formatted_text)
                    elif msg_type == "error": st.error(final_formatted_text)
                    elif msg_type == "success": st.success(final_formatted_text)
                    else: st.write(f"[{msg_type.upper()}] {final_formatted_text}") # Fallback per tipi non gestiti

            # Bottone per scaricare l'Excel dei risultati statistici
            if excel_file_created and os.path.exists(excel_file_created):
                try:
                    with open(excel_file_created, "rb") as fp:
                        excel_bytes = fp.read()
                    st.download_button(
                        label=T("DOWNLOAD_STATS_EXCEL_LABEL"),
                        data=excel_bytes,
                        file_name=excel_file_created,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help=T("DOWNLOAD_STATS_EXCEL_HELP")
                    )
                except Exception as e:
                    st.error(f"Errore lettura file Excel per download: {e}")
        # Se test_results è None (a causa di un errore imprevisto in run_all_tests),
        # l'errore è già stato mostrato sopra.

# ================================================================
# Logica Principale per Generazione PDF / Main Logic for PDF Generation
# ================================================================
if generate_button:
    output_placeholder.empty(); transient_status_placeholder.empty()
    st.session_state.action_performed = True
    current_block_requests = st.session_state.get('block_requests', {})
    active_block_requests = {bid: k for bid, k in current_block_requests.items() if k > 0}
    total_requested = sum(active_block_requests.values())

    if uploaded_file is None:
        output_placeholder.warning(T("UPLOAD_FIRST_WARNING")); st.stop()
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         output_placeholder.error(T("LOAD_ERROR", error_msg=F("LOAD_ERROR", error_msg="Dati blocchi non caricati. Ricarica il file."))); st.stop()
    if total_requested <= 0:
        output_placeholder.error(T("TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS")); st.stop()

    pdf_generated = False; pdf_data = None; final_generation_messages = []

    with st.spinner(T("GENERATING_DATA_SPINNER")):
        try:
            all_tests_data, generation_messages = generate_all_tests_data(
                st.session_state.all_questions,
                active_block_requests,
                num_tests_input,
                status_callback # Usa la callback per mostrare warning/error nel transient placeholder
            )
            final_generation_messages.extend(generation_messages) # Accumula tutti i messaggi

            if all_tests_data is None: # Se la generazione dei dati fallisce criticamente
                # Cerca un messaggio di errore specifico tra quelli raccolti
                error_msg_from_core = next((m[1] for m in generation_messages if m[0] == 'error'), "Test data generation failed.")
                raise ValueError(error_msg_from_core)

            pdf_strings = {
                "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
                "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
                "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")
            }
            pdf_data = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)

            if pdf_data is None: # Se la generazione PDF fallisce
                 # Cerca un messaggio di errore specifico (es. da WeasyPrint)
                error_msg_from_pdf = next((m[1] for m in generation_messages if m[0] == 'error' and m[1].startswith("PG_")), "PDF generation failed.")
                raise ValueError(error_msg_from_pdf)
            pdf_generated = True

        except ValueError as ve: # Cattura errori sollevati esplicitamente
            msg_key_or_text = str(ve)
            # Aggiungi il messaggio di errore alla lista solo se non è già presente (per evitare duplicati)
            # o se è un messaggio generico di fallimento.
            is_known_key = msg_key_or_text in TEXTS['it'] or msg_key_or_text in TEXTS['en']
            if not any(m[1] == msg_key_or_text for m in final_generation_messages):
                if is_known_key:
                    final_generation_messages.append(("error", msg_key_or_text, {}))
                else: # Messaggio di errore generico
                    final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": msg_key_or_text}))
        except Exception as e: # Cattura altri errori imprevisti
            error_details = str(e)
            if not any(m[1] == "GENERATION_FAILED_ERROR" and m[2].get("error") == error_details for m in final_generation_messages):
                final_generation_messages.append(("error", "GENERATION_FAILED_ERROR", {"error": error_details}))

    # Visualizza i messaggi finali e il bottone di download nell'area principale
    with output_placeholder:
        if final_generation_messages:
            st.markdown(f"**{T('GENERATION_MESSAGES_HEADER')}**")
            for msg_type, msg_key, msg_kwargs in final_generation_messages:
                final_formatted_text = F(msg_key, **msg_kwargs)
                if msg_type == "warning": st.warning(final_formatted_text)
                elif msg_type == "error": st.error(final_formatted_text)
                # Non mostrare messaggi di successo qui, solo warning/error

        if pdf_generated and pdf_data:
            st.success(T("PDF_SUCCESS")) # Messaggio di successo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
            pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests_input}tests_{timestamp}.pdf"
            st.download_button(
                label=T("PDF_DOWNLOAD_BUTTON_LABEL"),
                data=pdf_data,
                file_name=pdf_filename,
                mime="application/pdf",
                help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=pdf_filename),
                use_container_width=True,
                type="primary"
            )
        elif not final_generation_messages and not pdf_generated : # Nessun messaggio e nessun PDF
            st.error(T("PDF_GENERATION_ERROR")) # Errore generico se non ci sono altri dettagli


# ================================================================
# Messaggio Iniziale / Initial Message
# ================================================================
if not st.session_state.action_performed:
    output_placeholder.info(T("INITIAL_INFO_NEW"))

# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
