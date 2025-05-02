# -*- coding: utf-8 -*-

# ================================================================
# EvilProf 😈 - Generatore Verifiche da Excel - v1.0
# ================================================================

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io
import os

# Import e controllo per WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# ================================================================
# Testo Introduttivo e Istruzioni
# ================================================================
# Testo visualizzato nell'expander delle istruzioni
INTRO_TEXT = """
Questo strumento legge un file Excel contenente domande (colonna A) e le relative risposte multiple (colonne B, C, D, ...) OPPURE domande aperte (senza risposte nelle colonne B, C, D...).

Genera un singolo file PDF contenente il numero desiderato di verifiche. Ogni verifica contiene un numero specifico di domande a scelta multipla e aperte, mescolate casualmente. Le risposte (se presenti) sono in ordine casuale. Ogni verifica inizia su una nuova pagina.

**Preparazione File Excel:**
 - Una domanda per riga.
 - **Colonna A:** Testo della domanda.
 - **Colonne B, C, D...:** Testo delle risposte (per domande a scelta multipla, almeno 2). Lasciare VUOTE per domande aperte.
 - Non inserire intestazioni di colonna nel file Excel.
 - *Vedi immagine di esempio qui sotto.*

**Utilizzo:**
 - Carica il tuo file Excel usando il riquadro nella sidebar.
 - Imposta i parametri desiderati (materia, n. verifiche, n. domande...).
 - Clicca su "Genera Verifiche PDF".
 - Se la generazione ha successo, apparirà un pulsante per scaricare il PDF.

---
**Opzione "Garantire test diversi":**

* Se attivi questa opzione, il programma controlla se hai abbastanza domande nel file Excel per variare i test uno dopo l'altro.
* **Requisito:** Per ciascun tipo (a scelta multipla / aperte), devi avere nel file **almeno il doppio** delle domande rispetto a quante ne usi in *ogni singola verifica*.
    * *Esempio Pratico:* Se chiedi 8 domande a scelta multipla per verifica, te ne servono almeno 16 totali nel file Excel (lo stesso vale per le aperte).
* **Motivo:** Serve una "riserva" di domande sufficiente per creare nuovi test senza ripetere subito le domande. L'app verifica questo all'inizio e si ferma con un errore se le domande non bastano.
---
"""

# ================================================================
# Funzione Caricamento Domande da Excel
# ================================================================
def load_questions_from_excel(uploaded_file):
    """Carica domande/risposte da file Excel (UploadedFile)."""
    if uploaded_file is None:
        return None

    try:
        st.info(f"Lettura file: {uploaded_file.name}...")
        df = pd.read_excel(uploaded_file, header=None)
        questions_data = []
        mc_count_temp = 0
        oe_count_temp = 0
        warnings = []

        for index, row in df.iterrows():
            row_list = [str(item) if pd.notna(item) else "" for item in row]
            question_text = row_list[0].strip()
            answers = [ans.strip() for ans in row_list[1:] if ans.strip()]

            if question_text:
                if len(answers) >= 2:
                    question_type = 'multiple_choice'
                    mc_count_temp += 1
                    questions_data.append({
                        'question': question_text,
                        'answers': answers,
                        'original_index': index,
                        'type': question_type
                    })
                else:
                    question_type = 'open_ended'
                    oe_count_temp += 1
                    questions_data.append({
                        'question': question_text,
                        'answers': [],
                        'original_index': index,
                        'type': question_type
                    })
                    if len(answers) == 1:
                        warnings.append(f"Attenzione: Domanda '{question_text[:50]}...' riga {index+1} ha solo 1 risposta, trattata come aperta.")
            elif any(answers):
                warnings.append(f"Attenzione: Riga {index+1} ha risposte ma manca la domanda e sarà ignorata.")

        for warning in warnings:
            st.warning(warning)

        if not questions_data:
            st.error(f"Errore: Nessuna domanda valida trovata nel file.")
            return None

        st.info(f"Caricate {len(questions_data)} domande ({mc_count_temp} MC, {oe_count_temp} aperte).")
        return questions_data

    except Exception as e:
        st.error(f"Errore imprevisto lettura Excel: {e}")
        return None

