# -*- coding: utf-8 -*-
# app.py (Gestisce input dinamici per blocco)

import streamlit as st
from datetime import datetime
import os
import pandas as pd

# Importa funzioni e costanti dai moduli separati
from localization import TEXTS, get_text, format_text
from config import (
    # DEFAULT_NUM_TESTS, DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, # Non più usati globalmente
    DEFAULT_NUM_TESTS, EXAMPLE_IMAGE_PATH # Mantiene questi
)
# Importa versioni aggiornate / Import updated versions
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
from test import run_all_tests # Assumendo che test.py sia aggiornato o non usato qui
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Stato Sessione e Logica Lingua / Session State and Language Logic
# ================================================================
if 'lang' not in st.session_state: st.session_state.lang = 'it'
# Inizializza stato per dati caricati e richieste utente
# Initialize state for loaded data and user requests
if 'blocks_summary' not in st.session_state: st.session_state.blocks_summary = None
if 'all_questions' not in st.session_state: st.session_state.all_questions = None
if 'block_requests' not in st.session_state: st.session_state.block_requests = {}

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
st.subheader(T("SUBHEADER_NEW")) # <-- Nuova chiave per sottotitolo / New key for subheader
if not WEASYPRINT_AVAILABLE: st.error(T("WEASYPRINT_ERROR")); st.stop()

# ================================================================
# Istruzioni (Espandibili) / Instructions (Expandable)
# ================================================================
with st.expander(T("INSTRUCTIONS_HEADER"), expanded=False):
    # Usa nuovo testo istruzioni / Use new instruction text
    st.markdown(T("INTRO_TEXT_NEW"), unsafe_allow_html=True) # <-- Nuova chiave / New key
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
    key="file_uploader" # Aggiunta chiave per possibile reset
)

# --- Placeholder per messaggi critici durante caricamento/analisi ---
sidebar_status_placeholder = st.sidebar.empty()

# --- Funzione Callback per Sidebar ---
def sidebar_status_callback(msg_type, msg_key, **kwargs):
     """Mostra solo warning/error nella sidebar."""
     if msg_type not in ["warning", "error"]: return
     formatted_text = F(msg_key, **kwargs)
     if formatted_text.startswith("MISSING_TEXT["): formatted_text = f"{msg_key}: {kwargs}" # Fallback
     if msg_type == "warning": sidebar_status_placeholder.warning(formatted_text)
     elif msg_type == "error": sidebar_status_placeholder.error(formatted_text)

# --- 2. Logica di Caricamento e Creazione Input Dinamici ---
if uploaded_file is not None:
    # Tenta di caricare/analizzare solo se il file è cambiato o non ancora processato
    # Attempt to load/analyze only if file changed or not yet processed
    if 'processed_filename' not in st.session_state or st.session_state.processed_filename != uploaded_file.name:
        sidebar_status_placeholder.info(F("FH_READING_EXCEL", file_name=uploaded_file.name)) # Messaggio caricamento
        all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, sidebar_status_callback)
        if error_k:
            # Errore mostrato dal callback, resetta stato
            st.session_state.all_questions = None
            st.session_state.blocks_summary = None
            st.session_state.block_requests = {}
            st.session_state.processed_filename = None
        else:
            # Successo: salva dati in sessione e resetta richieste precedenti
            st.session_state.all_questions = all_q
            st.session_state.blocks_summary = blocks_sum
            st.session_state.block_requests = {b['block_id']: 0 for b in blocks_sum} # Inizializza richieste a 0
            st.session_state.processed_filename = uploaded_file.name
            sidebar_status_placeholder.success(F("FH_LOAD_COMPLETE_BLOCKS", count=len(all_q), num_blocks=len(blocks_sum))) # Messaggio successo

# --- 3. Mostra Input Dinamici se Blocchi sono stati Identificati ---
if st.session_state.blocks_summary:
    st.sidebar.markdown("---")
    st.sidebar.subheader(T("BLOCK_REQUESTS_HEADER")) # <-- Nuova chiave / New key
    total_questions_requested = 0
    # Crea input per ogni blocco trovato / Create input for each found block
    for block_info in st.session_state.blocks_summary:
        block_id = block_info['block_id']
        block_type_str = block_info['type'] # Es. "Scelta Multipla" / e.g., "Multiple Choice"
        available_count = block_info['count']
        label = F("BLOCK_REQUEST_LABEL", block_id=block_id, type=block_type_str, n=available_count) # <-- Nuova chiave / New key

        # Legge/Scrive valore da/in st.session_state.block_requests
        # Read/Write value from/to st.session_state.block_requests
        st.session_state.block_requests[block_id] = st.sidebar.number_input(
            label=label,
            min_value=0,
            max_value=available_count,
            value=st.session_state.block_requests.get(block_id, 0), # Mantieni valore precedente se esiste / Keep previous value if exists
            step=1,
            key=f"block_input_{block_id}" # Chiave univoca per widget / Unique key for widget
        )
        total_questions_requested += st.session_state.block_requests[block_id]

    # Mostra totale domande selezionate / Show total selected questions
    st.sidebar.markdown(f"**{T('TOTAL_QUESTIONS_SELECTED')}: {total_questions_requested}**") # <-- Nuova chiave / New key
