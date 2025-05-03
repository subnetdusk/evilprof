# core_logic.py
import random
import math

# ================================================================
# Funzione Helper WRSwOR
# ================================================================
def weighted_random_sample_without_replacement(population, weights, k):
    """
    Seleziona k elementi unici da una popolazione data, senza reinserimento,
    utilizzando un campionamento ponderato. (Implementazione A-ExpJ)

    Args:
        population: Lista di elementi (es. indici originali delle domande).
        weights: Lista di pesi numerici corrispondenti.
        k: Numero di elementi da selezionare.

    Returns:
        Lista di k elementi campionati.

    Raises:
        ValueError: Se k > len(population), len(population) != len(weights),
                    o non ci sono abbastanza elementi con peso > 0.
    """
    n = len(population)
    if k < 0: raise ValueError("k non può essere negativo")
    if k == 0: return []
    if k > n: raise ValueError(f"k ({k}) > dimensione popolazione ({n})")
    if n != len(weights): raise ValueError("Lunghezze popolazione e pesi non coincidono")

    # Filtra elementi con peso 0 o negativo (improbabile con la logica dei pesi usata, ma per sicurezza)
    # e gestisce il caso in cui non ci siano abbastanza elementi validi
    valid_indices = [i for i, w in enumerate(weights) if isinstance(w, (int, float)) and w > 0]
    if k > len(valid_indices):
        raise ValueError(f"k ({k}) è maggiore del numero di elementi con peso positivo ({len(valid_indices)})")

    population_valid = [population[i] for i in valid_indices]
    weights_valid = [weights[i] for i in valid_indices]

    # Algoritmo A-ExpJ (Efraimidis & Spirakis)
    # Calcola chiavi: key = random.random()**(1/weight)
    # Mantiene i k elementi con le chiavi più GRANDI (quindi usa un min-heap sui primi k trovati)
    import heapq # Importazione locale per mantenere il modulo pulito
    min_heap = [] # Conterrà tuple (key, element)

    for i, item in enumerate(population_valid):
        weight = weights_valid[i]
        u = random.uniform(0, 1)
        # Evita u = 0 per prevenire potenziali errori matematici
        epsilon = 1e-9 # Piccola costante per evitare log(0) o divisione per zero
        if u < epsilon: u = epsilon
        # Calcola la chiave. Aggiunge epsilon al peso per evitare divisione per zero se w=0 (anche se filtrato)
        try:
            key = u**(1.0 / (weight + epsilon))
        except OverflowError:
            # Assegna una chiave molto bassa in caso di overflow (improbabile con u tra 0 e 1)
            key = 0.0

        # Usa un min-heap per tenere traccia dei k elementi con le chiavi più grandi
        if len(min_heap) < k:
            heapq.heappush(min_heap, (key, item))
        elif key > min_heap[0][0]: # Se la chiave corrente è > della più piccola nel heap
            heapq.heapreplace(min_heap, (key, item)) # Rimpiazza la più piccola con la nuova

    # Estrae gli elementi (gli item corrispondenti alle k chiavi più grandi)
    return [item for key, item in min_heap]


