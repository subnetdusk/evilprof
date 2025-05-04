# test.py (Dual analysis: WRSwOR vs Simple Random & Improved Excel Output)
import pandas as pd
import random
import os
import math
from collections import defaultdict

# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data, weighted_random_sample_without_replacement # Importa anche WRSwOR se serve

# Costante per il nome del file di test e output / Constants for test file and output
TEST_EXCEL_FILE = "test_set_4_by_12_questions.xlsx"
OUTPUT_EXCEL_FILE = "similarity_analysis_comparison_dice_mc_15t.xlsx" # Nome file output aggiornato / Updated output filename

def _load_test_questions(status_callback):
    """
    Carica domande da TEST_EXCEL_FILE, rileva blocchi e tipi.
    Restituisce (all_questions, blocks_summary, None) o (None, None, chiave_errore).
    Chiama status_callback solo per errori critici.
    """
    if not os.path.exists(TEST_EXCEL_FILE):
        status_callback("error", "TEST_FILE_NOT_FOUND", filename=TEST_EXCEL_FILE)
        return None, None, "TEST_FILE_NOT_FOUND"
    try:
        _, file_extension = os.path.splitext(TEST_EXCEL_FILE)
        if file_extension.lower() not in ['.xlsx', '.xls']:
             status_callback("error", "FH_UNSUPPORTED_FORMAT", filename=TEST_EXCEL_FILE, extension=file_extension)
             return None, None, "FH_UNSUPPORTED_FORMAT"

        df = pd.read_excel(TEST_EXCEL_FILE, header=None)
        df = df.fillna('').astype(str)

        all_questions = []
        blocks_summary = []
        current_block_id = 1
        current_block_questions = []
        current_block_type = None
        first_question_in_block = True

        df.loc[len(df)] = [""] * df.shape[1]

        for index, row in df.iterrows():
            is_empty_row = all(s is None or str(s).strip() == "" for s in row)

            if is_empty_row:
                if current_block_questions:
                    if current_block_type is None: current_block_type = 'Indeterminato'
                    blocks_summary.append({
                        'block_id': current_block_id,
                        'type': current_block_type,
                        'count': len(current_block_questions)
                    })
                    all_questions.extend(current_block_questions)
                current_block_id += 1
                current_block_questions = []
                current_block_type = None
                first_question_in_block = True
            else:
                row_list = [str(s).strip() for s in row]
                question_text = row_list[0]
                answers = [ans for ans in row_list[1:] if ans]

                if question_text:
                    question_type = 'Scelta Multipla' if len(answers) >= 2 else 'Aperte'
                    if first_question_in_block:
                        current_block_type = question_type
                        first_question_in_block = False
                    elif question_type != current_block_type:
                        status_callback("warning", "FH_BLOCK_MIXED_TYPES", block_id=current_block_id, expected=current_block_type, found=question_type, row_num=index + 1)
                        continue # Ignora domande di tipo misto nel blocco

                    question_dict = {
                        'question': question_text,
                        'answers': answers if current_block_type == 'Scelta Multipla' else [],
                        'original_index': index,
                        'type': current_block_type,
                        'block_id': current_block_id
                    }
                    current_block_questions.append(question_dict)

        blocks_summary = [b for b in blocks_summary if b['count'] > 0]

        if not all_questions:
            status_callback("error", "FH_NO_VALID_QUESTIONS", filename=TEST_EXCEL_FILE)
            return None, None, "FH_NO_VALID_QUESTIONS"

        return all_questions, blocks_summary, None

    except Exception as e:
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, None, "TEST_LOAD_ERROR"

def _calculate_dice(set1, set2):
    """Calcola il coefficiente di Sørensen–Dice tra due insiemi."""
    intersection_cardinality = len(set1.intersection(set2))
    denominator = len(set1) + len(set2)
    if denominator == 0: return 1.0
    return 2 * intersection_cardinality / denominator

def _generate_test_sequence_wrswor(all_questions_list, block_requests, num_tests_to_generate):
    """
    Genera una sequenza di test usando WRSwOR per blocco.
    Restituisce (lista_test_generati, lista_messaggi_errore).
    NON chiama status_callback.
    """
    def nop_callback(*args, **kwargs): pass
    # Chiama la funzione da core_logic
    generated_tests, gen_messages_internal = generate_all_tests_data(
        all_questions_list, block_requests, num_tests_to_generate, nop_callback
    )
    error_messages = [msg for msg in gen_messages_internal if msg[0] == 'error']
    if not generated_tests or len(generated_tests) != num_tests_to_generate:
         if not any(m[1] == "STAT_TEST_GENERATION_FAILED_KPB" for m in error_messages):
             k_per_block = list(block_requests.values())[0] if block_requests else 'N/A'
             error_messages.append(("error", "STAT_TEST_GENERATION_FAILED_KPB", {"k_per_block": k_per_block}))
         return None, error_messages
    return generated_tests, error_messages

