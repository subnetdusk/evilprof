# test.py (Updated with statistical similarity analysis)
import pandas as pd
import random
import os
import math # Needed for isnan if using numpy later, good practice

# Importa la funzione di generazione principale da core_logic
# Import the main generation function from core_logic
from core_logic import generate_all_tests_data

# Costante per il nome del file di test / Constant for the test file name
TEST_EXCEL_FILE = "test_questions.xlsx"

def _load_test_questions(status_callback):
    """
    Carica domande specificamente da TEST_EXCEL_FILE.
    Restituisce (lista_domande, None) o (None, chiave_errore).

    Loads questions specifically from TEST_EXCEL_FILE.
    Returns (question_list, None) or (None, error_key).
    """
    if not os.path.exists(TEST_EXCEL_FILE):
        status_callback("error", "TEST_FILE_NOT_FOUND", filename=TEST_EXCEL_FILE)
        return None, "TEST_FILE_NOT_FOUND"

    try:
        status_callback("info", "TEST_LOADING_DATA", filename=TEST_EXCEL_FILE)
        df = pd.read_excel(TEST_EXCEL_FILE, header=None)
        questions_data = []
        mc_count = 0
        oe_count = 0
        for index, row in df.iterrows():
            row_list = [str(item).strip() if pd.notna(item) else "" for item in row]
            question_text = row_list[0]
            answers = [ans for ans in row_list[1:] if ans]
            if question_text:
                if len(answers) >= 2:
                    question_type = 'multiple_choice'; mc_count += 1
                    questions_data.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': question_type})
                else:
                    question_type = 'open_ended'; oe_count += 1
                    questions_data.append({'question': question_text, 'answers': [], 'original_index': index, 'type': question_type})
        if not questions_data:
             status_callback("error", "TEST_NO_QUESTIONS_FOUND", filename=TEST_EXCEL_FILE)
             return None, "TEST_NO_QUESTIONS_FOUND"
        status_callback("info", "TEST_LOAD_SUCCESS", count=len(questions_data), mc=mc_count, oe=oe_count)
        return questions_data, None
    except Exception as e:
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, "TEST_LOAD_ERROR"

def _calculate_jaccard(set1, set2):
    """
    Calcola l'indice Jaccard tra due insiemi.
    Calculates the Jaccard Index between two sets.
    """
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    # Se l'unione è 0 (entrambi i set sono vuoti), Jaccard è 1 per definizione.
    # If union is 0 (both sets empty), Jaccard is 1 by definition.
    if union == 0:
        return 1.0
    return intersection / union

def _run_similarity_analysis_for_k(k_mc, k_oe, num_tests_to_generate, mc_questions, open_questions, status_callback):
    """
    Esegue l'analisi di similarità per un valore fisso di k_mc e k_oe.
    Genera una sequenza di test e calcola l'indice Jaccard medio vs distanza.
    Restituisce un dizionario {distance: avg_jaccard_index} o None in caso di fallimento.

    Performs similarity analysis for fixed k_mc and k_oe.
    Generates a test sequence and calculates average Jaccard index vs distance.
    Returns a dictionary {distance: avg_jaccard_index} or None on failure.
    """
    # Dizionario per memorizzare gli indici Jaccard per ogni distanza
    # Dictionary to store Jaccard indices for each distance
    jaccard_by_distance = {} # {distance: [list of jaccard indices]}
    # Distanza massima da controllare (es. 15 o meno se ci sono pochi test)
    # Maximum distance to check (e.g., 15 or less if few tests)
    max_distance_to_check = min(num_tests_to_generate - 1, 15)

    # Messaggio inizio generazione sequenza per questo k
    # Start sequence generation message for this k
    status_callback("info", "STAT_TEST_GENERATING_SEQUENCE", k_mc=k_mc, k_oe=k_oe, num_tests=num_tests_to_generate)

    # Genera la sequenza di test / Generate the test sequence
    generated_tests_data, gen_messages = generate_all_tests_data(
        mc_questions, open_questions, num_tests_to_generate, k_mc, k_oe, status_callback
    )

    # Controlla se la generazione ha avuto successo / Check if generation was successful
    if not generated_tests_data or len(generated_tests_data) != num_tests_to_generate:
        status_callback("error", "STAT_TEST_GENERATION_FAILED", k_mc=k_mc, k_oe=k_oe)
        # Potremmo voler aggiungere gen_messages al report finale / We might want to add gen_messages to the final report
        return None # Indica fallimento / Indicate failure

    # Converte i dati dei test in insiemi di indici per efficienza
    # Convert test data into sets of indices for efficiency
    test_sets = [set(q['original_index'] for q in test) for test in generated_tests_data]

    # Messaggio inizio calcolo similarità / Start similarity calculation message
    status_callback("info", "STAT_TEST_CALCULATING_SIMILARITY", k_mc=k_mc, k_oe=k_oe, max_dist=max_distance_to_check)

    # Calcola indici Jaccard per ogni distanza d / Calculate Jaccard indices for each distance d
    for d in range(1, max_distance_to_check + 1):
        jaccard_indices_for_d = []
        # Itera sulle coppie (test_i, test_{i+d}) / Iterate over pairs (test_i, test_{i+d})
        for i in range(num_tests_to_generate - d):
            set1 = test_sets[i]
            set2 = test_sets[i + d]
            jaccard_index = _calculate_jaccard(set1, set2)
            jaccard_indices_for_d.append(jaccard_index)

        # Memorizza la lista di indici per questa distanza / Store the list of indices for this distance
        if jaccard_indices_for_d:
            jaccard_by_distance[d] = jaccard_indices_for_d

    # Calcola la media per ogni distanza / Calculate the average for each distance
    avg_results_for_k = {}
    for d, indices in jaccard_by_distance.items():
         if indices:
             # Calcola la media, gestendo NaN se necessario (improbabile qui)
             # Calculate average, handling NaN if necessary (unlikely here)
             avg = sum(indices) / len(indices)
             avg_results_for_k[d] = avg if not math.isnan(avg) else 0.0
         else:
             avg_results_for_k[d] = None # Nessun dato per questa distanza / No data for this distance

    # Messaggio completamento analisi per questo k / Analysis completion message for this k
    status_callback("info", "STAT_TEST_ANALYSIS_COMPLETE", k_mc=k_mc, k_oe=k_oe)
    return avg_results_for_k # Ritorna {distanza: media_jaccard} / Return {distance: avg_jaccard}