# ================================================================
# Logica Principale Generazione Test
# ================================================================
def generate_all_tests_data(mc_questions, open_questions, num_tests, num_mc_q, num_open_q, status_callback):
    """
    Genera i dati per tutte le verifiche, gestendo la selezione
    ponderata (WRSwOR) con fallback a campionamento semplice.

    Args:
        mc_questions: Lista di dizionari domande a scelta multipla.
        open_questions: Lista di dizionari domande aperte.
        num_tests: Numero totale di verifiche da generare.
        num_mc_q: Numero domande MC per verifica.
        num_open_q: Numero domande aperte per verifica.
        status_callback: Funzione per inviare messaggi di stato/errore/warning.

    Returns:
        Una tupla: (lista_dati_test, lista_messaggi_finali)
        - lista_dati_test: Lista di liste, dove ogni sub-lista contiene i dizionari
                           delle domande per una singola verifica. None se errore critico.
        - lista_messaggi_finali: Lista di tuple (tipo_messaggio, testo_messaggio)
                                 accumulati durante la generazione (es. fallback, diversità).
    """
    total_mc = len(mc_questions)
    total_open = len(open_questions)
    all_tests_question_data = []
    final_messages = []
    fallback_activated = False

    # Dizionari per accesso rapido tramite indice originale e tracciamento ultimo uso
    mc_by_index = {q['original_index']: q for q in mc_questions}
    open_by_index = {q['original_index']: q for q in open_questions}
    last_used_mc = {idx: 0 for idx in mc_by_index.keys()}
    last_used_oe = {idx: 0 for idx in open_by_index.keys()}

    prev_mc_indices = set()
    prev_open_indices = set()

    for i in range(1, num_tests + 1):
        status_callback("info", f"⚙️ Generazione dati test {i}/{num_tests}...")
        current_test_data_unshuffled = []
        selected_mc_indices_current = set()
        selected_open_indices_current = set()
        current_fallback_mc = False
        current_fallback_oe = False

        # --- Selezione Scelta Multipla ---
        if num_mc_q > 0:
            candidate_mc_indices = list(mc_by_index.keys() - prev_mc_indices)
            # Fallback se non ci sono abbastanza candidati *diversi* dal test precedente
            if len(candidate_mc_indices) < num_mc_q:
                current_fallback_mc = True
                fallback_activated = True
                status_callback("warning", f"[Test {i}] Fallback attivo per Scelta Multipla: non abbastanza domande diverse ({len(candidate_mc_indices)}) rispetto al test precedente. Campiono da tutte ({total_mc}).")
                try:
                    # Campiona da *tutti* gli indici disponibili
                    sampled_mc_indices = random.sample(list(mc_by_index.keys()), num_mc_q)
                except ValueError:
                    # Questo errore non dovrebbe accadere se i controlli iniziali sono corretti
                    final_messages.append(("error", f"Errore Critico Test {i}: Impossibile campionare {num_mc_q} MC da {total_mc} totali."))
                    return None, final_messages
            else:
                # WRSwOR sui candidati disponibili
                weights_mc = [i - last_used_mc[idx] + 1 for idx in candidate_mc_indices] # Peso aumenta con "vecchiaia"
                try:
                    sampled_mc_indices = weighted_random_sample_without_replacement(candidate_mc_indices, weights_mc, num_mc_q)
                except ValueError as e:
                     final_messages.append(("error", f"Errore Critico Test {i} (WRSwOR MC): {e}"))
                     return None, final_messages

            selected_mc_indices_current = set(sampled_mc_indices)
            for idx in selected_mc_indices_current:
                current_test_data_unshuffled.append(mc_by_index[idx])
                last_used_mc[idx] = i # Aggiorna l'ultimo uso

        # --- Selezione Aperte ---
        if num_open_q > 0:
            candidate_oe_indices = list(open_by_index.keys() - prev_open_indices)
            # Fallback
            if len(candidate_oe_indices) < num_open_q:
                current_fallback_oe = True
                fallback_activated = True
                status_callback("warning", f"[Test {i}] Fallback attivo per Aperte: non abbastanza domande diverse ({len(candidate_oe_indices)}) rispetto al test precedente. Campiono da tutte ({total_open}).")
                try:
                    sampled_oe_indices = random.sample(list(open_by_index.keys()), num_open_q)
                except ValueError:
                    final_messages.append(("error", f"Errore Critico Test {i}: Impossibile campionare {num_open_q} Aperte da {total_open} totali."))
                    return None, final_messages
            else:
                # WRSwOR
                weights_oe = [i - last_used_oe[idx] + 1 for idx in candidate_oe_indices]
                try:
                    sampled_oe_indices = weighted_random_sample_without_replacement(candidate_oe_indices, weights_oe, num_open_q)
                except ValueError as e:
                     final_messages.append(("error", f"Errore Critico Test {i} (WRSwOR Aperte): {e}"))
                     return None, final_messages

            selected_open_indices_current = set(sampled_oe_indices)
            for idx in selected_open_indices_current:
                current_test_data_unshuffled.append(open_by_index[idx])
                last_used_oe[idx] = i

        # Mischia le domande all'interno del test corrente
        random.shuffle(current_test_data_unshuffled)
        all_tests_question_data.append(current_test_data_unshuffled)

        # Aggiorna gli indici usati per il prossimo ciclo
        prev_mc_indices = selected_mc_indices_current
        prev_open_indices = selected_open_indices_current

    # --- Messaggi Finali sulla Diversità ---
    if fallback_activated:
         final_messages.append(("error", "‼️ ATTENZIONE GENERALE: Il fallback è stato attivato per almeno un test. La diversità tra test *non* è garantita per tutti. Controllare i messaggi di warning specifici per i dettagli."))
    else:
        # Controlla la diversità potenziale (n < 3k) solo se il fallback NON è scattato
        if num_mc_q > 0 and total_mc < 3 * num_mc_q:
             final_messages.append(("warning", f"⚠️ Diversità Limitata (MC): Il totale domande ({total_mc}) è meno del triplo ({3*num_mc_q}) delle richieste ({num_mc_q}). Consigliato aumentare il pool di domande MC."))
        if num_open_q > 0 and total_open < 3 * num_open_q:
             final_messages.append(("warning", f"⚠️ Diversità Limitata (Aperte): Il totale domande ({total_open}) è meno del triplo ({3*num_open_q}) delle richieste ({num_open_q}). Consigliato aumentare il pool di domande Aperte."))
        if not final_messages: # Se non ci sono stati fallback o warning sulla diversità
             final_messages.append(("info", f"✅ Dati per {len(all_tests_question_data)} verifiche preparati (con diversità garantita)."))

    return all_tests_question_data, final_messages


