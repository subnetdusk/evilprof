# test.py (Less verbose during execution)
import pandas as pd
import random
import os
import math

# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data

# Costante per il nome del file di test e output / Constants for test file and output
TEST_EXCEL_FILE = "test_questions.xlsx"
OUTPUT_EXCEL_FILE = "similarity_analysis_results.xlsx" # Nome file output / Output filename

def _load_test_questions(status_callback):
    """
    Carica domande specificamente da TEST_EXCEL_FILE.
    Restituisce (lista_domande, None) o (None, chiave_errore).
    Chiama status_callback solo per errori critici o successo finale.
    """
    if not os.path.exists(TEST_EXCEL_FILE):
        # Errore critico, chiama il callback
        status_callback("error", "TEST_FILE_NOT_FOUND", filename=TEST_EXCEL_FILE)
        return None, "TEST_FILE_NOT_FOUND"
    try:
        # Non chiamare callback per inizio caricamento / Do not call callback for loading start
        # status_callback("info", "TEST_LOADING_DATA", filename=TEST_EXCEL_FILE)
        df = pd.read_excel(TEST_EXCEL_FILE, header=None)
        questions_data = []
        mc_count = 0; oe_count = 0
        for index, row in df.iterrows():
            row_list = [str(item).strip() if pd.notna(item) else "" for item in row]
            question_text = row_list[0]
            answers = [ans for ans in row_list[1:] if ans]
            if question_text:
                q_type = 'multiple_choice' if len(answers) >= 2 else 'open_ended'
                if q_type == 'multiple_choice': mc_count += 1
                else: oe_count += 1
                questions_data.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': q_type})
        if not questions_data:
             # Errore critico / Critical error
             status_callback("error", "TEST_NO_QUESTIONS_FOUND", filename=TEST_EXCEL_FILE)
             return None, "TEST_NO_QUESTIONS_FOUND"
        # Chiama callback solo per successo finale caricamento / Call callback only for final loading success
        status_callback("info", "TEST_LOAD_SUCCESS", count=len(questions_data), mc=mc_count, oe=oe_count)
        return questions_data, None
    except Exception as e:
        # Errore critico / Critical error
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, "TEST_LOAD_ERROR"

