# -*- coding: utf-8 -*-
# app.py (Modificato per i18n)

import streamlit as st
from datetime import datetime
import os

# Importa funzioni e costanti dai moduli separati
# Importa il modulo di localizzazione e la funzione helper
from localization import TEXTS, get_text, format_text
# Importa config per i default numerici e path immagine
from config import (
    DEFAULT_NUM_TESTS, DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, EXAMPLE_IMAGE_PATH
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data, run_validation_test
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE # WEASYPRINT_AVAILABLE viene da qui

# ================================================================
# Selezione Lingua e Helper Testo
# ================================================================

# Determina la lingua di default (es. 'it') o leggi da session_state se già impostata
if 'lang' not in st.session_state:
    st.session_state.lang = 'it' # Default a Italiano

# Widget per cambiare lingua - mettiamolo in cima alla sidebar
lang_options = {"🇮🇹 Italiano": "it", "🇬🇧 English": "en"}
display_lang = st.sidebar.radio(
    "Lingua / Language",
    options=lang_options.keys(),
    index=list(lang_options.values()).index(st.session_state.lang), # Imposta selezione corrente
    horizontal=True,
)
st.session_state.lang = lang_options[display_lang] # Aggiorna lingua in sessione

# Funzione helper locale per semplificare le chiamate get_text
def T(key):
    return get_text(st.session_state.lang, key)

# Funzione helper locale per semplificare le chiamate format_text
def F(key, **kwargs):
    return format_text(st.session_state.lang, key, **kwargs)

# ================================================================
# Setup Pagina e Titolo (ora usa T)
# ================================================================
st.set_page_config(page_title=T("PAGE_TITLE"), layout="wide", initial_sidebar_state="expanded")
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER"))

# Blocco critico se WeasyPrint non è disponibile (usa T)
if not WEASYPRINT_AVAILABLE:
    # Nota: Potremmo voler tradurre anche il messaggio di errore specifico di WeasyPrint se proviene dalla libreria,
    # ma per ora traduciamo solo il nostro avviso.
    st.error(T("WEASYPRINT_ERROR"))
    st.stop()

# ================================================================
# Istruzioni (Espandibili) (usa T)
# ================================================================
with st.expander(T("INSTRUCTIONS_HEADER"), expanded=False):
    # INTRO_TEXT viene ora da localization via T()
    st.markdown(T("INTRO_TEXT"), unsafe_allow_html=True)
    try:
        st.image(EXAMPLE_IMAGE_PATH, caption="Esempio di struttura file Excel valida", use_container_width=True) # Caption potrebbe essere tradotta se necessario
    except FileNotFoundError:
        st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
    except Exception as e:
        st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))

# ================================================================
# Sidebar per Input Utente (usa T)
# ================================================================
st.sidebar.header(T("GENERATION_PARAMS_HEADER"))

uploaded_file = st.sidebar.file_uploader(
    T("UPLOAD_LABEL"),
    type=['xlsx', 'xls'],
    help=T("UPLOAD_HELP")
)

# Usa T() per label e help. Il default viene ancora da config ma potrebbe essere tradotto.
subject_name = st.sidebar.text_input(
    T("SUBJECT_LABEL"),
    # Potremmo voler tradurre anche il valore di default, prendendolo da T()
    # value=T("SUBJECT_DEFAULT"), # Se presente in localization.py
    value=get_text('it', 'SUBJECT_DEFAULT') if st.session_state.lang == 'it' else get_text('en', 'SUBJECT_DEFAULT'), # Modo alternativo per default tradotto
    help=T("SUBJECT_HELP")
)

num_tests = st.sidebar.number_input(
    T("NUM_TESTS_LABEL"),
    min_value=1,
    value=DEFAULT_NUM_TESTS, # Valore numerico non cambia
    step=1,
    help=T("NUM_TESTS_HELP")
)

num_mc_q = st.sidebar.number_input(
    T("NUM_MC_LABEL"),
    min_value=0,
    value=DEFAULT_NUM_MC, # Valore numerico non cambia
    step=1,
    help=T("NUM_MC_HELP")
)

num_open_q = st.sidebar.number_input(
    T("NUM_OPEN_LABEL"),
    min_value=0,
    value=DEFAULT_NUM_OPEN, # Valore numerico non cambia
    step=1,
    help=T("NUM_OPEN_HELP")
)

generate_button = st.sidebar.button(T("GENERATE_BUTTON_LABEL"), type="primary", use_container_width=True)

# --- Sezione Test Validazione ---
st.sidebar.markdown("---")
st.sidebar.subheader(T("VALIDATION_TEST_HEADER"))
validation_button = st.sidebar.button(
    T("VALIDATE_BUTTON_LABEL"),
    help=T("VALIDATE_BUTTON_HELP"),
    use_container_width=True
)

