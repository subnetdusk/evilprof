# -*- coding: utf-8 -*-

# ================================================================
# EvilProf 😈 - Generatore Verifiche da Excel - v1.1
# ================================================================

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io
import os
import math

# Import e controllo per WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# ================================================================
# Testo Introduttivo e Istruzioni
# ================================================================
INTRO_TEXT = """
EvilProf è un'applicazione web realizzata con Streamlit che permette di generare rapidamente file PDF contenenti verifiche personalizzate.

Le caratteristiche principali includono:

- **Input da Excel:** Carica facilmente le tue domande da un file `.xlsx` o `.xls`.
- **Tipi di Domande:** Supporta sia domande a scelta multipla (con risposte casualizzate) sia domande a risposta aperta.
- **Personalizzazione:** Scegli il numero di verifiche da generare, il numero di domande per tipo (multiple/aperte) per ciascuna verifica e il nome della materia.
- **Randomizzazione Avanzata:** Le domande in ogni verifica sono selezionate casualmente dal pool disponibile nel file Excel. L'ordine delle risposte multiple è casuale.
- **Diversità Migliorata (con Fallback):** L'applicazione tenta di utilizzare una tecnica di **Campionamento Casuale Ponderato Senza Reinserimento (WRSwOR)**  per selezionare le domande. Questo metodo:
    - Tenta di **garantire** che le domande usate in una verifica non vengano ripetute nella verifica *immediatamente successiva*. Ciò richiede che il numero totale di domande di un certo tipo (`n`) sia strettamente maggiore del doppio del numero di domande di quel tipo richieste per verifica (`k`), ovvero `n >= 2k`. 
    - Tenta di **favorire statisticamente** la selezione di domande che non vengono utilizzate da più tempo. Per una buona rotazione e diversità a lungo termine, è **fortemente consigliato** avere un numero totale di domande almeno **tre volte superiore** (`n >= 3k`) a quelle richieste per singola verifica. L'app mostrerà un avviso se `n < 3k`.
    - **Fallback:** Se non ci sono abbastanza domande uniche disponibili per garantire la diversità rispetto al test precedente (`n <= 2k`), l'applicazione **passerà a un campionamento casuale semplice** da *tutte* le domande disponibili per quel tipo, **perdendo la garanzia di diversità** tra test adiacenti. Verrà mostrato un avviso rosso prominente in tal caso.
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
# Funzione Helper WRSwOR
# ================================================================
def weighted_random_sample_without_replacement(population, weights, k):
    """
        Seleziona k elementi unici da una popolazione data, senza reinserimento,
        utilizzando un campionamento ponderato. La probabilità di selezione di ciascun
        elemento è influenzata dal peso corrispondente. Implementa l'algoritmo
        basato su chiavi esponenziali (variante di Efraimidis & Spirakis) per efficienza.
    
        Args:
            population: Lista o set di elementi da cui campionare.
            weights: Lista di pesi numerici corrispondenti agli elementi in population.
                     Pesi maggiori aumentano la probabilità di selezione.
            k: Numero di elementi unici da selezionare.
    
        Returns:
            Lista di k elementi campionati dalla popolazione.
    
        Raises:
            ValueError: Se k è maggiore della dimensione della popolazione, se le lunghezze
                        di population e weights non coincidono, o se non ci sono elementi
                        con peso positivo sufficienti per campionare k elementi.
    """
    if k > len(population): raise ValueError(f"k ({k}) > len(population) ({len(population)})")
    if len(population) != len(weights): raise ValueError("len(population) != len(weights)")
    if k == 0: return []
    if k == len(population): result = list(population); random.shuffle(result); return result
    valid_indices = [i for i, w in enumerate(weights) if w > 0]
    if not valid_indices: raise ValueError("Nessun elemento con peso positivo.")
    filtered_population = [population[i] for i in valid_indices]
    filtered_weights = [weights[i] for i in valid_indices]
    if k > len(filtered_population): raise ValueError(f"Non abbastanza elementi con peso positivo ({len(filtered_population)}) per campionare k={k}.")
    keys = []
    for w in filtered_weights:
        u = random.uniform(0, 1); epsilon = 1e-9
        if u < epsilon: u = epsilon
        try: key = u**(1.0 / (w + epsilon))
        except OverflowError: key = 0.0
        keys.append(key)
    indexed_keys = list(zip(keys, range(len(filtered_population)))); indexed_keys.sort(key=lambda x: x[0], reverse=True)
    sampled_indices = [index for key, index in indexed_keys[:k]]
    return [filtered_population[i] for i in sampled_indices]

# ================================================================
# Funzione Caricamento Domande da Excel 
# ================================================================
def load_questions_from_excel(uploaded_file, status_placeholder=None):
    """Carica domande/risposte da file Excel (UploadedFile). Usa status_placeholder."""
    if uploaded_file is None: return None
    def update_status(message):
        if status_placeholder: status_placeholder.info(message)
        else: st.info(message)
    try:
        if 'loaded_file_name' not in st.session_state or st.session_state.loaded_file_name != uploaded_file.name:
             update_status(f"⏳ Lettura file Excel: {uploaded_file.name}...")
             st.session_state.loaded_file_name = uploaded_file.name
             st.session_state.excel_df = pd.read_excel(uploaded_file, header=None)
        else: update_status(f"ℹ️ Utilizzo dati già caricati per: {uploaded_file.name}")
        df = st.session_state.excel_df
        questions_data = []; mc_count_temp = 0; oe_count_temp = 0; warnings = []
        for index, row in df.iterrows():
            row_list = [str(item) if pd.notna(item) else "" for item in row]; question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
            if question_text:
                if len(answers) >= 2: question_type = 'multiple_choice'; mc_count_temp += 1; questions_data.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': question_type})
                else: question_type = 'open_ended'; oe_count_temp += 1; questions_data.append({'question': question_text, 'answers': [], 'original_index': index, 'type': question_type})
                if len(answers) == 1: warnings.append(f"Attenzione: Domanda '{question_text[:50]}...' riga {index+1} ha solo 1 risposta, trattata come aperta.")
            elif any(answers): warnings.append(f"Attenzione: Riga {index+1} ha risposte ma manca la domanda e sarà ignorata.")
        for warning in warnings: st.warning(warning)
        if not questions_data: st.error(f"Errore: Nessuna domanda valida trovata nel file."); return None
        update_status(f"✅ Dati caricati: {len(questions_data)} domande ({mc_count_temp} a scelta multipla, {oe_count_temp} aperte). Validazione parametri...")
        return questions_data
    except Exception as e: st.error(f"Errore imprevisto lettura Excel: {e}"); return None

# ================================================================
# Funzione Generazione PDF 
# ================================================================
def generate_pdf_data(tests_data_lists, timestamp, subject_name, status_placeholder=None):
    """Genera i dati binari del PDF."""
    if not WEASYPRINT_AVAILABLE: st.error("ERROR: WeasyPrint library not found/functional."); return None
    def update_status(message):
        if status_placeholder: status_placeholder.info(message)
        else: st.info(message)
    update_status("⚙️ Starting PDF generation...")
    
    # CSS 
    css_style = """
         @page {
             size: A4;
             margin: 2cm;
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
         .question {
             margin-top: 1.8em;
             margin-bottom: 0.4em; /* Ridotto da 0.8em */
             font-weight: bold;
         }
         .answer { display: flex; align-items: baseline; margin-left: 2.5em; margin-top: 0.1em; margin-bottom: 0.3em; padding-left: 0; text-indent: 0; }
         .checkbox { flex-shrink: 0; margin-right: 0.6em; }
         .answer-text { }
         /* .open-answer-space { ... } Rimosso */
    """

    update_status("⚙️ Building HTML document...")
    html_parts = []; checkbox_char = "☐"; safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;')
    for index, single_test_data in enumerate(tests_data_lists):
        test_html = f"<h2>Test for {safe_subject_name}</h2>\n";
        test_html += '<div class="pdf-header-info">\n <div class="header-line">\n <span class="header-label">Name:</span><span class="header-underline"></span>\n </div>\n <div class="header-line">\n <span class="header-label">Date:</span><span class="header-underline date-line"></span><span class="header-label class-label">Class:</span><span class="header-underline class-line"></span>\n </div>\n</div>\n'
        q_counter = 1
        for question_data in single_test_data:
            q_text = question_data['question'].strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;'); q_type = question_data['type']; nbsp = "&nbsp;"
            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'
            if q_type == 'multiple_choice':
                answers = question_data['answers'].copy(); random.shuffle(answers)
                for answer in answers: ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;'); test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'
            elif q_type == 'open_ended':
                # Non aggiunge più il div vuoto
                pass # Non fa nulla, lascia solo la domanda
            q_counter += 1
        page_break_class = " page-break" if index > 0 else ""; html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')
    final_html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Generated Tests</title><style>{css_style}</style></head><body>{''.join(html_parts)}</body></html>"""
    update_status("⚙️ Converting HTML to PDF with WeasyPrint (this may take time)...")
    try: html_doc = HTML(string=final_html_content); pdf_bytes = html_doc.write_pdf(); update_status("⚙️ PDF conversion complete."); return pdf_bytes
    except FileNotFoundError as e: st.error(f"ERROR WeasyPrint: Missing dependencies (GTK+?) {e}"); return None
    except Exception as e: st.error(f"ERROR WeasyPrint: {e}"); return None

# ================================================================
# Interfaccia Utente Streamlit
# ================================================================

st.set_page_config(page_title="EvilProf 😈", layout="wide", initial_sidebar_state="expanded")
st.title("EvilProf 😈")
st.subheader("Generatore di verifiche casuali e diverse, da Excel a PDF")

if not WEASYPRINT_AVAILABLE:
    st.error("🚨 **Attenzione:** WeasyPrint non disponibile/funzionante. Generazione PDF bloccata.")
    st.stop()

with st.expander("ℹ️ Istruzioni e Preparazione File Excel", expanded=False):
    st.markdown(INTRO_TEXT, unsafe_allow_html=True) # Usa INTRO_TEXT aggiornato
    image_path = "excel_example.jpg"
    try: st.image(image_path, caption="Esempio di struttura file Excel valida", use_container_width=True)
    except FileNotFoundError: st.warning(f"Nota: Immagine '{image_path}' non trovata.")
    except Exception as e: st.error(f"Errore caricamento immagine '{image_path}': {e}")

st.sidebar.header("Parametri di Generazione")
uploaded_file = st.sidebar.file_uploader("1. File Excel (.xlsx, .xls)", type=['xlsx', 'xls'], help="Trascina o seleziona il file Excel.")
subject_name = st.sidebar.text_input("2. Nome della Materia", value="Informatica", help="Apparirà nel titolo delle verifiche.")
num_tests = st.sidebar.number_input("3. Numero di Verifiche", min_value=1, value=30, step=1, help="Quante versioni creare?")
num_mc_q = st.sidebar.number_input("4. N. Domande Scelta Multipla / Verifica", min_value=0, value=8, step=1)
num_open_q = st.sidebar.number_input("5. N. Domande Aperte / Verifica", min_value=0, value=2, step=1)
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
    script_name = "evilprof_app.py" # Default
    if '__file__' in locals() and os.path.exists(__file__):
         script_name = os.path.basename(__file__)
         script_path = os.path.abspath(__file__)
         with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    else:
         source_code = "# Impossibile leggere il codice sorgente automaticamente in questo ambiente."
         st.sidebar.warning("Download codice sorgente non disponibile in questo ambiente.")
    if '__file__' in locals() and os.path.exists(__file__):
        st.sidebar.download_button(label="📥 Scarica Codice App (.py)", data=source_code, file_name=script_name, mime="text/x-python")
except Exception as e: st.sidebar.warning(f"Impossibile leggere codice sorgente: {e}")
# --- Fine Sidebar ---

st.subheader("Output Generazione")

# --- Logica Test di Validazione ---
if validation_button:
    st.markdown("---")
    st.subheader("Risultato Test di Validazione")
    if uploaded_file is None: st.warning("⚠️ Carica un file Excel per eseguire il test.")
    else:
        test_status_placeholder = st.empty(); test_status_placeholder.info("Avvio test...")
        if 'excel_df' not in st.session_state:
             test_status_placeholder.warning("Dati Excel non caricati in sessione. Ricaricamento per test..."); temp_questions = load_questions_from_excel(uploaded_file, test_status_placeholder)
             if not temp_questions: st.error("Errore caricamento dati per test."); st.stop()
        else:
            test_status_placeholder.info("Utilizzo dati Excel dalla sessione corrente per il test.")
            df_test = st.session_state.excel_df; temp_questions = []; mc_test_count = 0; oe_test_count = 0
            for index, row in df_test.iterrows():
                row_list = [str(item) if pd.notna(item) else "" for item in row]; question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
                if question_text:
                    if len(answers) >= 2: temp_questions.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': 'multiple_choice'}); mc_test_count += 1
                    else: temp_questions.append({'question': question_text, 'answers': [], 'original_index': index, 'type': 'open_ended'}); oe_test_count += 1
        if temp_questions:
            with st.spinner("⏳ Esecuzione test..."):
                test_num_tests = 2; test_num_mc = 2; test_num_open = 1
                test_status_placeholder.write(f"Configurazione test: {test_num_tests} verifiche, {test_num_mc} a scelta multipla, {test_num_open} Aperte.")
                temp_mc = [q for q in temp_questions if q['type'] == 'multiple_choice']; temp_oe = [q for q in temp_questions if q['type'] == 'open_ended']
                temp_total_mc = len(temp_mc); temp_total_oe = len(temp_oe); test_error = False
                if temp_total_mc < test_num_mc: st.error(f"Non abbastanza domande a scelta multipla ({temp_total_mc}) per test ({test_num_mc})."); test_error = True
                if temp_total_oe < test_num_open: st.error(f"Non abbastanza Aperte ({temp_total_oe}) per test ({test_num_open})."); test_error = True
                if test_num_mc > 0 and temp_total_mc <= test_num_mc: st.error(f"Servono >{test_num_mc} domande a scelta multipla totali per testare la non-ripetizione."); test_error = True
                if test_num_open > 0 and temp_total_oe <= test_num_open: st.error(f"Servono >{test_num_open} Aperte totali per testare la non-ripetizione."); test_error = True
                if not test_error:
                    try:
                        mc_by_idx = {q['original_index']: q for q in temp_mc}; oe_by_idx = {q['original_index']: q for q in temp_oe}
                        last_used_mc_test = {idx: 0 for idx in mc_by_idx.keys()}; last_used_oe_test = {idx: 0 for idx in oe_by_idx.keys()}
                        test_results_data = []; prev_mc_idx_test = set(); prev_oe_idx_test = set(); test_passed_overall = True
                        for i_test in range(1, test_num_tests + 1):
                            test_status_placeholder.write(f"Generazione dati test {i_test}/{test_num_tests}...")
                            current_test_unshuffled = []; selected_mc_current = set(); selected_oe_current = set()
                            if test_num_mc > 0:
                                candidates = list(mc_by_idx.keys() - prev_mc_idx_test); weights = [i_test - last_used_mc_test[idx] + 1 for idx in candidates]
                                if len(candidates) < test_num_mc:
                                     st.warning(f"[Test] Fallback attivo per Scelta Multipla test {i_test}: campiono da tutti.")
                                     sampled_mc = random.sample(list(mc_by_idx.keys()), test_num_mc)
                                else: sampled_mc = weighted_random_sample_without_replacement(candidates, weights, test_num_mc)
                                selected_mc_current = set(sampled_mc)
                                for idx in selected_mc_current: current_test_unshuffled.append(mc_by_idx[idx]); last_used_mc_test[idx] = i_test
                            if test_num_open > 0:
                                candidates = list(oe_by_idx.keys() - prev_oe_idx_test); weights = [i_test - last_used_oe_test[idx] + 1 for idx in candidates]
                                if len(candidates) < test_num_open:
                                     st.warning(f"[Test] Fallback attivo per Aperte test {i_test}: campiono da tutti.")
                                     sampled_oe = random.sample(list(oe_by_idx.keys()), test_num_open)
                                else: sampled_oe = weighted_random_sample_without_replacement(candidates, weights, test_num_open)
                                selected_oe_current = set(sampled_oe)
                                for idx in selected_oe_current: current_test_unshuffled.append(oe_by_idx[idx]); last_used_oe_test[idx] = i_test
                            random.shuffle(current_test_unshuffled); test_results_data.append(current_test_unshuffled)
                            prev_mc_idx_test = selected_mc_current; prev_oe_idx_test = selected_oe_current
                        test_status_placeholder.write(f"Validazione {len(test_results_data)} test generati...")
                        if len(test_results_data) == test_num_tests:
                            for i_val, test_data in enumerate(test_results_data):
                                expected_total = test_num_mc + test_num_open
                                if len(test_data) != expected_total: st.error(f"❌ Validazione Fallita: Test {i_val+1} ha {len(test_data)} domande invece di {expected_total}."); test_passed_overall = False
                            q_set_test1 = set(q['original_index'] for q in test_results_data[0]); q_set_test2 = set(q['original_index'] for q in test_results_data[1])
                            intersection = q_set_test1.intersection(q_set_test2)
                            if not intersection: st.success("✅ Validazione Passata: Test 1 e Test 2 non hanno domande in comune.")
                            else: st.warning(f"⚠️ Validazione: Test 1 e Test 2 hanno domande in comune (indici: {intersection}). Atteso se fallback attivo.")
                        else: st.error("❌ Validazione Fallita: Numero di test generati non corretto."); test_passed_overall = False
                        if test_passed_overall: test_status_placeholder.success("🎉 Test di validazione completato!")
                        else: test_status_placeholder.error("⚠️ Test di validazione fallito o con avvisi. Controllare i messaggi.")
                    except ValueError as e_val: st.error(f"❌ Errore durante l'esecuzione del test di validazione (ValueError): {e_val}")
                    except Exception as e_val: st.error(f"❌ Errore imprevisto durante l'esecuzione del test di validazione: {e_val}")
                else: st.error("❌ Impossibile eseguire il test a causa di errori nei prerequisiti.")
        else: st.error("❌ Errore nel caricamento/elaborazione dati per il test.")
    #st.markdown("---")

# ================================================================
# Logica Principale di Generazione 
# ================================================================
if generate_button:
    status_placeholder = st.empty()
    if 'fallback_warning_shown' in st.session_state: del st.session_state['fallback_warning_shown']

    if uploaded_file is None: st.warning("⚠️ Carica prima un file Excel.")
    else:
        if 'excel_df' not in st.session_state or st.session_state.loaded_file_name != uploaded_file.name:
             with st.spinner("⏳ Caricamento dati Excel..."): all_questions = load_questions_from_excel(uploaded_file, status_placeholder)
        else:
             status_placeholder.info("ℹ️ Utilizzo dati Excel dalla sessione corrente.")
             df_main = st.session_state.excel_df; all_questions = []; mc_main_count = 0; oe_main_count = 0
             for index, row in df_main.iterrows():
                 row_list = [str(item) if pd.notna(item) else "" for item in row]; question_text = row_list[0].strip(); answers = [ans.strip() for ans in row_list[1:] if ans.strip()]
                 if question_text:
                     if len(answers) >= 2: all_questions.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': 'multiple_choice'}); mc_main_count += 1
                     else: all_questions.append({'question': question_text, 'answers': [], 'original_index': index, 'type': 'open_ended'}); oe_main_count += 1
             status_placeholder.info(f"✅ Dati pronti: {len(all_questions)} domande ({mc_main_count} a scelta multipla, {oe_main_count} aperte). Validazione parametri...")

        if not all_questions: st.error("❌ Errore nel caricamento/elaborazione dati. Impossibile generare.")
        else:
             num_q_per_test = num_mc_q + num_open_q
             if num_q_per_test <= 0: st.error("ERRORE: N. domande totali per test deve essere > 0.")
             else:
                 st.info(f"Parametri Generazione PDF: {num_tests} verifiche, '{subject_name}', {num_mc_q} a scelta multipla + {num_open_q} Aperte = {num_q_per_test} Domande/Test")

                 mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']; open_questions = [q for q in all_questions if q['type'] == 'open_ended']
                 total_mc = len(mc_questions); total_open = len(open_questions); error_found_main = False

                 # --- Controlli di Fattibilità e Warning ---
                 # Controlli Critici (bloccano la generazione)
                 if total_mc == 0 and num_mc_q > 0: st.error(f"ERRORE: {num_mc_q} domande a scelta multipla richieste, 0 trovate."); error_found_main = True
                 if total_open == 0 and num_open_q > 0: st.error(f"ERRORE: {num_open_q} Aperte richieste, 0 trovate."); error_found_main = True
                 if total_mc < num_mc_q: st.error(f"ERRORE CRITICO: Non abbastanza domande a scelta multipla ({total_mc}) per {num_mc_q} richieste."); error_found_main = True
                 if total_open < num_open_q: st.error(f"ERRORE CRITICO: Non abbastanza Aperte ({total_open}) per {num_open_q} richieste."); error_found_main = True

                 # Warning per bassa diversità potenziale (n < 3k) - Mostrato solo se non ci sono errori critici
                 # E verrà comunque nascosto se il fallback si attiva dopo
                 if not error_found_main:
                     show_mc_warning = num_mc_q > 0 and total_mc < 3 * num_mc_q
                     show_oe_warning = num_open_q > 0 and total_open < 3 * num_open_q

                     # Memorizza se mostrare i warning (verranno mostrati solo se il fallback non scatta)
                     st.session_state['show_mc_low_diversity_warning'] = show_mc_warning
                     st.session_state['show_oe_low_diversity_warning'] = show_oe_warning

                 # --- Fine Controlli ---

                 if not error_found_main:
                     with st.spinner("⏳ Generazione verifiche in corso..."):
                         status_placeholder.info("⚙️ Preparazione dati verifiche...")
                         mc_by_index = {q['original_index']: q for q in mc_questions}; open_by_index = {q['original_index']: q for q in open_questions}
                         last_used_mc = {idx: 0 for idx in mc_by_index.keys()}; last_used_oe = {idx: 0 for idx in open_by_index.keys()}
                         all_tests_question_data = []; prev_mc_indices = set(); prev_open_indices = set()

                         for i in range(1, num_tests + 1):
                             status_placeholder.info(f"⚙️ Generazione dati test {i}/{num_tests}...")
                             current_test_data_unshuffled = []; selected_mc_indices_current = set(); selected_open_indices_current = set()
                             fallback_active_mc = False; fallback_active_oe = False

                             # --- Selezione Scelta Multipla con Fallback ---
                             if num_mc_q > 0:
                                 candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
                                 if len(candidate_mc_indices) < num_mc_q:
                                     fallback_active_mc = True
                                     if 'fallback_warning_shown' not in st.session_state:
                                         st.error(f"‼️ ATTENZIONE: Domande insufficienti. Si procede con campionamento casuale semplice da TUTTE le domande disponibili. I test adiacenti potrebbero contenere ripetizioni.")
                                         st.session_state.fallback_warning_shown = True # Imposta il flag
                                     try: sampled_mc_indices = random.sample(list(mc_by_index.keys()), num_mc_q)
                                     except ValueError: st.error(f"Errore Imprevisto: Impossibile campionare {num_mc_q} da {total_mc} domande totali."); break
                                 else:
                                     weights_mc = [i - last_used_mc[idx] + 1 for idx in candidate_mc_indices]
                                     try: sampled_mc_indices = weighted_random_sample_without_replacement(candidate_mc_indices, weights_mc, num_mc_q)
                                     except ValueError as e: st.error(f"Errore campionamento ponderato Scelta Multipla test {i}: {e}"); break
                                 selected_mc_indices_current = set(sampled_mc_indices)
                                 for idx in selected_mc_indices_current: current_test_data_unshuffled.append(mc_by_index[idx]); last_used_mc[idx] = i

                             # --- Selezione Aperte con Fallback ---
                             if num_open_q > 0:
                                 candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
                                 if len(candidate_oe_indices) < num_open_q:
                                     fallback_active_oe = True
                                     if 'fallback_warning_shown' not in st.session_state:
                                         st.error(f"‼️ ATTENZIONE: Domande insufficienti. Si procede con campionamento casuale semplice da TUTTE le domande disponibili. I test adiacenti potrebbero contenere ripetizioni.")
                                         st.session_state.fallback_warning_shown = True
                                     try: sampled_oe_indices = random.sample(list(open_by_index.keys()), num_open_q)
                                     except ValueError: st.error(f"Errore Imprevisto: Impossibile campionare {num_open_q} da {total_open} domande totali."); break
                                 else:
                                     weights_oe = [i - last_used_oe[idx] + 1 for idx in candidate_oe_indices]
                                     try: sampled_oe_indices = weighted_random_sample_without_replacement(candidate_oe_indices, weights_oe, num_open_q)
                                     except ValueError as e: st.error(f"Errore campionamento ponderato Aperte test {i}: {e}"); break
                                 selected_open_indices_current = set(sampled_oe_indices)
                                 for idx in selected_open_indices_current: current_test_data_unshuffled.append(open_by_index[idx]); last_used_oe[idx] = i

                             prev_mc_indices = selected_mc_indices_current; prev_open_indices = selected_open_indices_current
                             random.shuffle(current_test_data_unshuffled); all_tests_question_data.append(current_test_data_unshuffled)
                         # --- Fine Loop Generazione Test ---

                         # --- Mostra Warning Giallo SOLO se il Fallback NON è scattato ---
                         if 'fallback_warning_shown' not in st.session_state:
                             if st.session_state.get('show_mc_low_diversity_warning', False):
                                 st.warning(f"⚠️ Attenzione: Il numero totale di domande a scelta multipla ({total_mc}) è inferiore al triplo ({3*num_mc_q}) delle richieste per test ({num_mc_q}). La diversità tra i test adiacenti potrebbe essere limitata.")
                             if st.session_state.get('show_oe_low_diversity_warning', False):
                                 st.warning(f"⚠️ Attenzione: Il numero totale di domande aperte ({total_open}) è inferiore al triplo ({3*num_open_q}) delle richieste per test ({num_open_q}). La diversità tra i test adiacenti potrebbe essere limitata.")

                         # Messaggio finale prima del PDF
                         if 'fallback_warning_shown' not in st.session_state:
                              status_placeholder.info(f"✅ Dati per {len(all_tests_question_data)} verifiche preparati (con diversità garantita). Avvio conversione PDF...")
                         else:
                              status_placeholder.warning(f"✅ Dati per {len(all_tests_question_data)} verifiche preparati (ATTENZIONE: diversità non garantita per tutti i test). Avvio conversione PDF...")

                     # --- Generazione PDF ---
                     with st.spinner("⏳ Conversione in PDF..."):
                         pdf_data = generate_pdf_data(all_tests_question_data, datetime.now().strftime("%Y%m%d_%H%M%S"), subject_name, status_placeholder)

                     if pdf_data:
                         status_placeholder.empty()
                         st.success("✅ Generazione PDF completata!")
                         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                         safe_filename_subject = subject_name.replace(' ','_').replace('/','-').replace('\\','-')
                         pdf_filename = f"Verifiche_{safe_filename_subject}_{timestamp}.pdf"
                         st.download_button(label="📥 Scarica PDF Generato", data=pdf_data, file_name=pdf_filename, mime="application/pdf", help=f"Clicca per scaricare '{pdf_filename}'")
                     else:
                         status_placeholder.empty()
                         st.error("❌ Errore durante la creazione del PDF.")

# --- Footer ---
st.markdown("---")
st.markdown("EvilProf v1.1 - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit")