# ================================================================
# Funzione Generazione PDF
# ================================================================
def generate_pdf_data(tests_data_lists, timestamp, subject_name):
    """Genera i dati binari del PDF."""
    if not WEASYPRINT_AVAILABLE:
        st.error("ERRORE: Libreria WeasyPrint non trovata/funzionante.")
        return None

    st.info("Avvio generazione PDF...")
    css_style = """
       @page {
           size: A4;
           margin: 2cm;
           /* Aggiunto footer PDF */
           @bottom-center {
               content: "EvilProf v1.0"; /* Testo footer PDF */
               font-size: 9pt;
               color: #555;
               vertical-align: top;
               padding-top: 5pt;
            }
           @bottom-right {
               content: "Pagina " counter(page) " di " counter(pages); /* Numerazione pagine */
               font-size: 9pt;
               color: #555;
               vertical-align: top;
               padding-top: 5pt;
           }
       }
       body { font-family: Verdana, sans-serif; font-size: 11pt; line-height: 1.4; }
       .test-container { }
       .page-break { page-break-before: always; }
       h2 { margin-bottom: 0.8em; font-size: 1.6em; color: #000; font-weight: bold; }
       .pdf-header-info { margin-bottom: 2.5em; font-size: 1em; font-weight: normal; line-height: 1.6; }
       .header-line { display: flex; align-items: baseline; width: 100%; margin-bottom: 0.6em; }
       .header-label { white-space: nowrap; margin-right: 0.5em; flex-shrink: 0; }
       .header-underline { flex-grow: 1; border-bottom: 1px solid black; position: relative; top: -2px; min-width: 40px; }
       .class-label { margin-left: 2.5em; }
       .question { margin-top: 1.8em; margin-bottom: 0.8em; font-weight: bold; }
       .answer { display: flex; align-items: baseline; margin-left: 2.5em; margin-top: 0.1em; margin-bottom: 0.3em; padding-left: 0; text-indent: 0; }
       .checkbox { flex-shrink: 0; margin-right: 0.6em; }
       .answer-text { }
       .open-answer-space { min-height: 3em; margin-left: 1em; margin-top: 0.5em; margin-bottom: 1.5em; }
    """

    st.info("  Costruzione documento HTML...")
    html_parts = []
    checkbox_char = "☐"
    safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;')

    for index, single_test_data in enumerate(tests_data_lists):
        test_html = f"<h2>Verifica di {safe_subject_name}</h2>\n"
        # Intestazione Nome/Data/Classe con Flexbox/CSS
        test_html += '<div class="pdf-header-info">\n'
        test_html += ' <div class="header-line">\n <span class="header-label">Cognome e Nome:</span><span class="header-underline"></span>\n </div>\n'
        test_html += ' <div class="header-line">\n <span class="header-label">Data:</span><span class="header-underline date-line"></span><span class="header-label class-label">Classe:</span><span class="header-underline class-line"></span>\n </div>\n'
        test_html += '</div>\n'

        q_counter = 1
        for question_data in single_test_data:
            q_text = question_data['question'].strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
            q_type = question_data['type']
            nbsp = "&nbsp;"
            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'

            if q_type == 'multiple_choice':
                answers = question_data['answers'].copy()
                random.shuffle(answers)
                for answer in answers:
                    ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
                    test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'
            elif q_type == 'open_ended':
                test_html += '<div class="open-answer-space"></div>\n'
            q_counter += 1

        page_break_class = " page-break" if index > 0 else ""
        html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')

    final_html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Verifiche Generate</title><style>{css_style}</style></head><body>{''.join(html_parts)}</body></html>"""

    st.info("  Conversione HTML in PDF con WeasyPrint...")
    try:
        html_doc = HTML(string=final_html_content)
        pdf_bytes = html_doc.write_pdf()
        st.info("Conversione PDF completata.")
        return pdf_bytes
    except FileNotFoundError as e:
        st.error(f"ERRORE WeasyPrint: Dipendenze mancanti (GTK+?) {e}")
        return None
    except Exception as e:
        st.error(f"ERRORE WeasyPrint: {e}")
        return None

# ================================================================
# Interfaccia Utente Streamlit
# ================================================================

st.set_page_config(page_title="EvilProf 😈", layout="wide", initial_sidebar_state="expanded")
st.title("EvilProf 😈")
st.subheader("Generatore di Verifiche Casuali da Excel a PDF")

if not WEASYPRINT_AVAILABLE:
    st.error("🚨 **Attenzione:** WeasyPrint non disponibile/funzionante. Generazione PDF bloccata.")
    st.stop()

with st.expander("ℹ️ Istruzioni e Preparazione File Excel", expanded=False):
    st.markdown(INTRO_TEXT, unsafe_allow_html=True)
    image_path = "excel_example.jpg"
    try:
        st.image(image_path, caption="Esempio di struttura file Excel valida", use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Nota: Immagine '{image_path}' non trovata.")
    except Exception as e:
        st.error(f"Errore caricamento immagine '{image_path}': {e}")

st.sidebar.header("Parametri di Generazione")
uploaded_file = st.sidebar.file_uploader("1. File Excel (.xlsx, .xls)", type=['xlsx', 'xls'], help="Trascina o seleziona il file Excel.")
subject_name = st.sidebar.text_input("2. Nome della Materia", value="Informatica", help="Apparirà nel titolo delle verifiche.")
num_tests = st.sidebar.number_input("3. Numero di Verifiche", min_value=1, value=30, step=1, help="Quante versioni creare?")
num_mc_q = st.sidebar.number_input("4. N. Domande Scelta Multipla / Verifica", min_value=0, value=8, step=1)
num_open_q = st.sidebar.number_input("5. N. Domande Aperte / Verifica", min_value=0, value=2, step=1)
ensure_different = st.sidebar.checkbox("6. Garantire test adiacenti diversi?", value=True, help="Richiede più domande totali (vedi istruzioni).")
generate_button = st.sidebar.button("🚀 Genera Verifiche PDF", type="primary")

st.sidebar.markdown("---")
st.sidebar.subheader("Codice Sorgente")
try:
    # Determina il nome del file corrente per il download
    script_name = os.path.basename(__file__) if '__file__' in locals() else "evilprof_app.py"
    script_path = os.path.abspath(__file__)
    with open(script_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    st.sidebar.download_button(
        label="📥 Scarica Codice App (.py)",
        data=source_code,
        file_name=script_name, # Usa il nome del file corrente
        mime="text/x-python"
    )
except Exception as e:
    st.sidebar.warning(f"Impossibile leggere codice sorgente: {e}")

st.header("Output Generazione")
if generate_button:
    if uploaded_file is None:
        st.warning("⚠️ Carica prima un file Excel.")
    else:
        st.info(f"Richiesta per: {uploaded_file.name}")
        num_q_per_test = num_mc_q + num_open_q
        if num_q_per_test <= 0:
            st.error("ERRORE: N. domande totali per test deve essere > 0.")
        else:
            st.info(f"Parametri: {num_tests} verifiche, '{subject_name}', {num_mc_q} MC + {num_open_q} Aperte = {num_q_per_test} Domande/Test, Diversi: {'Sì' if ensure_different else 'No'}")
            st.info("---")

            with st.spinner("⏳ Caricamento e validazione domande..."):
                all_questions = load_questions_from_excel(uploaded_file)

            if all_questions:
                mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
                open_questions = [q for q in all_questions if q['type'] == 'open_ended']
                total_mc = len(mc_questions)
                total_open = len(open_questions)
                error_found = False

                # Controlli di fattibilità (separati su più righe)
                if total_mc == 0 and num_mc_q > 0:
                    st.error(f"ERRORE: {num_mc_q} MC richieste, 0 trovate.")
                    error_found = True
                if total_open == 0 and num_open_q > 0:
                    st.error(f"ERRORE: {num_open_q} Aperte richieste, 0 trovate.")
                    error_found = True
                if total_mc < num_mc_q:
                    st.error(f"ERRORE CRITICO: Non abbastanza MC ({total_mc}) per {num_mc_q} richieste.")
                    error_found = True
                if total_open < num_open_q:
                    st.error(f"ERRORE CRITICO: Non abbastanza Aperte ({total_open}) per {num_open_q} richieste.")
                    error_found = True

                if ensure_different and num_tests > 1 and not error_found:
                    min_mc_req = num_mc_q * 2 if num_mc_q > 0 else 0
                    min_open_req = num_open_q * 2 if num_open_q > 0 else 0
                    mc_ok = total_mc >= min_mc_req
                    open_ok = total_open >= min_open_req
                    if not (mc_ok and open_ok):
                        st.error("ERRORE CRITICO: Non abbastanza domande per 'Garantire test diversi':")
                        if not mc_ok and num_mc_q > 0:
                            st.error(f"  - MC: Servono {min_mc_req}, trovate {total_mc}")
                        if not open_ok and num_open_q > 0:
                            st.error(f"  - Aperte: Servono {min_open_req}, trovate {total_open}")
                        error_found = True

                if not error_found:
                    with st.spinner("⏳ Generazione dati verifiche..."):
                        mc_by_index = {q['original_index']: q for q in mc_questions}
                        open_by_index = {q['original_index']: q for q in open_questions}
                        all_mc_indices_set = set(mc_by_index.keys())
                        all_open_indices_set = set(open_by_index.keys())
                        all_tests_question_data = []
                        prev_mc_indices = set()
                        prev_prev_mc_indices = set()
                        prev_open_indices = set()
                        prev_prev_open_indices = set()
                        generation_logic_error = False

                        for i in range(1, num_tests + 1):
                            selected_mc_indices = set()
                            selected_open_indices = set()
                            current_test_data_unshuffled = []

                            # Selezione MC
                            if num_mc_q > 0:
                                if ensure_different and i > 1:
                                    avail_mc_set = (all_mc_indices_set - prev_mc_indices) | prev_prev_mc_indices
                                    if len(avail_mc_set) < num_mc_q:
                                        st.error(f"ERRORE LOGICO MC test {i}.")
                                        generation_logic_error = True; break
                                    selected_mc_indices = set(random.sample(list(avail_mc_set), num_mc_q))
                                    prev_prev_mc_indices = prev_mc_indices
                                    prev_mc_indices = selected_mc_indices
                                else:
                                    selected_mc_indices = set(random.sample(list(all_mc_indices_set), num_mc_q))
                                    if ensure_different:
                                        prev_prev_mc_indices = set()
                                        prev_mc_indices = selected_mc_indices
                                for idx in selected_mc_indices:
                                    current_test_data_unshuffled.append(mc_by_index[idx])

                            # Selezione Aperte
                            if num_open_q > 0:
                                if ensure_different and i > 1:
                                    avail_open_set = (all_open_indices_set - prev_open_indices) | prev_prev_open_indices
                                    if len(avail_open_set) < num_open_q:
                                        st.error(f"ERRORE LOGICO Aperte test {i}.")
                                        generation_logic_error = True; break
                                    selected_open_indices = set(random.sample(list(avail_open_set), num_open_q))
                                    prev_prev_open_indices = prev_open_indices
                                    prev_open_indices = selected_open_indices
                                else:
                                    selected_open_indices = set(random.sample(list(all_open_indices_set), num_open_q))
                                    if ensure_different:
                                        prev_prev_open_indices = set()
                                        prev_open_indices = selected_open_indices
                                for idx in selected_open_indices:
                                    current_test_data_unshuffled.append(open_by_index[idx])

                            if generation_logic_error:
                                break # Esce dal loop principale

                            random.shuffle(current_test_data_unshuffled)
                            all_tests_question_data.append(current_test_data_unshuffled)

                        if not generation_logic_error:
                            st.info(f"Dati per {len(all_tests_question_data)} verifiche preparati.")

                    # Generazione PDF
                    if not generation_logic_error:
                         with st.spinner("⏳ Conversione in PDF..."):
                             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                             safe_filename_subject = subject_name.replace(' ','_').replace('/','-').replace('\\','-')
                             pdf_filename = f"Verifiche_{safe_filename_subject}_{timestamp}.pdf"
                             pdf_data = generate_pdf_data(all_tests_question_data, timestamp, subject_name)

                         if pdf_data:
                             st.success("✅ Generazione PDF completata!")
                             st.download_button(
                                 label="📥 Scarica PDF Generato",
                                 data=pdf_data,
                                 file_name=pdf_filename,
                                 mime="application/pdf",
                                 help=f"Clicca per scaricare '{pdf_filename}'"
                             )
                         else:
                             st.error("❌ Errore durante la creazione del PDF.")
            else:
                st.error("❌ Impossibile procedere: errore caricamento/validazione domande.")

# --- Footer con Link GitHub ---
st.markdown("---")
st.markdown("EvilProf v1.0 - [GitHub](https://github.com/subnetdusk/evilprof) - Streamlit")
