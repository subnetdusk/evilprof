# -*- coding: utf-8 -*-
# app.py (Script Principale EvilProf)

import streamlit as st
from datetime import datetime
import os

# Importa funzioni e costanti dai moduli 
from config import (
    INTRO_TEXT, DEFAULT_SUBJECT, DEFAULT_NUM_TESTS,
    DEFAULT_NUM_MC, DEFAULT_NUM_OPEN, EXAMPLE_IMAGE_PATH
)
from file_handler import load_questions_from_excel
from core_logic import generate_all_tests_data, run_validation_test
from pdf_generator import generate_pdf_data, WEASYPRINT_AVAILABLE

# ================================================================
# Setup Pagina e Titolo
# ================================================================
st.set_page_config(page_title="EvilProf 😈", layout="wide", initial_sidebar_state="expanded")
st.title("EvilProf 😈")
st.subheader("Generatore di verifiche casuali e diverse, da Excel a PDF")

# Blocco critico se WeasyPrint non è disponibile
if not WEASYPRINT_AVAILABLE:
    st.error("🚨 **Attenzione:** La libreria WeasyPrint non è disponibile o funzionante. La generazione del PDF è bloccata. Assicurati di averla installata e che le sue dipendenze (GTK+, Pango, Cairo) siano presenti nel sistema.")
    st.stop() # Interrompe l'esecuzione dell'app