def _generate_test_sequence_simple_random(all_questions_list, block_requests, num_tests_to_generate):
    """
    Genera una sequenza di test usando Simple Random Sampling per blocco.
    Restituisce (lista_test_generati, lista_messaggi_errore).
    NON chiama status_callback.
    """
    all_tests_question_data = []
    error_messages = []

    # Raggruppa domande per blocco / Group questions by block
    questions_by_block = defaultdict(list)
    for q in all_questions_list:
        questions_by_block[q['block_id']].append(q)

    for i_test in range(1, num_tests_to_generate + 1):
        current_test_questions = []
        for block_id, k_requested in block_requests.items():
            if k_requested <= 0: continue

            block_questions = questions_by_block.get(block_id)
            if not block_questions:
                error_messages.append(("error", "BLOCK_NOT_FOUND_OR_EMPTY", {"block_id": block_id}))
                continue
            if k_requested > len(block_questions):
                error_messages.append(("error", "BLOCK_REQUEST_EXCEEDS_AVAILABLE", {"block_id": block_id, "k": k_requested, "n": len(block_questions)}))
                continue

            try:
                # Campionamento casuale semplice / Simple random sampling
                selected_questions = random.sample(block_questions, k_requested)
                current_test_questions.extend(selected_questions)
            except ValueError: # k > n (non dovrebbe succedere con i controlli sopra)
                error_messages.append(("error", "BLOCK_CRITICAL_SAMPLING_ERROR", {"block_id": block_id, "k": k_requested, "n": len(block_questions)}))
                continue

        random.shuffle(current_test_questions)
        all_tests_question_data.append(current_test_questions)

    # Controlla se sono stati generati il numero corretto di test
    # Check if the correct number of tests were generated
    if len(all_tests_question_data) != num_tests_to_generate:
         if not any(m[1] == "STAT_TEST_GENERATION_FAILED_KPB" for m in error_messages):
             k_per_block = list(block_requests.values())[0] if block_requests else 'N/A'
             error_messages.append(("error", "STAT_TEST_GENERATION_FAILED_KPB", {"k_per_block": k_per_block}))
         return None, error_messages

    return all_tests_question_data, error_messages


def _run_single_analysis_k_per_block(k_per_block, blocks_info, all_questions_list, num_tests_to_generate, use_wrswor=True):
    """
    Esegue UNA SINGOLA analisi di similarità per un dato k_per_block.
    Usa WRSwOR o Simple Random Sampling in base al flag use_wrswor.
    Restituisce dizionario {distance: avg_dice_index} e lista messaggi errore generazione.
    NON chiama status_callback.
    """
    dice_by_distance = {}
    max_distance_to_check = num_tests_to_generate - 1
    generation_error_messages = []

    # Costruisce le richieste per blocco
    block_requests = {block['block_id']: k_per_block for block in blocks_info if block['count'] >= k_per_block}
    if not block_requests:
         generation_error_messages.append(("error", "STAT_TEST_K_INVALID", {"k": k_per_block}))
         return None, generation_error_messages

    # Genera la sequenza di test usando il metodo scelto
    if use_wrswor:
        generated_tests_data, gen_errors = _generate_test_sequence_wrswor(
            all_questions_list, block_requests, num_tests_to_generate
        )
    else:
        generated_tests_data, gen_errors = _generate_test_sequence_simple_random(
            all_questions_list, block_requests, num_tests_to_generate
        )
    generation_error_messages.extend(gen_errors)

    if generated_tests_data is None:
        return None, generation_error_messages # Errori già in lista

    test_sets = [set(q['original_index'] for q in test) for test in generated_tests_data]

    for d in range(1, max_distance_to_check + 1):
        dice_indices_for_d = []
        for i in range(num_tests_to_generate - d):
            dice_index = _calculate_dice(test_sets[i], test_sets[i + d])
            dice_indices_for_d.append(dice_index)
        if dice_indices_for_d:
            dice_by_distance[d] = dice_indices_for_d

    avg_dice_results_for_k = {}
    for d, indices in dice_by_distance.items():
         if indices:
             avg = sum(indices) / len(indices)
             avg_dice_results_for_k[d] = avg if not math.isnan(avg) else 0.0
         else:
             avg_dice_results_for_k[d] = None
    return avg_dice_results_for_k, generation_error_messages


