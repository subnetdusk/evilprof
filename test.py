# test.py (Console Version for Statistical Analysis)
import pandas as pd
import random
import os
import math
from collections import defaultdict
import argparse # Per gestire argomenti da linea di comando (opzionale, ma buona pratica)

# Importa la funzione di generazione principale da core_logic
# ASSICURATI CHE core_logic.py SIA ACCESSIBILE (nella stessa cartella o nel PYTHONPATH)
try:
    from core_logic import generate_all_tests_data
except ImportError:
    print("ERRORE: Impossibile importare 'generate_all_tests_data' da 'core_logic.py'.")
    print("Assicurati che 'core_logic.py' sia nella stessa cartella o accessibile tramite PYTHONPATH.")
    exit(1)


# Costante per il nome del file di test e output
DEFAULT_TEST_EXCEL_FILE = "test_set_4_by_12_questions.xlsx"
DEFAULT_OUTPUT_EXCEL_FILE = "similarity_analysis_unified_dice_mc_15t.xlsx"
DEFAULT_NUM_MONTE_CARLO_RUNS = 30

def _print_message(level, message):
    """Helper function to print messages to console."""
    print(f"[{level.upper()}] {message}")

def _load_test_questions(test_excel_file):
    """
    Carica domande da test_excel_file, rileva blocchi e tipi.
    Restituisce (all_questions, blocks_summary, None) o (None, None, messaggio_errore).
    Stampa messaggi di errore/warning sulla console.
    """
    if not os.path.exists(test_excel_file):
        _print_message("error", f"File di test '{test_excel_file}' non trovato.")
        return None, None, f"File di test '{test_excel_file}' non trovato."

    _print_message("info", f"Caricamento dati dal file di test '{test_excel_file}'...")
    try:
        _, file_extension = os.path.splitext(test_excel_file)
        if file_extension.lower() not in ['.xlsx', '.xls']:
             _print_message("error", f"Formato file non supportato '{file_extension}' per il file '{test_excel_file}'. Usare .xlsx o .xls.")
             return None, None, "Formato file non supportato."

        df = pd.read_excel(test_excel_file, header=None)
        df = df.fillna('').astype(str)

        all_questions = []
        blocks_summary = []
        current_block_id = 1
        current_block_questions = []
        current_block_type = None
        first_question_in_block = True

        # Aggiunge una riga vuota virtuale alla fine per processare l'ultimo blocco
        df.loc[len(df)] = [""] * df.shape[1]

        for index, row in df.iterrows():
            is_empty_row = all(s is None or str(s).strip() == "" for s in row)
            if is_empty_row:
                if current_block_questions:
                    if current_block_type is None: current_block_type = 'Indeterminato' # Fallback se un blocco ha solo righe vuote prima
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
                if question_text: # Solo se c'è testo nella domanda
                    question_type = 'Scelta Multipla' if len(answers) >= 2 else 'Aperte'
                    if first_question_in_block:
                        current_block_type = question_type
                        first_question_in_block = False
                    elif question_type != current_block_type:
                        _print_message("warning", f"Blocco {current_block_id}: Trovata domanda di tipo '{question_type}' (riga {index + 1}), ma il blocco era stato identificato come '{current_block_type}'. La domanda verrà ignorata.")
                        continue # Ignora la domanda che non corrisponde al tipo del blocco
                    question_dict = {
                        'question': question_text,
                        'answers': answers if current_block_type == 'Scelta Multipla' else [],
                        'original_index': index, # Usato per l'unicità nel calcolo Dice
                        'type': current_block_type,
                        'block_id': current_block_id
                    }
                    current_block_questions.append(question_dict)

        blocks_summary = [b for b in blocks_summary if b['count'] > 0] # Rimuove blocchi vuoti
        if not all_questions:
            _print_message("error", f"Nessuna domanda valida trovata nel file '{test_excel_file}'.")
            return None, None, "Nessuna domanda valida trovata."

        num_mc = sum(1 for q in all_questions if q['type'] == 'Scelta Multipla')
        num_oe = sum(1 for q in all_questions if q['type'] == 'Aperte')
        _print_message("info", f"Dati di test caricati: {len(all_questions)} domande totali ({num_mc} Scelta Multipla, {num_oe} Aperte) in {len(blocks_summary)} blocchi.")
        return all_questions, blocks_summary, None
    except Exception as e:
        _print_message("error", f"Errore imprevisto durante il caricamento del file di test '{test_excel_file}': {e}")
        return None, None, f"Errore caricamento file: {e}"


def _calculate_dice(set1, set2):
    """Calcola il coefficiente di Sørensen–Dice tra due insiemi."""
    intersection_cardinality = len(set1.intersection(set2))
    denominator = len(set1) + len(set2)
    if denominator == 0: return 1.0 # Due insiemi vuoti sono identici
    return 2 * intersection_cardinality / denominator

