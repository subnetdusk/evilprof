# utils.py
import streamlit as st 

def parse_input_list(input_str, data_type=str):
    """
    Converte una stringa separata da virgole in una lista,
    tentando di convertire ogni elemento al tipo specificato.
    Restituisce una lista vuota se l'input è vuoto.
    Gestisce gli errori di conversione.
    """
    if not input_str.strip():
        return [], None # Lista vuota, nessun errore

    items = []
    raw_items = [item.strip() for item in input_str.split(',')]
    for i, raw_item in enumerate(raw_items):
        if not raw_item: # Ignora elementi vuoti risultanti da virgole multiple es. "a,,b"
             continue
        try:
            items.append(data_type(raw_item))
        except ValueError:
            error_msg = (
                f"Errore: Impossibile convertire '{raw_item}' al tipo {data_type.__name__} "
                f"(elemento {i+1} nella lista inserita)."
            )
            return None, error_msg # Indica errore
    return items, None # Lista processata, nessun errore
