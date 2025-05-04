# file_handler.py
import pandas as pd
import streamlit as st
import os

def load_questions_from_excel(uploaded_file, status_callback):
    """
    Carica domande/risposte da file Excel (.xlsx, .xls) o CSV (.csv).
    Rileva blocchi separati da righe vuote e determina il tipo di ogni blocco.
    Chiama status_callback solo per errori o warning significativi.
    Restituisce:
        - all_questions: Lista di tutti i dizionari domanda, ognuno con 'block_id' e 'type'.
        - blocks_summary: Lista di dizionari che descrivono ogni blocco {'block_id', 'type', 'count'}.
        - error_key: Chiave errore (str) o None se successo.
    """
    if uploaded_file is None:
        return None, None, "UPLOAD_FIRST_WARNING"

    file_name = uploaded_file.name
    df = None

    try:
        _, file_extension = os.path.splitext(file_name)
        file_extension = file_extension.lower()

        # Legge sempre il file fornito
        if file_extension in ['.xlsx', '.xls']:
            excel_df = pd.read_excel(uploaded_file, header=None)
            df = excel_df.fillna('').astype(str)
        elif file_extension == '.csv':
            try:
                content_bytes = uploaded_file.getvalue()
                content_str = content_bytes.decode('utf-8-sig')
                from io import StringIO
                csv_file_like = StringIO(content_str)
                csv_df = pd.read_csv(csv_file_like, header=None, sep=',', skipinitialspace=True, lineterminator='\n') # Aggiunto lineterminator
                df = csv_df.fillna('').astype(str)
            except Exception as e_comma:
                try:
                    uploaded_file.seek(0)
                    content_bytes = uploaded_file.getvalue()
                    content_str = content_bytes.decode('utf-8-sig')
                    from io import StringIO
                    csv_file_like = StringIO(content_str)
                    csv_df = pd.read_csv(csv_file_like, header=None, sep=';', skipinitialspace=True, lineterminator='\n') # Aggiunto lineterminator
                    df = csv_df.fillna('').astype(str)
                except Exception as e_semicolon:
                    status_callback("error", "FH_CSV_READ_ERROR", filename=file_name, error=f"Comma: {e_comma}, Semicolon: {e_semicolon}")
                    return None, None, "FH_CSV_READ_ERROR"
        else:
            status_callback("error", "FH_UNSUPPORTED_FORMAT", filename=file_name, extension=file_extension)
            return None, None, "FH_UNSUPPORTED_FORMAT"

        # Logica di analisi blocchi
        all_questions = []
        blocks_summary = []
        current_block_id = 1
        current_block_questions = []
        current_block_type = None
        first_question_in_block = True

        # Aggiunge riga vuota virtuale alla fine
        if df is not None:
             df.loc[len(df)] = [""] * df.shape[1]
        else:
             # Se df è None dopo la lettura, c'è stato un errore non catturato prima?
             raise ValueError("Failed to read the uploaded file into a DataFrame.")


        for index, row in df.iterrows():
            # Controlla se la riga è vuota (considerando anche stringhe vuote)
            is_empty_row = all(s is None or str(s).strip() == "" for s in row)

            if is_empty_row:
                # Finalizza blocco precedente
                if current_block_questions:
                    if current_block_type is None: current_block_type = 'Indeterminato'
                    blocks_summary.append({
                        'block_id': current_block_id,
                        'type': current_block_type,
                        'count': len(current_block_questions)
                    })
                    all_questions.extend(current_block_questions)
                # Prepara per il prossimo blocco
                current_block_id += 1
                current_block_questions = []
                current_block_type = None
                first_question_in_block = True
            else:
                # Processa riga non vuota
                row_list = [str(s).strip() for s in row]
                question_text = row_list[0]
                answers = [ans for ans in row_list[1:] if ans]

                if question_text:
                    question_type = 'Scelta Multipla' if len(answers) >= 2 else 'Aperte'

                    if first_question_in_block:
                        current_block_type = question_type
                        first_question_in_block = False
                    elif question_type != current_block_type:
                        status_callback("warning", "FH_BLOCK_MIXED_TYPES", block_id=current_block_id, expected=current_block_type, found=question_type, row_num=index + 1)
                        # Decide se ignorare o accettare (qui ignora)
                        continue

                    question_dict = {
                        'question': question_text,
                        'answers': answers if current_block_type == 'Scelta Multipla' else [],
                        'original_index': index,
                        'type': current_block_type, # Usa il tipo del BLOCCO
                        'block_id': current_block_id
                    }
                    current_block_questions.append(question_dict)

        # Rimuove blocchi vuoti
        blocks_summary = [b for b in blocks_summary if b['count'] > 0]

        if not all_questions:
            status_callback("error", "FH_NO_VALID_QUESTIONS", filename=file_name)
            return None, None, "FH_NO_VALID_QUESTIONS"

        # Salva in sessione per evitare ricaricamenti non necessari *durante la stessa esecuzione*
        st.session_state.excel_df = df # Salva il DataFrame processato
        st.session_state.processed_filename = file_name # Salva nome file processato
        st.session_state.all_questions = all_questions # Salva lista domande processate
        st.session_state.blocks_summary = blocks_summary # Salva sommario blocchi

        return all_questions, blocks_summary, None

    except Exception as e:
        status_callback("error", "FH_UNEXPECTED_ERROR", filename=file_name, error=str(e))
        if 'processed_filename' in st.session_state: del st.session_state['processed_filename']
        if 'excel_df' in st.session_state: del st.session_state['excel_df']
        if 'all_questions' in st.session_state: del st.session_state['all_questions']
        if 'blocks_summary' in st.session_state: del st.session_state['blocks_summary']
        return None, None, "FH_UNEXPECTED_ERROR"
