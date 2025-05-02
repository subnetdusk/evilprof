# -*- coding: utf-8 -*-

# ================================================================
# EvilProf 😈 - Generatore Verifiche da Excel - v1.1
# ================================================================
# Modifiche v1.1:
# - Sostituita logica "Garantire test diversi" con Campionamento Ponderato Ibrido (WRSwOR).
# - Rimossa opzione checkbox dalla UI.
# - Aggiornate istruzioni per descrivere il nuovo metodo.
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
- **Diversità Migliorata:** L'applicazione utilizza una tecnica di **Campionamento Casuale Ponderato** per selezionare le domande. Questo metodo:
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
    Args:
        population: Lista o set di elementi da cui campionare.
        weights: Lista di pesi corrispondenti agli elementi in population.
        k: Numero di elementi da campionare.
    Returns:
        Lista di k elementi campionati.
    Raises:
        ValueError: Se k è maggiore della dimensione della popolazione o se
                    population e weights hanno lunghezze diverse.
    """
    if k > len(population):
        raise ValueError("k non può essere maggiore della dimensione della popolazione")
    if len(population) != len(weights):
        raise ValueError("Population e weights devono avere la stessa lunghezza")
    if k == 0:
        return []
    if k == len(population):
        # Se chiediamo tutti gli elementi, non serve campionare
        # Restituiamo una copia mischiata per consistenza
        result = list(population)
        random.shuffle(result)
        return result

    # Filtra elementi con peso <= 0 se ce ne sono, potrebbero causare problemi
    valid_indices = [i for i, w in enumerate(weights) if w > 0]
    if not valid_indices:
         # Se non ci sono pesi positivi, non possiamo campionare
         # Potrebbe succedere se tutte le domande disponibili sono state appena usate
         # e la logica precedente le ha escluse. In questo caso, errore logico.
        raise ValueError("Nessun elemento con peso positivo disponibile per il campionamento.")

    filtered_population = [population[i] for i in valid_indices]
    filtered_weights = [weights[i] for i in valid_indices]

    if k > len(filtered_population):
         # Se dopo il filtraggio non ci sono abbastanza elementi, errore
         raise ValueError(f"Non ci sono abbastanza elementi con peso positivo ({len(filtered_population)}) per campionare k={k} elementi.")


    # Calcola le chiavi basate sui pesi e numeri casuali
    keys = []
    for w in filtered_weights:
        u = random.uniform(0, 1)
        # Aggiungi un piccolo epsilon per evitare log(0) o divisione per zero se w è piccolissimo
        # e per gestire il caso limite u=0 -> log(u) = -inf -> key = +inf
        epsilon = 1e-9
        if u < epsilon: u = epsilon
        # key = math.log(u) / w # Formula originale, sensibile a w piccoli
        # Formula alternativa più stabile (basata su u^(1/w)):
        try:
            # Aggiungere epsilon a w previene divisione per zero se w fosse 0 (improbabile dopo filtro)
            key = u**(1.0 / (w + epsilon))
        except OverflowError:
             # Se w è molto vicino a 0, 1/w può essere enorme, causando overflow in u^(1/w)
             # In questo caso, assegniamo una chiave molto piccola (bassa priorità)
             key = 0.0
        keys.append(key)


    # Abbina popolazione filtrata e chiavi, ordina per chiave decrescente
    # Usiamo l'indice originale per poter recuperare l'elemento corretto
    indexed_keys = list(zip(keys, range(len(filtered_population))))
    indexed_keys.sort(key=lambda x: x[0], reverse=True)

    # Prendi i primi k indici corrispondenti alle chiavi maggiori
    sampled_indices = [index for key, index in indexed_keys[:k]]

    # Restituisci gli elementi corrispondenti dalla popolazione filtrata
    return [filtered_population[i] for i in sampled_indices]


# ================================================================
# Funzione Caricamento Domande da Excel (Invariata)
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
        st.info(f"Caricate {len(questions_data)} domande ({mc_count_temp} MC, {oe_count_temp} aperte)."); return questions_data
    except Exception as e:
        st.error(f"Errore imprevisto lettura Excel: {e}"); return None

# ================================================================
# Funzione Generazione PDF (Invariata rispetto a v1.0.1)
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
# Interfaccia Utente Streamlit (AGGIORNATA)
# ================================================================

st.set_page_config(page_title="EvilProf 😈", layout="wide", initial_sidebar_state="expanded")
st.title("EvilProf 😈")
st.subheader("Generatore di verifiche casuali e diverse, da Excel a PDF")

# --- AGGIUNTO BANNER SVG ---
banner_path = "banner.svg" # Nome del file banner
try:
    # Legge il contenuto SVG come stringa e lo visualizza
    # Questo metodo è più robusto per SVG rispetto a st.image
    with open(banner_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    st.markdown(svg_content, unsafe_allow_html=True)
except FileNotFoundError:
    # Non mostrare un errore se il banner non c'è
    pass
except Exception as e:
    st.error(f"Errore caricamento banner '{banner_path}': {e}")
# --- FINE BANNER ---


if not WEASYPRINT_AVAILABLE:
    st.error("🚨 **Attenzione:** WeasyPrint non disponibile/funzionante. Generazione PDF bloccata.")
    st.stop()

# Istruzioni aggiornate
with st.expander("ℹ️ Istruzioni e Preparazione File Excel", expanded=False):
    st.markdown(INTRO_TEXT, unsafe_allow_html=True) # Usa INTRO_TEXT aggiornato
    image_path = "excel_example.jpg"
    try:
        st.image(image_path, caption="Esempio di struttura file Excel valida", use_container_width=True)
    except FileNotFoundError: st.warning(f"Nota: Immagine '{image_path}' non trovata.")
    except Exception as e: st.error(f"Errore caricamento immagine '{image_path}': {e}")

st.sidebar.header("Parametri di Generazione")
uploaded_file = st.sidebar.file_uploader("1. File Excel (.xlsx, .xls)", type=['xlsx', 'xls'], help="Trascina o seleziona il file Excel.")
subject_name = st.sidebar.text_input("2. Nome della Materia", value="Informatica", help="Apparirà nel titolo delle verifiche.")
num_tests = st.sidebar.number_input("3. Numero di Verifiche", min_value=1, value=30, step=1, help="Quante versioni creare?")
num_mc_q = st.sidebar.number_input("4. N. Domande Scelta Multipla / Verifica", min_value=0, value=8, step=1)
num_open_q = st.sidebar.number_input("5. N. Domande Aperte / Verifica", min_value=0, value=2, step=1)
# Rimossa checkbox "ensure_different"
generate_button = st.sidebar.button("🚀 Genera Verifiche PDF", type="primary")

st.sidebar.markdown("---")
st.sidebar.subheader("Codice Sorgente")
try:
    script_name = os.path.basename(__file__) if '__file__' in locals() else "evilprof_app.py"
    script_path = os.path.abspath(__file__)
    with open(script_path, 'r', encoding='utf-8') as f: source_code = f.read()
    st.sidebar.download_button(label="📥 Scarica Codice App (.py)", data=source_code, file_name=script_name, mime="text/x-python")
except Exception as e: st.sidebar.warning(f"Impossibile leggere codice sorgente: {e}")

st.subheader("Output Generazione") # Spostato header qui

# ================================================================
# Logica Principale di Generazione (AGGIORNATA)
# ================================================================
if generate_button:
    if uploaded_file is None:
        st.warning("⚠️ Carica prima un file Excel.")
    else:
        st.info(f"Richiesta per: {uploaded_file.name}")
        num_q_per_test = num_mc_q + num_open_q
        if num_q_per_test <= 0:
            st.error("ERRORE: N. domande totali per test deve essere > 0.")
        else:
            # Rimosso riferimento a "Diversi" dai parametri mostrati
            st.info(f"Parametri: {num_tests} verifiche, '{subject_name}', {num_mc_q} MC + {num_open_q} Aperte = {num_q_per_test} Domande/Test")
            st.info("---")

            with st.spinner("⏳ Caricamento e validazione domande..."):
                all_questions = load_questions_from_excel(uploaded_file)

            if all_questions:
                mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
                open_questions = [q for q in all_questions if q['type'] == 'open_ended']
                total_mc = len(mc_questions)
                total_open = len(open_questions)
                error_found = False

                # Controlli di fattibilità minimi (bastano domande per UN test)
                if total_mc == 0 and num_mc_q > 0: st.error(f"ERRORE: {num_mc_q} MC richieste, 0 trovate."); error_found = True
                if total_open == 0 and num_open_q > 0: st.error(f"ERRORE: {num_open_q} Aperte richieste, 0 trovate."); error_found = True
                if total_mc < num_mc_q: st.error(f"ERRORE CRITICO: Non abbastanza MC ({total_mc}) per {num_mc_q} richieste."); error_found = True
                if total_open < num_open_q: st.error(f"ERRORE CRITICO: Non abbastanza Aperte ({total_open}) per {num_open_q} richieste."); error_found = True

                # Controllo aggiuntivo: servono almeno k+1 domande se num_tests > 1 per garantire N != N-1
                if num_tests > 1:
                    if num_mc_q > 0 and total_mc <= num_mc_q:
                         st.error(f"ERRORE CRITICO: Per generare più test diversi dal precedente, servono più di {num_mc_q} domande MC totali (ne hai {total_mc}).")
                         error_found = True
                    if num_open_q > 0 and total_open <= num_open_q:
                         st.error(f"ERRORE CRITICO: Per generare più test diversi dal precedente, servono più di {num_open_q} domande aperte totali (ne hai {total_open}).")
                         error_found = True


                if not error_found:
                    with st.spinner("⏳ Generazione dati verifiche con campionamento ponderato..."):
                        # Dizionari per mappare indice originale a dati domanda
                        mc_by_index = {q['original_index']: q for q in mc_questions}
                        open_by_index = {q['original_index']: q for q in open_questions}

                        # Strutture per tracciare l'ultimo utilizzo di ogni domanda
                        # Inizializza a 0 (mai usate)
                        last_used_mc = {idx: 0 for idx in mc_by_index.keys()}
                        last_used_oe = {idx: 0 for idx in open_by_index.keys()}

                        all_tests_question_data = [] # Lista finale dei dati dei test
                        prev_mc_indices = set()      # Indici MC usati nel test N-1
                        prev_open_indices = set()    # Indici OE usati nel test N-1
                        generation_logic_error = False

                        # Loop per generare ciascun test
                        for i in range(1, num_tests + 1):
                            current_test_data_unshuffled = []
                            selected_mc_indices_current = set()
                            selected_open_indices_current = set()

                            # --- Selezione Domande a Scelta Multipla (Ponderata) ---
                            if num_mc_q > 0:
                                # Popolazione candidata: tutte le MC tranne quelle usate nel test precedente
                                candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
                                if len(candidate_mc_indices) < num_mc_q:
                                    st.error(f"ERRORE LOGICO MC test {i}: Non abbastanza domande MC disponibili ({len(candidate_mc_indices)}) escludendo il test precedente.")
                                    generation_logic_error = True; break

                                # Calcola i pesi per i candidati basati sull'età
                                weights_mc = []
                                for idx in candidate_mc_indices:
                                    age = i - last_used_mc[idx]
                                    weight = age + 1 # Formula peso lineare semplice
                                    weights_mc.append(weight)

                                # Esegui campionamento ponderato senza reinserimento
                                try:
                                    sampled_mc_indices = weighted_random_sample_without_replacement(
                                        candidate_mc_indices, weights_mc, num_mc_q
                                    )
                                except ValueError as e:
                                     st.error(f"Errore campionamento MC test {i}: {e}")
                                     generation_logic_error = True; break

                                selected_mc_indices_current = set(sampled_mc_indices)
                                # Aggiungi le domande selezionate e aggiorna last_used
                                for idx in selected_mc_indices_current:
                                    current_test_data_unshuffled.append(mc_by_index[idx])
                                    last_used_mc[idx] = i # Aggiorna l'ultimo utilizzo

                            # --- Selezione Domande Aperte (Ponderata - logica analoga) ---
                            if num_open_q > 0:
                                candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
                                if len(candidate_oe_indices) < num_open_q:
                                    st.error(f"ERRORE LOGICO Aperte test {i}: Non abbastanza domande Aperte disponibili ({len(candidate_oe_indices)}) escludendo il test precedente.")
                                    generation_logic_error = True; break

                                weights_oe = []
                                for idx in candidate_oe_indices:
                                    age = i - last_used_oe[idx]
                                    weight = age + 1
                                    weights_oe.append(weight)

                                try:
                                    sampled_oe_indices = weighted_random_sample_without_replacement(
                                        candidate_oe_indices, weights_oe, num_open_q
                                    )
                                except ValueError as e:
                                     st.error(f"Errore campionamento Aperte test {i}: {e}")
                                     generation_logic_error = True; break

                                selected_open_indices_current = set(sampled_oe_indices)
                                for idx in selected_open_indices_current:
                                    current_test_data_unshuffled.append(open_by_index[idx])
                                    last_used_oe[idx] = i

                            # Se errore logico, esci dal loop
                            if generation_logic_error: break

                            # Aggiorna i set delle domande precedenti per il prossimo ciclo
                            prev_mc_indices = selected_mc_indices_current
                            prev_open_indices = selected_open_indices_current

                            # Mescola le domande all'interno del test corrente
                            random.shuffle(current_test_data_unshuffled)
                            all_tests_question_data.append(current_test_data_unshuffled)
                        # --- Fine Loop Generazione Test ---

                        if not generation_logic_error:
                            st.info(f"Dati per {len(all_tests_question_data)} verifiche preparati.")

                    # --- Generazione PDF ---
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

# --- Footer ---
st.markdown("---")
st.markdown("EvilProf v1.1 - [GitHub](https://github.com/subnetdusk/evilprof) - Streamlit") 
