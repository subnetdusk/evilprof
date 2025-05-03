# test.py (Updated with Monte Carlo simulation, using run_all_tests name)
import pandas as pd
import random
import os
import math
from collections import defaultdict # Usato per accumulare risultati / Used for accumulating results

# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data

# Costante per il nome del file di test e output / Constants for test file and output
TEST_EXCEL_FILE = "test_questions.xlsx"
OUTPUT_EXCEL_FILE = "similarity_analysis_results_mc.xlsx" # Nome file output / Output filename

def _load_test_questions(status_callback):
    """
    Carica domande specificamente da TEST_EXCEL_FILE.
    Restituisce (lista_domande, None) o (None, chiave_errore).
    Chiama status_callback solo per errori critici o successo finale.
    """
    if not os.path.exists(TEST_EXCEL_FILE):
        status_callback("error", "TEST_FILE_NOT_FOUND", filename=TEST_EXCEL_FILE)
        return None, "TEST_FILE_NOT_FOUND"
    try:
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
             status_callback("error", "TEST_NO_QUESTIONS_FOUND", filename=TEST_EXCEL_FILE)
             return None, "TEST_NO_QUESTIONS_FOUND"
        # Messaggio successo caricamento (meno verboso)
        # status_callback("info", "TEST_LOAD_SUCCESS", count=len(questions_data), mc=mc_count, oe=oe_count)
        return questions_data, None
    except Exception as e:
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, "TEST_LOAD_ERROR"

