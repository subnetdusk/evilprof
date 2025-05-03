# test.py 
import random
# Importa la funzione di generazione principale da core_logic
from core_logic import generate_all_tests_data

# ================================================================
# Logica Test di Validazione / Functional Test Logic
# ================================================================
def run_validation_test(all_questions, status_callback):
    """
    Esegue un test di validazione semplificato generando 2 test
    e verificando se hanno domande in comune.
    Utilizza status_callback(type, key, **kwargs) per i messaggi.
    Restituisce lista di tuple (type, key, kwargs_dict) con i risultati.

    Runs a simplified validation test by generating 2 tests
    and checking if they share common questions.
    Uses status_callback(type, key, **kwargs) for messages.
    Returns a list of tuples (type, key, kwargs_dict) with the results.
    """
    # Lista per messaggi / List for messages (type, key, kwargs)
    validation_messages = []
    test_num_tests = 2
    test_num_mc = 2
    test_num_open = 1
    # status_callback("info", "CL_GENERATING_TEST_DATA", current_test=1, total_tests=test_num_tests) # Potrebbe servire chiave specifica per inizio test

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions)
    total_open = len(open_questions)

    # Controlli preliminari / Preliminary checks
    if total_mc < test_num_mc:
        validation_messages.append(("error", "CL_VALIDATION_INSUFFICIENT_MC_ERROR", {"total": total_mc, "k": test_num_mc}))
        return validation_messages
    if total_open < test_num_open:
        validation_messages.append(("error", "CL_VALIDATION_INSUFFICIENT_OE_ERROR", {"total": total_open, "k": test_num_open}))
        return validation_messages
    # Warning se non ci sono abbastanza domande per testare WRSwOR (n > 2k)
    # Warning if there aren't enough questions to test WRSwOR (n > 2k)
    if test_num_mc > 0 and total_mc <= test_num_mc * 2 :
         validation_messages.append(("warning", "CL_VALIDATION_INSUFFICIENT_MC_WARN", {"k": test_num_mc * 2 }))
    if test_num_open > 0 and total_open <= test_num_open * 2:
         validation_messages.append(("warning", "CL_VALIDATION_INSUFFICIENT_OE_WARN", {"k": test_num_open * 2 }))


    try:
        # Chiama la funzione di generazione principale / Call main generation function
        test_data, test_gen_messages = generate_all_tests_data(
            mc_questions, open_questions, test_num_tests, test_num_mc, test_num_open, status_callback
        )
        # Aggiunge i messaggi / Add generation messages
        validation_messages.extend(test_gen_messages)

        # Controlla se la generazione ha fallito / Check if generation failed
        if test_data is None or len(test_data) != test_num_tests:
            if not any(m[1] == "CL_VALIDATION_TEST_FAILED_GENERATION" for m in validation_messages):
                 validation_messages.append(("error", "CL_VALIDATION_TEST_FAILED_GENERATION", {}))
            return validation_messages

        # Messaggio stato validazione / Validation status message
        status_callback("info", "CL_VALIDATION_RUNNING", num_tests_generated=len(test_data))

        test_passed_overall = True
        # Controlla numero domande / Check question count per test
        for i_val, single_test_data in enumerate(test_data):
            expected_total = test_num_mc + test_num_open
            if len(single_test_data) != expected_total:
                validation_messages.append(("error", "CL_VALIDATION_TEST_WRONG_Q_COUNT", {"test_num": i_val + 1, "actual_count": len(single_test_data), "expected_count": expected_total}))
                test_passed_overall = False

        # Controlla intersezione se 2 test generati / Check intersection if 2 tests generated
        if test_passed_overall and len(test_data) == 2:
            q_set_test1 = set(q['original_index'] for q in test_data[0])
            q_set_test2 = set(q['original_index'] for q in test_data[1])
            intersection = q_set_test1.intersection(q_set_test2)
            if not intersection:
                validation_messages.append(("success", "CL_VALIDATION_TESTS_NO_INTERSECTION", {}))
            else:
                # Warning se c'è intersezione (atteso con fallback)
                # Warning if intersection exists (expected with fallback)
                validation_messages.append(("warning", "CL_VALIDATION_TESTS_INTERSECTION_WARNING", {"intersection": intersection}))
        elif len(test_data) != 2:
             # Errore se numero test non è 2 / Error if test count is not 2
             if not any(m[1] == "CL_VALIDATION_TESTS_WRONG_COUNT" for m in validation_messages):
                 validation_messages.append(("error", "CL_VALIDATION_TESTS_WRONG_COUNT", {"actual_count": len(test_data), "expected_count": test_num_tests}))
             test_passed_overall = False

        # Messaggio successo finale / Final success message
        if test_passed_overall and not any(m[0] == 'error' for m in validation_messages):
             validation_messages.append(("success", "CL_VALIDATION_COMPLETE_SUCCESS", {}))

    except Exception as e_val:
        # Errore imprevisto / Unexpected error
        validation_messages.append(("error", "CL_VALIDATION_UNEXPECTED_ERROR", {"error": str(e_val)}))

    return validation_messages
