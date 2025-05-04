# file_handler.py (Rilevamento blocchi e tipi)
import pandas as pd
import streamlit as st

def load_questions_from_excel(uploaded_file, status_callback):
    """
    Carica domande/risposte, rileva blocchi separati da righe vuote
    e determina il tipo di ogni blocco (Scelta Multipla o Aperte).
    Chiama status_callback solo per errori o warning significativi.
    Restituisce:
        - all_questions: Lista di tutti i dizionari domanda, ognuno con 'block_id' e 'type'.
        - blocks_summary: Lista di dizionari che descrivono ogni blocco {'block_id', 'type', 'count'}.
        - error_key: Chiave errore (str) o None se successo.

    Loads questions/answers, detects blocks separated by empty rows,
    and determines the type of each block (Multiple Choice or Open-Ended).
    Calls status_callback only for significant errors or warnings.
    Returns:
        - all_questions: List of all question dicts, each with 'block_id' and 'type'.
        - blocks_summary: List of dicts describing each block {'block_id', 'type', 'count'}.
        - error_key: Error key (str) or None on success.
    """
    if uploaded_file is None:
        return None, None, "UPLOAD_FIRST_WARNING"

    file_name = uploaded_file.name
    try:
        # Usa cache sessione (logica invariata)
        if 'loaded_file_name' not in st.session_state or st.session_state.loaded_file_name != file_name:
            # status_callback("info", "FH_READING_EXCEL", file_name=file_name) # Silenziato
            excel_df = pd.read_excel(uploaded_file, header=None)
            st.session_state.excel_df = excel_df
            st.session_state.loaded_file_name = file_name
        else:
            # status_callback("info", "FH_USING_CACHE", file_name=file_name) # Silenziato
            excel_df = st.session_state.excel_df

        df = excel_df
        all_questions = []
        blocks_summary = []
        current_block_id = 1
        current_block_questions = []
        current_block_type = None # Determinato dalla prima domanda del blocco
        first_question_in_block = True

        # Aggiunge una riga vuota virtuale alla fine per processare l'ultimo blocco
        # Add a virtual empty row at the end to process the last block
        df.loc[len(df)] = [None] * df.shape[1]

        for index, row in df.iterrows():
            # Controlla se la riga è completamente vuota (o contiene solo NaN/None)
            # Check if the row is completely empty (or only NaN/None)
            is_empty_row = row.isnull().all() or all(s is None or str(s).strip() == "" for s in row)

            if is_empty_row:
                # Riga vuota: finalizza il blocco precedente se conteneva domande
                # Empty row: finalize the previous block if it contained questions
                if current_block_questions:
                    if current_block_type is None: # Se il blocco era vuoto o solo spazi
                         current_block_type = 'Indeterminato' # O gestisci come errore
                    blocks_summary.append({
                        'block_id': current_block_id,
                        'type': current_block_type,
                        'count': len(current_block_questions)
                    })
                    # Aggiunge le domande del blocco completato alla lista totale
                    # Add questions from the completed block to the total list
                    all_questions.extend(current_block_questions)

                # Prepara per il prossimo blocco / Prepare for the next block
                current_block_id += 1
                current_block_questions = []
                current_block_type = None
                first_question_in_block = True
            else:
                # Riga non vuota: processa la domanda / Non-empty row: process the question
                row_list = [str(item).strip() if pd.notna(item) else "" for item in row]
                question_text = row_list[0]
                answers = [ans for ans in row_list[1:] if ans]

                if question_text: # Processa solo se c'è testo nella domanda / Process only if there's question text
                    question_type = 'Scelta Multipla' if len(answers) >= 2 else 'Aperte'

                    # Determina/verifica il tipo del blocco alla prima domanda valida
                    # Determine/verify block type on the first valid question
                    if first_question_in_block:
                        current_block_type = question_type
                        first_question_in_block = False
                    elif question_type != current_block_type:
                        # Errore/Warning: Tipi misti nello stesso blocco!
                        # Error/Warning: Mixed types in the same block!
                        status_callback("warning", "FH_BLOCK_MIXED_TYPES", block_id=current_block_id, expected=current_block_type, found=question_type, row_num=index + 1)
                        # Decide se continuare ignorando la domanda o fermarsi
                        # Decide whether to continue ignoring the question or stop
                        continue # Ignora questa domanda / Ignore this question

                    # Crea il dizionario domanda / Create question dictionary
                    question_dict = {
                        'question': question_text,
                        'answers': answers if question_type == 'Scelta Multipla' else [],
                        'original_index': index,
                        'type': question_type, # Tipo della domanda specifica / Specific question type
                        'block_id': current_block_id
                    }
                    current_block_questions.append(question_dict)

        # Rimuove eventuali blocchi vuoti dalla summary / Remove potential empty blocks from summary
        blocks_summary = [b for b in blocks_summary if b['count'] > 0]

        if not all_questions:
            status_callback("error", "FH_NO_VALID_QUESTIONS", filename=file_name)
            return None, None, "FH_NO_VALID_QUESTIONS"

        # status_callback("info", "FH_LOAD_COMPLETE_BLOCKS", count=len(all_questions), num_blocks=len(blocks_summary)) # Silenziato
        return all_questions, blocks_summary, None

    except Exception as e:
        status_callback("error", "FH_UNEXPECTED_ERROR", filename=file_name, error=str(e))
        if 'loaded_file_name' in st.session_state: del st.session_state['loaded_file_name']
        if 'excel_df' in st.session_state: del st.session_state['excel_df']
        return None, None, "FH_UNEXPECTED_ERROR"

