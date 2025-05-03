# test.py (Updated with statistical similarity analysis and Excel output)
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
    """
    if not os.path.exists(TEST_EXCEL_FILE):
        status_callback("error", "TEST_FILE_NOT_FOUND", filename=TEST_EXCEL_FILE)
        return None, "TEST_FILE_NOT_FOUND"
    try:
        status_callback("info", "TEST_LOADING_DATA", filename=TEST_EXCEL_FILE)
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
        status_callback("info", "TEST_LOAD_SUCCESS", count=len(questions_data), mc=mc_count, oe=oe_count)
        return questions_data, None
    except Exception as e:
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
    Restituisce un dizionario {distance: avg_jaccard_index} o None in caso di fallimento.
    """
    jaccard_by_distance = {}
    max_distance_to_check = min(num_tests_to_generate - 1, 15)

    status_callback("info", "STAT_TEST_GENERATING_SEQUENCE", k_mc=k_mc, k_oe=k_oe, num_tests=num_tests_to_generate)
    generated_tests_data, gen_messages = generate_all_tests_data(
        mc_questions, open_questions, num_tests_to_generate, k_mc, k_oe, status_callback
    )

    if not generated_tests_data or len(generated_tests_data) != num_tests_to_generate:
        status_callback("error", "STAT_TEST_GENERATION_FAILED", k_mc=k_mc, k_oe=k_oe)
        # Aggiunge i messaggi di errore specifici della generazione fallita
        # Add specific error messages from the failed generation
        return None, gen_messages

    test_sets = [set(q['original_index'] for q in test) for test in generated_tests_data]
    status_callback("info", "STAT_TEST_CALCULATING_SIMILARITY", k_mc=k_mc, k_oe=k_oe, max_dist=max_distance_to_check)

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

    status_callback("info", "STAT_TEST_ANALYSIS_COMPLETE", k_mc=k_mc, k_oe=k_oe)
    # Ritorna sia i risultati medi che i messaggi generati durante la sequenza
    # Return both average results and messages generated during the sequence
    return avg_results_for_k, gen_messages

# ================================================================
# Funzione Orchestratore Test Statistico / Statistical Test Orchestrator Function
# ================================================================
def run_statistical_similarity_test(status_callback):
    """
    Orchestra l'analisi statistica di similarità per k (MC=OE) da 11 a 1.
    Salva i risultati dettagliati in un file Excel.
    Restituisce lista di tuple (type, key, kwargs_dict) con i risultati sommari
    e include un messaggio di successo/fallimento per l'Excel.

    Orchestrates the statistical similarity analysis for k (MC=OE) from 11 down to 1.
    Saves detailed results to an Excel file.
    Returns a list of tuples (type, key, kwargs_dict) with summary results,
    including a success/failure message for the Excel file.
    """
    statistical_results_summary = []
    detailed_results_list = [] # Lista per raccogliere dati per DataFrame / List to collect data for DataFrame

    # 1. Carica dati / Load data
    all_questions, error_key = _load_test_questions(status_callback)
    if error_key:
        statistical_results_summary.append(("error", "TEST_ABORTED_LOAD_FAILED", {}))
        return statistical_results_summary

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions); total_open = len(open_questions)
    expected_count = 24
    if total_mc != expected_count or total_open != expected_count:
         statistical_results_summary.append(("error", "TEST_WRONG_QUESTION_COUNT", {"mc": total_mc, "oe": total_open, "expected": expected_count}))
         return statistical_results_summary

    # 2. Definisci parametri / Define parameters
    num_tests_per_k = 30 # Numero di test consecutivi da generare per ogni k / Number of consecutive tests per k
    k_values_to_test = range(11, 0, -1) # Da 11 a 1 / From 11 down to 1

    statistical_results_summary.append(("info", "STAT_TEST_STARTING", {"num_k": len(k_values_to_test), "num_tests": num_tests_per_k}))

    # 3. Ciclo sui valori di k / Loop through k values
    analysis_successful = False # Flag per tracciare se almeno un'analisi è riuscita / Flag to track if at least one analysis succeeded
    for k in k_values_to_test:
        status_callback("info", "STAT_TEST_RUNNING_FOR_K", k=k)
        # Esegui l'analisi per questo k / Run analysis for this k
        avg_jaccard_by_distance, gen_messages_for_k = _run_similarity_analysis_for_k(
            k, k, num_tests_per_k, mc_questions, open_questions, status_callback
        )
        # Aggiunge eventuali messaggi dalla generazione della sequenza
        # Add any messages from sequence generation
        statistical_results_summary.extend(gen_messages_for_k)

        if avg_jaccard_by_distance is not None:
             analysis_successful = True # Almeno un k ha funzionato / At least one k worked
             result_str_parts = []
             # Aggiunge i dati dettagliati alla lista per l'Excel
             # Add detailed data to the list for Excel
             for d, avg_j in avg_jaccard_by_distance.items():
                 detailed_results_list.append({'k': k, 'distance': d, 'avg_jaccard': avg_j})
                 result_str_parts.append(f"d{d}={avg_j:.3f}" if avg_j is not None else f"d{d}=N/A")
             result_str = ", ".join(sorted(result_str_parts, key=lambda x: int(x.split('=')[0][1:]))) # Ordina per distanza / Sort by distance
             statistical_results_summary.append(("info", "STAT_TEST_RESULTS_FOR_K", {"k": k, "results": result_str}))
        else:
             statistical_results_summary.append(("error", "STAT_TEST_FAILED_FOR_K", {"k": k}))

    # 4. Crea e salva il file Excel se ci sono risultati / Create and save Excel if results exist
    excel_created = False
    if detailed_results_list:
        try:
            df_results = pd.DataFrame(detailed_results_list)
            # Pivota per avere k come righe, distanze come colonne / Pivot for k as rows, distances as columns
            df_pivot = df_results.pivot(index='k', columns='distance', values='avg_jaccard')
            # Ordina le righe per k decrescente / Sort rows by k descending
            df_pivot = df_pivot.sort_index(ascending=False)
            # Ordina le colonne per distanza crescente / Sort columns by distance ascending
            df_pivot = df_pivot.sort_index(axis=1, ascending=True)

            # Salva in Excel / Save to Excel
            df_pivot.to_excel(OUTPUT_EXCEL_FILE)
            statistical_results_summary.append(("success", "STAT_TEST_EXCEL_CREATED", {"filename": OUTPUT_EXCEL_FILE}))
            excel_created = True
        except Exception as e:
            statistical_results_summary.append(("error", "STAT_TEST_EXCEL_SAVE_ERROR", {"filename": OUTPUT_EXCEL_FILE, "error": str(e)}))
    elif analysis_successful: # C'erano analisi riuscite ma nessun dato raccolto? Improbabile. / Successful analyses but no data? Unlikely.
         statistical_results_summary.append(("warning", "STAT_TEST_NO_DATA_FOR_EXCEL", {}))
    # else: Nessuna analisi riuscita, non tenta di creare Excel / No successful analysis, don't try creating Excel

    # 5. Messaggio finale / Final message
    statistical_results_summary.append(("info" if analysis_successful else "warning", "STAT_TEST_ALL_COMPLETE", {}))

    # Ritorna i messaggi e il nome del file se creato / Return messages and filename if created
    return statistical_results_summary, OUTPUT_EXCEL_FILE if excel_created else None

# Funzione test scenari precedenti commentata / Previous test scenarios function commented out
# def run_all_tests(status_callback):
#    pass
