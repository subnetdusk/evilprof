# core_logic.py 
import random
import math
import heapq

# ================================================================
# Funzione Helper WRSwOR (invariata)
# ================================================================
def weighted_random_sample_without_replacement(population, weights, k):
    """
    Seleziona k elementi unici da una popolazione data, senza reinserimento,
    utilizzando un campionamento ponderato. (Implementazione A-ExpJ)
    """
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

# ================================================================
# Logica Generazione Test basata su Blocchi
# ================================================================
# --- ASSICURATI CHE QUESTA FUNZIONE SIA DEFINITA CORRETTAMENTE ---
# --- MAKE SURE THIS FUNCTION IS DEFINED CORRECTLY ---
def generate_all_tests_data(all_questions_list, block_requests, num_tests, status_callback):
    """
    Genera i dati per i test selezionando un numero esatto di domande da blocchi specifici.
    Applica WRSwOR separatamente per ogni blocco.
    Args:
        all_questions_list: Lista completa di tutti i dizionari domanda (con 'block_id').
        block_requests: Dizionario {block_id: k_requested} con le richieste utente.
        num_tests: Numero di verifiche da generare.
        status_callback: Funzione per segnalare warning/error critici.
    Returns:
        (lista_dati_test, lista_messaggi_finali)
    """
    all_tests_question_data = []
    final_messages = [] # Solo warning/error critici
    fallback_activated_ever = False # Traccia se il fallback è mai stato attivato

    # Raggruppa le domande per block_id per accesso efficiente
    questions_by_block = {}
    for q in all_questions_list:
        block_id = q['block_id']
        if block_id not in questions_by_block:
            questions_by_block[block_id] = []
        questions_by_block[block_id].append(q)

    # Dizionario per mantenere lo stato WRSwOR per ogni blocco
    wors_state_per_block = {}
    for block_id, questions in questions_by_block.items():
        wors_state_per_block[block_id] = {
            'last_used_indices': set(),
            'questions': questions,
            'n_block': len(questions)
        }

    # Ciclo principale per generare ogni test
    for i_test in range(1, num_tests + 1):
        current_test_questions = []
        fallback_active_this_test = False

        # Itera sui blocchi richiesti dall'utente
        for block_id, k_requested in block_requests.items():
            if k_requested <= 0: continue

            block_state = wors_state_per_block.get(block_id)
            if not block_state or not block_state['questions']:
                final_messages.append(("error", "BLOCK_NOT_FOUND_OR_EMPTY", {"block_id": block_id}))
                continue

            block_questions = block_state['questions']
            last_used_indices_block = block_state['last_used_indices']
            n_block = block_state['n_block']
            block_question_indices = [q['original_index'] for q in block_questions]

            if k_requested > n_block:
                 final_messages.append(("error", "BLOCK_REQUEST_EXCEEDS_AVAILABLE", {"block_id": block_id, "k": k_requested, "n": n_block}))
                 continue

            # Applica WRSwOR all'interno del blocco
            candidate_indices = list(set(block_question_indices) - last_used_indices_block)
            selected_indices_for_block = []

            if len(candidate_indices) < k_requested:
                fallback_active_this_test = True
                fallback_activated_ever = True
                status_callback("warning", "BLOCK_FALLBACK_WARNING",
                                block_id=block_id, test_num=i_test,
                                candidates=len(candidate_indices), k=k_requested)
                candidate_indices = list(block_question_indices)
                try:
                    selected_indices_for_block = random.sample(candidate_indices, k_requested)
                except ValueError:
                    final_messages.append(("error", "BLOCK_CRITICAL_SAMPLING_ERROR", {"block_id": block_id, "k": k_requested, "n": len(candidate_indices)}))
                    continue
            else:
                weights = [1] * len(candidate_indices) # Pesi uguali per semplicità
                try:
                     selected_indices_for_block = weighted_random_sample_without_replacement(candidate_indices, weights, k_requested)
                except ValueError as e:
                     final_messages.append(("error", "BLOCK_WRSWOR_ERROR", {"block_id": block_id, "k": k_requested, "error": str(e)}))
                     continue

            questions_dict_in_block = {q['original_index']: q for q in block_questions}
            for idx in selected_indices_for_block:
                current_test_questions.append(questions_dict_in_block[idx])

            block_state['last_used_indices'] = set(selected_indices_for_block)

        random.shuffle(current_test_questions)
        all_tests_question_data.append(current_test_questions)

    # Aggiungi messaggio finale se fallback è avvenuto
    if fallback_activated_ever and not any(m[1] == "CL_FINAL_FALLBACK_ACTIVE" for m in final_messages):
         final_messages.append(("warning", "CL_FINAL_FALLBACK_ACTIVE", {})) # Segnalalo come warning

    return all_tests_question_data, final_messages

