# core_logic.py (Aggiornato per i18n callbacks e return format)
import random
import math
import heapq # Ora importato qui direttamente dato che è usato solo da WRSwOR

# ================================================================
# Funzione Helper WRSwOR (invariata internamente)
# ================================================================
def weighted_random_sample_without_replacement(population, weights, k):
    # ... (codice interno della funzione WRSwOR rimane uguale) ...
    n = len(population)
    if k < 0: raise ValueError("k non può essere negativo")
    if k == 0: return []
    if k > n: raise ValueError(f"k ({k}) > dimensione popolazione ({n})")
    if n != len(weights): raise ValueError("Lunghezze popolazione e pesi non coincidono")
    valid_indices = [i for i, w in enumerate(weights) if isinstance(w, (int, float)) and w > 0]
    if k > len(valid_indices):
        raise ValueError(f"k ({k}) è maggiore del numero di elementi con peso positivo ({len(valid_indices)})")
    population_valid = [population[i] for i in valid_indices]
    weights_valid = [weights[i] for i in valid_indices]
    min_heap = []
    for i, item in enumerate(population_valid):
        weight = weights_valid[i]; u = random.uniform(0, 1); epsilon = 1e-9
        if u < epsilon: u = epsilon
        try: key = u**(1.0 / (weight + epsilon))
        except OverflowError: key = 0.0
        if len(min_heap) < k: heapq.heappush(min_heap, (key, item))
        elif key > min_heap[0][0]: heapq.heapreplace(min_heap, (key, item))
    return [item for key, item in min_heap]

# ================================================================
# Logica Principale Generazione Test (Aggiornata)
# ================================================================
def generate_all_tests_data(mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback):
    """
    Genera dati test, usa status_callback(type, key, **kwargs).
    Restituisce (lista_dati_test, lista_messaggi) dove lista_messaggi
    contiene tuple (type, key, kwargs_dict).
    """
    total_mc = len(mc_questions); total_open = len(open_questions)
    all_tests_question_data = []
    # Lista per messaggi finali nel formato (type, key, kwargs)
    final_messages = []
    fallback_activated = False

    mc_by_index = {q['original_index']: q for q in mc_questions}
    open_by_index = {q['original_index']: q for q in open_questions}
    last_used_mc = {idx: 0 for idx in mc_by_index.keys()}
    last_used_oe = {idx: 0 for idx in open_by_index.keys()}
    prev_mc_indices = set(); prev_open_indices = set()

    for i in range(1, num_tests + 1):
        # Usa chiave e kwargs per status callback
        status_callback("info", "CL_GENERATING_TEST_DATA", current_test=i, total_tests=num_tests)
        current_test_data_unshuffled = []; selected_mc_indices_current = set(); selected_open_indices_current = set()
        current_fallback_mc = False; current_fallback_oe = False

        # --- Selezione Scelta Multipla ---
        if num_mc_q > 0:
            candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
            if len(candidate_mc_indices) < num_mc_q:
                current_fallback_mc = True; fallback_activated = True
                # Usa chiave e kwargs per warning callback
                status_callback("warning", "CL_FALLBACK_MC_WARNING",
                                test_num=i, candidates=len(candidate_mc_indices), total=total_mc)
                try: sampled_mc_indices = random.sample(list(mc_by_index.keys()), num_mc_q)
                except ValueError:
                    # Aggiunge messaggio di errore critico alla lista finale
                    final_messages.append(("error", "CL_CRITICAL_SAMPLING_ERROR_MC", {"test_num": i, "k": num_mc_q, "n": total_mc}))
                    return None, final_messages # Errore fatale
            else:
                weights_mc = [i - last_used_mc[idx] + 1 for idx in candidate_mc_indices]
                try: sampled_mc_indices = weighted_random_sample_without_replacement(candidate_mc_indices, weights_mc, num_mc_q)
                except ValueError as e:
                     final_messages.append(("error", "CL_CRITICAL_WRSWOR_ERROR_MC", {"test_num": i, "error": str(e)}))
                     return None, final_messages

            selected_mc_indices_current = set(sampled_mc_indices)
            for idx in selected_mc_indices_current: current_test_data_unshuffled.append(mc_by_index[idx]); last_used_mc[idx] = i

        # --- Selezione Aperte ---
        if num_open_q > 0:
            candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
            if len(candidate_oe_indices) < num_open_q:
                current_fallback_oe = True; fallback_activated = True
                status_callback("warning", "CL_FALLBACK_OE_WARNING",
                                test_num=i, candidates=len(candidate_oe_indices), total=total_open)
                try: sampled_oe_indices = random.sample(list(open_by_index.keys()), num_open_q)
                except ValueError:
                     final_messages.append(("error", "CL_CRITICAL_SAMPLING_ERROR_OE", {"test_num": i, "k": num_open_q, "n": total_open}))
                     return None, final_messages
            else:
                weights_oe = [i - last_used_oe[idx] + 1 for idx in candidate_oe_indices]
                try: sampled_oe_indices = weighted_random_sample_without_replacement(candidate_oe_indices, weights_oe, num_open_q)
                except ValueError as e:
                     final_messages.append(("error", "CL_CRITICAL_WRSWOR_ERROR_OE", {"test_num": i, "error": str(e)}))
                     return None, final_messages

            selected_open_indices_current = set(sampled_oe_indices)
            for idx in selected_open_indices_current: current_test_data_unshuffled.append(open_by_index[idx]); last_used_oe[idx] = i

        random.shuffle(current_test_data_unshuffled)
        all_tests_question_data.append(current_test_data_unshuffled)
        prev_mc_indices = selected_mc_indices_current; prev_open_indices = selected_open_indices_current

    # --- Messaggi Finali (formato [type, key, kwargs]) ---
    if fallback_activated:
         final_messages.append(("error", "CL_FINAL_FALLBACK_ACTIVE", {}))
    else:
        if num_mc_q > 0 and total_mc < 3 * num_mc_q:
             final_messages.append(("warning", "CL_FINAL_LOW_DIVERSITY_MC", {"total_mc": total_mc, "k": num_mc_q, "three_k": 3 * num_mc_q}))
        if num_open_q > 0 and total_open < 3 * num_open_q:
             final_messages.append(("warning", "CL_FINAL_LOW_DIVERSITY_OE", {"total_open": total_open, "k": num_open_q, "three_k": 3 * num_open_q}))
        if not fallback_activated and not any(m[1].startswith("CL_FINAL_LOW_DIVERSITY") for m in final_messages):
             final_messages.append(("info", "CL_FINAL_OK_DIVERSITY", {"num_tests": len(all_tests_question_data)}))

    return all_tests_question_data, final_messages


