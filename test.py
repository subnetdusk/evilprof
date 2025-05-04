# test.py (New statistical analysis based on questions per block)
import pandas as pd
import random
import os
import math
from collections import defaultdict

# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data

# Costante per il nome del file di test e output / Constants for test file and output
# --- USA IL NUOVO FILE EXCEL ---
# --- USE THE NEW EXCEL FILE ---
TEST_EXCEL_FILE = "test_set_4_by_12_questions.xlsx"
# --- NUOVO NOME FILE OUTPUT ---
# --- NEW OUTPUT FILENAME ---
OUTPUT_EXCEL_FILE = "similarity_analysis_k_per_block_dice_mc.xlsx"

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
        # Legge direttamente da Excel, gestendo estensione
        # Read directly from Excel, handling extension
        _, file_extension = os.path.splitext(TEST_EXCEL_FILE)
        if file_extension.lower() not in ['.xlsx', '.xls']:
             status_callback("error", "FH_UNSUPPORTED_FORMAT", filename=TEST_EXCEL_FILE, extension=file_extension)
             return None, None, "FH_UNSUPPORTED_FORMAT"

        df = pd.read_excel(TEST_EXCEL_FILE, header=None)
        df = df.fillna('').astype(str) # Converte in stringa per consistenza

        all_questions = []
        blocks_summary = []
        current_block_id = 1
        current_block_questions = []
        current_block_type = None
        first_question_in_block = True

        # Aggiunge riga vuota virtuale
        df.loc[len(df)] = [""] * df.shape[1]

        for index, row in df.iterrows():
            is_empty_row = all(s is None or str(s).strip() == "" for s in row)

            if is_empty_row:
                if current_block_questions:
                    if current_block_type is None: current_block_type = 'Indeterminato'
                    blocks_summary.append({
                        'block_id': current_block_id,
                        'type': current_block_type, # Tipo rilevato per il blocco
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
                    # Determina tipo DOMANDA (per verifica tipo blocco)
                    # Determine QUESTION type (to verify block type)
                    question_type = 'Scelta Multipla' if len(answers) >= 2 else 'Aperte'

                    if first_question_in_block:
                        current_block_type = question_type # Imposta tipo blocco / Set block type
                        first_question_in_block = False
                    elif question_type != current_block_type:
                        # Segnala tipi misti ma continua, associando al tipo del blocco
                        # Report mixed types but continue, associating with block type
                        status_callback("warning", "FH_BLOCK_MIXED_TYPES", block_id=current_block_id, expected=current_block_type, found=question_type, row_num=index + 1)
                        # Potremmo decidere di saltare la domanda: continue

                    question_dict = {
                        'question': question_text,
                        'answers': answers if current_block_type == 'Scelta Multipla' else [], # Usa tipo BLOCCO
                        'original_index': index,
                        'type': current_block_type, # Associa tipo BLOCCO alla domanda
                        'block_id': current_block_id
                    }
                    current_block_questions.append(question_dict)

        blocks_summary = [b for b in blocks_summary if b['count'] > 0]

        if not all_questions:
            status_callback("error", "FH_NO_VALID_QUESTIONS", filename=TEST_EXCEL_FILE)
            return None, None, "FH_NO_VALID_QUESTIONS"

        # status_callback("info", "TEST_LOAD_SUCCESS", count=len(all_questions), num_blocks=len(blocks_summary)) # Silenziato
        return all_questions, blocks_summary, None # Ritorna anche block_summary

    except Exception as e:
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, None, "TEST_LOAD_ERROR"

def _calculate_dice(set1, set2):
    """Calcola il coefficiente di Sørensen–Dice tra due insiemi."""
    intersection_cardinality = len(set1.intersection(set2))
    denominator = len(set1) + len(set2)
    if denominator == 0: return 1.0
    return 2 * intersection_cardinality / denominator

def _run_single_analysis_k_per_block(k_per_block, blocks_info, all_questions_list, num_tests_to_generate):
    """
    Esegue UNA SINGOLA analisi di similarità per un dato k_per_block.
    Restituisce dizionario {distance: avg_dice_index} e lista messaggi errore generazione.
    NON chiama status_callback.
    """
    dice_by_distance = {}
    max_distance_to_check = num_tests_to_generate - 1
    generation_error_messages = []
    def nop_callback(*args, **kwargs): pass

    # Costruisce le richieste per blocco / Build block requests
    block_requests = {block['block_id']: k_per_block for block in blocks_info if block['count'] >= k_per_block}
    # Verifica se k_per_block è valido per almeno un blocco / Check if k_per_block is valid for at least one block
    if not block_requests:
         generation_error_messages.append(("error", "STAT_TEST_K_INVALID", {"k": k_per_block}))
         return None, generation_error_messages

    # Genera la sequenza di test usando la logica per blocchi
    # Generate test sequence using block logic
    generated_tests_data, gen_messages_internal = generate_all_tests_data(
        all_questions_list, # Passa la lista completa
        block_requests,     # Passa le richieste specifiche
        num_tests_to_generate,
        nop_callback        # Callback silenziato
    )
    # Salva solo errori critici / Save only critical errors
    generation_error_messages.extend([msg for msg in gen_messages_internal if msg[0] == 'error'])

    if not generated_tests_data or len(generated_tests_data) != num_tests_to_generate:
        if not any(m[1] == "STAT_TEST_GENERATION_FAILED_KPB" for m in generation_error_messages): # Nuova chiave errore
             generation_error_messages.append(("error", "STAT_TEST_GENERATION_FAILED_KPB", {"k_per_block": k_per_block}))
        return None, generation_error_messages

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
    Orchestra l'analisi statistica di similarità (Dice) con Monte Carlo,
    variando k_per_block da 1 a 6, usando test_set_4_by_12_questions.xlsx.
    Salva i risultati medi finali in un file Excel.
    Restituisce lista di tuple (type, key, kwargs_dict) con messaggi sommari finali
    e include un messaggio di successo/fallimento per l'Excel.
    Chiama status_callback solo per errori critici e messaggi finali.
    """
    monte_carlo_summary = []
    # Accumulatore basato su k_per_block / Accumulator based on k_per_block
    results_accumulator = defaultdict(lambda: defaultdict(lambda: {'sum': 0.0, 'count': 0}))

    # 1. Carica dati e info blocchi / Load data and block info
    all_questions, blocks_summary, error_key = _load_test_questions(status_callback)
    if error_key:
        monte_carlo_summary.append(("error", "TEST_ABORTED_LOAD_FAILED", {}))
        return monte_carlo_summary, None

    # Verifica numero blocchi (dovrebbero essere 4) / Verify block count (should be 4)
    expected_blocks = 4
    if not blocks_summary or len(blocks_summary) != expected_blocks:
        monte_carlo_summary.append(("error", "TEST_WRONG_BLOCK_COUNT", {"found": len(blocks_summary) if blocks_summary else 0, "expected": expected_blocks}))
        return monte_carlo_summary, None
    # Verifica che ogni blocco abbia 12 domande / Verify each block has 12 questions
    expected_q_per_block = 12
    for block in blocks_summary:
        if block['count'] != expected_q_per_block:
             monte_carlo_summary.append(("error", "TEST_WRONG_Q_PER_BLOCK_COUNT", {"block_id": block['block_id'], "found": block['count'], "expected": expected_q_per_block}))
             return monte_carlo_summary, None

    # 2. Definisci parametri / Define parameters
    num_tests_per_sequence = 30 # Numero di test consecutivi da generare / Number of consecutive tests
    # Itera k_per_block da 1 a 6 / Iterate k_per_block from 1 to 6
    k_per_block_values = range(1, 7)
    max_distance_overall = 0
    progress_update_frequency = 5

    monte_carlo_summary.append(("info", "MC_TEST_KPB_STARTING", {"num_runs": num_monte_carlo_runs, "num_k": len(k_per_block_values), "k_range": f"1-{max(k_per_block_values)}", "num_tests": num_tests_per_sequence})) # Nuova chiave / New key

    # 3. Ciclo Monte Carlo Esterno / Outer Monte Carlo Loop
    for run in range(1, num_monte_carlo_runs + 1):
        if run % progress_update_frequency == 0 or run == num_monte_carlo_runs:
             status_callback("info", "MC_TEST_RUN_PROGRESS", current_run=run, total_runs=num_monte_carlo_runs)
        run_successful = True

        # Ciclo sui valori di k_per_block interno / Inner loop over k_per_block values
        for k_block in k_per_block_values:
            # Esegui una singola analisi per questo k_block / Perform single analysis for this k_block
            avg_dice_by_distance, gen_errors = _run_single_analysis_k_per_block(
                k_block, blocks_summary, all_questions, num_tests_per_sequence
            )
            # Accumula solo errori critici dalla generazione / Accumulate only critical errors
            monte_carlo_summary.extend(gen_errors)

            if avg_dice_by_distance is not None:
                for d, avg_d in avg_dice_by_distance.items():
                    if avg_d is not None:
                        # Accumula per k_block e distanza / Accumulate by k_block and distance
                        results_accumulator[k_block][d]['sum'] += avg_d
                        results_accumulator[k_block][d]['count'] += 1
                        max_distance_overall = max(max_distance_overall, d)
            else:
                # Segnala fallimento per questo k_block in questa run / Signal failure for this k_block in this run
                monte_carlo_summary.append(("warning", "MC_TEST_FAILED_FOR_KPB_IN_RUN", {"k_per_block": k_block, "run": run})) # Nuova chiave / New key
                run_successful = False

    # 4. Calcola Medie Finali e Prepara Output / Calculate Final Averages and Prepare Output
    final_avg_results = defaultdict(dict)
    detailed_results_for_excel = []
    sorted_k = sorted(results_accumulator.keys()) # Ordina k_per_block crescente / Sort k_per_block ascending
    if not max_distance_overall and any(results_accumulator.values()): max_distance_overall = 1

    for k_block in sorted_k:
        # result_str_parts = [] # Rimosso per silenziare output intermedio
        for d in range(1, max_distance_overall + 1):
            data = results_accumulator[k_block].get(d)
            final_avg = None
            num_samples = 0
            if data and data['count'] > 0:
                final_avg = data['sum'] / data['count']
                num_samples = data['count']
            final_avg_results[k_block][d] = final_avg
            # Usa k_per_block come indice / Use k_per_block as index
            detailed_results_for_excel.append({'k_per_block': k_block, 'distance': d, 'avg_dice': final_avg, 'num_samples': num_samples})
            # result_str_parts.append(f"d{d}={final_avg:.3f}({num_samples})" if final_avg is not None else f"d{d}=N/A")
        # result_str = ", ".join(result_str_parts)
        # monte_carlo_summary.append(("info", "MC_TEST_FINAL_RESULTS_DICE_FOR_KPB", {"k_per_block": k_block, "results": result_str})) # Nuova chiave, ma silenziata

    # 5. Crea e salva il file Excel
    excel_created = False
    excel_filename = None
    if detailed_results_for_excel:
        try:
            df_results = pd.DataFrame(detailed_results_for_excel)
            # Pivot con k_per_block come indice / Pivot with k_per_block as index
            df_pivot = pd.pivot_table(df_results, values='avg_dice', index='k_per_block', columns='distance')
            df_pivot = df_pivot.sort_index(ascending=True) # Ordina k crescente / Sort k ascending
            df_pivot = df_pivot.reindex(sorted(df_pivot.columns), axis=1) # Ordina distanze / Sort distances
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