def _calculate_jaccard(set1, set2):
    """Calcola l'indice Jaccard tra due insiemi."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return 1.0 if union == 0 else intersection / union

def _run_single_similarity_analysis_for_k(k_mc, k_oe, num_tests_to_generate, mc_questions, open_questions):
    """
    Esegue UNA SINGOLA analisi di similarità per k_mc e k_oe.
    Restituisce un dizionario {distance: avg_jaccard_index} e lista messaggi errore generazione.
    NON chiama status_callback.
    """
    jaccard_by_distance = {}
    max_distance_to_check = min(num_tests_to_generate - 1, 15) # Limita la distanza massima / Limit max distance
    generation_error_messages = []

    # Callback NOP per silenziare generate_all_tests_data / NOP callback to silence generate_all_tests_data
    def nop_callback(*args, **kwargs): pass

    generated_tests_data, gen_messages_internal = generate_all_tests_data(
        mc_questions, open_questions, num_tests_to_generate, k_mc, k_oe, nop_callback
    )
    # Salva solo errori critici dalla generazione / Save only critical errors from generation
    generation_error_messages = [msg for msg in gen_messages_internal if msg[0] == 'error']

    if not generated_tests_data or len(generated_tests_data) != num_tests_to_generate:
        if not any(m[1] == "STAT_TEST_GENERATION_FAILED" for m in generation_error_messages):
             generation_error_messages.append(("error", "STAT_TEST_GENERATION_FAILED", {"k_mc": k_mc, "k_oe": k_oe}))
        return None, generation_error_messages

    test_sets = [set(q['original_index'] for q in test) for test in generated_tests_data]

    for d in range(1, max_distance_to_check + 1):
        jaccard_indices_for_d = []
        for i in range(num_tests_to_generate - d):
            jaccard_index = _calculate_jaccard(test_sets[i], test_sets[i + d])
            jaccard_indices_for_d.append(jaccard_index)
        if jaccard_indices_for_d:
            jaccard_by_distance[d] = jaccard_indices_for_d # Salva la lista completa per ora / Save the full list for now

    # Calcola le medie DOPO aver raccolto tutte le liste
    # Calculate averages AFTER collecting all lists
    avg_results_for_k = {}
    for d, indices in jaccard_by_distance.items():
         if indices:
             avg = sum(indices) / len(indices)
             avg_results_for_k[d] = avg if not math.isnan(avg) else 0.0
         else:
             avg_results_for_k[d] = None

    return avg_results_for_k, generation_error_messages

# ================================================================
# Funzione Orchestratore Test Monte Carlo (rinominata run_all_tests)
# Monte Carlo Test Orchestrator Function (renamed run_all_tests)
# ================================================================
def run_all_tests(status_callback, num_monte_carlo_runs=30): # <<< NOME FUNZIONE CAMBIATO / FUNCTION NAME CHANGED
    """
    Orchestra l'analisi statistica di similarità con approccio Monte Carlo.
    Ripete l'analisi per k (MC=OE) da 11 a 1, per num_monte_carlo_runs volte.
    Salva i risultati medi finali in un file Excel.
    Restituisce lista di tuple (type, key, kwargs_dict) con i risultati sommari finali
    e include un messaggio di successo/fallimento per l'Excel.
    Chiama status_callback per messaggi sommari, critici e progresso Monte Carlo.
    """
    monte_carlo_summary = [] # Lista per messaggi sommari / List for summary messages
    results_accumulator = defaultdict(lambda: defaultdict(lambda: {'sum': 0.0, 'count': 0}))

    # 1. Carica dati (una sola volta) / Load data (only once)
    all_questions, error_key = _load_test_questions(status_callback)
    if error_key:
        monte_carlo_summary.append(("error", "TEST_ABORTED_LOAD_FAILED", {}))
        return monte_carlo_summary, None

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions); total_open = len(open_questions)
    expected_count = 24
    if total_mc != expected_count or total_open != expected_count:
         monte_carlo_summary.append(("error", "TEST_WRONG_QUESTION_COUNT", {"mc": total_mc, "oe": total_open, "expected": expected_count}))
         return monte_carlo_summary, None

    # 2. Definisci parametri / Define parameters
    num_tests_per_k_sequence = 30
    k_values_to_test = range(11, 0, -1)
    max_distance_overall = 0

    monte_carlo_summary.append(("info", "MC_TEST_STARTING", {"num_runs": num_monte_carlo_runs, "num_k": len(k_values_to_test), "num_tests": num_tests_per_k_sequence}))

    # 3. Ciclo Monte Carlo Esterno / Outer Monte Carlo Loop
    for run in range(1, num_monte_carlo_runs + 1):
        status_callback("info", "MC_TEST_RUN_PROGRESS", current_run=run, total_runs=num_monte_carlo_runs)
        run_successful = True

        # Ciclo sui valori di k interno / Inner loop over k values
        for k in k_values_to_test:
            avg_jaccard_by_distance, gen_errors = _run_single_similarity_analysis_for_k(
                k, k, num_tests_per_k_sequence, mc_questions, open_questions
            )
            monte_carlo_summary.extend(gen_errors)
            if avg_jaccard_by_distance is not None:
                for d, avg_j in avg_jaccard_by_distance.items():
                    if avg_j is not None:
                        results_accumulator[k][d]['sum'] += avg_j
                        results_accumulator[k][d]['count'] += 1
                        max_distance_overall = max(max_distance_overall, d)
            else:
                monte_carlo_summary.append(("warning", "MC_TEST_FAILED_FOR_K_IN_RUN", {"k": k, "run": run}))
                run_successful = False

    # 4. Calcola Medie Finali e Prepara Output / Calculate Final Averages and Prepare Output
    final_avg_results = defaultdict(dict)
    detailed_results_for_excel = []
    status_callback("info", "MC_TEST_CALCULATING_FINAL_AVERAGES", {})
    sorted_k = sorted(results_accumulator.keys(), reverse=True)
    for k in sorted_k:
        result_str_parts = []
        for d in range(1, max_distance_overall + 1):
            data = results_accumulator[k].get(d)
            final_avg = None
            num_samples = 0
            if data and data['count'] > 0:
                final_avg = data['sum'] / data['count']
                num_samples = data['count']
            final_avg_results[k][d] = final_avg
            detailed_results_for_excel.append({'k': k, 'distance': d, 'avg_jaccard': final_avg, 'num_samples': num_samples})
            result_str_parts.append(f"d{d}={final_avg:.3f}({num_samples})" if final_avg is not None else f"d{d}=N/A")
        result_str = ", ".join(result_str_parts)
        monte_carlo_summary.append(("info", "MC_TEST_FINAL_RESULTS_FOR_K", {"k": k, "results": result_str}))

    # 5. Crea e salva il file Excel / Create and save Excel file
    excel_created = False
    excel_filename = None
    if detailed_results_for_excel:
        try:
            df_results = pd.DataFrame(detailed_results_for_excel)
            df_pivot = pd.pivot_table(df_results, values='avg_jaccard', index='k', columns='distance')
            df_pivot = df_pivot.sort_index(ascending=False)
            df_pivot = df_pivot.sort_index(axis=1, ascending=True)
            df_pivot.to_excel(OUTPUT_EXCEL_FILE)
            monte_carlo_summary.append(("success", "STAT_TEST_EXCEL_CREATED", {"filename": OUTPUT_EXCEL_FILE}))
            excel_created = True
            excel_filename = OUTPUT_EXCEL_FILE
        except Exception as e:
            monte_carlo_summary.append(("error", "STAT_TEST_EXCEL_SAVE_ERROR", {"filename": OUTPUT_EXCEL_FILE, "error": str(e)}))
    elif any(results_accumulator.values()):
         monte_carlo_summary.append(("warning", "STAT_TEST_NO_DATA_FOR_EXCEL", {}))

    # 6. Messaggio finale completamento / Final completion message
    monte_carlo_summary.append(("info", "MC_TEST_ALL_COMPLETE", {}))

    return monte_carlo_summary, excel_filename