# --- Sezione Download Codice Sorgente ---
st.sidebar.markdown("---")
st.sidebar.subheader(T("SOURCE_CODE_HEADER"))
try:
    script_path = os.path.abspath(__file__)
    script_name = os.path.basename(script_path)
    with open(script_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    st.sidebar.download_button(
        label=T("DOWNLOAD_SOURCE_BUTTON_LABEL"), # Usa T
        data=source_code,
        file_name=script_name,
        mime="text/x-python",
        use_container_width=True
    )
    st.sidebar.caption(T("DOWNLOAD_SOURCE_CAPTION")) # Usa T
except Exception as e:
    st.sidebar.warning(F("SOURCE_UNAVAILABLE_WARNING", error=e)) # Usa F

# ================================================================
# Area Output Principale (usa T e F)
# ================================================================
st.subheader(T("OUTPUT_AREA_HEADER"))

output_placeholder = st.container()

# Funzione display_message aggiornata per usare chiavi e formattazione
def display_message(message_type, key_or_raw_text, **kwargs):
    """
    Mostra messaggi nell'area output principale.
    Se key_or_raw_text è una chiave valida in localization.py, la usa.
    Altrimenti, tratta key_or_raw_text come testo grezzo.
    Formatta il testo se vengono passati kwargs.
    """
    # Tenta di recuperare il testo tradotto usando la chiave
    formatted_text = F(key_or_raw_text, **kwargs) if kwargs else T(key_or_raw_text)

    # Se il testo recuperato è tipo "MISSING_TEXT[...]" o uguale alla chiave
    # significa che la chiave non esiste, quindi usiamo il testo grezzo originale.
    # Oppure, se non ci sono kwargs, e T() restituisce la chiave stessa, usa la chiave come testo raw.
    # Questo gestisce sia chiavi mancanti sia il caso in cui la funzione backend
    # passi testo grezzo invece di una chiave.
    if formatted_text.startswith("MISSING_TEXT[") or (not kwargs and formatted_text == key_or_raw_text):
         # Se c'erano kwargs, prova a formattare il testo grezzo originale
         if kwargs:
             try:
                 formatted_text = key_or_raw_text.format(**kwargs)
             except: # Errore formattazione testo grezzo
                 formatted_text = key_or_raw_text # Usa testo grezzo non formattato
         else:
             formatted_text = key_or_raw_text # Usa testo grezzo


    # Mostra il messaggio finale
    if message_type == "info":
        output_placeholder.info(formatted_text)
    elif message_type == "warning":
        output_placeholder.warning(formatted_text)
    elif message_type == "error":
        output_placeholder.error(formatted_text)
    elif message_type == "success":
        output_placeholder.success(formatted_text)
    else:
        output_placeholder.write(f"[{message_type.upper()}] {formatted_text}")

# --- Callback per funzioni backend ---
# Questa funzione verrà passata a file_handler, core_logic, pdf_generator.
# Si aspetta una chiave e kwargs da quelle funzioni.
def status_callback(msg_type, msg_key, **kwargs):
     display_message(msg_type, msg_key, **kwargs)

# ================================================================
# Logica per il Test di Validazione (usa T, F e status_callback)
# ================================================================
if validation_button:
    output_placeholder.empty()
    display_message("info", "VALIDATION_START") # Usa chiave

    if uploaded_file is None:
        display_message("warning", "VALIDATION_UPLOAD_FIRST") # Usa chiave
    else:
        # Passa status_callback che si aspetta chiavi e kwargs
        with st.spinner(T("LOADING_DATA_VALIDATION_SPINNER")): # Usa T per testo spinner
            all_questions_test, error_msg_load_key = load_questions_from_excel(uploaded_file, status_callback)
            # Nota: load_questions_from_excel ora dovrebbe ritornare la CHIAVE dell'errore, non il messaggio formattato

        if error_msg_load_key:
             # error_msg_load_key dovrebbe essere tipo "FH_UNEXPECTED_ERROR" o "FH_NO_VALID_QUESTIONS"
             # Se ritorna testo grezzo, display_message lo gestirà.
             display_message("error", error_msg_load_key) # Mostra l'errore (già tradotto se chiave valida)
        elif not all_questions_test:
             display_message("error", "NO_VALID_QUESTIONS_VALIDATION") # Usa chiave
        else:
             # Dati caricati (il messaggio viene da status_callback). Esegui logica test.
             display_message("info", "CL_VALIDATION_RUNNING", num_tests_generated=2) # Esempio con chiave e param
             with st.spinner(T("VALIDATION_LOGIC_SPINNER")):
                # Passa status_callback a run_validation_test
                validation_results_keys = run_validation_test(all_questions_test, status_callback)

             display_message("info", "VALIDATION_RESULTS_HEADER") # Usa chiave
             if not validation_results_keys:
                 display_message("warning", "VALIDATION_NO_MESSAGES") # Usa chiave
             else:
                 # validation_results_keys dovrebbe essere una lista di tuple (tipo, chiave, kwargs)
                 for msg_type, msg_key, msg_kwargs in validation_results_keys:
                     display_message(msg_type, msg_key, **msg_kwargs) # Usa display_message aggiornato
            st.markdown("---")

# ================================================================
# Logica Principale per Generazione PDF (usa T, F e status_callback)
# ================================================================
if generate_button:
    output_placeholder.empty()
    display_message("info", "GENERATION_START") # Usa chiave

    if uploaded_file is None:
        display_message("warning", "UPLOAD_FIRST_WARNING") # Usa chiave
        st.stop()

    with st.spinner(T("LOADING_DATA_SPINNER")):
         # Passa status_callback che si aspetta chiavi
         all_questions, error_msg_load_key = load_questions_from_excel(uploaded_file, status_callback)

    if error_msg_load_key:
         display_message("error", error_msg_load_key) # Mostra errore (tradotto se chiave valida)
         st.stop()
    if not all_questions:
         display_message("error", "NO_VALID_QUESTIONS_ERROR") # Usa chiave
         st.stop()

    num_q_per_test = num_mc_q + num_open_q
    if num_q_per_test <= 0:
         display_message("error", "TOTAL_QUESTIONS_ZERO_ERROR") # Usa chiave
         st.stop()

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions)
    total_open = len(open_questions)
    error_found_main = False

    if total_mc == 0 and num_mc_q > 0: display_message("error", "MC_ZERO_ERROR", num_mc_q=num_mc_q); error_found_main = True # Usa F
    if total_open == 0 and num_open_q > 0: display_message("error", "OPEN_ZERO_ERROR", num_open_q=num_open_q); error_found_main = True # Usa F
    if total_mc < num_mc_q: display_message("error", "MC_INSUFFICIENT_ERROR", total_mc=total_mc, num_mc_q=num_mc_q); error_found_main = True # Usa F
    if total_open < num_open_q: display_message("error", "OPEN_INSUFFICIENT_ERROR", total_open=total_open, num_open_q=num_open_q); error_found_main = True # Usa F

    if error_found_main:
        display_message("error", "CORRECT_ERRORS_ERROR") # Usa chiave
        st.stop()

    display_message("info", "PARAMS_OK_INFO", num_tests=num_tests, subject_name=subject_name, num_mc_q=num_mc_q, num_open_q=num_open_q, num_q_per_test=num_q_per_test) # Usa F

    with st.spinner(F("GENERATING_DATA_SPINNER", num_tests=num_tests)): # Usa F per testo spinner
        # Passa status_callback
        all_tests_data, generation_messages_keys = generate_all_tests_data(
            mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback
        )

    if generation_messages_keys:
         display_message("info", "GENERATION_MESSAGES_HEADER") # Usa chiave
         # generation_messages_keys dovrebbe essere lista di (tipo, chiave, kwargs)
         for msg_type, msg_key, msg_kwargs in generation_messages_keys:
             display_message(msg_type, msg_key, **msg_kwargs)
         st.markdown("---")

    if all_tests_data is None:
        display_message("error", "GENERATION_FAILED_ERROR") # Usa chiave
        st.stop()

    # Prepara testi tradotti per il PDF
    pdf_strings = {
        "title_format": T("PDF_TEST_TITLE"), # Passa il formato stringa
        "name_label": T("PDF_NAME_LABEL"),
        "date_label": T("PDF_DATE_LABEL"),
        "class_label": T("PDF_CLASS_LABEL"),
        "missing_question": T("PDF_MISSING_QUESTION"),
        "no_options": T("PDF_NO_OPTIONS")
    }

    display_message("info", "DATA_READY_PDF_INFO", num_tests=len(all_tests_data)) # Usa F
    with st.spinner(T("PDF_CREATION_SPINNER")):
         # Passa status_callback e i testi tradotti necessari
         pdf_data = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)

    if pdf_data:
        display_message("success", "PDF_SUCCESS") # Usa chiave
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
        pdf_filename = f"Tests_{safe_filename_subject}_{num_tests}x{num_q_per_test}q_{timestamp}.pdf" # Nome file più internazionale

        st.download_button(
            label=T("PDF_DOWNLOAD_BUTTON_LABEL"), # Usa T
            data=pdf_data,
            file_name=pdf_filename,
            mime="application/pdf",
            help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=pdf_filename), # Usa F
            use_container_width=True,
            type="primary"
        )
    else:
        display_message("error", "PDF_GENERATION_ERROR") # Usa chiave


if not generate_button and not validation_button:
     output_placeholder.info(T("INITIAL_INFO")) # Usa T

# ================================================================
# Footer (usa T)
# ================================================================
st.markdown("---")
st.markdown(T("FOOTER_TEXT")) # Usa T
