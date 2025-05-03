# test.py (Updated for specific test scenarios using test_questions.xlsx)
import pandas as pd
import random
import os
# Importa la funzione di generazione principale da core_logic
from core_logic import generate_all_tests_data

# Costante per il nome del file di test
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
        # Itera sulle righe del DataFrame per estrarre le domande
        # Iterate over DataFrame rows to extract questions
        for index, row in df.iterrows():
            # Converte tutti gli elementi della riga in stringa, gestendo NaN
            # Convert all row items to string, handling NaN
            row_list = [str(item).strip() if pd.notna(item) else "" for item in row]
            question_text = row_list[0]
            # Filtra le risposte vuote
            # Filter out empty answers
            answers = [ans for ans in row_list[1:] if ans]

            if question_text: # Processa solo se la domanda non è vuota / Process only if question is not empty
                if len(answers) >= 2: # Considerata MC se ha almeno 2 risposte / Considered MC if at least 2 answers
                    question_type = 'multiple_choice'
                    mc_count += 1
                    questions_data.append({
                        'question': question_text,
                        'answers': answers,
                        'original_index': index, # Usa l'indice della riga Excel come ID univoco / Use Excel row index as unique ID
                        'type': question_type
                    })
                else: # Altrimenti è considerata aperta / Otherwise considered open-ended
                    question_type = 'open_ended'
                    oe_count += 1
                    questions_data.append({
                        'question': question_text,
                        'answers': [], # Le domande aperte non hanno risposte predefinite / Open questions have no predefined answers
                        'original_index': index,
                        'type': question_type
                    })
        # Controlla se sono state trovate domande valide / Check if valid questions were found
        if not questions_data:
             status_callback("error", "TEST_NO_QUESTIONS_FOUND", filename=TEST_EXCEL_FILE)
             return None, "TEST_NO_QUESTIONS_FOUND"
        # Segnala successo caricamento / Signal successful loading
        status_callback("info", "TEST_LOAD_SUCCESS", count=len(questions_data), mc=mc_count, oe=oe_count)
        return questions_data, None
    except Exception as e:
        # Segnala errore imprevisto durante il caricamento / Signal unexpected loading error
        status_callback("error", "TEST_LOAD_ERROR", filename=TEST_EXCEL_FILE, error=str(e))
        return None, "TEST_LOAD_ERROR"


def _compare_tests(test1_data, test2_data):
    """
    Confronta due test (liste di dizionari domanda) basandosi
    sull'insieme degli indici originali delle domande.
    Restituisce True se i test contengono esattamente le stesse domande, False altrimenti.

    Compares two tests (lists of question dictionaries) based on
    the set of original question indices.
    Returns True if the tests contain exactly the same questions, False otherwise.
    """
    set1 = set(q['original_index'] for q in test1_data)
    set2 = set(q['original_index'] for q in test2_data)
    # Devono avere la stessa dimensione E gli stessi elementi / Must have same size AND same elements
    return len(set1) == len(set2) and set1 == set2