# ================================================================
# Istruzioni 
# ================================================================
with st.expander("ℹ️ Istruzioni e Preparazione File Excel", expanded=False):
    st.markdown(INTRO_TEXT, unsafe_allow_html=True)
    try:
        st.image(EXAMPLE_IMAGE_PATH, caption="Esempio di struttura file Excel valida", use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Nota: Immagine di esempio '{EXAMPLE_IMAGE_PATH}' non trovata.")
    except Exception as e:
        st.error(f"Errore caricamento immagine '{EXAMPLE_IMAGE_PATH}': {e}")

# ================================================================
# Sidebar per Input Utente
# ================================================================
st.sidebar.header("Parametri di Generazione")

uploaded_file = st.sidebar.file_uploader(
    "1. Carica File Excel (.xlsx, .xls)",
    type=['xlsx', 'xls'],
    help="Trascina o seleziona il file Excel con le domande."
)

subject_name = st.sidebar.text_input(
    "2. Nome della Materia",
    value=DEFAULT_SUBJECT,
    help="Apparirà nel titolo di ogni verifica."
)

num_tests = st.sidebar.number_input(
    "3. Numero di Verifiche da Generare",
    min_value=1,
    value=DEFAULT_NUM_TESTS,
    step=1,
    help="Quante versioni diverse della verifica creare?"
)

num_mc_q = st.sidebar.number_input(
    "4. N. Domande Scelta Multipla / Verifica",
    min_value=0,
    value=DEFAULT_NUM_MC,
    step=1,
    help="Quante domande a scelta multipla includere in ogni verifica."
)

num_open_q = st.sidebar.number_input(
    "5. N. Domande Aperte / Verifica",
    min_value=0,
    value=DEFAULT_NUM_OPEN,
    step=1,
    help="Quante domande a risposta aperta includere in ogni verifica."
)

generate_button = st.sidebar.button("🚀 Genera Verifiche PDF", type="primary", use_container_width=True)

# --- Sezione Test Validazione ---
st.sidebar.markdown("---")
st.sidebar.subheader("Test Funzionale")
validation_button = st.sidebar.button(
    "🧪 Esegui Test di Validazione",
    help="Genera 2 test con poche domande per verificare la logica base (richiede file caricato).",
    use_container_width=True
)

# --- Sezione Download Codice Sorgente ---
st.sidebar.markdown("---")
st.sidebar.subheader("Codice Sorgente")
try:
    # Tenta di leggere il codice sorgente di questo script (app.py)
    script_path = os.path.abspath(__file__)
    script_name = os.path.basename(script_path)
    with open(script_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    st.sidebar.download_button(
        label="📥 Scarica Codice App (app.py)",
        data=source_code,
        file_name=script_name,
        mime="text/x-python",
        use_container_width=True
    )
    # Nota: Questo scaricherà solo app.py. L'utente dovrà scaricare manualmente gli altri.
    # Si potrebbe creare uno zip, ma aumenta la complessità.
    st.sidebar.caption("Scarica gli altri file (.py) separatamente.")

except Exception as e:
    st.sidebar.warning(f"Download codice sorgente non disponibile: {e}")

# ================================================================
# Area Output Principale
# ================================================================
st.subheader("Output e Messaggi")

# Placeholder per messaggi di stato e risultati
output_placeholder = st.container()

# Funzione helper per mostrare messaggi tramite placeholder o direttamente
def display_message(message_type, message_text):
    """Mostra messaggi nell'area output principale."""
    if message_type == "info":
        output_placeholder.info(message_text)
    elif message_type == "warning":
        output_placeholder.warning(message_text)
    elif message_type == "error":
        output_placeholder.error(message_text)
    elif message_type == "success":
        output_placeholder.success(message_text)
    else: # Fallback per tipi non riconosciuti
        output_placeholder.write(f"[{message_type.upper()}] {message_text}")

# ================================================================
# Logica per il Test di Validazione
# ================================================================
if validation_button:
    output_placeholder.empty() # Pulisce l'output precedente
    display_message("info", "Avvio Test di Validazione...")

    if uploaded_file is None:
        display_message("warning", "⚠️ Carica un file Excel per eseguire il test.")
    else:
        with st.spinner("⏳ Caricamento dati per validazione..."):
            # Usa lo stesso loader, ma mostra i messaggi nell'output principale
            all_questions_test, error_msg_load = load_questions_from_excel(uploaded_file, display_message)

        if error_msg_load:
            display_message("error", f"Errore caricamento dati per test: {error_msg_load}")
        elif not all_questions_test:
             display_message("error", "Nessuna domanda valida trovata per il test.")
        else:
            display_message("info", f"Dati caricati ({len(all_questions_test)} domande). Esecuzione logica di validazione...")
            with st.spinner("⏳ Esecuzione test logico..."):
                validation_results = run_validation_test(all_questions_test, display_message)

            display_message("info", "--- Risultato Test Validazione ---")
            if not validation_results:
                 display_message("warning", "Il test di validazione non ha prodotto messaggi.")
            else:
                 for msg_type, msg_text in validation_results:
                     display_message(msg_type, msg_text)
            st.markdown("---") # Separatore dopo il test

# ================================================================
# Logica Principale per Generazione PDF
# ================================================================
if generate_button:
    output_placeholder.empty() # Pulisce l'output precedente
    display_message("info", "Avvio Generazione Verifiche...")

    # 1. Controllo Preliminare File
    if uploaded_file is None:
        display_message("warning", "⚠️ Per favore, carica prima un file Excel.")
        st.stop() # Interrompe se manca il file

    # 2. Caricamento Domande (usa cache sessione interna a load_questions)
    with st.spinner("⏳ Caricamento e validazione domande..."):
         all_questions, error_msg_load = load_questions_from_excel(uploaded_file, display_message)

    if error_msg_load:
         display_message("error", f"Errore caricamento dati: {error_msg_load}")
         st.stop()
    if not all_questions:
         display_message("error", "Nessuna domanda valida trovata nel file. Impossibile procedere.")
         st.stop()

    # 3. Validazione Parametri Utente
    num_q_per_test = num_mc_q + num_open_q
    if num_q_per_test <= 0:
         display_message("error", "ERRORE: Il numero totale di domande per verifica (Multiple + Aperte) deve essere maggiore di zero.")
         st.stop()

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions)
    total_open = len(open_questions)
    error_found_main = False

    # Controlli critici di fattibilità
    if total_mc == 0 and num_mc_q > 0: display_message("error", f"ERRORE: Richieste {num_mc_q} domande a scelta multipla, ma 0 trovate nel file."); error_found_main = True
    if total_open == 0 and num_open_q > 0: display_message("error", f"ERRORE: Richieste {num_open_q} domande aperte, ma 0 trovate nel file."); error_found_main = True
    if total_mc < num_mc_q: display_message("error", f"ERRORE CRITICO: Non ci sono abbastanza domande a scelta multipla ({total_mc}) per soddisfare le {num_mc_q} richieste per verifica."); error_found_main = True
    if total_open < num_open_q: display_message("error", f"ERRORE CRITICO: Non ci sono abbastanza domande aperte ({total_open}) per soddisfare le {num_open_q} richieste per verifica."); error_found_main = True

    if error_found_main:
        display_message("error", "Correggi gli errori sopra prima di generare.")
        st.stop()

    # Se i controlli passano, informa l'utente e procedi
    display_message("info", f"Parametri OK. Generazione di {num_tests} verifiche per '{subject_name}' con {num_mc_q} MC + {num_open_q} Aperte = {num_q_per_test} Domande/Test.")

    # 4. Generazione Dati dei Test (logica core)
    with st.spinner(f"⏳ Generazione dati per {num_tests} verifiche..."):
        all_tests_data, generation_messages = generate_all_tests_data(
            mc_questions, open_questions, num_tests, num_mc_q, num_open_q, display_message
        )

    # Mostra messaggi accumulati dalla generazione (es. fallback, diversità)
    if generation_messages:
         display_message("info", "--- Messaggi dalla Generazione dei Dati ---")
         for msg_type, msg_text in generation_messages:
             display_message(msg_type, msg_text)
         st.markdown("---") # Separatore

    if all_tests_data is None:
        display_message("error", "❌ Generazione dati fallita a causa di errori critici. Controllare i messaggi sopra.")
        st.stop()

    # 5. Generazione PDF
    display_message("info", f"Dati per {len(all_tests_data)} verifiche pronti. Avvio generazione PDF...")
    with st.spinner("⏳ Creazione del file PDF in corso (può richiedere tempo)..."):
         pdf_data = generate_pdf_data(all_tests_data, subject_name, display_message)

    # 6. Offri Download PDF
    if pdf_data:
        display_message("success", "✅ Generazione PDF completata!")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Pulisce il nome file da caratteri problematici
        safe_filename_subject = "".join(c if c.isalnum() else "_" for c in subject_name)
        pdf_filename = f"Verifiche_{safe_filename_subject}_{num_tests}x{num_q_per_test}q_{timestamp}.pdf"

        st.download_button(
            label="📥 Scarica PDF Generato",
            data=pdf_data,
            file_name=pdf_filename,
            mime="application/pdf",
            help=f"Clicca per scaricare il file '{pdf_filename}'",
            use_container_width=True,
            type="primary" # Pulsante download primario
        )
    else:
        display_message("error", "❌ Errore durante la creazione del file PDF. Controllare i messaggi sopra, specialmente quelli relativi a WeasyPrint.")

# Messaggio iniziale se nessun bottone è stato premuto
if not generate_button and not validation_button:
     output_placeholder.info("Configura i parametri nella sidebar e premi 'Genera Verifiche PDF' o 'Esegui Test di Validazione'.")


# ================================================================
# Footer
# ================================================================
st.markdown("---")
st.markdown("EvilProf v1.1 (Refactored) - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit")