def _run_single_unified_analysis_for_k(k_per_block, blocks_info, all_questions_list, num_tests_to_generate):
    """
    Esegue UNA SINGOLA analisi di similarità per un dato k_per_block.
    Restituisce dizionario {distance: avg_dice_index} e lista messaggi errore generazione.
    """
    dice_by_distance = {}
    max_distance_to_check = num_tests_to_generate - 1
    generation_error_messages_console = [] # Messaggi da stampare sulla console

    # Definisce una callback dummy per core_logic, che ora stamperà i suoi warning/error
    def console_status_callback(msg_type, msg_key, **kwargs):
        # core_logic usa chiavi di localizzazione, qui le traduciamo rozzamente o stampiamo la chiave
        # In una versione console pura, core_logic dovrebbe essere adattato per non usare chiavi di localizzazione.
        # Per ora, stampiamo la chiave e i parametri.
        message = f"CORE_LOGIC_{msg_type.upper()}: {msg_key} - Params: {kwargs}"
        if msg_type in ["warning", "error"]:
            _print_message(msg_type, message)
            generation_error_messages_console.append(message)


    block_requests = {block['block_id']: k_per_block for block in blocks_info if block['count'] >= k_per_block}
    if not block_requests:
         msg = f"k={k_per_block} richiesto non è valido per nessun blocco con sufficienti domande."
         generation_error_messages_console.append(msg)
         return None, generation_error_messages_console

    generated_tests_data, gen_messages_internal = generate_all_tests_data(
        all_questions_list, block_requests, num_tests_to_generate, console_status_callback
    )
    # gen_messages_internal da core_logic sono già stati gestiti da console_status_callback se sono warning/error

    if generated_tests_data is None:
        msg = f"Fallita generazione sequenza test per k_per_block={k_per_block}."
        if not any(msg in m for m in generation_error_messages_console): # Evita duplicati
            generation_error_messages_console.append(msg)
        return None, generation_error_messages_console

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
             avg_dice_results_for_k[d] = None # O 0.0 se preferito
    return avg_dice_results_for_k, generation_error_messages_console


