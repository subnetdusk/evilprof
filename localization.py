# localization.py (Subheader Aggiornato)

TEXTS = {
    "it": {
        # Titoli e Header principali
        "PAGE_TITLE": "EvilProf 😈",
        "MAIN_TITLE": "EvilProf 😈",
        "SUBHEADER_NEW": "Crea verifiche da Excel/CSV con selezione mirata per massimizzare la diversità delle domande.", # MODIFICATO
        "INSTRUCTIONS_HEADER": "ℹ️ Guida Rapida e Link Utili",
        "GENERATION_PARAMS_HEADER": "Parametri di Generazione",
        "OUTPUT_AREA_HEADER": "Output e Messaggi",
        "GENERATION_MESSAGES_HEADER": "--- Messaggi dalla Generazione ---",
        "FOOTER_TEXT": "EvilProf v1.2 - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit",

        # Link README
        "README_LINK_TEXT": "🔗 Consulta la guida completa su GitHub (README)",
        "README_LINK_URL_IT": "https://github.com/subnetdusk/evilprof/blob/main/README.md",
        "README_LINK_URL_EN": "https://github.com/subnetdusk/evilprof/blob/main/README.md#english-version",

        # Widget e Label
        "UPLOAD_LABEL": "1. Carica File Excel/CSV",
        "UPLOAD_HELP": "Trascina o seleziona il file (.xlsx, .xls, .csv) con le domande organizzate in blocchi separati da righe vuote.",
        "SUBJECT_LABEL": "2. Nome della Materia",
        "SUBJECT_HELP": "Apparirà nel titolo di ogni verifica.",
        "SUBJECT_DEFAULT": "Informatica",
        "NUM_TESTS_LABEL": "3. Numero di Verifiche da Generare",
        "NUM_TESTS_HELP": "Quante versioni diverse della verifica creare?",
        "BLOCK_REQUESTS_HEADER": "Domande per Blocco:",
        "BLOCK_REQUEST_SUGGESTION_INFO_TEXT": "ℹ️ Per massimizzare la diversità, si consiglia di selezionare circa 1/3 delle domande disponibili per blocco (valore preimpostato con arrotondamento per difetto).",
        "BLOCK_REQUEST_LABEL": "N. Domande da Blocco {block_id} ({type}) (Max: {n})",
        "TOTAL_QUESTIONS_SELECTED": "Domande Totali Selezionate",
        "GENERATE_BUTTON_LABEL": "🚀 Genera Verifiche PDF",

        # Messaggi di stato, errore, warning
        "WEASYPRINT_ERROR": "🚨 **Attenzione:** La libreria WeasyPrint non è disponibile o funzionante...",
        "IMAGE_CAPTION": "Esempio di struttura file Excel valida (con blocchi separati)",
        "IMAGE_NOT_FOUND_WARNING": "Nota: Immagine di esempio '{image_path}' non trovata.",
        "IMAGE_LOAD_ERROR": "Errore caricamento immagine '{image_path}': {error}",
        "GENERATION_START": "Avvio Generazione Verifiche...",
        "UPLOAD_FIRST_WARNING": "⚠️ Per favore, carica prima un file Excel/CSV.",
        "LOADING_DATA_SPINNER": "⏳ Analisi file e identificazione blocchi...",
        "LOAD_ERROR": "Errore caricamento dati: {error_msg}",
        "NO_VALID_QUESTIONS_ERROR": "Nessuna domanda valida trovata nel file caricato.",
        "TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS": "ERRORE: Non hai selezionato nessuna domanda dai blocchi.",
        "PARAMS_OK_INFO": "Parametri OK. Generazione di {num_tests} verifiche...",
        "CORRECT_ERRORS_ERROR": "Correggi gli errori nei parametri prima di generare.",
        "GENERATING_DATA_SPINNER": "⏳ Generazione verifiche...",
        "GENERATION_FAILED_ERROR": "❌ Generazione fallita a causa di errori critici: {error}",
        "DATA_READY_PDF_INFO": "Dati per {num_tests} verifiche pronti. Avvio generazione PDF...",
        "PDF_CREATION_SPINNER": "⏳ Creazione del file PDF in corso...",
        "PDF_SUCCESS": "✅ Generazione PDF completata!",
        "PDF_DOWNLOAD_BUTTON_LABEL": "📥 Scarica PDF Generato",
        "PDF_DOWNLOAD_BUTTON_HELP": "Clicca per scaricare il file '{pdf_filename}'",
        "PDF_GENERATION_ERROR": "❌ Errore durante la creazione del file PDF.",
        "INITIAL_INFO_NEW": "Carica un file Excel/CSV, specifica quante domande prendere da ogni blocco nei campi appositi e premi 'Genera Verifiche PDF'.",

        # Testo Intro
        "INTRO_TEXT_NEW": """
EvilProf genera verifiche PDF da file Excel/CSV, organizzando le domande in blocchi.

**Obiettivo:** Creare rapidamente multiple versioni di verifiche, mirando alla **massima diversità possibile delle domande in un intorno ristretto di test consecutivi**, grazie all'uso del campionamento pesato (WRSwOR) quando le condizioni lo permettono.

**Come Funziona:**

1.  **Prepara il File (Excel/CSV):**
    * **Colonna A:** Testo della domanda.
    * **Colonne B, C,... (solo per Scelta Multipla):** Opzioni di risposta.
    * **Blocchi:** Separa gruppi di domande (blocchi) con una **riga completamente vuota**. Ogni blocco deve contenere solo domande dello stesso tipo (tutte a Scelta Multipla o tutte Aperte). L'app rileva il tipo automaticamente.
    * Non includere intestazioni di colonna o nomi per i blocchi nel file.
    * *Vedi un esempio della struttura del file nella sidebar.*

2.  **Carica e Configura:**
    * Carica il tuo file Excel/CSV nell'applicazione.
    * Per ogni blocco identificato, specifica **quante domande esatte (`k`)** vuoi estrarre. Il sistema suggerisce un valore ottimale (circa 1/3 delle disponibili, arrotondato per difetto).

3.  **Logica di Campionamento (per una maggiore diversità tra verifiche):**
    * **Campionamento Ponderato (WRSwOR):** Se le domande disponibili nel blocco (`n`) sono più del doppio di quelle richieste (`k`), cioè **`n > 2k`**, l'app usa questo metodo. Garantisce che le domande usate in una verifica non vengano ripetute nella verifica *immediatamente successiva* (per quel blocco) e favorisce la selezione di domande meno recenti.
    * **Campionamento Casuale Semplice:** Se **`n <= 2k`** (cioè se richiedi la metà o più delle domande del blocco), l'app usa questo metodo, che non garantisce la stessa diversità tra test consecutivi per quel blocco. Può attivarsi anche per WRSwOR se `k` è alto rispetto alle domande *nuove* disponibili.

4.  **Genera PDF:** Ottieni un singolo file PDF con tutte le verifiche generate.

*Per istruzioni dettagliate sulla preparazione del file ed esempi, consulta la guida completa su GitHub.*
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
    },
    "en": {
        # Titles & Headers
        "PAGE_TITLE": "EvilProf 😈",
        "MAIN_TITLE": "EvilProf 😈",
        "SUBHEADER_NEW": "Create tests from Excel/CSV with targeted selection to maximize question diversity.", # MODIFIED
        "INSTRUCTIONS_HEADER": "ℹ️ Quick Guide & Useful Links",
        "GENERATION_PARAMS_HEADER": "Generation Parameters",
        "OUTPUT_AREA_HEADER": "Output & Messages",
        "GENERATION_MESSAGES_HEADER": "--- Messages from Generation ---",
        "FOOTER_TEXT": "EvilProf v1.2 - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit",

        # Link README
        "README_LINK_TEXT": "🔗 Check out the full guide on GitHub (README)",
        "README_LINK_URL_IT": "https://github.com/subnetdusk/evilprof/blob/main/README.md",
        "README_LINK_URL_EN": "https://github.com/subnetdusk/evilprof/blob/main/README.md#english-version",

        # Widget Sidebar (now Main Body for these) & Labels
        "UPLOAD_LABEL": "1. Upload Excel/CSV File",
        "UPLOAD_HELP": "Drag and drop or select the Excel/CSV file (.xlsx, .xls, .csv) with questions organized in blocks separated by empty rows.",
        "SUBJECT_LABEL": "2. Subject Name",
        "SUBJECT_HELP": "Will appear in the title of each test.",
        "SUBJECT_DEFAULT": "Computer Science",
        "NUM_TESTS_LABEL": "3. Number of Tests to Generate",
        "NUM_TESTS_HELP": "How many different versions of the test to create?",
        "BLOCK_REQUESTS_HEADER": "Questions per Block:",
        "BLOCK_REQUEST_SUGGESTION_INFO_TEXT": "ℹ️ To maximize diversity, selecting about 1/3 of the available questions per block is recommended (default value is preset, rounded down).",
        "BLOCK_REQUEST_LABEL": "N. Questions from Block {block_id} ({type}) (Max: {n})",
        "TOTAL_QUESTIONS_SELECTED": "Total Questions Selected",
        "GENERATE_BUTTON_LABEL": "🚀 Generate PDF Tests",

        # Status / Error / Warning Messages
        "WEASYPRINT_ERROR": "🚨 **Warning:** The WeasyPrint library is not available or not functional. PDF generation is blocked...",
        "IMAGE_CAPTION": "Example of valid Excel file structure (with separated blocks)",
        "IMAGE_NOT_FOUND_WARNING": "Note: Example image '{image_path}' not found.",
        "IMAGE_LOAD_ERROR": "Error loading image '{image_path}': {error}",
        "GENERATION_START": "Starting Test Generation...",
        "UPLOAD_FIRST_WARNING": "⚠️ Please upload an Excel/CSV file first.",
        "LOADING_DATA_SPINNER": "⏳ Analyzing file and identifying blocks...",
        "LOAD_ERROR": "Error loading data: {error_msg}",
        "NO_VALID_QUESTIONS_ERROR": "No valid questions found in the uploaded file.",
        "TOTAL_QUESTIONS_ZERO_ERROR_BLOCKS": "ERROR: You haven't selected any questions from the blocks.",
        "PARAMS_OK_INFO": "Parameters OK. Generating {num_tests} tests...",
        "CORRECT_ERRORS_ERROR": "Please correct the parameter errors before generating.",
        "GENERATING_DATA_SPINNER": "⏳ Generating tests...",
        "GENERATION_FAILED_ERROR": "❌ Generation failed due to critical errors: {error}",
        "DATA_READY_PDF_INFO": "Data for {num_tests} tests ready. Starting PDF generation...",
        "PDF_CREATION_SPINNER": "⏳ Creating PDF file...",
        "PDF_SUCCESS": "✅ PDF Generation Complete!",
        "PDF_DOWNLOAD_BUTTON_LABEL": "📥 Download Generated PDF",
        "PDF_DOWNLOAD_BUTTON_HELP": "Click to download '{pdf_filename}'",
        "PDF_GENERATION_ERROR": "❌ Error during PDF creation.",
        "INITIAL_INFO_NEW": "Upload an Excel/CSV file, specify how many questions to take from each block in the respective fields, and press 'Generate PDF Tests'.",

        # Intro Text
        "INTRO_TEXT_NEW": """
EvilProf generates PDF tests from Excel/CSV files, organizing questions into blocks.

**Objective:** Quickly create multiple test versions, aiming for the **maximum possible diversity of questions within a close range of consecutive tests**, by using weighted sampling (WRSwOR) when conditions allow.

**How It Works:**

1.  **Prepare Your File (Excel/CSV):**
    * **Column A:** Question text.
    * **Columns B, C,... (Multiple Choice only):** Answer options.
    * **Blocks:** Separate groups of questions (blocks) with a **completely empty row**. Each block must contain only questions of the same type (all Multiple Choice or all Open Ended). The app detects the type automatically.
    * Do not include column headers or block names in the file.
    * *See an example of the file structure in the sidebar.*

2.  **Upload and Configure:**
    * Upload your Excel/CSV file into the application.
    * For each identified block, specify **exactly how many questions (`k`)** you want to extract. The system suggests an optimal value (about 1/3 of available, rounded down).

3.  **Sampling Logic (for greater diversity between tests):**
    * **Weighted Sampling (WRSwOR):** If the available questions in the block (`n`) are more than double the requested ones (`k`), i.e., **`n > 2k`**, the app uses this method. It ensures that questions used in one test are not repeated in the *immediately following* test (for that block) and favors selecting less recently used questions.
    * **Simple Random Sampling:** If **`n <= 2k`** (i.e., if you request half or more of the block's questions), the app uses this method, which doesn't guarantee the same diversity between consecutive tests for that block. It may also be triggered for WRSwOR if `k` is high relative to the *new* available questions.

4.  **Generate PDF:** Get a single PDF file with all generated tests.

*For detailed file preparation instructions and examples, please refer to the full guide on GitHub.*
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
     if raw_text == f"MISSING_TEXT[{key}]":
         return raw_text
     try:
         return raw_text.format(**kwargs)
     except KeyError as e:
         return raw_text
     except Exception as e:
         return raw_text
