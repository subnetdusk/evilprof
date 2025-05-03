# test.py (Updated to use Sørensen–Dice coefficient)
import pandas as pd
import random
import os
import math
from collections import defaultdict

# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data

# Costante per il nome del file di test e output
# Constants for test file and output
TEST_EXCEL_FILE = "test_questions.xlsx"
# Aggiornato nome file output per riflettere l'uso di Dice
# Updated output filename to reflect Dice usage
OUTPUT_EXCEL_FILE = "similarity_analysis_dice_mc.xlsx"

def _load_test_questions(status_callback):
    """
    Carica domande specificamente da TEST_EXCEL_FILE.
    Restituisce (lista_domande, None) o (None, chiave_errore).
    Chiama status_callback solo per errori critici.
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
        return questions_data, None
    except Exception as e:
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, "TEST_LOAD_ERROR"

# --- MODIFICA: Calcola Dice invece di Jaccard ---
# --- CHANGE: Calculate Dice instead of Jaccard ---
def _calculate_dice(set1, set2):
    """
    Calcola il coefficiente di Sørensen–Dice tra due insiemi.
    Formula: 2 * |A ∩ B| / (|A| + |B|)

    Calculates the Sørensen–Dice coefficient between two sets.
    Formula: 2 * |A ∩ B| / (|A| + |B|)
    """
    intersection_cardinality = len(set1.intersection(set2))
    set1_cardinality = len(set1)
    set2_cardinality = len(set2)
    denominator = set1_cardinality + set2_cardinality

    # Se entrambi gli insiemi sono vuoti, il coefficiente è 1.
    # Se il denominatore è 0 (improbabile qui), ritorna 1 se anche intersezione è 0, altrimenti 0.
    # If both sets are empty, the coefficient is 1.
    # If the denominator is 0 (unlikely here), return 1 if intersection is also 0, else 0.
    if denominator == 0:
        return 1.0 if intersection_cardinality == 0 else 0.0

    return 2 * intersection_cardinality / denominator
# --- FINE MODIFICA ---

def _run_single_similarity_analysis_for_k(k_mc, k_oe, num_tests_to_generate, mc_questions, open_questions):
    """
    Esegue UNA SINGOLA analisi di similarità per k_mc e k_oe usando Dice.
    Restituisce un dizionario {distance: avg_dice_index} e lista messaggi errore generazione.
    NON chiama status_callback.

    Performs A SINGLE similarity analysis for k_mc and k_oe using Dice.
    Returns a dictionary {distance: avg_dice_index} and a list of generation error messages.
    Does NOT call status_callback.
    """
    # --- MODIFICA: Nome variabile / Variable name change ---
    dice_by_distance = {}
    # --- FINE MODIFICA ---
    max_distance_to_check = num_tests_to_generate - 1
    generation_error_messages = []
    def nop_callback(*args, **kwargs): pass

    generated_tests_data, gen_messages_internal = generate_all_tests_data(
        mc_questions, open_questions, num_tests_to_generate, k_mc, k_oe, nop_callback
    )
    generation_error_messages = [msg for msg in gen_messages_internal if msg[0] == 'error']

    if not generated_tests_data or len(generated_tests_data) != num_tests_to_generate:
        if not any(m[1] == "STAT_TEST_GENERATION_FAILED" for m in generation_error_messages):
             generation_error_messages.append(("error", "STAT_TEST_GENERATION_FAILED", {"k_mc": k_mc, "k_oe": k_oe}))
        return None, generation_error_messages

    test_sets = [set(q['original_index'] for q in test) for test in generated_tests_data]

    for d in range(1, max_distance_to_check + 1):
        # --- MODIFICA: Nome variabile / Variable name change ---
        dice_indices_for_d = []
        # --- FINE MODIFICA ---
        for i in range(num_tests_to_generate - d):
            # --- MODIFICA: Chiama _calculate_dice / Call _calculate_dice ---
            dice_index = _calculate_dice(test_sets[i], test_sets[i + d])
            dice_indices_for_d.append(dice_index)
            # --- FINE MODIFICA ---
        if dice_indices_for_d:
            # --- MODIFICA: Nome variabile / Variable name change ---
            dice_by_distance[d] = dice_indices_for_d
            # --- FINE MODIFICA ---

    # --- MODIFICA: Nome variabile / Variable name change ---
    avg_dice_results_for_k = {}
    for d, indices in dice_by_distance.items():
         if indices:
             avg = sum(indices) / len(indices)
             avg_dice_results_for_k[d] = avg if not math.isnan(avg) else 0.0
         else:
             avg_dice_results_for_k[d] = None
    return avg_dice_results_for_k, generation_error_messages
    # --- FINE MODIFICA ---


# ================================================================
# Funzione Orchestratore Test Monte Carlo (run_all_tests)
# ================================================================
def run_all_tests(status_callback, num_monte_carlo_runs=30):
    """
    Orchestra l'analisi statistica di similarità (Dice) con approccio Monte Carlo.
    Salva i risultati medi finali in un file Excel.
    Restituisce lista di tuple (type, key, kwargs_dict) con messaggi sommari finali
    e include un messaggio di successo/fallimento per l'Excel.
    Chiama status_callback per messaggi essenziali e aggiornamenti progresso meno frequenti.
    """
    monte_carlo_summary = []
    results_accumulator = defaultdict(lambda: defaultdict(lambda: {'sum': 0.0, 'count': 0}))

    # 1. Carica dati
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

    # 2. Definisci parametri
    num_tests_per_k_sequence = 30
    k_values_to_test = range(11, 0, -1)
    max_distance_overall = 0
    progress_update_frequency = 5

    monte_carlo_summary.append(("info", "MC_TEST_STARTING", {"num_runs": num_monte_carlo_runs, "num_k": len(k_values_to_test), "num_tests": num_tests_per_k_sequence}))

    # 3. Ciclo Monte Carlo Esterno
    for run in range(1, num_monte_carlo_runs + 1):
        if run % progress_update_frequency == 0 or run == num_monte_carlo_runs:
             status_callback("info", "MC_TEST_RUN_PROGRESS", current_run=run, total_runs=num_monte_carlo_runs)
        run_successful = True

        # Ciclo sui valori di k interno
        for k in k_values_to_test:
            # --- MODIFICA: Nome variabile / Variable name change ---
            avg_dice_by_distance, gen_errors = _run_single_similarity_analysis_for_k(
                k, k, num_tests_per_k_sequence, mc_questions, open_questions
            )
            # --- FINE MODIFICA ---
            monte_carlo_summary.extend(gen_errors)
            # --- MODIFICA: Nome variabile / Variable name change ---
            if avg_dice_by_distance is not None:
                for d, avg_d in avg_dice_by_distance.items(): # Usa avg_d per chiarezza / Use avg_d for clarity
                    if avg_d is not None:
                        results_accumulator[k][d]['sum'] += avg_d
                        results_accumulator[k][d]['count'] += 1
                        max_distance_overall = max(max_distance_overall, d)
            # --- FINE MODIFICA ---
            else:
                monte_carlo_summary.append(("warning", "MC_TEST_FAILED_FOR_K_IN_RUN", {"k": k, "run": run}))
                run_successful = False

    # 4. Calcola Medie Finali e Prepara Output
    final_avg_results = defaultdict(dict)
    detailed_results_for_excel = []
    sorted_k = sorted(results_accumulator.keys(), reverse=True)
    if not max_distance_overall and any(results_accumulator.values()): max_distance_overall = 1

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
            # --- MODIFICA: Nome colonna per Excel / Column name change for Excel ---
            detailed_results_for_excel.append({'k': k, 'distance': d, 'avg_dice': final_avg, 'num_samples': num_samples})
            result_str_parts.append(f"d{d}={final_avg:.3f}({num_samples})" if final_avg is not None else f"d{d}=N/A")
            # --- FINE MODIFICA ---
        result_str = ", ".join(result_str_parts)
        # --- MODIFICA: Chiave messaggio (opzionale ma consigliato) / Message key change (optional but recommended) ---
        monte_carlo_summary.append(("info", "MC_TEST_FINAL_RESULTS_DICE_FOR_K", {"k": k, "results": result_str}))
        # --- FINE MODIFICA ---


    # 5. Crea e salva il file Excel
    excel_created = False
    excel_filename = None
    if detailed_results_for_excel:
        try:
            df_results = pd.DataFrame(detailed_results_for_excel)
            # --- MODIFICA: Nome valore nel pivot / Value name in pivot ---
            df_pivot = pd.pivot_table(df_results, values='avg_dice', index='k', columns='distance')
            # --- FINE MODIFICA ---
            df_pivot = df_pivot.sort_index(ascending=False)
            df_pivot = df_pivot.reindex(sorted(df_pivot.columns), axis=1)
            df_pivot.to_excel(OUTPUT_EXCEL_FILE)
            monte_carlo_summary.append(("success", "STAT_TEST_EXCEL_CREATED", {"filename": OUTPUT_EXCEL_FILE}))
            excel_created = True
            excel_filename = OUTPUT_EXCEL_FILE
        except Exception as e:
            monte_carlo_summary.append(("error", "STAT_TEST_EXCEL_SAVE_ERROR", {"filename": OUTPUT_EXCEL_FILE, "error": str(e)}))
    elif any(results_accumulator.values()):
         monte_carlo_summary.append(("warning", "STAT_TEST_NO_DATA_FOR_EXCEL", {}))

    # 6. Messaggio finale completamento
    monte_carlo_summary.append(("info", "MC_TEST_ALL_COMPLETE", {}))

    return monte_carlo_summary, excel_filename
