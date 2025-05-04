# core_logic.py (Unified sampling logic: Simple Random if k >= n/2)
import random
import math
import heapq

# Funzione WRSwOR (invariata)
def weighted_random_sample_without_replacement(population, weights, k):
    n = len(population)
    if k < 0: raise ValueError("k non può essere negativo")
    if k == 0: return []
    if k >= n:
        shuffled_population = list(population)
        random.shuffle(shuffled_population)
        return shuffled_population
    if n != len(weights): raise ValueError("Lunghezze popolazione e pesi non coincidono")
    valid_indices = [i for i, w in enumerate(weights) if isinstance(w, (int, float)) and w > 0]
    if k > len(valid_indices): raise ValueError(f"k ({k}) > n. elementi con peso positivo ({len(valid_indices)})")
    population_valid = [population[i] for i in valid_indices]
    weights_valid = [weights[i] for i in valid_indices]
    if k >= len(population_valid):
         shuffled_valid = list(population_valid)
         random.shuffle(shuffled_valid)
         return shuffled_valid
    min_heap = []
    for i, item in enumerate(population_valid):
        weight = weights_valid[i]; u = random.uniform(1e-9, 1.0)
        try: key = u**(1.0 / (weight + 1e-9))
        except OverflowError: key = float('inf')
        except ZeroDivisionError: key = float('inf')
        if len(min_heap) < k: heapq.heappush(min_heap, (key, item))
        elif key > min_heap[0][0]: heapq.heapreplace(min_heap, (key, item))
    return [item for key, item in min_heap]

# Logica Generazione Test basata su Blocchi (con soglia n=2k per Simple Random)
def generate_all_tests_data(all_questions_list, block_requests, num_tests, status_callback):
    """
    Genera dati test. Usa Simple Random Sampling se k richiesto >= n_blocco / 2,
    altrimenti usa WRSwOR. Chiama status_callback solo per warning/error critici.
    Restituisce (lista_dati_test, lista_messaggi_finali).
    """
    all_tests_question_data = []
    final_messages = []
    fallback_activated_ever = False # Traccia fallback *solo* per WRSwOR

    questions_by_block = defaultdict(list)
    for q in all_questions_list:
        questions_by_block[q['block_id']].append(q)

    wors_state_per_block = {}
    for block_id, questions in questions_by_block.items():
        wors_state_per_block[block_id] = {
            'last_used_indices': set(),
            'questions': questions,
            'n_block': len(questions)
        }

    for i_test in range(1, num_tests + 1):
        current_test_questions = []

        for block_id, k_requested in block_requests.items():
            if k_requested <= 0: continue

            block_state = wors_state_per_block.get(block_id)
            if not block_state or not block_state['questions']:
                final_messages.append(("error", "BLOCK_NOT_FOUND_OR_EMPTY", {"block_id": block_id}))
                continue

            block_questions = block_state['questions']
            last_used_indices_block = block_state['last_used_indices']
            n_block = block_state['n_block']
            block_question_indices_set = set(q['original_index'] for q in block_questions)

            if k_requested > n_block:
                 final_messages.append(("error", "BLOCK_REQUEST_EXCEEDS_AVAILABLE", {"block_id": block_id, "k": k_requested, "n": n_block}))
                 continue

            selected_indices_for_block = []
            use_simple_random = (k_requested * 2 >= n_block) # Condizione n <= 2k

            if use_simple_random:
                # --- Usa Campionamento Casuale Semplice ---
                candidate_indices_simple = list(block_question_indices_set)
                try:
                    # Assicura k <= n
                    actual_k = min(k_requested, len(candidate_indices_simple))
                    if actual_k < k_requested: # Non dovrebbe succedere
                         final_messages.append(("warning", "BLOCK_K_ADJUSTED_IN_FALLBACK", {"block_id": block_id, "requested": k_requested, "actual": actual_k}))
                    selected_indices_for_block = random.sample(candidate_indices_simple, actual_k)
                    # Non resettare last_used_indices qui, WRSwOR lo farà se/quando verrà usato di nuovo per k < n/2
                    # Do not reset last_used_indices here, WRSwOR will handle it if/when used again for k < n/2
                except ValueError:
                    final_messages.append(("error", "BLOCK_CRITICAL_SAMPLING_ERROR", {"block_id": block_id, "k": k_requested, "n": len(candidate_indices_simple)}))
                    continue
            else:
                # --- Usa WRSwOR (k < n/2) ---
                candidate_indices_wrswor = list(block_question_indices_set - last_used_indices_block)
                if len(candidate_indices_wrswor) < k_requested:
                    # Fallback *all'interno* di WRSwOR
                    fallback_activated_ever = True
                    status_callback("warning", "BLOCK_FALLBACK_WARNING",
                                    block_id=block_id, test_num=i_test,
                                    candidates=len(candidate_indices_wrswor), k=k_requested)
                    candidate_indices_fallback = list(block_question_indices_set)
                    try:
                        actual_k = min(k_requested, len(candidate_indices_fallback))
                        if actual_k < k_requested:
                             final_messages.append(("warning", "BLOCK_K_ADJUSTED_IN_FALLBACK", {"block_id": block_id, "requested": k_requested, "actual": actual_k}))
                        selected_indices_for_block = random.sample(candidate_indices_fallback, actual_k)
                    except ValueError:
                        final_messages.append(("error", "BLOCK_CRITICAL_SAMPLING_ERROR", {"block_id": block_id, "k": k_requested, "n": len(candidate_indices_fallback)}))
                        continue
                else:
                    # WRSwOR normale
                    weights = [1] * len(candidate_indices_wrswor)
                    try:
                         selected_indices_for_block = weighted_random_sample_without_replacement(candidate_indices_wrswor, weights, k_requested)
                    except ValueError as e:
                         final_messages.append(("error", "BLOCK_WRSWOR_ERROR", {"block_id": block_id, "k": k_requested, "error": str(e)}))
                         continue
                # Aggiorna last_used solo quando si usa WRSwOR
                # Update last_used only when using WRSwOR
                block_state['last_used_indices'] = set(selected_indices_for_block)

            # Aggiunge domande selezionate
            questions_dict_in_block = {q['original_index']: q for q in block_questions}
            for idx in selected_indices_for_block:
                if idx in questions_dict_in_block:
                    current_test_questions.append(questions_dict_in_block[idx])
                else:
                    print(f"ERRORE GRAVE: Indice {idx} selezionato ma non trovato nel Blocco {block_id}")

        random.shuffle(current_test_questions)
        all_tests_question_data.append(current_test_questions)

    if fallback_activated_ever and not any(m[0] == 'error' for m in final_messages):
         final_messages.append(("warning", "CL_FINAL_FALLBACK_ACTIVE", {}))

    return all_tests_question_data, final_messages
