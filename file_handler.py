# file_handler.py
import pandas as pd
import streamlit as st # Necessario per st.session_state e potenzialmente messaggi di errore/warning diretti

def load_questions_from_excel(uploaded_file, status_callback):
    """
    Carica domande e risposte da un file Excel (UploadedFile Streamlit).
    Utilizza st.session_state per caching semplice e chiama status_callback per aggiornamenti.
    Restituisce la lista di dizionari delle domande o None in caso di errore.
    """
    if uploaded_file is None:
        return None, "Nessun file caricato."

    file_name = uploaded_file.name
    try:
        # Usa session_state per evitare di ricaricare lo stesso file continuamente
        if 'loaded_file_name' not in st.session_state or st.session_state.loaded_file_name != file_name:
            status_callback(f"info", f"⏳ Lettura file Excel: {file_name}...")
            # Legge direttamente dai bytes del file caricato
            excel_df = pd.read_excel(uploaded_file, header=None)
            st.session_state.excel_df = excel_df # Salva il DataFrame in sessione
            st.session_state.loaded_file_name = file_name # Salva il nome del file caricato
        else:
            status_callback(f"info", f"ℹ️ Utilizzo dati già caricati per: {file_name}")
            excel_df = st.session_state.excel_df # Recupera il DataFrame dalla sessione

        df = excel_df
        questions_data = []
        mc_count_temp = 0
        oe_count_temp = 0
        warnings = []

        for index, row in df.iterrows():
            # Pulisce la riga e gestisce valori NaN
            row_list = [str(item).strip() if pd.notna(item) else "" for item in row]
            question_text = row_list[0]
            answers = [ans for ans in row_list[1:] if ans] # Risposte non vuote

            if question_text:
                if len(answers) >= 2:
                    question_type = 'multiple_choice'
                    mc_count_temp += 1
                    questions_data.append({
                        'question': question_text,
                        'answers': answers,
                        'original_index': index,
                        'type': question_type
                    })
                else:
                    question_type = 'open_ended'
                    oe_count_temp += 1
                    questions_data.append({
                        'question': question_text,
                        'answers': [], # Le domande aperte non hanno risposte predefinite
                        'original_index': index,
                        'type': question_type
                    })
                    # Aggiunge warning se c'era una sola risposta (ora trattata come aperta)
                    if len(answers) == 1:
                         warnings.append(f"Attenzione: Domanda '{question_text[:50]}...' (riga Excel {index+1}) ha solo 1 risposta ed è stata trattata come Aperta.")
            elif any(answers):
                # Warning se ci sono risposte ma manca la domanda
                warnings.append(f"Attenzione: Riga Excel {index+1} ha risposte ma manca la domanda e sarà ignorata.")

        # Invia i warning raccolti tramite il callback
        for warning in warnings:
            status_callback("warning", warning)

        if not questions_data:
            return None, f"Errore: Nessuna domanda valida trovata nel file '{file_name}'."

        status_callback("info", f"✅ Dati caricati: {len(questions_data)} domande ({mc_count_temp} a scelta multipla, {oe_count_temp} aperte).")
        return questions_data, None # Ritorna i dati e nessun errore

    except Exception as e:
        error_message = f"Errore imprevisto durante la lettura del file Excel '{file_name}': {e}"
        status_callback("error", error_message)
        # Pulisce lo stato in caso di errore per forzare ricaricamento al prossimo tentativo
        if 'loaded_file_name' in st.session_state: del st.session_state['loaded_file_name']
        if 'excel_df' in st.session_state: del st.session_state['excel_df']
        return None, error_message