# ================================================================
# Funzione Orchestratore Test Statistico / Statistical Test Orchestrator Function
# ================================================================
def run_statistical_similarity_test(status_callback):
    """
    Orchestra l'analisi statistica di similarità per k (MC=OE) da 11 a 1.
    Utilizza status_callback(type, key, **kwargs) per i messaggi.
    Restituisce lista di tuple (type, key, kwargs_dict) con i risultati sommari.

    Orchestrates the statistical similarity analysis for k (MC=OE) from 11 down to 1.
    Uses status_callback(type, key, **kwargs) for messages.
    Returns a list of tuples (type, key, kwargs_dict) with summary results.
    """
    statistical_results_summary = [] # Lista per messaggi sommari / List for summary messages

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
    # Numero di test consecutivi da generare per ogni k
    # Number of consecutive tests to generate for each k
    num_tests_per_k = 30 # Puoi aumentarlo per statistiche più robuste / Can increase for more robust stats
    # Valori di k (MC=OE) da testare / k values (MC=OE) to test
    k_values_to_test = range(11, 0, -1) # Da 11 a 1 / From 11 down to 1

    statistical_results_summary.append(("info", "STAT_TEST_STARTING", {"num_k": len(k_values_to_test), "num_tests": num_tests_per_k}))

    # 3. Ciclo sui valori di k / Loop through k values
    all_k_results = {} # Memorizza risultati dettagliati / Store detailed results: {k: {distance: avg_jaccard}}
    for k in k_values_to_test:
        status_callback("info", "STAT_TEST_RUNNING_FOR_K", k=k)
        # Esegui l'analisi per questo k / Run analysis for this k
        avg_jaccard_by_distance = _run_similarity_analysis_for_k(
            k, k, num_tests_per_k, mc_questions, open_questions, status_callback
        )
        # Memorizza e riporta i risultati se l'analisi ha avuto successo
        # Store and report results if analysis was successful
        if avg_jaccard_by_distance is not None:
             all_k_results[k] = avg_jaccard_by_distance
             # Formatta i risultati per un output leggibile / Format results for readable output
             result_str_parts = []
             # Ordina per distanza per leggibilità / Sort by distance for readability
             for d in sorted(avg_jaccard_by_distance.keys()):
                 avg_j = avg_jaccard_by_distance[d]
                 # Mostra "N/A" se non calcolabile / Show "N/A" if not calculable
                 result_str_parts.append(f"d{d}={avg_j:.3f}" if avg_j is not None else f"d{d}=N/A")
             result_str = ", ".join(result_str_parts)
             # Aggiunge il sommario per questo k ai messaggi finali
             # Add summary for this k to final messages
             statistical_results_summary.append(("info", "STAT_TEST_RESULTS_FOR_K", {"k": k, "results": result_str}))
        else:
             # Segnala fallimento per questo k / Signal failure for this k
             statistical_results_summary.append(("error", "STAT_TEST_FAILED_FOR_K", {"k": k}))

    # 4. Messaggio finale / Final message
    statistical_results_summary.append(("success", "STAT_TEST_ALL_COMPLETE", {}))

    # TODO: Potresti voler restituire 'all_k_results' per visualizzazioni in app.py
    # You might want to return 'all_k_results' for visualizations in app.py
    return statistical_results_summary


# ================================================================
# Funzione Test Scenari Precedenti (Commentata o Rimossa)
# Previous Scenario Test Function (Commented out or Removed)
# ================================================================
# def run_all_tests(status_callback):
#    """Esegue i 3 scenari di test originali."""
#    # ... [codice dei 3 test precedenti] ...
#    pass # Lasciata vuota o commentata / Left empty or commented out