def _calculate_jaccard(set1, set2):
    """Calcola l'indice Jaccard tra due insiemi."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return 1.0 if union == 0 else intersection / union

def _run_similarity_analysis_for_k(k_mc, k_oe, num_tests_to_generate, mc_questions, open_questions, status_callback):
    """
    Esegue l'analisi di similarità per un valore fisso di k_mc e k_oe.
    Restituisce un dizionario {distance: avg_jaccard_index} e lista messaggi (solo errori generazione).
    NON chiama status_callback per messaggi intermedi.
    """
    jaccard_by_distance = {}
    max_distance_to_check = min(num_tests_to_generate - 1, 15)
    generation_messages = [] # Lista per eventuali errori dalla generazione / List for potential errors from generation

    # NON chiamare callback per inizio generazione sequenza / DO NOT call callback for sequence generation start
    # status_callback("info", "STAT_TEST_GENERATING_SEQUENCE", k_mc=k_mc, k_oe=k_oe, num_tests=num_tests_to_generate)

    # Passa un callback NOP (che non fa nulla) a generate_all_tests_data per silenziare i suoi messaggi intermedi
    # Pass a NOP (no-operation) callback to generate_all_tests_data to silence its intermediate messages
    def nop_callback(*args, **kwargs):
        pass

    generated_tests_data, gen_messages_internal = generate_all_tests_data(
        mc_questions, open_questions, num_tests_to_generate, k_mc, k_oe, nop_callback # Usa NOP callback
    )
    # Salva solo i messaggi di errore critico restituiti da generate_all_tests_data
    # Save only critical error messages returned by generate_all_tests_data
    generation_messages = [msg for msg in gen_messages_internal if msg[0] == 'error']


    if not generated_tests_data or len(generated_tests_data) != num_tests_to_generate:
        # Segnala errore solo se non già presente nei messaggi di generazione
        # Signal error only if not already present in generation messages
        if not any(m[1] == "STAT_TEST_GENERATION_FAILED" for m in generation_messages):
             generation_messages.append(("error", "STAT_TEST_GENERATION_FAILED", {"k_mc": k_mc, "k_oe": k_oe}))
        return None, generation_messages # Indica fallimento e ritorna errori / Indicate failure and return errors

    test_sets = [set(q['original_index'] for q in test) for test in generated_tests_data]

    # NON chiamare callback per inizio calcolo similarità / DO NOT call callback for similarity calculation start
    # status_callback("info", "STAT_TEST_CALCULATING_SIMILARITY", k_mc=k_mc, k_oe=k_oe, max_dist=max_distance_to_check)

    for d in range(1, max_distance_to_check + 1):
        jaccard_indices_for_d = []
        for i in range(num_tests_to_generate - d):
            jaccard_index = _calculate_jaccard(test_sets[i], test_sets[i + d])
            jaccard_indices_for_d.append(jaccard_index)
        if jaccard_indices_for_d:
            jaccard_by_distance[d] = jaccard_indices_for_d

    avg_results_for_k = {}
    for d, indices in jaccard_by_distance.items():
         if indices:
             avg = sum(indices) / len(indices)
             avg_results_for_k[d] = avg if not math.isnan(avg) else 0.0
         else:
             avg_results_for_k[d] = None

    # NON chiamare callback per fine analisi / DO NOT call callback for analysis end
    # status_callback("info", "STAT_TEST_ANALYSIS_COMPLETE", k_mc=k_mc, k_oe=k_oe)
    # Ritorna risultati medi e solo messaggi di ERRORE dalla generazione
    # Return average results and only ERROR messages from generation
    return avg_results_for_k, generation_messages

# ================================================================
# Funzione Orchestratore Test Statistico / Statistical Test Orchestrator Function
# ================================================================
def run_statistical_similarity_test(status_callback):
    """
    Orchestra l'analisi statistica di similarità per k (MC=OE) da 11 a 1.
    Salva i risultati dettagliati in un file Excel.
    Restituisce lista di tuple (type, key, kwargs_dict) con i risultati sommari finali
    e include un messaggio di successo/fallimento per l'Excel.
    Chiama status_callback solo per messaggi sommari e critici.
    """
    statistical_results_summary = []
    detailed_results_list = []

    # 1. Carica dati (chiama callback solo per successo/errore)
    all_questions, error_key = _load_test_questions(status_callback)
    if error_key:
        statistical_results_summary.append(("error", "TEST_ABORTED_LOAD_FAILED", {}))
        return statistical_results_summary, None # Aggiunto None per nome file / Added None for filename

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions); total_open = len(open_questions)
    expected_count = 24
    if total_mc != expected_count or total_open != expected_count:
         statistical_results_summary.append(("error", "TEST_WRONG_QUESTION_COUNT", {"mc": total_mc, "oe": total_open, "expected": expected_count}))
         return statistical_results_summary, None

    # 2. Definisci parametri
    num_tests_per_k = 30
    k_values_to_test = range(11, 0, -1)

    # Messaggio iniziale test statistico / Initial statistical test message
    statistical_results_summary.append(("info", "STAT_TEST_STARTING", {"num_k": len(k_values_to_test), "num_tests": num_tests_per_k}))

    # 3. Ciclo sui valori di k
    analysis_successful = False
    for k in k_values_to_test:
        # NON chiamare callback per inizio analisi k / DO NOT call callback for start of k analysis
        # status_callback("info", "STAT_TEST_RUNNING_FOR_K", k=k)

        # Esegui l'analisi per questo k (passando il callback principale, ma _run... lo ignorerà per i msg intermedi)
        # Run analysis for this k (passing the main callback, but _run... will ignore it for intermediate msgs)
        avg_jaccard_by_distance, gen_errors_for_k = _run_similarity_analysis_for_k(
            k, k, num_tests_per_k, mc_questions, open_questions, status_callback
        )
        # Aggiunge eventuali messaggi di ERRORE dalla generazione
        # Add any ERROR messages from generation
        statistical_results_summary.extend(gen_errors_for_k)

        if avg_jaccard_by_distance is not None:
             analysis_successful = True
             result_str_parts = []
             for d, avg_j in avg_jaccard_by_distance.items():
                 detailed_results_list.append({'k': k, 'distance': d, 'avg_jaccard': avg_j})
                 result_str_parts.append(f"d{d}={avg_j:.3f}" if avg_j is not None else f"d{d}=N/A")
             result_str = ", ".join(sorted(result_str_parts, key=lambda x: int(x.split('=')[0][1:])))
             # Aggiunge il sommario per questo k ai messaggi finali (visibili all'utente)
             # Add summary for this k to final messages (visible to user)
             statistical_results_summary.append(("info", "STAT_TEST_RESULTS_FOR_K", {"k": k, "results": result_str}))
        else:
             # Aggiunge errore sommario per questo k / Add summary error for this k
             statistical_results_summary.append(("error", "STAT_TEST_FAILED_FOR_K", {"k": k}))

    # 4. Crea e salva il file Excel se ci sono risultati
    excel_created = False
    excel_filename = None
    if detailed_results_list:
        try:
            df_results = pd.DataFrame(detailed_results_list)
            df_pivot = df_results.pivot(index='k', columns='distance', values='avg_jaccard')
            df_pivot = df_pivot.sort_index(ascending=False)
            df_pivot = df_pivot.sort_index(axis=1, ascending=True)
            df_pivot.to_excel(OUTPUT_EXCEL_FILE)
            # Aggiunge messaggio successo creazione Excel / Add Excel creation success message
            statistical_results_summary.append(("success", "STAT_TEST_EXCEL_CREATED", {"filename": OUTPUT_EXCEL_FILE}))
            excel_created = True
            excel_filename = OUTPUT_EXCEL_FILE
        except Exception as e:
            # Aggiunge messaggio errore creazione Excel / Add Excel creation error message
            statistical_results_summary.append(("error", "STAT_TEST_EXCEL_SAVE_ERROR", {"filename": OUTPUT_EXCEL_FILE, "error": str(e)}))
    elif analysis_successful:
         statistical_results_summary.append(("warning", "STAT_TEST_NO_DATA_FOR_EXCEL", {}))

    # 5. Messaggio finale completamento test / Final test completion message
    statistical_results_summary.append(("info" if analysis_successful else "warning", "STAT_TEST_ALL_COMPLETE", {}))

    # Ritorna i messaggi sommari e il nome del file se creato / Return summary messages and filename if created
    return statistical_results_summary, excel_filename

# Funzione test scenari precedenti commentata / Previous test scenarios function commented out
# def run_all_tests(status_callback):
#    pass
