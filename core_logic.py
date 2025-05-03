# core_logic.py
import random
import math
import heapq

def weighted_sample_without_replacement(population, weights, k):
    """
    Seleziona k elementi unici da una popolazione data, senza reinserimento,
    utilizzando un campionamento ponderato. La probabilità di selezione di ciascun
    elemento è influenzata dal peso corrispondente. Implementa l'algoritmo
    basato su chiavi esponenziali (variante di Efraimidis & Spirakis) per efficienza.

    Args:
        population: Lista o set di elementi da cui campionare.
        weights: Lista di pesi numerici corrispondenti agli elementi in population.
                 Pesi maggiori aumentano la probabilità di selezione.
        k: Numero di elementi unici da selezionare.

    Returns:
        Lista di k elementi campionati dalla popolazione.

    Raises:
        ValueError: Se k è maggiore della dimensione della popolazione, se le lunghezze
                    di population e weights non coincidono, se k è negativo,
                    o se non ci sono elementi con peso positivo sufficienti
                    per campionare k elementi.
        TypeError: Se i pesi non sono numerici o se qualche peso è negativo.
    """
    if not isinstance(k, int) or k < 0:
        raise ValueError("k deve essere un intero non negativo.")
    if len(population) != len(weights):
        raise ValueError("Le lunghezze di 'population' e 'weights' devono coincidere.")
    if k > len(population):
        raise ValueError("k non può essere maggiore della dimensione della popolazione.")
    if k == 0:
        return []

    # Controlla la validità dei pesi e filtra elementi con peso zero o negativo
    valid_items = []
    for item, weight in zip(population, weights):
        if not isinstance(weight, (int, float)):
            raise TypeError(f"Il peso '{weight}' per l'elemento '{item}' non è numerico.")
        if weight < 0:
             raise TypeError(f"Il peso '{weight}' per l'elemento '{item}' non può essere negativo.")
        if weight > 0:
            valid_items.append((item, weight))

    if k > len(valid_items):
         raise ValueError(f"k ({k}) è maggiore del numero di elementi con peso positivo ({len(valid_items)}).")

    # Algoritmo A-ExpJ (Efraimidis & Spirakis)
    # Calcola una chiave per ogni elemento valido: key = random.random()**(1/weight)
    # Usa un min-heap per tenere traccia dei k elementi con le chiavi più grandi
    min_heap = []
    for item, weight in valid_items:
        key = random.uniform(0, 1) ** (1.0 / weight)

        if len(min_heap) < k:
            heapq.heappush(min_heap, (key, item))
        elif key > min_heap[0][0]: # Se la chiave è maggiore della più piccola nel heap
            heapq.heapreplace(min_heap, (key, item)) # Sostituisci il più piccolo

    # Estrai gli elementi dall'heap (che ora contiene i k elementi con le chiavi più alte)
    return [item for key, item in min_heap]
