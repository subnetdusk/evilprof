# -*- coding: utf-8 -*-

# ================================================================
# EvilProf 😈 - Generatore Verifiche da Excel - v1.1
# ================================================================
# Modifiche v1.1:
# - Sostituita logica "Garantire test diversi" con Campionamento Ponderato Ibrido (WRSwOR).
# - Rimossa opzione checkbox dalla UI.
# - Aggiornate istruzioni per descrivere il nuovo metodo e aggiunto link a paper.
# - Aggiunto bottone per Test di Validazione funzionale.
# - Versione incrementata.
# ================================================================

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io
import os
import math # Necessario per l'algoritmo WRSwOR

# Import e controllo per WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# ================================================================
# Testo Introduttivo e Istruzioni (AGGIORNATO)
# ================================================================
INTRO_TEXT = """
EvilProf è un'applicazione web realizzata con Streamlit che permette di generare rapidamente file PDF contenenti verifiche personalizzate.

Le caratteristiche principali includono:

- **Input da Excel:** Carica facilmente le tue domande da un file `.xlsx` o `.xls`.
- **Tipi di Domande:** Supporta sia domande a scelta multipla (con risposte casualizzate) sia domande a risposta aperta.
- **Personalizzazione:** Scegli il numero di verifiche da generare, il numero di domande per tipo (multiple/aperte) per ciascuna verifica e il nome della materia.
- **Randomizzazione Avanzata:** Le domande in ogni verifica sono selezionate casualmente dal pool disponibile nel file Excel. L'ordine delle risposte multiple è casuale.
- **Diversità Migliorata:** L'applicazione utilizza una tecnica di **Campionamento Casuale Ponderato Senza Reinserimento (WRSwOR)** basata sull'algoritmo A di Efraimidis e Spirakis (descritto in [questo paper](https://www.wellesu.com/10.1016/j.ipl.2005.11.003)) per selezionare le domande. Questo metodo:
    - **Garantisce** che le domande usate in una verifica non vengano ripetute nella verifica *immediatamente successiva*.
    - **Favorisce statisticamente** la selezione di domande che non vengono utilizzate da più tempo, promuovendo una maggiore rotazione e diversità tra le verifiche nel lungo periodo, senza richiedere un numero eccessivo di domande nel file di partenza.
- **Output PDF:** Genera un singolo file PDF pronto per la stampa, con ogni verifica che inizia su una nuova pagina e un'intestazione per nome, data e classe.

**Struttura del File Excel**

Perché l'applicazione funzioni correttamente, il file Excel deve rispettare la seguente struttura **senza intestazioni di colonna**:

- **Colonna A:** Contiene il testo completo della domanda.
- **Colonne B, C, D, ...:** Contengono le diverse opzioni di risposta *solo* per le domande a scelta multipla. Devono esserci almeno due opzioni di risposta perché la domanda sia considerata a scelta multipla.
- **Domande Aperte:** Per una domanda aperta, lasciare semplicemente vuote le celle nelle colonne B, C, D, ...
- *Vedi immagine di esempio qui sotto.*

---
"""

# ================================================================
# Funzione Helper per Campionamento Ponderato Senza Reinserimento (WRSwOR)
# ================================================================
def weighted_random_sample_without_replacement(population, weights, k):
    """
    Seleziona k elementi unici da population senza reinserimento,
    rispettando i pesi forniti.
    Implementa l'algoritmo basato su chiavi esponenziali (Efraimsson & Ting).
    """
    if k > len(population):
        raise ValueError("k non può essere maggiore della dimensione della popolazione")
    if len(population) != len(weights):
        raise ValueError("Population e weights devono avere la stessa lunghezza")
    if k == 0:
        return []
    if k == len(population):
        result = list(population)
        random.shuffle(result)
        return result

    valid_indices = [i for i, w in enumerate(weights) if w > 0]
    if not valid_indices:
        raise ValueError("Nessun elemento con peso positivo disponibile per il campionamento.")

    filtered_population = [population[i] for i in valid_indices]
    filtered_weights = [weights[i] for i in valid_indices]

    if k > len(filtered_population):
         raise ValueError(f"Non ci sono abbastanza elementi con peso positivo ({len(filtered_population)}) per campionare k={k} elementi.")

    keys = []
    for w in filtered_weights:
        u = random.uniform(0, 1)
        epsilon = 1e-9
        if u < epsilon: u = epsilon
        try:
            key = u**(1.0 / (w + epsilon))
        except OverflowError:
             key = 0.0
        keys.append(key)

    indexed_keys = list(zip(keys, range(len(filtered_population))))
    indexed_keys.sort(key=lambda x: x[0], reverse=True)
    sampled_indices = [index for key, index in indexed_keys[:k]]
    return [filtered_population[i] for i in sampled_indices]