else:
    # Resetta se non ci sono blocchi (es. file rimosso)
    st.session_state.block_requests = {}


# --- 4. Input Generali Rimasti ---
st.sidebar.markdown("---")
subject_name = st.sidebar.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
num_tests_to_generate = st.sidebar.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))

# --- 5. Bottone Generazione ---
generate_button = st.sidebar.button(T("GENERATE_BUTTON_LABEL"), type="primary", use_container_width=True)

# --- 6. Test Funzionale (lasciato per ora, ma da aggiornare) ---
st.sidebar.markdown("---")
st.sidebar.subheader(T("VALIDATION_TEST_HEADER"))
validation_button = st.sidebar.button(
    T("VALIDATE_BUTTON_LABEL"),
    help=T("VALIDATE_BUTTON_HELP_NEW"), # Questo help non è più accurato / This help text is no longer accurate
    use_container_width=True,
    disabled=True # Disabilitato finché non aggiorniamo test.py / Disabled until test.py is updated
)


# ================================================================
# Area Output Principale e Gestione Messaggi / Main Output Area and Message Handling
# ================================================================
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder = st.container()
transient_status_placeholder = st.empty()

# Funzione per mostrare messaggi critici durante l'esecuzione
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

# Callback passato alle funzioni backend
def status_callback(msg_type, msg_key, **kwargs):
     display_critical_message(msg_type, msg_key, **kwargs)

# ================================================================
# Logica per il Test Funzionale (Disabilitata) / Logic for Functional Test (Disabled)
# ================================================================
if validation_button:
    output_placeholder.info("Il test funzionale deve essere aggiornato per la nuova logica a blocchi.")
    # ... (logica precedente commentata o rimossa) ...

# ================================================================
# Logica Principale per Generazione PDF / Main Logic for PDF Generation
# ================================================================
if generate_button:
    output_placeholder.empty()
    transient_status_placeholder.empty()

    # 1. Recupera richieste utente dai widget dinamici / Retrieve user requests from dynamic widgets
    current_block_requests = st.session_state.get('block_requests', {})
    # Filtra solo i blocchi con k > 0 / Filter only blocks with k > 0
    active_block_requests = {bid: k for bid, k in current_block_requests.items() if k > 0}
    total_requested = sum(active_block_requests.values())

    # 2. Validazione Input / Input Validation
    if uploaded_file is None:
        output_placeholder.warning(T("UPLOAD_FIRST_WARNING"))
        st.stop()
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         output_placeholder.error(T("LOAD_ERROR", error_msg="Dati blocchi non caricati correttamente.")) # Usa chiave generica
         st.stop()
    if total_requested <= 0:
        output_placeholder.error(T("TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS")) # <-- Nuova chiave / New key
        st.stop()

    # 3. Esecuzione Generazione / Run Generation
    pdf_generated = False
    pdf_data = None
    final_generation_messages = []

    with st.spinner(T("GENERATING_DATA_SPINNER", num_tests=num_tests_to_generate)): # Usa nuova variabile nome
        try:
            # Chiama la NUOVA logica passando la lista completa delle domande,
            # le richieste per blocco, e il numero di test
            # Call the NEW logic passing the full question list,
            # block requests, and number of tests
            all_tests_data, generation_messages = generate_all_tests_data(
                st.session_state.all_questions,
                active_block_requests,
                num_tests_to_generate, # Usa la variabile corretta
                status_callback
            )
            final_generation_messages.extend(generation_messages)
            if all_tests_data is None: raise ValueError("Test data generation failed.")

            # Prepara stringhe PDF (invariato)
            pdf_strings = {
                "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
                "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
                "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")
            }

            # Genera PDF (invariato, usa callback silenziato)
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

    # 4. Mostra Risultati Finali / Display Final Results
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
            # Aggiorna nome file per riflettere totale domande variabile
            # Update filename to reflect variable total questions
            pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests_to_generate}tests_{timestamp}.pdf"
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
    output_placeholder.info(T("INITIAL_INFO_NEW")) # <-- Nuova chiave / New key

# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
