# app.py
import streamlit as st
from core_logic import weighted_sample_without_replacement # Importa la funzione logica
from utils import parse_input_list # Importa la funzione di utilità

st.set_page_config(layout="wide") 

st.title("Campionamento Ponderato Senza Reinserimento")

st.write("""
Questa applicazione seleziona un numero specificato di elementi unici (k)
da una popolazione data, utilizzando un campionamento ponderato. Gli elementi
con un peso maggiore hanno una probabilità più alta di essere selezionati.
""")

st.sidebar.header("Input Dati")

# Input per la popolazione
population_str = st.sidebar.text_area(
    "Popolazione (elementi separati da virgola)",
    "A, B, C, D, E, F, G"
)

# Input per i pesi
weights_str = st.sidebar.text_area(
    "Pesi (numeri separati da virgola, nello stesso ordine della popolazione)",
    "10, 1, 5, 8, 12, 3, 7"
)

# Input per k
k_input = st.sidebar.number_input(
    "Numero di elementi da campionare (k)",
    min_value=0,
    value=3,
    step=1
)

# Bottone per eseguire il campionamento
if st.sidebar.button("Esegui Campionamento"):
    st.subheader("Risultati")

    # Pulisci e valida l'input della popolazione
    population, error_pop = parse_input_list(population_str, str)
    if error_pop:
        st.error(f"Errore nell'input della popolazione: {error_pop}")
        st.stop() # Interrompe l'esecuzione dello script se l'input non è valido

    # Pulisci e valida l'input dei pesi
    weights, error_weights = parse_input_list(weights_str, float) # Prova a convertire in float
    if error_weights:
        st.error(f"Errore nell'input dei pesi: {error_weights}")
        st.stop()

    # Controlli di coerenza di base
    if not population:
        st.warning("Inserisci almeno un elemento nella popolazione.")
        st.stop()
    if len(population) != len(weights):
        st.error(f"Il numero di elementi nella popolazione ({len(population)}) non corrisponde al numero di pesi ({len(weights)}).")
        st.stop()

    k = int(k_input) # Assicurati che k sia intero (number_input dovrebbe già garantirlo)

    # Esegui il campionamento chiamando la funzione dal modulo core_logic
    try:
        sampled_elements = weighted_sample_without_replacement(population, weights, k)

        st.success(f"Campionamento di {k} elementi completato:")
        if sampled_elements:
             # Mostra i risultati in modo più leggibile
             st.dataframe({'Elementi Campionati': sampled_elements})
             # O usa st.write se preferisci una lista semplice
             # st.write(sampled_elements)
        else:
             st.info("Nessun elemento campionato (k=0 o input vuoto).")

    except (ValueError, TypeError) as e:
        st.error(f"Errore durante il campionamento: {e}")
    except Exception as e:
        st.error(f"Si è verificato un errore inaspettato: {e}")
        # Potresti voler loggare l'errore completo per il debug
        # import traceback
        # st.text(traceback.format_exc())

else:
    st.info("Inserisci i dati nella sidebar e premi 'Esegui Campionamento'.")