# ================================================================
# Funzione Caricamento Domande da Excel (Invariata)
# ================================================================
def load_questions_from_excel(uploaded_file):
    """Carica domande/risposte da file Excel (UploadedFile)."""
    if uploaded_file is None:
        return None
    try:
        # Usa st.session_state per memorizzare il nome file e facilitare il reload per il test
        if 'loaded_file_name' not in st.session_state or st.session_state.loaded_file_name != uploaded_file.name:
             st.info(f"Lettura file: {uploaded_file.name}...")
             st.session_state.loaded_file_name = uploaded_file.name # Memorizza nome
             # Legge i dati e li memorizza in session_state per evitare ricariche inutili
             st.session_state.excel_df = pd.read_excel(uploaded_file, header=None)
        else:
             # Se il nome file è lo stesso, usa il df già caricato
             st.info(f"Utilizzo dati già caricati per: {uploaded_file.name}")

        df = st.session_state.excel_df # Usa il DataFrame memorizzato
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
                    questions_data.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': question_type})
                else:
                    question_type = 'open_ended'
                    oe_count_temp += 1
                    questions_data.append({'question': question_text, 'answers': [], 'original_index': index, 'type': question_type})
                    if len(answers) == 1: warnings.append(f"Attenzione: Domanda '{question_text[:50]}...' riga {index+1} ha solo 1 risposta, trattata come aperta.")
            elif any(answers): warnings.append(f"Attenzione: Riga {index+1} ha risposte ma manca la domanda e sarà ignorata.")
        for warning in warnings: st.warning(warning)
        if not questions_data:
            st.error(f"Errore: Nessuna domanda valida trovata nel file."); return None
        # Non mostrare più il messaggio "Caricate..." qui, lo mostriamo dopo la validazione iniziale
        return questions_data
    except Exception as e:
        st.error(f"Errore imprevisto lettura Excel: {e}"); return None