# ================================================================
# Funzione Orchestratore Test Monte Carlo (run_all_tests)
# ================================================================
def run_all_tests(status_callback, num_monte_carlo_runs=30):
    """
    Orchestra l'analisi statistica di similarità (Dice) con Monte Carlo.
    Esegue due analisi:
    1. WRSwOR per k_per_block da 1 a 6.
    2. Simple Random per k_per_block da 7 a 11.
    Salva i risultati medi finali in due fogli di un file Excel.
    Restituisce lista di tuple (type, key, kwargs_dict) con messaggi sommari finali
    e include un messaggio di successo/fallimento per l'Excel.
    Chiama status_callback solo per errori critici e messaggi finali.
    """
    monte_carlo_summary = []
    # Accumulatori separati per i due metodi / Separate accumulators for the two methods
    results_accumulator_wrswor = defaultdict(lambda: defaultdict(lambda: {'sum': 0.0, 'count': 0}))
    results_accumulator_simple = defaultdict(lambda: defaultdict(lambda: {'sum': 0.0, 'count': 0}))

    # 1. Carica dati e info blocchi
    all_questions, blocks_summary, error_key = _load_test_questions(status_callback)
    if error_key:
        monte_carlo_summary.append(("error", "TEST_ABORTED_LOAD_FAILED", {}))
        return monte_carlo_summary, None

    expected_blocks = 4
    if not blocks_summary or len(blocks_summary) != expected_blocks:
        monte_carlo_summary.append(("error", "TEST_WRONG_BLOCK_COUNT", {"found": len(blocks_summary) if blocks_summary else 0, "expected": expected_blocks}))
        return monte_carlo_summary, None
    expected_q_per_block = 12
    for block in blocks_summary:
        if block['count'] != expected_q_per_block:
             monte_carlo_summary.append(("error", "TEST_WRONG_Q_PER_BLOCK_COUNT", {"block_id": block['block_id'], "found": block['count'], "expected": expected_q_per_block}))
             return monte_carlo_summary, None

    # 2. Definisci parametri
    num_tests_per_sequence = 15
    k_wrswor_values = range(1, 7)    # Da 1 a 6 per WRSwOR
    k_simple_values = range(7, 12)   # Da 7 a 11 per Simple Random
    max_distance_overall = 0
    progress_update_frequency = 5

    monte_carlo_summary.append(("info", "MC_TEST_KPB_STARTING", {
        "num_runs": num_monte_carlo_runs,
        "num_k_wrswor": len(k_wrswor_values),
        "k_range_wrswor": f"1-{max(k_wrswor_values)}",
        "num_k_simple": len(k_simple_values),
        "k_range_simple": f"{min(k_simple_values)}-{max(k_simple_values)}",
        "num_tests": num_tests_per_sequence
    })) # Chiave aggiornata / Updated key

    # 3. Ciclo Monte Carlo Esterno
    for run in range(1, num_monte_carlo_runs + 1):
        if run % progress_update_frequency == 0 or run == num_monte_carlo_runs:
             status_callback("info", "MC_TEST_RUN_PROGRESS", current_run=run, total_runs=num_monte_carlo_runs)

        # --- Analisi WRSwOR (k=1 a 6) ---
        for k_block in k_wrswor_values:
            avg_dice_by_distance, gen_errors = _run_single_analysis_k_per_block(
                k_block, blocks_summary, all_questions, num_tests_per_sequence, use_wrswor=True
            )
            monte_carlo_summary.extend(gen_errors)
            if avg_dice_by_distance is not None:
                for d, avg_d in avg_dice_by_distance.items():
                    if avg_d is not None:
                        results_accumulator_wrswor[k_block][d]['sum'] += avg_d
                        results_accumulator_wrswor[k_block][d]['count'] += 1
                        max_distance_overall = max(max_distance_overall, d)
            else:
                monte_carlo_summary.append(("warning", "MC_TEST_FAILED_FOR_KPB_IN_RUN", {"k_per_block": k_block, "run": run, "method": "WRSwOR"}))

        # --- Analisi Simple Random (k=7 a 11) ---
        for k_block in k_simple_values:
            avg_dice_by_distance, gen_errors = _run_single_analysis_k_per_block(
                k_block, blocks_summary, all_questions, num_tests_per_sequence, use_wrswor=False
            )
            monte_carlo_summary.extend(gen_errors)
            if avg_dice_by_distance is not None:
                for d, avg_d in avg_dice_by_distance.items():
                    if avg_d is not None:
                        results_accumulator_simple[k_block][d]['sum'] += avg_d
                        results_accumulator_simple[k_block][d]['count'] += 1
                        max_distance_overall = max(max_distance_overall, d)
            else:
                monte_carlo_summary.append(("warning", "MC_TEST_FAILED_FOR_KPB_IN_RUN", {"k_per_block": k_block, "run": run, "method": "Simple Random"}))


    # 4. Calcola Medie Finali e Prepara Output per Excel
    detailed_results_wrswor = []
    detailed_results_simple = []
    if not max_distance_overall and (any(results_accumulator_wrswor.values()) or any(results_accumulator_simple.values())):
        max_distance_overall = 1 # Assicura almeno distanza 1 / Ensure at least distance 1

    # Calcola medie WRSwOR
    sorted_k_wrswor = sorted(results_accumulator_wrswor.keys())
    for k_block in sorted_k_wrswor:
        for d in range(1, max_distance_overall + 1):
            data = results_accumulator_wrswor[k_block].get(d)
            final_avg, num_samples = (data['sum'] / data['count'], data['count']) if data and data['count'] > 0 else (None, 0)
            detailed_results_wrswor.append({'k_per_block': k_block, 'distance': d, 'avg_dice': final_avg, 'num_samples': num_samples})

    # Calcola medie Simple Random
    sorted_k_simple = sorted(results_accumulator_simple.keys())
    for k_block in sorted_k_simple:
        for d in range(1, max_distance_overall + 1):
            data = results_accumulator_simple[k_block].get(d)
            final_avg, num_samples = (data['sum'] / data['count'], data['count']) if data and data['count'] > 0 else (None, 0)
            detailed_results_simple.append({'k_per_block': k_block, 'distance': d, 'avg_dice': final_avg, 'num_samples': num_samples})

    # 5. Crea e salva il file Excel con due fogli
    excel_created = False
    excel_filename = None
    if detailed_results_wrswor or detailed_results_simple:
        try:
            with pd.ExcelWriter(OUTPUT_EXCEL_FILE) as writer:
                if detailed_results_wrswor:
                    df_results_wrswor = pd.DataFrame(detailed_results_wrswor)
                    df_pivot_wrswor = pd.pivot_table(df_results_wrswor, values='avg_dice', index='k_per_block', columns='distance')
                    df_pivot_wrswor = df_pivot_wrswor.sort_index(ascending=True)
                    df_pivot_wrswor = df_pivot_wrswor.reindex(sorted(df_pivot_wrswor.columns), axis=1)
                    # Formatta header colonne / Format column headers
                    df_pivot_wrswor.columns = [f"Distanza {col}" for col in df_pivot_wrswor.columns]
                    df_pivot_wrswor.to_excel(writer, sheet_name='WRSwOR_Results (k=1-6)')

                if detailed_results_simple:
                    df_results_simple = pd.DataFrame(detailed_results_simple)
                    df_pivot_simple = pd.pivot_table(df_results_simple, values='avg_dice', index='k_per_block', columns='distance')
                    df_pivot_simple = df_pivot_simple.sort_index(ascending=True)
                    df_pivot_simple = df_pivot_simple.reindex(sorted(df_pivot_simple.columns), axis=1)
                    # Formatta header colonne / Format column headers
                    df_pivot_simple.columns = [f"Distanza {col}" for col in df_pivot_simple.columns]
                    df_pivot_simple.to_excel(writer, sheet_name='SimpleRandom_Results (k=7-11)')

            monte_carlo_summary.append(("success", "STAT_TEST_EXCEL_CREATED", {"filename": OUTPUT_EXCEL_FILE}))
            excel_created = True
            excel_filename = OUTPUT_EXCEL_FILE
        except Exception as e:
            monte_carlo_summary.append(("error", "STAT_TEST_EXCEL_SAVE_ERROR", {"filename": OUTPUT_EXCEL_FILE, "error": str(e)}))
    elif any(results_accumulator_wrswor.values()) or any(results_accumulator_simple.values()):
         monte_carlo_summary.append(("warning", "STAT_TEST_NO_DATA_FOR_EXCEL", {}))

    # 6. Messaggio finale completamento
    monte_carlo_summary.append(("info", "MC_TEST_ALL_COMPLETE", {}))

    return monte_carlo_summary, excel_filename