# ================================================================
# Logica Test di Validazione (Aggiornata)
# ================================================================
def run_validation_test(all_questions, status_callback):
    """
    Esegue test, usa status_callback(type, key, **kwargs).
    Restituisce lista di tuple (type, key, kwargs_dict).
    """
    # Lista per messaggi nel formato (type, key, kwargs)
    validation_messages = []
    test_num_tests = 2; test_num_mc = 2; test_num_open = 1
    # Usa status_callback con chiave e kwargs
    status_callback("info", "CL_GENERATING_TEST_DATA", current_test=1, total_tests=test_num_tests) # Messaggio generico inizio

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions); total_open = len(open_questions)

    # Controlli preliminari (aggiungono messaggi nel nuovo formato)
    if total_mc < test_num_mc: validation_messages.append(("error", "CL_VALIDATION_INSUFFICIENT_MC_ERROR", {"total": total_mc, "k": test_num_mc})); return validation_messages
    if total_open < test_num_open: validation_messages.append(("error", "CL_VALIDATION_INSUFFICIENT_OE_ERROR", {"total": total_open, "k": test_num_open})); return validation_messages
    if test_num_mc > 0 and total_mc <= test_num_mc : validation_messages.append(("warning", "CL_VALIDATION_INSUFFICIENT_MC_WARN", {"k": test_num_mc}))
    if test_num_open > 0 and total_open <= test_num_open: validation_messages.append(("warning", "CL_VALIDATION_INSUFFICIENT_OE_WARN", {"k": test_num_open}))

    try:
        # generate_all_tests_data ora ritorna messaggi nel nuovo formato
        test_data, test_gen_messages = generate_all_tests_data(
            mc_questions, open_questions, test_num_tests, test_num_mc, test_num_open, status_callback
        )
        # Aggiunge i messaggi della generazione a quelli della validazione
        validation_messages.extend(test_gen_messages)

        if test_data is None or len(test_data) != test_num_tests:
            # Aggiunge errore nel nuovo formato se non già presente da test_gen_messages
            if not any(m[1] == "CL_VALIDATION_TEST_FAILED_GENERATION" for m in validation_messages):
                 validation_messages.append(("error", "CL_VALIDATION_TEST_FAILED_GENERATION", {}))
            return validation_messages

        status_callback("info", "CL_VALIDATION_RUNNING", num_tests_generated=len(test_data))

        test_passed_overall = True
        for i_val, single_test_data in enumerate(test_data):
            expected_total = test_num_mc + test_num_open
            if len(single_test_data) != expected_total:
                validation_messages.append(("error", "CL_VALIDATION_TEST_WRONG_Q_COUNT", {"test_num": i_val + 1, "actual_count": len(single_test_data), "expected_count": expected_total}))
                test_passed_overall = False

        if test_passed_overall and len(test_data) == 2:
            q_set_test1 = set(q['original_index'] for q in test_data[0])
            q_set_test2 = set(q['original_index'] for q in test_data[1])
            intersection = q_set_test1.intersection(q_set_test2)
            if not intersection:
                validation_messages.append(("success", "CL_VALIDATION_TESTS_NO_INTERSECTION", {}))
            else:
                validation_messages.append(("warning", "CL_VALIDATION_TESTS_INTERSECTION_WARNING", {"intersection": intersection}))
        elif len(test_data) != 2:
             # Aggiunge errore nel nuovo formato se non già presente
             if not any(m[1] == "CL_VALIDATION_TESTS_WRONG_COUNT" for m in validation_messages):
                 validation_messages.append(("error", "CL_VALIDATION_TESTS_WRONG_COUNT", {"actual_count": len(test_data), "expected_count": test_num_tests}))
             test_passed_overall = False

        if test_passed_overall:
            # Aggiunge messaggio successo finale se non ci sono errori (anche se ci sono warning)
            if not any(m[0] == 'error' for m in validation_messages):
                 validation_messages.append(("success", "CL_VALIDATION_COMPLETE_SUCCESS", {}))

    except Exception as e_val:
        # Aggiunge errore imprevisto nel nuovo formato
        validation_messages.append(("error", "CL_VALIDATION_UNEXPECTED_ERROR", {"error": str(e_val)}))

    return validation_messages