# ================================================================
# Funzione Generazione PDF (Invariata rispetto a v1.1)
# ================================================================
def generate_pdf_data(tests_data_lists, timestamp, subject_name):
    """Genera i dati binari del PDF, senza footer."""
    if not WEASYPRINT_AVAILABLE:
        st.error("ERRORE: Libreria WeasyPrint non trovata/funzionante."); return None
    st.info("Avvio generazione PDF...")
    css_style = """@page { size: A4; margin: 2cm; } body { font-family: Verdana, sans-serif; font-size: 11pt; line-height: 1.4; } .test-container { } .page-break { page-break-before: always; } h2 { margin-bottom: 0.8em; font-size: 1.6em; color: #000; font-weight: bold; } .pdf-header-info { margin-bottom: 2.5em; font-size: 1em; font-weight: normal; line-height: 1.6; } .header-line { display: flex; align-items: baseline; width: 100%; margin-bottom: 0.6em; } .header-label { white-space: nowrap; margin-right: 0.5em; flex-shrink: 0; } .header-underline { flex-grow: 1; border-bottom: 1px solid black; position: relative; top: -2px; min-width: 40px; } .class-label { margin-left: 2.5em; } .question { margin-top: 1.8em; margin-bottom: 0.8em; font-weight: bold; } .answer { display: flex; align-items: baseline; margin-left: 2.5em; margin-top: 0.1em; margin-bottom: 0.3em; padding-left: 0; text-indent: 0; } .checkbox { flex-shrink: 0; margin-right: 0.6em; } .answer-text { } .open-answer-space { min-height: 3em; margin-left: 1em; margin-top: 0.5em; margin-bottom: 1.5em; }"""
    st.info("  Costruzione documento HTML...")
    html_parts = []; checkbox_char = "☐"; safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;')
    for index, single_test_data in enumerate(tests_data_lists):
        test_html = f"<h2>Verifica di {safe_subject_name}</h2>\n"
        test_html += '<div class="pdf-header-info">\n <div class="header-line">\n <span class="header-label">Cognome e Nome:</span><span class="header-underline"></span>\n </div>\n <div class="header-line">\n <span class="header-label">Data:</span><span class="header-underline date-line"></span><span class="header-label class-label">Classe:</span><span class="header-underline class-line"></span>\n </div>\n</div>\n'
        q_counter = 1
        for question_data in single_test_data:
            q_text = question_data['question'].strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
            q_type = question_data['type']; nbsp = "&nbsp;"
            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'
            if q_type == 'multiple_choice':
                answers = question_data['answers'].copy(); random.shuffle(answers)
                for answer in answers:
                    ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
                    test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'
            elif q_type == 'open_ended': test_html += '<div class="open-answer-space"></div>\n'
            q_counter += 1
        page_break_class = " page-break" if index > 0 else ""
        html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')
    final_html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Verifiche Generate</title><style>{css_style}</style></head><body>{''.join(html_parts)}</body></html>"""
    st.info("  Conversione HTML in PDF con WeasyPrint...")
    try:
        html_doc = HTML(string=final_html_content)
        pdf_bytes = html_doc.write_pdf(); st.info("Conversione PDF completata."); return pdf_bytes
    except FileNotFoundError as e: st.error(f"ERRORE WeasyPrint: Dipendenze mancanti (GTK+?) {e}"); return None
    except Exception as e: st.error(f"ERRORE WeasyPrint: {e}"); return None

# ================================================================
# Interfaccia Utente Streamlit
# ================================================================

st.set_page_config(page_title="EvilProf 😈", layout="wide", initial_sidebar_state="expanded")
st.title("EvilProf 😈")
st.subheader("Generatore di verifiche casuali e diverse, da Excel a PDF")

# --- Banner SVG ---
banner_path = "banner.svg"
try:
    with open(banner_path, "r", encoding="utf-8") as f: svg_content = f.read()
    st.markdown(svg_content, unsafe_allow_html=True)
except FileNotFoundError: pass # Non fare nulla se manca il banner
except Exception as e: st.error(f"Errore caricamento banner '{banner_path}': {e}")
# --- Fine Banner ---

if not WEASYPRINT_AVAILABLE:
    st.error("🚨 **Attenzione:** WeasyPrint non disponibile/funzionante. Generazione PDF bloccata.")
    st.stop()

# --- Istruzioni ---
with st.expander("ℹ️ Istruzioni e Preparazione File Excel", expanded=False):
    st.markdown(INTRO_TEXT, unsafe_allow_html=True) # Usa INTRO_TEXT aggiornato
    image_path = "excel_example.jpg"
    try:
        st.image(image_path, caption="Esempio di struttura file Excel valida", use_container_width=True)
    except FileNotFoundError: st.warning(f"Nota: Immagine '{image_path}' non trovata.")
    except Exception as e: st.error(f"Errore caricamento immagine '{image_path}': {e}")

# --- Sidebar ---
st.sidebar.header("Parametri di Generazione")
uploaded_file = st.sidebar.file_uploader("1. File Excel (.xlsx, .xls)", type=['xlsx', 'xls'], help="Trascina o seleziona il file Excel.")
subject_name = st.sidebar.text_input("2. Nome della Materia", value="Informatica", help="Apparirà nel titolo delle verifiche.")
num_tests = st.sidebar.number_input("3. Numero di Verifiche", min_value=1, value=30, step=1, help="Quante versioni creare?")
num_mc_q = st.sidebar.number_input("4. N. Domande Scelta Multipla / Verifica", min_value=0, value=8, step=1)
num_open_q = st.sidebar.number_input("5. N. Domande Aperte / Verifica", min_value=0, value=2, step=1)
# Rimossa checkbox "ensure_different"
generate_button = st.sidebar.button("🚀 Genera Verifiche PDF", type="primary")

# --- Test di Validazione ---
st.sidebar.markdown("---")
st.sidebar.subheader("Test Funzionale")
validation_button = st.sidebar.button(
    "🧪 Esegui Test di Validazione",
    help="Genera 2 test con poche domande per verificare la logica base (richiede file caricato)."
)

# --- Download Codice Sorgente ---
st.sidebar.markdown("---")
st.sidebar.subheader("Codice Sorgente")
try:
    script_name = os.path.basename(__file__) if '__file__' in locals() else "evilprof_app.py"
    script_path = os.path.abspath(__file__)
    with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    st.sidebar.download_button(label="📥 Scarica Codice App (.py)", data=source_code, file_name=script_name, mime="text/x-python")
except Exception as e: st.sidebar.warning(f"Impossibile leggere codice sorgente: {e}")
# --- Fine Sidebar ---

# --- Area Principale ---
st.subheader("Output Generazione") # Spostato qui per visibilità

# --- Logica Test di Validazione ---
if validation_button:
    st.markdown("---") # Separatore per l'output del test
    st.subheader("Risultato Test di Validazione")
    if uploaded_file is None:
        st.warning("⚠️ Carica un file Excel per eseguire il test.")
    else:
        # Ricarica i dati o usa quelli in sessione se disponibili
        # Questo assicura che il test usi i dati attuali senza rieseguire tutto
        if 'excel_df' not in st.session_state:
             st.warning("Dati Excel non ancora caricati nella sessione. Ricaricamento...")
             # Forza ricaricamento per il test (potrebbe essere lento)
             # Sarebbe meglio gestire lo stato in modo più robusto, ma per ora facciamo così
             temp_questions = load_questions_from_excel(uploaded_file)
             if not temp_questions:
                 st.error("Errore nel caricamento dati per il test.")
                 st.stop() # Ferma qui se il caricamento fallisce
        else:
            # Se df è in sessione, rielabora le domande da lì
            st.info("Utilizzo dati Excel dalla sessione corrente per il test.")
            # Questa parte è duplicata da load_questions_from_excel, idealmente andrebbe in una funzione separata
            df_test = st.session_state.excel_df
            temp_questions = []
            mc_test_count = 0; oe_test_count = 0
            for index, row in df_test.iterrows():
                row_list = [str(item) if pd.notna(item) else "" for item in row]
                question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
                if question_text:
                    if len(answers) >= 2: temp_questions.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': 'multiple_choice'}); mc_test_count += 1
                    else: temp_questions.append({'question': question_text, 'answers': [], 'original_index': index, 'type': 'open_ended'}); oe_test_count += 1
            st.info(f"Dati per test: {len(temp_questions)} domande ({mc_test_count} MC, {oe_test_count} aperte).")


        if temp_questions:
            with st.spinner("⏳ Esecuzione test..."):
                test_num_tests = 2
                test_num_mc = 2   # Parametri fissi per il test
                test_num_open = 1
                st.write(f"Configurazione test: {test_num_tests} verifiche, {test_num_mc} MC, {test_num_open} Aperte.")

                temp_mc = [q for q in temp_questions if q['type'] == 'multiple_choice']
                temp_oe = [q for q in temp_questions if q['type'] == 'open_ended']
                temp_total_mc = len(temp_mc)
                temp_total_oe = len(temp_oe)

                # Controlli preliminari per il test
                test_error = False
                if temp_total_mc < test_num_mc: st.error(f"Non abbastanza MC ({temp_total_mc}) per test ({test_num_mc})."); test_error = True
                if temp_total_oe < test_num_open: st.error(f"Non abbastanza Aperte ({temp_total_oe}) per test ({test_num_open})."); test_error = True
                # Controllo per la non-ripetizione (serve almeno k+1)
                if test_num_mc > 0 and temp_total_mc <= test_num_mc: st.error(f"Servono >{test_num_mc} MC totali per testare la non-ripetizione."); test_error = True
                if test_num_open > 0 and temp_total_oe <= test_num_open: st.error(f"Servono >{test_num_open} Aperte totali per testare la non-ripetizione."); test_error = True

                if not test_error:
                    try:
                        # Esegui logica generazione (simile a quella principale ma con parametri test)
                        mc_by_idx = {q['original_index']: q for q in temp_mc}
                        oe_by_idx = {q['original_index']: q for q in temp_oe}
                        last_used_mc_test = {idx: 0 for idx in mc_by_idx.keys()}
                        last_used_oe_test = {idx: 0 for idx in oe_by_idx.keys()}
                        test_results_data = []
                        prev_mc_idx_test = set()
                        prev_oe_idx_test = set()
                        test_passed_overall = True # Flag generale

                        for i_test in range(1, test_num_tests + 1):
                            current_test_unshuffled = []
                            selected_mc_current = set()
                            selected_oe_current = set()

                            # MC Selection
                            if test_num_mc > 0:
                                candidates = list(mc_by_idx.keys() - prev_mc_idx_test)
                                weights = [i_test - last_used_mc_test[idx] + 1 for idx in candidates]
                                sampled_mc = weighted_random_sample_without_replacement(candidates, weights, test_num_mc)
                                selected_mc_current = set(sampled_mc)
                                for idx in selected_mc_current:
                                    current_test_unshuffled.append(mc_by_idx[idx])
                                    last_used_mc_test[idx] = i_test

                            # OE Selection
                            if test_num_open > 0:
                                candidates = list(oe_by_idx.keys() - prev_oe_idx_test)
                                weights = [i_test - last_used_oe_test[idx] + 1 for idx in candidates]
                                sampled_oe = weighted_random_sample_without_replacement(candidates, weights, test_num_open)
                                selected_oe_current = set(sampled_oe)
                                for idx in selected_oe_current:
                                    current_test_unshuffled.append(oe_by_idx[idx])
                                    last_used_oe_test[idx] = i_test

                            random.shuffle(current_test_unshuffled)
                            test_results_data.append(current_test_unshuffled)
                            prev_mc_idx_test = selected_mc_current
                            prev_oe_idx_test = selected_oe_current

                        # Validazione Risultati Test
                        st.write(f"Generati {len(test_results_data)} test per la validazione.")
                        if len(test_results_data) == test_num_tests:
                            # Controllo numero domande per test
                            for i_val, test_data in enumerate(test_results_data):
                                expected_total = test_num_mc + test_num_open
                                if len(test_data) != expected_total:
                                    st.error(f"❌ Validazione Fallita: Test {i_val+1} ha {len(test_data)} domande invece di {expected_total}.")
                                    test_passed_overall = False
                                else:
                                     st.write(f"Test {i_val+1}: Numero domande corretto ({expected_total}).")

                            # Controllo non-ripetizione tra test 1 e 2
                            q_set_test1 = set(q['original_index'] for q in test_results_data[0])
                            q_set_test2 = set(q['original_index'] for q in test_results_data[1])
                            intersection = q_set_test1.intersection(q_set_test2)

                            if not intersection:
                                st.success("✅ Validazione Passata: Test 1 e Test 2 non hanno domande in comune.")
                            else:
                                st.error(f"❌ Validazione Fallita: Test 1 e Test 2 hanno domande in comune (indici: {intersection}).")
                                test_passed_overall = False

                        else:
                            st.error("❌ Validazione Fallita: Numero di test generati non corretto.")
                            test_passed_overall = False

                        if test_passed_overall:
                             st.success("🎉 Test di validazione completato con successo!")
                        else:
                             st.error("⚠️ Test di validazione fallito. Controllare i messaggi.")

                    except ValueError as e_val: # Cattura errori specifici dal campionamento
                        st.error(f"❌ Errore durante l'esecuzione del test di validazione (ValueError): {e_val}")
                    except Exception as e_val: # Cattura altri errori imprevisti
                        st.error(f"❌ Errore imprevisto durante l'esecuzione del test di validazione: {e_val}")
                else:
                     st.error("❌ Impossibile eseguire il test a causa di errori nei prerequisiti.")
        else:
             st.error("❌ Errore nel caricamento/elaborazione dati per il test.")
    st.markdown("---") # Separatore dopo l'output del test


# ================================================================
# Logica Principale di Generazione (PDF Effettivo)
# ================================================================
if generate_button:
    # Questo blocco ora viene eseguito solo per la generazione PDF principale
    if uploaded_file is None:
        # Questo warning ora dovrebbe apparire solo se si clicca "Genera" senza file
        st.warning("⚠️ Carica prima un file Excel.")
    else:
        # Assicurati che i dati siano caricati (potrebbero essere già in sessione)
        if 'excel_df' not in st.session_state or st.session_state.loaded_file_name != uploaded_file.name:
             # Se non sono in sessione o il file è cambiato, ricarica
             with st.spinner("⏳ Caricamento dati Excel..."):
                 all_questions = load_questions_from_excel(uploaded_file)
        else:
             # Altrimenti, rielabora da session_state (più veloce)
             st.info("Utilizzo dati Excel dalla sessione corrente.")
             df_main = st.session_state.excel_df
             all_questions = []
             mc_main_count = 0; oe_main_count = 0
             for index, row in df_main.iterrows():
                 row_list = [str(item) if pd.notna(item) else "" for item in row]
                 question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
                 if question_text:
                     if len(answers) >= 2: all_questions.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': 'multiple_choice'}); mc_main_count += 1
                     else: all_questions.append({'question': question_text, 'answers': [], 'original_index': index, 'type': 'open_ended'}); oe_main_count += 1
             st.info(f"Dati pronti: {len(all_questions)} domande ({mc_main_count} MC, {oe_main_count} aperte).")


        if not all_questions:
             st.error("❌ Errore nel caricamento/elaborazione dei dati. Impossibile generare.")
        else:
             num_q_per_test = num_mc_q + num_open_q
             if num_q_per_test <= 0:
                 st.error("ERRORE: N. domande totali per test deve essere > 0.")
             else:
                 st.info(f"Parametri Generazione PDF: {num_tests} verifiche, '{subject_name}', {num_mc_q} MC + {num_open_q} Aperte = {num_q_per_test} Domande/Test")
                 st.info("---")

                 # Esegui controlli di fattibilità per la generazione principale
                 mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
                 open_questions = [q for q in all_questions if q['type'] == 'open_ended']
                 total_mc = len(mc_questions)
                 total_open = len(open_questions)
                 error_found_main = False

                 if total_mc == 0 and num_mc_q > 0: st.error(f"ERRORE: {num_mc_q} MC richieste, 0 trovate."); error_found_main = True
                 if total_open == 0 and num_open_q > 0: st.error(f"ERRORE: {num_open_q} Aperte richieste, 0 trovate."); error_found_main = True
                 if total_mc < num_mc_q: st.error(f"ERRORE CRITICO: Non abbastanza MC ({total_mc}) per {num_mc_q} richieste."); error_found_main = True
                 if total_open < num_open_q: st.error(f"ERRORE CRITICO: Non abbastanza Aperte ({total_open}) per {num_open_q} richieste."); error_found_main = True
                 if num_tests > 1:
                     if num_mc_q > 0 and total_mc <= num_mc_q: st.error(f"ERRORE CRITICO: Servono >{num_mc_q} MC totali per generare test diversi (ne hai {total_mc})."); error_found_main = True
                     if num_open_q > 0 and total_open <= num_open_q: st.error(f"ERRORE CRITICO: Servono >{num_open_q} Aperte totali per generare test diversi (ne hai {total_open})."); error_found_main = True

                 if not error_found_main:
                     # --- Logica di Generazione Principale (Identica a prima, ma usa i dati caricati/validati) ---
                     with st.spinner("⏳ Generazione dati verifiche con campionamento ponderato..."):
                         mc_by_index = {q['original_index']: q for q in mc_questions}
                         open_by_index = {q['original_index']: q for q in open_questions}
                         last_used_mc = {idx: 0 for idx in mc_by_index.keys()}
                         last_used_oe = {idx: 0 for idx in open_by_index.keys()}
                         all_tests_question_data = []
                         prev_mc_indices = set()
                         prev_open_indices = set()
                         generation_logic_error_main = False

                         for i in range(1, num_tests + 1):
                             current_test_data_unshuffled = []
                             selected_mc_indices_current = set()
                             selected_open_indices_current = set()

                             if num_mc_q > 0:
                                 candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
                                 if len(candidate_mc_indices) < num_mc_q: st.error(f"ERRORE LOGICO MC test {i}."); generation_logic_error_main = True; break
                                 weights_mc = [i - last_used_mc[idx] + 1 for idx in candidate_mc_indices]
                                 try: sampled_mc_indices = weighted_random_sample_without_replacement(candidate_mc_indices, weights_mc, num_mc_q)
                                 except ValueError as e: st.error(f"Errore campionamento MC test {i}: {e}"); generation_logic_error_main = True; break
                                 selected_mc_indices_current = set(sampled_mc_indices)
                                 for idx in selected_mc_indices_current: current_test_data_unshuffled.append(mc_by_index[idx]); last_used_mc[idx] = i

                             if num_open_q > 0:
                                 candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
                                 if len(candidate_oe_indices) < num_open_q: st.error(f"ERRORE LOGICO Aperte test {i}."); generation_logic_error_main = True; break
                                 weights_oe = [i - last_used_oe[idx] + 1 for idx in candidate_oe_indices]
                                 try: sampled_oe_indices = weighted_random_sample_without_replacement(candidate_oe_indices, weights_oe, num_open_q)
                                 except ValueError as e: st.error(f"Errore campionamento Aperte test {i}: {e}"); generation_logic_error_main = True; break
                                 selected_open_indices_current = set(sampled_oe_indices)
                                 for idx in selected_open_indices_current: current_test_data_unshuffled.append(open_by_index[idx]); last_used_oe[idx] = i

                             if generation_logic_error_main: break
                             prev_mc_indices = selected_mc_indices_current
                             prev_open_indices = selected_open_indices_current
                             random.shuffle(current_test_data_unshuffled)
                             all_tests_question_data.append(current_test_data_unshuffled)

                         if not generation_logic_error_main: st.info(f"Dati per {len(all_tests_question_data)} verifiche preparati.")

                     # --- Generazione PDF ---
                     if not generation_logic_error_main:
                          with st.spinner("⏳ Conversione in PDF..."):
                              timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                              safe_filename_subject = subject_name.replace(' ','_').replace('/','-').replace('\\','-')
                              pdf_filename = f"Verifiche_{safe_filename_subject}_{timestamp}.pdf"
                              pdf_data = generate_pdf_data(all_tests_question_data, timestamp, subject_name)
                          if pdf_data:
                              st.success("✅ Generazione PDF completata!")
                              st.download_button(label="📥 Scarica PDF Generato", data=pdf_data, file_name=pdf_filename, mime="application/pdf", help=f"Clicca per scaricare '{pdf_filename}'")
                          else: st.error("❌ Errore durante la creazione del PDF.")

# --- Footer ---
st.markdown("---")
st.markdown("EvilProf v1.1 - [GitHub](https://github.com/subnetdusk/evilprof) - Streamlit") # Versione aggiornata
# --- Fine Applicazione ---