def run_statistical_analysis(test_excel_file, output_excel_file, num_monte_carlo_runs):
    """
    Orchestra l'analisi statistica di similarità (Dice) con Monte Carlo.
    Salva i risultati medi finali in un file Excel formattato.
    Stampa messaggi sulla console.
    """
    _print_message("info", f"Avvio analisi statistica con {num_monte_carlo_runs} run Monte Carlo.")
    _print_message("info", f"File di input: {test_excel_file}")
    _print_message("info", f"File di output: {output_excel_file}")

    results_accumulator = defaultdict(lambda: defaultdict(lambda: {'sum': 0.0, 'count': 0}))
    sampling_method_used = {} # Traccia quale metodo (WRSwOR/Simple) è atteso per k
    fallback_counts = defaultdict(int)

    all_questions, blocks_summary, error_msg = _load_test_questions(test_excel_file)
    if error_msg:
        _print_message("error", f"Test annullato: impossibile caricare i dati di test. {error_msg}")
        return

    # Validazioni specifiche del set di dati di test (come in app.py)
    expected_blocks = 4
    expected_q_per_block = 12
    if not blocks_summary or len(blocks_summary) != expected_blocks:
        _print_message("error", f"ERRORE Dati Test: Trovati {len(blocks_summary) if blocks_summary else 0} blocchi, attesi {expected_blocks}.")
        return
    for block in blocks_summary:
        if block['count'] != expected_q_per_block:
             _print_message("error", f"ERRORE Dati Test: Blocco {block['block_id']} ha {block['count']} domande, attese {expected_q_per_block}.")
             return

    num_tests_per_sequence = 15 # Quanti test generare in ogni sequenza per calcolare la similarità
    k_per_block_values = range(1, expected_q_per_block) # Da 1 a 11 per un blocco da 12
    max_distance_overall = 0

    for run in range(1, num_monte_carlo_runs + 1):
        if run % 5 == 0 or run == 1 or run == num_monte_carlo_runs: # Stampa progresso ogni 5 run
            _print_message("info", f"Progresso Monte Carlo: Run {run}/{num_monte_carlo_runs}...")

        for k_block in k_per_block_values:
            method_expected = "WRSwOR" if (k_block * 2 < expected_q_per_block) else "Simple Random"
            if k_block not in sampling_method_used:
                sampling_method_used[k_block] = method_expected

            avg_dice_by_distance, gen_errors_console = _run_single_unified_analysis_for_k(
                k_block, blocks_summary, all_questions, num_tests_per_sequence
            )

            # Controlla se ci sono stati messaggi di fallback da core_logic (tramite console_status_callback)
            # Questo è un modo indiretto, ideale sarebbe che core_logic restituisse info più strutturate
            if any("CORE_LOGIC_WARNING: BLOCK_FALLBACK_WARNING" in msg for msg in gen_errors_console):
                 fallback_counts[k_block] +=1

            if avg_dice_by_distance is not None:
                for d, avg_d in avg_dice_by_distance.items():
                    if avg_d is not None:
                        results_accumulator[k_block][d]['sum'] += avg_d
                        results_accumulator[k_block][d]['count'] += 1
                        max_distance_overall = max(max_distance_overall, d)
            else:
                _print_message("warning", f"Analisi fallita per k/blocco={k_block} (Metodo atteso: {method_expected}) nella run {run}.")

    _print_message("info", "--- Simulazione Monte Carlo completata. Elaborazione risultati... ---")

    detailed_results_for_excel = []
    sorted_k = sorted(results_accumulator.keys())
    if not max_distance_overall and any(results_accumulator.values()): max_distance_overall = 1 # Assicura almeno distanza 1

    for k_block in sorted_k:
        for d in range(1, max_distance_overall + 1): # Calcola per tutte le distanze osservate
            data = results_accumulator[k_block].get(d)
            final_avg, num_samples_for_avg = (data['sum'] / data['count'], data['count']) if data and data['count'] > 0 else (None, 0)
            detailed_results_for_excel.append({
                'k_per_block': k_block,
                'distance': d,
                'avg_dice': final_avg,
                'num_samples': num_samples_for_avg, # Numero di coppie di test usate per calcolare questa media
                'method_expected': sampling_method_used.get(k_block, 'Unknown'),
                'fallback_runs': fallback_counts.get(k_block, 0)
            })

    if detailed_results_for_excel:
        try:
            df_results = pd.DataFrame(detailed_results_for_excel)
            df_pivot = pd.pivot_table(df_results, values='avg_dice', index='k_per_block', columns='distance')
            
            # Aggiungi colonne Metodo Atteso e Fallback Runs
            method_map = pd.Series({k: sampling_method_used.get(k, 'Unknown') for k in df_pivot.index}, name='Metodo Atteso')
            fallback_map_series = pd.Series({k: fallback_counts.get(k,0) for k in df_pivot.index}, name=f'WRSwOR Fallback Runs (su {num_monte_carlo_runs})')
            
            df_pivot = df_pivot.join(method_map)
            df_pivot = df_pivot.join(fallback_map_series)
            
            df_pivot = df_pivot.sort_index(ascending=True)
            df_pivot.index = [f"{k} su {expected_q_per_block}" for k in df_pivot.index]
            df_pivot.index.name = f"k / n (n={expected_q_per_block} per blocco)"

            distance_cols = sorted([col for col in df_pivot.columns if isinstance(col, int)], key=int)
            other_cols = [col for col in df_pivot.columns if not isinstance(col, int) and col in df_pivot.columns] # Assicura che le colonne esistano
            
            # Ricostruisci l'ordine delle colonne
            final_columns_order = [f"Distanza {d}" for d in distance_cols] + \
                                  [col for col in ['Metodo Atteso', f'WRSwOR Fallback Runs (su {num_monte_carlo_runs})'] if col in other_cols]
            
            # Rinomina le colonne distanza prima di riordinare
            df_pivot.rename(columns={d: f"Distanza {d}" for d in distance_cols}, inplace=True)
            df_pivot = df_pivot.reindex(columns=final_columns_order)


            df_pivot.to_excel(output_excel_file, sheet_name='Similarity_Analysis')
            _print_message("success", f"File Excel con risultati statistici '{output_excel_file}' creato.")
        except Exception as e:
            _print_message("error", f"Errore durante il salvataggio del file Excel '{output_excel_file}': {e}")
    else:
         _print_message("warning", "Nessun dato dettagliato raccolto per creare il file Excel.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Esegue l'analisi statistica di similarità per EvilProf.")
    parser.add_argument(
        "--input_file",
        type=str,
        default=DEFAULT_TEST_EXCEL_FILE,
        help=f"Path del file Excel di test (default: {DEFAULT_TEST_EXCEL_FILE})"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=DEFAULT_OUTPUT_EXCEL_FILE,
        help=f"Path del file Excel di output per i risultati (default: {DEFAULT_OUTPUT_EXCEL_FILE})"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_NUM_MONTE_CARLO_RUNS,
        help=f"Numero di run Monte Carlo da eseguire (default: {DEFAULT_NUM_MONTE_CARLO_RUNS})"
    )
    args = parser.parse_args()

    run_statistical_analysis(args.input_file, args.output_file, args.runs)
