# file_handler.py (Gestisce sia CSV che XLSX)
import pandas as pd
import streamlit as st
import os # Necessario per controllare estensione file

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
    df = None # Inizializza DataFrame a None

    try:
        # Controlla l'estensione del file per usare il lettore corretto
        # Check file extension to use the correct reader
        _, file_extension = os.path.splitext(file_name)
        file_extension = file_extension.lower()

        # Usa cache sessione basata sul nome file
        # Use session cache based on filename
        if 'processed_filename' not in st.session_state or st.session_state.processed_filename != file_name:
            # status_callback("info", "FH_READING_FILE", filename=file_name) # Messaggio generico lettura

            if file_extension in ['.xlsx', '.xls']:
                excel_df = pd.read_excel(uploaded_file, header=None)
                # Converti tutto in stringa subito per consistenza
                # Convert everything to string immediately for consistency
                df = excel_df.fillna('').astype(str)
            elif file_extension == '.csv':
                # Prova con virgola, poi punto e virgola come delimitatori comuni
                # Try comma, then semicolon as common delimiters
                try:
                    # Legge i bytes e decodifica, gestendo potenziali BOM
                    # Read bytes and decode, handling potential BOM
                    content_bytes = uploaded_file.getvalue()
                    content_str = content_bytes.decode('utf-8-sig') # utf-8-sig gestisce BOM
                    from io import StringIO
                    csv_file_like = StringIO(content_str)
                    csv_df = pd.read_csv(csv_file_like, header=None, sep=',', skipinitialspace=True)
                    df = csv_df.fillna('').astype(str)
                except Exception as e_comma: # Se fallisce con virgola, prova punto e virgola
                    try:
                        content_bytes = uploaded_file.getvalue()
                        content_str = content_bytes.decode('utf-8-sig')
                        from io import StringIO
                        csv_file_like = StringIO(content_str)
                        csv_df = pd.read_csv(csv_file_like, header=None, sep=';', skipinitialspace=True)
                        df = csv_df.fillna('').astype(str)
                    except Exception as e_semicolon:
                        status_callback("error", "FH_CSV_READ_ERROR", filename=file_name, error=f"Comma: {e_comma}, Semicolon: {e_semicolon}")
                        return None, None, "FH_CSV_READ_ERROR" # Nuova chiave errore CSV
            else:
                status_callback("error", "FH_UNSUPPORTED_FORMAT", filename=file_name, extension=file_extension)
                return None, None, "FH_UNSUPPORTED_FORMAT" # Nuova chiave errore formato

            st.session_state.excel_df = df # Salva il DataFrame letto in sessione
            st.session_state.processed_filename = file_name
        else:
            # status_callback("info", "FH_USING_CACHE", file_name=file_name) # Silenziato
            df = st.session_state.excel_df # Recupera dalla sessione

        # --- Logica di analisi blocchi (invariata da qui in poi) ---
        all_questions = []
        blocks_summary = []
        current_block_id = 1
        current_block_questions = []
        current_block_type = None
        first_question_in_block = True

        # Aggiunge riga vuota virtuale
        df.loc[len(df)] = [""] * df.shape[1] # Usa stringa vuota per coerenza

        for index, row in df.iterrows():
            # Ora tutti i dati sono stringhe, controllo più semplice per vuoto
            # Now all data are strings, easier check for empty
            is_empty_row = all(s is None or str(s).strip() == "" for s in row)

            if is_empty_row:
                if current_block_questions:
                    if current_block_type is None:
                         current_block_type = 'Indeterminato'
                    blocks_summary.append({
                        'block_id': current_block_id,
                        'type': current_block_type,
                        'count': len(current_block_questions)
                    })
                    all_questions.extend(current_block_questions)
                current_block_id += 1
                current_block_questions = []
                current_block_type = None
                first_question_in_block = True
            else:
                row_list = [str(s).strip() for s in row] # Già stringhe, basta strip
                question_text = row_list[0]
                answers = [ans for ans in row_list[1:] if ans] # Filtra stringhe vuote

                if question_text:
                    # Determina tipo domanda (MC se >= 2 risposte)
                    # Determine question type (MC if >= 2 answers)
                    question_type = 'Scelta Multipla' if len(answers) >= 2 else 'Aperte'

                    if first_question_in_block:
                        current_block_type = question_type
                        first_question_in_block = False
                    elif question_type != current_block_type:
                        status_callback("warning", "FH_BLOCK_MIXED_TYPES", block_id=current_block_id, expected=current_block_type, found=question_type, row_num=index + 1)
                        continue

                    question_dict = {
                        'question': question_text,
                        'answers': answers if question_type == 'Scelta Multipla' else [],
                        'original_index': index,
                        'type': question_type,
                        'block_id': current_block_id
                    }
                    current_block_questions.append(question_dict)

        blocks_summary = [b for b in blocks_summary if b['count'] > 0]

        if not all_questions:
            status_callback("error", "FH_NO_VALID_QUESTIONS", filename=file_name)
            return None, None, "FH_NO_VALID_QUESTIONS"

        # status_callback("info", "FH_LOAD_COMPLETE_BLOCKS", count=len(all_questions), num_blocks=len(blocks_summary)) # Silenziato
        return all_questions, blocks_summary, None

    except Exception as e:
        status_callback("error", "FH_UNEXPECTED_ERROR", filename=file_name, error=str(e))
        if 'processed_filename' in st.session_state: del st.session_state['processed_filename']
        if 'excel_df' in st.session_state: del st.session_state['excel_df']
        return None, None, "FH_UNEXPECTED_ERROR"
