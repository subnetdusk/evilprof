# localization.py (Cleaned Indentation & Updated Keys)

TEXTS = {
    "it": {
        # Titoli e Intestazioni
        "PAGE_TITLE": "EvilProf 😈 - Per Blocchi",
        "MAIN_TITLE": "EvilProf 😈 - Generatore per Blocchi",
        "SUBHEADER_NEW": "Genera verifiche selezionando il numero esatto di domande per blocco dall'Excel.",
        "INSTRUCTIONS_HEADER": "ℹ️ Istruzioni e Preparazione File Excel (Logica a Blocchi)",
        "GENERATION_PARAMS_HEADER": "Parametri di Generazione",
        "VALIDATION_TEST_HEADER": "Test Funzionale",
        "OUTPUT_AREA_HEADER": "Output e Messaggi",
        "VALIDATION_RESULTS_HEADER": "--- Risultato Test Funzionale ---",
        "GENERATION_MESSAGES_HEADER": "--- Messaggi dalla Generazione ---",
        "FOOTER_TEXT": "EvilProf v1.1 (Blocchi) - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit",

        # Widget Sidebar
        "UPLOAD_LABEL": "1. Carica File Excel/CSV",
        "UPLOAD_HELP": "Trascina o seleziona il file (.xlsx, .xls, .csv) con le domande organizzate in blocchi separati da righe vuote.",
        "SUBJECT_LABEL": "2. Nome della Materia",
        "SUBJECT_HELP": "Apparirà nel titolo di ogni verifica.",
        "SUBJECT_DEFAULT": "Informatica",
        "NUM_TESTS_LABEL": "3. Numero di Verifiche da Generare",
        "NUM_TESTS_HELP": "Quante versioni diverse della verifica creare?",
        "BLOCK_REQUESTS_HEADER": "Domande per Blocco:",
        "BLOCK_REQUEST_LABEL": "N. Domande da Blocco {block_id} ({type}) (Max: {n})",
        "TOTAL_QUESTIONS_SELECTED": "Domande Totali Selezionate",
        "GENERATE_BUTTON_LABEL": "🚀 Genera Verifiche PDF",
        "VALIDATE_BUTTON_LABEL": "🧪 Esegui Test Funzionale",
        "VALIDATE_BUTTON_HELP_NEW": "Esegue l'analisi statistica Monte Carlo (usando 'test_set_4_by_12_questions.xlsx') sulla similarità dei test.",

        # Messaggi di Stato / Errori / Warning
        "WEASYPRINT_ERROR": "🚨 **Attenzione:** La libreria WeasyPrint non è disponibile o funzionante...",
        "IMAGE_CAPTION": "Esempio di struttura file Excel valida (con blocchi separati)",
        "IMAGE_NOT_FOUND_WARNING": "Nota: Immagine di esempio '{image_path}' non trovata.",
        "IMAGE_LOAD_ERROR": "Errore caricamento immagine '{image_path}': {error}",
        "VALIDATION_START": "Avvio Test Funzionale...",
        "GENERATION_START": "Avvio Generazione Verifiche...",
        "UPLOAD_FIRST_WARNING": "⚠️ Per favore, carica prima un file Excel/CSV.",
        "LOADING_DATA_SPINNER": "⏳ Analisi file e identificazione blocchi...",
        "LOAD_ERROR": "Errore caricamento dati: {error_msg}",
        "NO_VALID_QUESTIONS_ERROR": "Nessuna domanda valida trovata nel file caricato.",
        "TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS": "ERRORE: Non hai selezionato nessuna domanda dai blocchi.",
        "PARAMS_OK_INFO": "Parametri OK. Generazione di {num_tests} verifiche...",
        "CORRECT_ERRORS_ERROR": "Correggi gli errori nei parametri prima di generare.",
        "GENERATING_DATA_SPINNER": "⏳ Generazione verifiche...",
        "VALIDATION_LOGIC_SPINNER": "⏳ Esecuzione test funzionale...",
        "GENERATION_FAILED_ERROR": "❌ Generazione fallita a causa di errori critici: {error}",
        "DATA_READY_PDF_INFO": "Dati per {num_tests} verifiche pronti. Avvio generazione PDF...",
        "PDF_CREATION_SPINNER": "⏳ Creazione del file PDF in corso...",
        "PDF_SUCCESS": "✅ Generazione PDF completata!",
        "PDF_DOWNLOAD_BUTTON_LABEL": "📥 Scarica PDF Generato",
        "PDF_DOWNLOAD_BUTTON_HELP": "Clicca per scaricare il file '{pdf_filename}'",
        "PDF_GENERATION_ERROR": "❌ Errore durante la creazione del file PDF.",
        "INITIAL_INFO_NEW": "Carica un file Excel/CSV, specifica quante domande prendere da ogni blocco nella sidebar e premi 'Genera Verifiche PDF'.",
        "VALIDATION_NO_MESSAGES": "Il test funzionale non ha prodotto messaggi specifici.",

        # Testo Intro (AGGIORNATO CON CONDIZIONE WRSwOR)
        "INTRO_TEXT_NEW": """
EvilProf (Versione Blocchi) genera verifiche PDF selezionando un numero esatto di domande da blocchi definiti nel tuo file Excel o CSV.

**Caratteristiche:**

- **Input da Excel/CSV:** Carica un file `.xlsx`, `.xls` o `.csv`.
- **Struttura a Blocchi:** Organizza le domande in blocchi separati da **una riga completamente vuota**.
- **Tipi di Blocco:** Ogni blocco deve contenere **solo domande a scelta multipla** OPPURE **solo domande aperte**. L'app rileva automaticamente il tipo. Non mischiare i tipi nello stesso blocco.
- **Selezione Esatta:** Dopo aver caricato il file, potrai specificare nella sidebar **quante domande esatte (`k`)** vuoi selezionare da ciascun blocco identificato (che contiene `n` domande).
- **Randomizzazione e Diversità:**
    - Se per un blocco il numero totale di domande disponibili (`n`) è **strettamente maggiore** del doppio delle domande richieste (`k`) (cioè, **`n > 2k`**), l'applicazione userà un **Campionamento Ponderato (WRSwOR)** per selezionare le `k` domande da quel blocco. Questo metodo tenta di evitare la ripetizione immediata delle stesse domande *da quel blocco* nelle verifiche consecutive.
    - Se invece **`n <= 2k`** (cioè se chiedi la metà o più delle domande disponibili nel blocco), l'applicazione userà un **Campionamento Casuale Semplice** per selezionare le `k` domande da quel blocco, perdendo la garanzia di diversità tra test consecutivi per quel blocco.
    - Il fallback a campionamento casuale semplice può attivarsi anche per WRSwOR se le richieste (`k`) sono alte rispetto ai candidati *nuovi* disponibili in quel momento.
- **Output PDF:** Genera un singolo file PDF con le verifiche composte secondo le tue selezioni.

**Preparazione File Excel/CSV:**

1.  Inizia a inserire le domande del primo blocco (tutte MC o tutte OE) dalla riga 1.
    * **Colonna A (o prima colonna):** Testo della domanda.
    * **Colonne B, C,... (o successive, solo per MC):** Opzioni di risposta. Lasciare vuote per domande Aperte.
2.  Quando vuoi iniziare un nuovo blocco (di tipo uguale o diverso), **inserisci una riga completamente vuota**.
3.  Nella riga successiva a quella vuota, inizia a inserire le domande del nuovo blocco.
4.  Ripeti i passaggi 2 e 3 per tutti i blocchi desiderati.
5.  **Non inserire nomi di argomento o intestazioni di colonna.**

*Vedi immagine di esempio qui sotto.*
""",
        # Testi usati nel PDF
        "PDF_TEST_TITLE": "Verifica di {subject_name}",
        "PDF_NAME_LABEL": "Nome e Cognome:",
        "PDF_DATE_LABEL": "Data:",
        "PDF_CLASS_LABEL": "Classe:",
        "PDF_MISSING_QUESTION": "DOMANDA MANCANTE",
        "PDF_NO_OPTIONS": "<em>(Nessuna opzione di risposta fornita)</em>",

        # Messaggi file_handler
        "FH_READING_EXCEL": "⏳ Analisi file: {filename}...",
        "FH_USING_CACHE": "ℹ️ Utilizzo dati già analizzati per: {filename}",
        "FH_ROW_WARNING_ANSWERS_ONLY": "Attenzione: Riga {row_num} ha risposte ma manca la domanda e sarà ignorata.",
        "FH_ROW_WARNING_ONE_ANSWER": "Attenzione: Domanda '{q_text}' (riga {row_num}) ha solo 1 risposta ed è stata trattata come Aperta.",
        "FH_LOAD_COMPLETE_BLOCKS": "✅ File analizzato: {num_blocks} blocchi trovati ({count} domande totali).",
        "FH_NO_VALID_QUESTIONS": "Errore: Nessuna domanda valida trovata nel file '{filename}'.",
        "FH_UNEXPECTED_ERROR": "Errore imprevisto durante la lettura/analisi del file '{filename}': {error}",
        "FH_BLOCK_MIXED_TYPES": "⚠️ Attenzione Blocco {block_id}: Trovata domanda di tipo '{found}' (riga {row_num}), ma il blocco era stato identificato come '{expected}'. La domanda verrà ignorata.",
        "FH_CSV_READ_ERROR": "Errore lettura CSV '{filename}'. Controlla delimitatore (virgola/punto e virgola) e codifica. Dettagli: {error}",
        "FH_UNSUPPORTED_FORMAT": "ERRORE: Formato file non supportato '{extension}' per il file '{filename}'. Usare .xlsx, .xls o .csv.",

        # Messaggi core_logic
        "BLOCK_FALLBACK_WARNING": "[Blocco {block_id} - Test {test_num}] Fallback WRSwOR: non abbastanza domande nuove ({candidates} < {k}). Campiono da tutte ({total}) nel blocco.",
        "BLOCK_NOT_FOUND_OR_EMPTY": "ERRORE Interno: Blocco {block_id} richiesto ma non trovato o vuoto.",
        "BLOCK_REQUEST_EXCEEDS_AVAILABLE": "ERRORE Interno: Richieste {k} domande dal Blocco {block_id}, ma ne sono disponibili solo {n}.",
        "BLOCK_CRITICAL_SAMPLING_ERROR": "Errore Critico Campionamento Blocco {block_id}: Impossibile campionare {k} da {n} candidati.",
        "BLOCK_WRSWOR_ERROR": "Errore Critico WRSwOR Blocco {block_id} (k={k}): {error}",
        "CL_FINAL_FALLBACK_ACTIVE": "‼️ ATTENZIONE GENERALE: Il fallback WRSwOR è stato attivato per almeno un blocco durante la generazione. La diversità *all'interno* di quei blocchi potrebbe non essere garantita per tutti i test.",
        "BLOCK_K_ADJUSTED_IN_FALLBACK": "⚠️ Attenzione Blocco {block_id}: Richieste {requested} domande, ma solo {actual} disponibili durante il fallback. Numero adattato.",

        # Messaggi pdf_generator
        "PG_PDF_GENERATION_START": "⚙️ Inizio generazione PDF...",
        "PG_WEASYPRINT_UNAVAILABLE": "Libreria WeasyPrint non trovata o non funzionante. Impossibile generare PDF.",
        "PG_HTML_BUILDING": "⚙️ Costruzione documento HTML...",
        "PG_PDF_CONVERTING": "⚙️ Conversione HTML in PDF con WeasyPrint (potrebbe richiedere tempo)...",
        "PG_PDF_CONVERSION_COMPLETE": "⚙️ Conversione PDF completata.",
        "PG_WEASYPRINT_DEPENDENCY_ERROR": "ERRORE WeasyPrint: Dipendenze mancanti (GTK+/Pango/Cairo?). Dettagli: {error}",
        "PG_WEASYPRINT_OTHER_ERROR": "ERRORE durante la generazione PDF con WeasyPrint: {error}",

        # Chiavi per test.py (Test Statistici e Monte Carlo)
        "TEST_FILE_NOT_FOUND": "ERRORE: File di test '{filename}' non trovato. Assicurati che sia nella stessa cartella dell'app.",
        "TEST_LOADING_DATA": "Caricamento dati dal file di test '{filename}'...",
        "TEST_NO_QUESTIONS_FOUND": "ERRORE: Nessuna domanda valida trovata nel file di test '{filename}'.",
        "TEST_LOAD_SUCCESS": "Dati di test caricati: {count} domande ({mc} MC, {oe} OE).",
        "TEST_LOAD_ERROR": "ERRORE imprevisto durante il caricamento del file di test '{filename}': {error}",
        "TEST_ABORTED_LOAD_FAILED": "❌ Test annullato: impossibile caricare i dati di test.",
        "TEST_WRONG_QUESTION_COUNT": "ERRORE Dati Test: Trovate {mc} MC e {oe} OE domande, attese {expected} per tipo.",
        "TEST_WRONG_BLOCK_COUNT": "ERRORE Dati Test: Trovati {found} blocchi, attesi {expected}.",
        "TEST_WRONG_Q_PER_BLOCK_COUNT": "ERRORE Dati Test: Blocco {block_id} ha {found} domande, attese {expected}.",
        "STAT_TEST_K_INVALID": "ERRORE Test: k={k} richiesto non è valido per nessun blocco.",
        "STAT_TEST_GENERATION_FAILED_KPB": "❌ Fallita generazione sequenza test per k_per_block={k_per_block}.",
        "MC_TEST_UNIFIED_STARTING": "Avvio simulazione Monte Carlo ({num_runs} run, {num_k} valori k/blocco [{k_range}], {num_tests} test/seq)...",
        "MC_TEST_RUN_PROGRESS": "Progresso Monte Carlo: Run {current_run}/{total_runs}...",
        "MC_TEST_FAILED_FOR_KPB_IN_RUN": "⚠️ Fallita analisi per k/blocco={k_per_block} (Metodo: {method}) nella run {run}.",
        "MC_TEST_ALL_COMPLETE": "--- Simulazione Monte Carlo completata. ---",
        "STAT_TEST_EXCEL_CREATED": "✅ File Excel con risultati statistici '{filename}' creato.",
        "STAT_TEST_EXCEL_SAVE_ERROR": "❌ Errore durante il salvataggio del file Excel '{filename}': {error}",
        "STAT_TEST_NO_DATA_FOR_EXCEL": "⚠️ Nessun dato dettagliato raccolto per creare il file Excel.",
        "DOWNLOAD_STATS_EXCEL_LABEL": "📊 Scarica Risultati Statistici (.xlsx)",
        "DOWNLOAD_STATS_EXCEL_HELP": "Scarica il file Excel con l'analisi di similarità Dice (WRSwOR/Semplice) per distanza e k/blocco.",
        "CL_VALIDATION_UNEXPECTED_ERROR": "❌ Errore imprevisto durante l'esecuzione del test funzionale: {error}",
    },
    "en": {
        # Titles & Headers
        "PAGE_TITLE": "EvilProf 😈 - By Blocks",
        "MAIN_TITLE": "EvilProf 😈 - Block-Based Generator",
        "SUBHEADER_NEW": "Generate tests by selecting the exact number of questions per block from Excel.",
        "INSTRUCTIONS_HEADER": "ℹ️ Instructions & Excel File Preparation (Block Logic)",
        "GENERATION_PARAMS_HEADER": "Generation Parameters",
        "VALIDATION_TEST_HEADER": "Functional Test",
        # "SOURCE_CODE_HEADER": "Source Code", # Removed
        "OUTPUT_AREA_HEADER": "Output & Messages",
        "VALIDATION_RESULTS_HEADER": "--- Functional Test Results ---",
        "GENERATION_MESSAGES_HEADER": "--- Messages from Generation ---",
        "FOOTER_TEXT": "EvilProf v1.1 (Blocks) - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit",

        # Widget Sidebar
        "UPLOAD_LABEL": "1. Upload Excel/CSV File",
        "UPLOAD_HELP": "Drag and drop or select the Excel/CSV file (.xlsx, .xls, .csv) with questions organized in blocks separated by empty rows.",
        "SUBJECT_LABEL": "2. Subject Name",
        "SUBJECT_HELP": "Will appear in the title of each test.",
        "SUBJECT_DEFAULT": "Computer Science",
        "NUM_TESTS_LABEL": "3. Number of Tests to Generate",
        "NUM_TESTS_HELP": "How many different versions of the test to create?",
        "BLOCK_REQUESTS_HEADER": "Questions per Block:",
        "BLOCK_REQUEST_LABEL": "N. Questions from Block {block_id} ({type}) (Max: {n})",
        "TOTAL_QUESTIONS_SELECTED": "Total Questions Selected",
        "GENERATE_BUTTON_LABEL": "🚀 Generate PDF Tests",
        "VALIDATE_BUTTON_LABEL": "🧪 Run Functional Test",
        "VALIDATE_BUTTON_HELP_NEW": "Runs the Monte Carlo statistical analysis (using 'test_set_4_by_12_questions.xlsx') on test similarity.",
        # Source code download removed

        # Status / Error / Warning Messages
        "WEASYPRINT_ERROR": "🚨 **Warning:** The WeasyPrint library is not available or not functional. PDF generation is blocked...",
        "IMAGE_CAPTION": "Example of valid Excel file structure (with separated blocks)",
        "IMAGE_NOT_FOUND_WARNING": "Note: Example image '{image_path}' not found.",
        "IMAGE_LOAD_ERROR": "Error loading image '{image_path}': {error}",
        "VALIDATION_START": "Starting Functional Test...",
        "GENERATION_START": "Starting Test Generation...",
        "UPLOAD_FIRST_WARNING": "⚠️ Please upload an Excel/CSV file first.",
        "LOADING_DATA_SPINNER": "⏳ Analyzing file and identifying blocks...",
        "LOAD_ERROR": "Error loading data: {error_msg}",
        "NO_VALID_QUESTIONS_ERROR": "No valid questions found in the uploaded file.",
        "TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS": "ERROR: You haven't selected any questions from the blocks.",
        "PARAMS_OK_INFO": "Parameters OK. Generating {num_tests} tests...",
        "CORRECT_ERRORS_ERROR": "Please correct the parameter errors before generating.",
        "GENERATING_DATA_SPINNER": "⏳ Generating tests...",
        "VALIDATION_LOGIC_SPINNER": "⏳ Running functional test...",
        "GENERATION_FAILED_ERROR": "❌ Generation failed due to critical errors: {error}",
        "DATA_READY_PDF_INFO": "Data for {num_tests} tests ready. Starting PDF generation...",
        "PDF_CREATION_SPINNER": "⏳ Creating PDF file...",
        "PDF_SUCCESS": "✅ PDF Generation Complete!",
        "PDF_DOWNLOAD_BUTTON_LABEL": "📥 Download Generated PDF",
        "PDF_DOWNLOAD_BUTTON_HELP": "Click to download '{pdf_filename}'",
        "PDF_GENERATION_ERROR": "❌ Error during PDF creation.",
        "INITIAL_INFO_NEW": "Upload an Excel/CSV file, specify how many questions to take from each block in the sidebar, and press 'Generate PDF Tests'.",
        "VALIDATION_NO_MESSAGES": "The functional test produced no specific messages.",

        # Intro Text (UPDATED WITH WRSwOR CONDITION)
        "INTRO_TEXT_NEW": """
EvilProf (Block Version) generates PDF tests by selecting an exact number of questions from blocks defined in your Excel or CSV file.

**Features:**

- **Input from Excel/CSV:** Load an `.xlsx`, `.xls`, or `.csv` file.
- **Block Structure:** Organize questions into blocks separated by **a completely empty row**.
- **Block Types:** Each block must contain **only multiple-choice questions** OR **only open-ended questions**. The app detects the type automatically. Do not mix types within the same block.
- **Exact Selection:** After uploading the file, you can specify in the sidebar **exactly how many questions (`k`)** you want to select from each identified block (which contains `n` questions).
- **Randomization and Diversity:**
    - If, for a block, the total number of available questions (`n`) is **strictly greater** than twice the requested questions (`k`) (i.e., **`n > 2k`**), the application will use **Weighted Sampling (WRSwOR)** to select the `k` questions from that block. This method attempts to avoid immediate repetition of the same questions *from that block* in consecutive tests.
    - If **`n <= 2k`** (i.e., if you request half or more of the available questions in the block), the application will use **Simple Random Sampling** to select the `k` questions from that block, losing the diversity guarantee between consecutive tests for that block.
    - Fallback to simple random sampling may also occur for WRSwOR if requests (`k`) are high relative to the *new* available candidates at that moment.
- **PDF Output:** Generates a single PDF file with the tests composed according to your selections.

**Excel/CSV File Preparation:**

1.  Start entering questions for the first block (all MC or all OE) from row 1.
    * **Column A (or first column):** Question text.
    * **Columns B, C,... (or subsequent, MC Only):** Answer options. Leave empty for Open-Ended questions.
2.  When you want to start a new block, **insert a completely empty row**.
3.  On the row after the empty one, start entering the questions for the new block.
4.  Repeat steps 2 and 3 for all desired blocks.
5.  **Do not include topic names or column headers.**

*See example image below.*
""",
        # Texts used in PDF
        "PDF_TEST_TITLE": "Test for {subject_name}",
        "PDF_NAME_LABEL": "Name:",
        "PDF_DATE_LABEL": "Date:",
        "PDF_CLASS_LABEL": "Class:",
        "PDF_MISSING_QUESTION": "MISSING QUESTION",
        "PDF_NO_OPTIONS": "<em>(No answer options provided)</em>",

        # file_handler messages
        "FH_READING_EXCEL": "⏳ Analyzing file: {filename}...",
        "FH_USING_CACHE": "ℹ️ Using already analyzed data for: {filename}",
        "FH_ROW_WARNING_ANSWERS_ONLY": "Warning: Row {row_num} has answers but is missing the question and will be ignored.",
        "FH_ROW_WARNING_ONE_ANSWER": "Warning: Question '{q_text}' (row {row_num}) has only 1 answer and was treated as Open-Ended.",
        "FH_LOAD_COMPLETE_BLOCKS": "✅ File analyzed: {num_blocks} blocks found ({count} total questions).",
        "FH_NO_VALID_QUESTIONS": "Error: No valid questions found in file '{filename}'.",
        "FH_UNEXPECTED_ERROR": "Unexpected error while reading/analyzing file '{filename}': {error}",
        "FH_BLOCK_MIXED_TYPES": "⚠️ Warning Block {block_id}: Found question of type '{found}' (row {row_num}), but block was identified as '{expected}'. Question will be ignored.",
        "FH_CSV_READ_ERROR": "Error reading CSV '{filename}'. Check delimiter (comma/semicolon) and encoding. Details: {error}",
        "FH_UNSUPPORTED_FORMAT": "ERROR: Unsupported file format '{extension}' for file '{filename}'. Use .xlsx, .xls, or .csv.",

        # core_logic messages
        "BLOCK_FALLBACK_WARNING": "[Block {block_id} - Test {test_num}] WRSwOR Fallback: not enough new questions ({candidates} < {k}). Sampling from all ({total}) in block.",
        "BLOCK_NOT_FOUND_OR_EMPTY": "Internal ERROR: Block {block_id} requested but not found or empty.",
        "BLOCK_REQUEST_EXCEEDS_AVAILABLE": "Internal ERROR: Requested {k} questions from Block {block_id}, but only {n} are available.",
        "BLOCK_CRITICAL_SAMPLING_ERROR": "Critical Sampling Error Block {block_id}: Cannot sample {k} from {n} candidates.",
        "BLOCK_WRSWOR_ERROR": "Critical WRSwOR Error Block {block_id} (k={k}): {error}",
        "CL_FINAL_FALLBACK_ACTIVE": "‼️ GENERAL WARNING: WRSwOR fallback was activated for at least one block during generation. Diversity *within* those blocks might not be guaranteed for all tests.",
        "BLOCK_K_ADJUSTED_IN_FALLBACK": "⚠️ Warning Block {block_id}: Requested {requested} questions, but only {actual} available during fallback. Number adjusted.",

        # pdf_generator messages
        "PG_PDF_GENERATION_START": "⚙️ Starting PDF generation...",
        "PG_WEASYPRINT_UNAVAILABLE": "WeasyPrint library not found or not functional. Cannot generate PDF.",
        "PG_HTML_BUILDING": "⚙️ Building HTML document...",
        "PG_PDF_CONVERTING": "⚙️ Converting HTML to PDF with WeasyPrint (this may take time)...",
        "PG_PDF_CONVERSION_COMPLETE": "⚙️ PDF conversion complete.",
        "PG_WEASYPRINT_DEPENDENCY_ERROR": "ERROR WeasyPrint: Missing dependencies (GTK+/Pango/Cairo?). Details: {error}",
        "PG_WEASYPRINT_OTHER_ERROR": "ERROR during PDF generation with WeasyPrint: {error}",

        # Keys for test.py (Statistical Tests and Monte Carlo)
        "TEST_FILE_NOT_FOUND": "ERROR: Test file '{filename}' not found. Ensure it's in the same folder as the app.",
        "TEST_LOADING_DATA": "Loading data from test file '{filename}'...",
        "TEST_NO_QUESTIONS_FOUND": "ERROR: No valid questions found in test file '{filename}'.",
        "TEST_LOAD_SUCCESS": "Test data loaded: {count} questions ({mc} MC, {oe} OE).",
        "TEST_LOAD_ERROR": "Unexpected ERROR while loading test file '{filename}': {error}",
        "TEST_ABORTED_LOAD_FAILED": "❌ Test aborted: failed to load test data.",
        "TEST_WRONG_QUESTION_COUNT": "ERROR Test Data: Found {mc} MC and {oe} OE questions, expected {expected} of each.",
        "TEST_WRONG_BLOCK_COUNT": "ERROR Test Data: Found {found} blocks, expected {expected}.",
        "TEST_WRONG_Q_PER_BLOCK_COUNT": "ERROR Test Data: Block {block_id} has {found} questions, expected {expected}.",
        "STAT_TEST_K_INVALID": "ERROR Test: Requested k={k} is invalid for any block.",
        "STAT_TEST_GENERATION_FAILED_KPB": "❌ Failed test sequence generation for k_per_block={k_per_block}.",
        "MC_TEST_UNIFIED_STARTING": "Starting Monte Carlo simulation ({num_runs} runs, {num_k} k/block values [{k_range}], {num_tests} tests/seq)...",
        "MC_TEST_RUN_PROGRESS": "Monte Carlo Progress: Run {current_run}/{total_runs}...",
        "MC_TEST_FAILED_FOR_KPB_IN_RUN": "⚠️ Analysis failed for k/block={k_per_block} (Method: {method}) in run {run}.",
        "MC_TEST_ALL_COMPLETE": "--- Monte Carlo simulation completed. ---",
        "STAT_TEST_EXCEL_CREATED": "✅ Excel file with statistical results '{filename}' created.",
        "STAT_TEST_EXCEL_SAVE_ERROR": "❌ Error saving Excel file '{filename}': {error}",
        "STAT_TEST_NO_DATA_FOR_EXCEL": "⚠️ No detailed data collected to create the Excel file.",
        "DOWNLOAD_STATS_EXCEL_LABEL": "📊 Download Statistical Results (.xlsx)",
        "DOWNLOAD_STATS_EXCEL_HELP": "Download the Excel file with the Dice similarity analysis (WRSwOR/Simple) by distance and k/block.",
        "CL_VALIDATION_UNEXPECTED_ERROR": "❌ Unexpected error during functional test execution: {error}",
        "VALIDATION_NO_MESSAGES": "The functional test produced no specific messages.",
    }
}

# Funzioni get_text e format_text (invariate)
def get_text(lang_code, key):
    """Recupera il testo per una data chiave nella lingua specificata."""
    lang_dict = TEXTS.get(lang_code, TEXTS.get("en", {}))
    return lang_dict.get(key, f"MISSING_TEXT[{key}]")

def format_text(lang_code, key, **kwargs):
     """Recupera testo e lo formatta con i parametri forniti."""
     raw_text = get_text(lang_code, key)
     if raw_text == f"MISSING_TEXT[{key}]": return raw_text
     try: return raw_text.format(**kwargs)
     except KeyError as e: print(f"WARN: Missing placeholder key {e} in text key '{key}' for lang '{lang_code}' when formatting with {kwargs}"); return raw_text
     except Exception as e: print(f"WARN: Generic formatting error for text key '{key}' with args {kwargs} for lang '{lang_code}': {e}"); return raw_text
