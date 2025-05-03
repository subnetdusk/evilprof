# core_logic.py (Quieter version - Cleaned Indentation)
import random
import math
import heapq

# Funzione WRSwOR (invariata)
def weighted_random_sample_without_replacement(population, weights, k):
    n = len(population)
    if k < 0: raise ValueError("k non può essere negativo")
    if k == 0: return []
    if k > n: raise ValueError(f"k ({k}) > dimensione popolazione ({n})")
    if n != len(weights): raise ValueError("Lunghezze popolazione e pesi non coincidono")
    valid_indices = [i for i, w in enumerate(weights) if isinstance(w, (int, float)) and w > 0]
    if k > len(valid_indices): raise ValueError(f"k ({k}) è maggiore del numero di elementi con peso positivo ({len(valid_indices)})")
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

# Logica Generazione Test (Meno Verbosa)
def generate_all_tests_data(mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback):
    """
    Genera dati test. Chiama status_callback solo per warning/error critici
    (es. fallback, diversità limitata, errori campionamento).
    Restituisce (lista_dati_test, lista_messaggi_finali).
    """
    total_mc = len(mc_questions); total_open = len(open_questions)
    all_tests_question_data = []
    final_messages = [] # Raccoglie solo warning/error da restituire
    fallback_activated_ever = False # Traccia se il fallback è mai stato attivato

    mc_by_index = {q['original_index']: q for q in mc_questions}
    open_by_index = {q['original_index']: q for q in open_questions}
    last_used_mc = {idx: 0 for idx in mc_by_index.keys()}
    last_used_oe = {idx: 0 for idx in open_by_index.keys()}
    prev_mc_indices = set(); prev_open_indices = set()

    for i in range(1, num_tests + 1):
        # NON chiamare callback per progresso generazione test / DO NOT call callback for test generation progress
        # status_callback("info", "CL_GENERATING_TEST_DATA", current_test=i, total_tests=num_tests)
        current_test_data_unshuffled = []; selected_mc_indices_current = set(); selected_open_indices_current = set()
        fallback_active_this_test = False # Traccia fallback per questo specifico test

        # --- Selezione Scelta Multipla ---
        if num_mc_q > 0:
            candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
            if len(candidate_mc_indices) < num_mc_q:
                fallback_active_this_test = True
                fallback_activated_ever = True
                # MANTIENI questo warning perché è importante / KEEP this warning as it's important
                status_callback("warning", "CL_FALLBACK_MC_WARNING", test_num=i, candidates=len(candidate_mc_indices), total=total_mc)
                try: sampled_mc_indices = random.sample(list(mc_by_index.keys()), num_mc_q)
                except ValueError:
                    # Errore critico / Critical error
                    final_messages.append(("error", "CL_CRITICAL_SAMPLING_ERROR_MC", {"test_num": i, "k": num_mc_q, "n": total_mc}))
                    return None, final_messages
            else:
                weights_mc = [i - last_used_mc[idx] + 1 for idx in candidate_mc_indices]
                try: sampled_mc_indices = weighted_random_sample_without_replacement(candidate_mc_indices, weights_mc, num_mc_q)
                except ValueError as e:
                     # Errore critico / Critical error
                     final_messages.append(("error", "CL_CRITICAL_WRSWOR_ERROR_MC", {"test_num": i, "error": str(e)}))
                     return None, final_messages
            selected_mc_indices_current = set(sampled_mc_indices)
            for idx in selected_mc_indices_current: current_test_data_unshuffled.append(mc_by_index[idx]); last_used_mc[idx] = i

        # --- Selezione Aperte ---
        if num_open_q > 0:
            candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
            if len(candidate_oe_indices) < num_open_q:
                fallback_active_this_test = True
                fallback_activated_ever = True
                # MANTIENI questo warning / KEEP this warning
                status_callback("warning", "CL_FALLBACK_OE_WARNING", test_num=i, candidates=len(candidate_oe_indices), total=total_open)
                try: sampled_oe_indices = random.sample(list(open_by_index.keys()), num_open_q)
                except ValueError:
                     # Errore critico / Critical error
                     final_messages.append(("error", "CL_CRITICAL_SAMPLING_ERROR_OE", {"test_num": i, "k": num_open_q, "n": total_open}))
                     return None, final_messages
            else:
                weights_oe = [i - last_used_oe[idx] + 1 for idx in candidate_oe_indices]
                try: sampled_oe_indices = weighted_random_sample_without_replacement(candidate_oe_indices, weights_oe, num_open_q)
                except ValueError as e:
                     # Errore critico / Critical error
                     final_messages.append(("error", "CL_CRITICAL_WRSWOR_ERROR_OE", {"test_num": i, "error": str(e)}))
                     return None, final_messages
            selected_open_indices_current = set(sampled_oe_indices)
            for idx in selected_open_indices_current: current_test_data_unshuffled.append(open_by_index[idx]); last_used_oe[idx] = i

        random.shuffle(current_test_data_unshuffled)
        all_tests_question_data.append(current_test_data_unshuffled)
        prev_mc_indices = selected_mc_indices_current; prev_open_indices = selected_open_indices_current

    # --- Messaggi Finali (solo warning/error importanti) ---
    if fallback_activated_ever:
         final_messages.append(("error", "CL_FINAL_FALLBACK_ACTIVE", {})) # Questo è un errore/warning importante
    else:
        # Mostra warning diversità limitata solo se fallback NON attivo
        # Show limited diversity warning only if fallback was NOT active
        if num_mc_q > 0 and total_mc < 3 * num_mc_q:
             final_messages.append(("warning", "CL_FINAL_LOW_DIVERSITY_MC", {"total_mc": total_mc, "k": num_mc_q, "three_k": 3 * num_mc_q}))
        if num_open_q > 0 and total_open < 3 * num_open_q:
             final_messages.append(("warning", "CL_FINAL_LOW_DIVERSITY_OE", {"total_open": total_open, "k": num_open_q, "three_k": 3 * num_open_q}))
        # Non aggiungere messaggio OK diversità / Do not add OK diversity message
        # if not fallback_activated_ever and not any(m[1].startswith("CL_FINAL_LOW_DIVERSITY") for m in final_messages):
        #      final_messages.append(("info", "CL_FINAL_OK_DIVERSITY", {"num_tests": len(all_tests_question_data)}))

    return all_tests_question_data, final_messages