# ================================================================
# Logica Test di Validazione (Semplificata)
# ================================================================
def run_validation_test(all_questions, status_callback):
    """
    Esegue un test di validazione semplificato generando 2 test
    e verificando se hanno domande in comune (dovrebbe accadere solo con fallback).

    Args:
        all_questions: Lista completa di tutte le domande caricate.
        status_callback: Funzione per inviare messaggi.

    Returns:
        Lista di tuple (tipo_messaggio, testo_messaggio) con i risultati.
    """
    validation_messages = []
    test_num_tests = 2
    test_num_mc = 2
    test_num_open = 1
    status_callback("info", f"Avvio test di validazione ({test_num_tests} verifiche, {test_num_mc} MC, {test_num_open} Aperte)...")

    mc_questions = [q for q in all_questions if q['type'] == 'multiple_choice']
    open_questions = [q for q in all_questions if q['type'] == 'open_ended']
    total_mc = len(mc_questions)
    total_open = len(open_questions)

    # Controlli preliminari per il test
    if total_mc < test_num_mc: validation_messages.append(("error", f"Test Fallito: Non abbastanza MC ({total_mc}) per test ({test_num_mc}).")); return validation_messages
    if total_open < test_num_open: validation_messages.append(("error", f"Test Fallito: Non abbastanza Aperte ({total_open}) per test ({test_num_open}).")); return validation_messages
    # Per testare la *non* ripetizione, servono più domande del necessario per un test
    if num_mc_q > 0 and total_mc <= test_num_mc : validation_messages.append(("warning", f"Test Warning: Servono >{test_num_mc} MC totali per testare efficacemente la non-ripetizione."))
    if num_open_q > 0 and total_open <= test_num_open: validation_messages.append(("warning", f"Test Warning: Servono >{test_num_open} Aperte totali per testare efficacemente la non-ripetizione."))


    try:
        test_data, test_gen_messages = generate_all_tests_data(
            mc_questions, open_questions, test_num_tests, test_num_mc, test_num_open, status_callback
        )
        validation_messages.extend(test_gen_messages) # Aggiunge messaggi dalla generazione

        if test_data is None or len(test_data) != test_num_tests:
            validation_messages.append(("error", "❌ Validazione Fallita: Errore durante la generazione dei dati di test."))
            return validation_messages

        status_callback("info", f"Validazione {len(test_data)} test generati...")

        test_passed_overall = True
        for i_val, single_test_data in enumerate(test_data):
            expected_total = test_num_mc + test_num_open
            if len(single_test_data) != expected_total:
                validation_messages.append(("error", f"❌ Validazione Fallita: Test {i_val+1} ha {len(single_test_data)} domande invece di {expected_total}."))
                test_passed_overall = False

        if test_passed_overall and len(test_data) == 2:
            q_set_test1 = set(q['original_index'] for q in test_data[0])
            q_set_test2 = set(q['original_index'] for q in test_data[1])
            intersection = q_set_test1.intersection(q_set_test2)

            if not intersection:
                validation_messages.append(("success", "✅ Validazione Passata: Test 1 e Test 2 non hanno domande in comune."))
            else:
                # È un warning perché può essere normale se il fallback è stato attivato
                validation_messages.append(("warning", f"⚠️ Validazione: Test 1 e Test 2 hanno domande in comune (indici: {intersection}). Atteso se il fallback è stato attivato durante il test."))

        elif len(test_data) != 2:
             validation_messages.append(("error", "❌ Validazione Fallita: Numero di test generati non corretto."))
             test_passed_overall = False

        if test_passed_overall:
             validation_messages.append(("success", "🎉 Test di validazione completato con successo (o con warning attesi)."))
        # else: # Gli errori specifici sono già stati aggiunti
        #     validation_messages.append(("error", "⚠️ Test di validazione fallito o con errori. Controllare i messaggi."))

    except Exception as e_val:
        validation_messages.append(("error", f"❌ Errore imprevisto durante l'esecuzione del test di validazione: {e_val}"))

    return validation_messages