# ================================================================
# Funzione Principale di Test / Main Test Function
# ================================================================
def run_all_tests(status_callback):
    """
    Esegue i 3 scenari di test definiti usando test_questions.xlsx.
    Utilizza status_callback(type, key, **kwargs) per i messaggi.
    Restituisce lista di tuple (type, key, kwargs_dict) con i risultati sommari.

    Runs the 3 defined test scenarios using test_questions.xlsx.
    Uses status_callback(type, key, **kwargs) for messages.
    Returns a list of tuples (type, key, kwargs_dict) with summary results.
    """
    test_summary_results = [] # Lista per i risultati finali / List for final results

    # 0. Carica i dati dal file di test dedicato / Load data from dedicated test file
    all_questions, error_key = _load_test_questions(status_callback)
    if error_key:
        # Il messaggio di errore è già stato inviato dal loader / Error message already sent by loader
        test_summary_results.append(("error", "TEST_ABORTED_LOAD_FAILED", {}))
        return test_summary_results

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions)
    total_open = len(open_questions)

    # Verifica numero domande caricate (dovrebbero essere 24+24)
    # Verify loaded question count (should be 24+24)
    expected_count = 24
    if total_mc != expected_count or total_open != expected_count:
         test_summary_results.append(("error", "TEST_WRONG_QUESTION_COUNT", {"mc": total_mc, "oe": total_open, "expected": expected_count}))
         # Non prosegue se il numero di domande non è quello atteso / Do not proceed if question count is not as expected
         return test_summary_results

    # --- Parametri Comuni / Common Parameters ---
    num_simulations = 100 # Numero di test da generare per scenario / Number of tests per scenario

    # --- Scenario 1: Green Condition (n=24, k=2 MC, k=2 OE => n >= 3k) ---
    test_1_params = {"mc": 2, "oe": 2}
    status_callback("info", "TEST_RUNNING_SCENARIO", scenario=1, mc=test_1_params["mc"], oe=test_1_params["oe"], n_sim=num_simulations)
    # Genera i dati per lo scenario 1 / Generate data for scenario 1
    test_1_data, test_1_gen_msgs = generate_all_tests_data(
        mc_questions, open_questions, num_simulations, test_1_params["mc"], test_1_params["oe"], status_callback
    )
    test_1_passed_assertion = True
    test_1_failures = 0
    # Controlla se la generazione è andata a buon fine / Check if generation was successful
    if test_1_data and len(test_1_data) == num_simulations:
        # Confronta ogni test con il precedente / Compare each test with the previous one
        for i in range(1, num_simulations):
            if _compare_tests(test_1_data[i], test_1_data[i-1]):
                test_1_passed_assertion = False
                test_1_failures += 1
                # Log dettagliato opzionale per debug / Optional detailed log for debugging
                # status_callback("warning", "TEST_ASSERT_FAIL_DETAIL", scenario=1, test_index=i)
        # Aggiunge risultato sommario / Add summary result
        if test_1_passed_assertion:
            test_summary_results.append(("success", "TEST_SCENARIO_PASSED", {"scenario": 1}))
        else:
            test_summary_results.append(("error", "TEST_SCENARIO_ASSERT_FAILED", {"scenario": 1, "failures": test_1_failures, "total": num_simulations}))
    else: # Errore durante la generazione / Error during generation
        test_summary_results.append(("error", "TEST_SCENARIO_GENERATION_FAILED", {"scenario": 1}))
        test_summary_results.extend(test_1_gen_msgs) # Aggiunge errori specifici / Add specific generation errors

    # --- Scenario 2: Yellow Condition (n=24, k=10 MC, k=10 OE => 2k < n < 3k) ---
    test_2_params = {"mc": 10, "oe": 10}
    status_callback("info", "TEST_RUNNING_SCENARIO", scenario=2, mc=test_2_params["mc"], oe=test_2_params["oe"], n_sim=num_simulations)
    test_2_data, test_2_gen_msgs = generate_all_tests_data(
        mc_questions, open_questions, num_simulations, test_2_params["mc"], test_2_params["oe"], status_callback
    )
    test_2_passed_assertion = True
    test_2_failures = 0
    if test_2_data and len(test_2_data) == num_simulations:
        for i in range(1, num_simulations):
            if _compare_tests(test_2_data[i], test_2_data[i-1]):
                test_2_passed_assertion = False
                test_2_failures += 1
        if test_2_passed_assertion:
            test_summary_results.append(("success", "TEST_SCENARIO_PASSED", {"scenario": 2}))
        else:
            # Questo sarebbe inaspettato se WRSwOR funziona correttamente senza fallback
            # This would be unexpected if WRSwOR works correctly without fallback
            test_summary_results.append(("error", "TEST_SCENARIO_ASSERT_FAILED", {"scenario": 2, "failures": test_2_failures, "total": num_simulations}))
    else:
        test_summary_results.append(("error", "TEST_SCENARIO_GENERATION_FAILED", {"scenario": 2}))
        test_summary_results.extend(test_2_gen_msgs)

    # --- Scenario 3: Limit Condition (n=24, k=12 MC, k=12 OE => n = 2k) ---
    test_3_params = {"mc": 12, "oe": 12}
    status_callback("info", "TEST_RUNNING_SCENARIO", scenario=3, mc=test_3_params["mc"], oe=test_3_params["oe"], n_sim=num_simulations)
    test_3_data, test_3_gen_msgs = generate_all_tests_data(
        mc_questions, open_questions, num_simulations, test_3_params["mc"], test_3_params["oe"], status_callback
    )
    test_3_passed_assertion = True
    test_3_failures = 0
    # Controlla se il fallback è stato attivato durante la generazione
    # Check if fallback was activated during generation
    fallback_activated_scenario3 = any(msg[1] == "CL_FINAL_FALLBACK_ACTIVE" for msg in test_3_gen_msgs)

    if test_3_data and len(test_3_data) == num_simulations:
        for i in range(1, num_simulations):
            if _compare_tests(test_3_data[i], test_3_data[i-1]):
                test_3_passed_assertion = False
                test_3_failures += 1
        if test_3_passed_assertion:
            # Passare questo test è possibile ma meno probabile a causa del fallback
            # Passing this test is possible but less likely due to fallback
             test_summary_results.append(("success", "TEST_SCENARIO_PASSED", {"scenario": 3}))
             if fallback_activated_scenario3:
                 # Segnala che è passato nonostante il fallback fosse attivo
                 # Signal that it passed even though fallback was active
                 test_summary_results.append(("info", "TEST_SCENARIO_3_PASSED_WITH_FALLBACK", {}))
        else:
            # Fallire l'assertion è più probabile qui a causa del fallback
            # Failing the assertion is more likely here due to fallback
            test_summary_results.append(("warning", "TEST_SCENARIO_ASSERT_FAILED_EXPECTED", {"scenario": 3, "failures": test_3_failures, "total": num_simulations}))
    else:
        test_summary_results.append(("error", "TEST_SCENARIO_GENERATION_FAILED", {"scenario": 3}))
        test_summary_results.extend(test_3_gen_msgs) # Aggiunge errori specifici / Add specific errors

    # Aggiungi un messaggio finale di completamento / Add final completion message
    test_summary_results.append(("info", "TEST_ALL_SCENARIOS_COMPLETE", {}))

    return test_summary_results
