# -*- coding: utf-8 -*-
# app.py (Fix Logica Floor e Posizionamento UI)

import streamlit as st
from datetime import datetime
import os
import math 

from localization import TEXTS, get_text, format_text
from config import (
    DEFAULT_NUM_TESTS,
    EXAMPLE_IMAGE_PATH 
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Stato Sessione e Logica Lingua
# ================================================================
if 'lang' not in st.session_state: st.session_state.lang = 'it'
if 'blocks_summary' not in st.session_state: st.session_state.blocks_summary = None
if 'all_questions' not in st.session_state: st.session_state.all_questions = None
if 'block_requests' not in st.session_state: st.session_state.block_requests = {} # Memorizza le richieste utente per blocco
if 'action_performed' not in st.session_state: st.session_state.action_performed = False
if 'processed_filename' not in st.session_state: st.session_state.processed_filename = None
if 'generated_pdf_data_for_button' not in st.session_state: st.session_state.generated_pdf_data_for_button = None
if 'generated_pdf_filename_for_button' not in st.session_state: st.session_state.generated_pdf_filename_for_button = None
if 'show_download_button' not in st.session_state: st.session_state.show_download_button = False
# Nuova chiave per forzare l'aggiornamento dei valori di default dei number_input dopo il caricamento del file
if 'force_default_block_values' not in st.session_state: st.session_state.force_default_block_values = False


def T(key): return get_text(st.session_state.lang, key)
def F(key, **kwargs): kwargs = kwargs or {}; return format_text(st.session_state.lang, key, **kwargs)

# ================================================================
# Setup Pagina
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
        .sidebar-image {{
            margin-top: 10px;
            margin-bottom: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================================================================
# Toggle Button Lingua
# ================================================================
cols_lang_title = st.columns([0.85, 0.075, 0.075])
with cols_lang_title[1]:
    button_it_type = "primary" if st.session_state.lang == 'it' else "secondary"
    if st.button("🇮🇹", key="lang_it_btn_main", type=button_it_type, help="Passa a Italiano / Switch to Italian", use_container_width=True):
        if st.session_state.lang != 'it':
            st.session_state.lang = 'it'
            st.session_state.show_download_button = False 
            st.rerun()
with cols_lang_title[2]:
    button_en_type = "primary" if st.session_state.lang == 'en' else "secondary"
    if st.button("🇬🇧", key="lang_en_btn_main", type=button_en_type, help="Passa a Inglese / Switch to English", use_container_width=True):
        if st.session_state.lang != 'en':
            st.session_state.lang = 'en'
            st.session_state.show_download_button = False 
            st.rerun()

# ================================================================
# Titolo e Contenuto Principale
# ================================================================
st.title(T("MAIN_TITLE"))
st.subheader(T("SUBHEADER_NEW")) 
st.caption(T("SUBHEADER_NOTE_SIDEBAR_INFO"))

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
    try:
        st.image(EXAMPLE_IMAGE_PATH, caption=T("IMAGE_CAPTION"), use_container_width=True, output_format='auto')
        st.markdown('<div class="sidebar-image"></div>', unsafe_allow_html=True) 
    except FileNotFoundError:
        st.warning(F("IMAGE_NOT_FOUND_WARNING", image_path=EXAMPLE_IMAGE_PATH))
    except Exception as e:
        st.error(F("IMAGE_LOAD_ERROR", image_path=EXAMPLE_IMAGE_PATH, error=e))
    st.markdown("---")

# ================================================================
# Corpo Principale
# ================================================================
main_upload_status_placeholder = st.empty()
transient_status_placeholder = st.empty() 
# output_placeholder_messages sarà definito più avanti, prima della sua effettiva necessità

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
     
     if transient_status_placeholder: 
        if msg_type == "warning": transient_status_placeholder.warning(formatted_text)
        elif msg_type == "error": transient_status_placeholder.error(formatted_text)
     else: 
        if msg_type == "warning": st.warning(formatted_text)
        elif msg_type == "error": st.error(formatted_text)


st.header(T("UPLOAD_LABEL")) 
uploaded_file = st.file_uploader(
    label="‎", 
    type=['xlsx', 'xls', 'csv'],
    help=T("UPLOAD_HELP"),
    key="file_uploader_main", # Chiave univoca
    on_change=lambda: st.session_state.update(show_download_button=False, force_default_block_values=True) # Resetta al cambio file
)

if uploaded_file is not None:
    if st.session_state.processed_filename != uploaded_file.name or st.session_state.force_default_block_values:
        main_upload_status_placeholder.empty() 
        transient_status_placeholder.empty() 
        # Non pulire output_placeholder_messages qui, potrebbe contenere il messaggio iniziale
        
        with st.spinner(T("LOADING_DATA_SPINNER")):
            all_q, blocks_sum, error_k = load_questions_from_excel(uploaded_file, main_upload_status_callback)
        
        if error_k:
            st.session_state.all_questions = None; st.session_state.blocks_summary = None
            st.session_state.block_requests = {}; st.session_state.processed_filename = None
        else:
            st.session_state.all_questions = all_q; st.session_state.blocks_summary = blocks_sum
            st.session_state.processed_filename = uploaded_file.name # Aggiorna il nome del file processato
            
            # Calcola e imposta i valori di default per block_requests
            temp_block_requests = {}
            for block_info in blocks_sum:
                block_id = block_info['block_id']
                available_count = block_info['count']
                suggested_value = 0
                if available_count > 0:
                    suggested_value = math.floor(available_count / 3) # FLOOR
                    # Assicura che il suggerimento sia almeno 1 se ci sono domande, ma non 0.
                    if suggested_value == 0 and available_count > 0:
                        suggested_value = 1
                    suggested_value = min(suggested_value, available_count) # Non superare il massimo
                temp_block_requests[block_id] = suggested_value
            st.session_state.block_requests = temp_block_requests
            
            # Forza l'aggiornamento dei widget number_input nel form al prossimo rerun
            # Questo è un po' un workaround per come Streamlit gestisce i default dei widget nei form
            # quando lo stato sottostante cambia.
            # Invece di modificare direttamente st.session_state[key_widget],
            # il valore corretto verrà preso da st.session_state.block_requests
            # quando il form viene renderizzato.
            st.session_state.force_default_block_values = False # Resetta il flag
            # Potrebbe essere necessario un st.rerun() qui se i widget non si aggiornano immediatamente
            # st.rerun() # Scommenta se i valori di default non si aggiornano al caricamento del file


elif st.session_state.processed_filename is not None and uploaded_file is None: # File rimosso
     st.session_state.all_questions = None; st.session_state.blocks_summary = None
     st.session_state.block_requests = {}; st.session_state.processed_filename = None
     main_upload_status_placeholder.empty()
     transient_status_placeholder.empty()
     st.session_state.show_download_button = False 

st.markdown("---")
st.header(T("GENERATION_PARAMS_HEADER"))

with st.form(key="generation_form"):
    subject_name = st.text_input(T("SUBJECT_LABEL"), value=T("SUBJECT_DEFAULT"), help=T("SUBJECT_HELP"))
    num_tests_input = st.number_input(T("NUM_TESTS_LABEL"), min_value=1, value=DEFAULT_NUM_TESTS, step=1, help=T("NUM_TESTS_HELP"))

    total_questions_requested_form = 0
    if st.session_state.blocks_summary:
        st.subheader(T("BLOCK_REQUESTS_HEADER"))
        st.caption(T("BLOCK_REQUEST_SUGGESTION_INFO_TEXT")) 
        
        if not isinstance(st.session_state.block_requests, dict): 
            st.session_state.block_requests = {}

        for block_info in st.session_state.blocks_summary:
            block_id = block_info['block_id']
            block_type_str = block_info['type']
            available_count = block_info['count']
            label = F("BLOCK_REQUEST_LABEL", block_id=block_id, type=block_type_str, n=available_count)
            
            # Prende il valore da st.session_state.block_requests (che contiene il default calcolato)
            # o 0 se non presente (non dovrebbe accadere se la logica di caricamento è corretta)
            default_value_for_block = st.session_state.block_requests.get(block_id, 0)
            
            # Assicura che il valore per il widget non superi il massimo disponibile
            value_to_set_in_widget = min(default_value_for_block, available_count)
            if available_count == 0: value_to_set_in_widget = 0
            
            num_input_key = f"form_block_input_{block_id}"
            # L'utente modifica questo widget. Il suo valore è in st.session_state[num_input_key]
            user_input_for_block = st.number_input(
                label=label, min_value=0, max_value=available_count,
                value=value_to_set_in_widget, 
                step=1, key=num_input_key
            )
            # Aggiorna st.session_state.block_requests con l'input effettivo dell'utente nel form
            # Questo è fatto qui per assicurare che `block_requests` sia la fonte della verità
            # per la logica di generazione, e rifletta le scelte dell'utente nel form.
            st.session_state.block_requests[block_id] = user_input_for_block
            total_questions_requested_form += user_input_for_block

        st.markdown(f"**{T('TOTAL_QUESTIONS_SELECTED')}: {total_questions_requested_form}**")
    else:
        if uploaded_file is not None and not st.session_state.blocks_summary :
             # Questo caso dovrebbe essere gestito da main_upload_status_placeholder se ci sono errori nel file
             pass 
        elif uploaded_file is None: 
            if st.session_state.processed_filename is None: # Mostra solo se nessun file è stato mai processato
                st.info(T("UPLOAD_FIRST_WARNING"))

    generate_button_form = st.form_submit_button(
        T("GENERATE_BUTTON_LABEL"),
        type="primary",
        use_container_width=True,
        disabled=(uploaded_file is None or not st.session_state.blocks_summary)
    )

# --- Pulsante di download e messaggio di successo PDF ---
# Questa sezione viene visualizzata DOPO il form e PRIMA dell'area "Output e Messaggi"
# solo se un PDF è stato generato con successo.
download_area_placeholder = st.empty() # Placeholder per il pulsante e il messaggio di successo

if st.session_state.get('show_download_button', False) and st.session_state.get('generated_pdf_data_for_button'):
    with download_area_placeholder.container(): # Usa un container per raggruppare messaggio e bottone
        st.success(T("PDF_SUCCESS")) # Messaggio di successo
        st.download_button( 
            label=T("PDF_DOWNLOAD_BUTTON_LABEL"), 
            data=st.session_state.generated_pdf_data_for_button, 
            file_name=st.session_state.generated_pdf_filename_for_button,
            mime="application/pdf", 
            help=F("PDF_DOWNLOAD_BUTTON_HELP", pdf_filename=st.session_state.generated_pdf_filename_for_button),
            use_container_width=True, 
            type="primary",
            key="manual_download_button_key" # Chiave univoca
        )
        # Considera di resettare show_download_button qui se vuoi che scompaia dopo un po' o un'altra azione
        # st.session_state.show_download_button = False 

st.markdown("---") 
st.subheader(T("OUTPUT_AREA_HEADER"))
output_placeholder_messages = st.container() # Placeholder per messaggi informativi o errori generici

if generate_button_form:
    # Pulisci i placeholder PRIMA di eseguire la logica di generazione
    transient_status_placeholder.empty() 
    main_upload_status_placeholder.empty() 
    output_placeholder_messages.empty() # Pulisce messaggi precedenti in quest'area
    download_area_placeholder.empty() # Pulisce area download precedente

    st.session_state.action_performed = True
    st.session_state.show_download_button = False # Nasconde il pulsante di download precedente

    active_block_requests = {bid: k for bid, k in st.session_state.block_requests.items() if k > 0}
    total_requested_final = sum(active_block_requests.values())

    # Validazioni iniziali
    if uploaded_file is None and st.session_state.processed_filename is None: 
        with output_placeholder_messages: st.warning(T("UPLOAD_FIRST_WARNING"))
        st.stop() 
    if not st.session_state.all_questions or not st.session_state.blocks_summary:
         with output_placeholder_messages: st.error(F("LOAD_ERROR", error_msg="Dati blocchi non caricati. Ricarica il file."))
         st.stop() 
    if total_requested_final <= 0:
        with output_placeholder_messages: st.error(T("TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS"))
        st.stop() 

    pdf_generated_successfully = False
    pdf_data_bytes = None
    generated_pdf_filename = None
    final_generation_messages = [] # Per messaggi 'info' da core_logic

    with st.spinner(T("GENERATING_DATA_SPINNER")):
        try:
            all_tests_data, generation_messages_core = generate_all_tests_data(
                st.session_state.all_questions, active_block_requests, num_tests_input, status_callback 
            )
            # Aggiungi solo messaggi informativi a final_generation_messages
            # gli errori/warning sono gestiti da status_callback
            final_generation_messages.extend([msg for msg in generation_messages_core if msg[0] == 'info'])


            if all_tests_data is None or any(msg[0] == 'error' for msg in generation_messages_core):
                # Errore già gestito da status_callback, non fare nulla per evitare duplicati
                pass
            else: 
                pdf_strings = { 
                    "title_format": T("PDF_TEST_TITLE"), "name_label": T("PDF_NAME_LABEL"),
                    "date_label": T("PDF_DATE_LABEL"), "class_label": T("PDF_CLASS_LABEL"),
                    "missing_question": T("PDF_MISSING_QUESTION"), "no_options": T("PDF_NO_OPTIONS")
                }
                pdf_data_bytes = generate_pdf_data(all_tests_data, subject_name, status_callback, pdf_strings)
                if pdf_data_bytes is not None:
                    pdf_generated_successfully = True
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
                    generated_pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests_input}tests_{timestamp}.pdf"
            
        except Exception as e: 
            status_callback("error", "GENERATION_FAILED_ERROR", error=str(e))
            # Non aggiungere a final_generation_messages qui, status_callback lo ha già fatto.

    # Dopo lo spinner, gestisci il risultato
    if pdf_generated_successfully and pdf_data_bytes and generated_pdf_filename:
        st.session_state.generated_pdf_data_for_button = pdf_data_bytes
        st.session_state.generated_pdf_filename_for_button = generated_pdf_filename
        st.session_state.show_download_button = True
        # Il messaggio di successo e il pulsante verranno mostrati al rerun nel loro placeholder
        st.rerun() 
    elif not pdf_generated_successfully:
        # Se la generazione non è riuscita E nessun errore specifico è stato mostrato da status_callback
        # (cioè transient_status_placeholder è ancora vuoto), mostra un errore generico.
        if transient_status_placeholder.empty(): 
            with output_placeholder_messages: # Mostra l'errore generico nell'area messaggi
                st.error(T("PDF_GENERATION_ERROR"))
        # Altrimenti, l'errore specifico è già visibile nel transient_status_placeholder.

    # Mostra messaggi 'info' raccolti da core_logic, se ce ne sono
    if final_generation_messages: # Solo se ci sono messaggi 'info'
        with output_placeholder_messages:
            st.markdown(f"**{T('GENERATION_MESSAGES_HEADER')}**")
            for msg_type, msg_key, msg_kwargs in final_generation_messages:
                final_formatted_text = F(msg_key, **msg_kwargs)
                if msg_type == "info": st.info(final_formatted_text)


if not st.session_state.action_performed and not uploaded_file and st.session_state.processed_filename is None:
    with output_placeholder_messages: 
        st.info(T("INITIAL_INFO_NEW"))

st.markdown("---")
st.markdown(T("FOOTER_TEXT"))
