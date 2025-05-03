# file_handler.py (Aggiornato per i18n callbacks)
import pandas as pd
import streamlit as st

def load_questions_from_excel(uploaded_file, status_callback):
    """
    Carica domande/risposte da file Excel. Usa status_callback(type, key, **kwargs).
    Restituisce (lista_domande, None) o (None, chiave_errore).
    """
    if uploaded_file is None:
        # Non serve callback qui, l'errore viene gestito in app.py
        return None, "UPLOAD_FIRST_WARNING" # Chiave errore

    file_name = uploaded_file.name
    try:
        if 'loaded_file_name' not in st.session_state or st.session_state.loaded_file_name != file_name:
            # Usa chiave e kwargs per il callback
            status_callback("info", "FH_READING_EXCEL", file_name=file_name)
            excel_df = pd.read_excel(uploaded_file, header=None)
            st.session_state.excel_df = excel_df
            st.session_state.loaded_file_name = file_name
        else:
            status_callback("info", "FH_USING_CACHE", file_name=file_name)
            excel_df = st.session_state.excel_df

        df = excel_df
        questions_data = []
        mc_count_temp = 0
        oe_count_temp = 0
        warnings_data = [] # Raccoglie (key, kwargs) per i warning

        for index, row in df.iterrows():
            row_list = [str(item).strip() if pd.notna(item) else "" for item in row]
            question_text = row_list[0]
            answers = [ans for ans in row_list[1:] if ans]

            if question_text:
                if len(answers) >= 2:
                    question_type = 'multiple_choice'; mc_count_temp += 1
                    questions_data.append({'question': question_text, 'answers': answers, 'original_index': index, 'type': question_type})
                else:
                    question_type = 'open_ended'; oe_count_temp += 1
                    questions_data.append({'question': question_text, 'answers': [], 'original_index': index, 'type': question_type})
                    if len(answers) == 1:
                         # Aggiunge dati per il warning
                         warnings_data.append( ("warning", "FH_ROW_WARNING_ONE_ANSWER", {"q_text": question_text[:50], "row_num": index + 1}) )
            elif any(answers):
                 warnings_data.append( ("warning", "FH_ROW_WARNING_ANSWERS_ONLY", {"row_num": index + 1}) )

        # Invia i warning raccolti
        for msg_type, msg_key, msg_kwargs in warnings_data:
            status_callback(msg_type, msg_key, **msg_kwargs)

        if not questions_data:
            # Restituisce chiave errore
            return None, "FH_NO_VALID_QUESTIONS"

        status_callback("info", "FH_LOAD_COMPLETE", count=len(questions_data), mc_count=mc_count_temp, oe_count=oe_count_temp)
        return questions_data, None # Successo: dati e nessuna chiave errore

    except Exception as e:
        error_key = "FH_UNEXPECTED_ERROR"
        status_callback("error", error_key, file_name=file_name, error=str(e))
        if 'loaded_file_name' in st.session_state: del st.session_state['loaded_file_name']
        if 'excel_df' in st.session_state: del st.session_state['excel_df']
        return None, error_key # Restituisce chiave errore
