# localization.py (Versione COMPLETA con tutte le chiavi)

TEXTS = {
    "it": {
        # Titoli e Intestazioni
        "PAGE_TITLE": "EvilProf 😈",
        "MAIN_TITLE": "EvilProf 😈",
        "SUBHEADER": "Generatore di verifiche casuali e diverse, da Excel a PDF",
        "INSTRUCTIONS_HEADER": "ℹ️ Istruzioni e Preparazione File Excel",
        "GENERATION_PARAMS_HEADER": "Parametri di Generazione",
        "VALIDATION_TEST_HEADER": "Test Funzionale",
        "SOURCE_CODE_HEADER": "Codice Sorgente",
        "OUTPUT_AREA_HEADER": "Output e Messaggi",
        "VALIDATION_RESULTS_HEADER": "--- Risultato Test Funzionale ---",
        "GENERATION_MESSAGES_HEADER": "--- Messaggi dalla Generazione dei Dati ---",
        "FOOTER_TEXT": "EvilProf v1.1 (Refactored) - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit",

        # Widget Sidebar
        "UPLOAD_LABEL": "1. Carica File Excel (.xlsx, .xls)",
        "UPLOAD_HELP": "Trascina o seleziona il file Excel con le domande.",
        "SUBJECT_LABEL": "2. Nome della Materia",
        "SUBJECT_HELP": "Apparirà nel titolo di ogni verifica.",
        "SUBJECT_DEFAULT": "Informatica",
        "NUM_TESTS_LABEL": "3. Numero di Verifiche da Generare",
        "NUM_TESTS_HELP": "Quante versioni diverse della verifica creare?",
        "NUM_MC_LABEL": "4. N. Domande Scelta Multipla / Verifica",
        "NUM_MC_HELP": "Quante domande a scelta multipla includere in ogni verifica.",
        "NUM_OPEN_LABEL": "5. N. Domande Aperte / Verifica",
        "NUM_OPEN_HELP": "Quante domande a risposta aperta includere in ogni verifica.",
        "GENERATE_BUTTON_LABEL": "🚀 Genera Verifiche PDF",
        "VALIDATE_BUTTON_LABEL": "🧪 Esegui Test Funzionale",
        "VALIDATE_BUTTON_HELP_NEW": "Esegue scenari di test interni usando 'test_questions.xlsx' per verificare la logica di diversità e similarità.",
        "DOWNLOAD_SOURCE_BUTTON_LABEL": "📥 Scarica Codice App (app.py)",
        "DOWNLOAD_SOURCE_CAPTION": "Scarica gli altri file (.py) separatamente.",
        "SOURCE_UNAVAILABLE_WARNING": "Download codice sorgente non disponibile: {error}",

        # Messaggi di Stato / Errori / Warning (in app.py)
        "WEASYPRINT_ERROR": "🚨 **Attenzione:** La libreria WeasyPrint non è disponibile o funzionante. La generazione del PDF è bloccata. Assicurati di averla installata e che le sue dipendenze (GTK+, Pango, Cairo) siano presenti nel sistema.",
        "IMAGE_CAPTION": "Esempio di struttura file Excel valida",
        "IMAGE_NOT_FOUND_WARNING": "Nota: Immagine di esempio '{image_path}' non trovata.",
        "IMAGE_LOAD_ERROR": "Errore caricamento immagine '{image_path}': {error}",
        "VALIDATION_START": "Avvio Test Funzionale...",
        "GENERATION_START": "Avvio Generazione Verifiche...",
        "UPLOAD_FIRST_WARNING": "⚠️ Per favore, carica prima un file Excel.",
        "LOADING_DATA_SPINNER": "⏳ Caricamento e validazione domande...",
        "LOADING_DATA_VALIDATION_SPINNER": "⏳ Caricamento dati per test...",
        "LOAD_ERROR": "Errore caricamento dati: {error_msg}",
        "NO_VALID_QUESTIONS_ERROR": "Nessuna domanda valida trovata nel file. Impossibile procedere.",
        "TOTAL_QUESTIONS_ZERO_ERROR": "ERRORE: Il numero totale di domande per verifica (Multiple + Aperte) deve essere maggiore di zero.",
        "PARAMS_OK_INFO": "Parametri OK. Generazione di {num_tests} verifiche per '{subject_name}' con {num_mc_q} MC + {num_open_q} Aperte = {num_q_per_test} Domande/Test.",
        "MC_ZERO_ERROR": "ERRORE: Richieste {num_mc_q} domande a scelta multipla, ma 0 trovate nel file.",
        "OPEN_ZERO_ERROR": "ERRORE: Richieste {num_open_q} domande aperte, ma 0 trovate nel file.",
        "MC_INSUFFICIENT_ERROR": "ERRORE CRITICO: Non ci sono abbastanza domande a scelta multipla ({total_mc}) per soddisfare le {num_mc_q} richieste per verifica.",
        "OPEN_INSUFFICIENT_ERROR": "ERRORE CRITICO: Non ci sono abbastanza domande aperte ({total_open}) per soddisfare le {num_open_q} richieste per verifica.",
        "CORRECT_ERRORS_ERROR": "Correggi gli errori sopra prima di generare.",
        "GENERATING_DATA_SPINNER": "⏳ Generazione dati per {num_tests} verifiche...",
        "VALIDATION_LOGIC_SPINNER": "⏳ Esecuzione test funzionale...",
        "GENERATION_FAILED_ERROR": "❌ Generazione dati fallita a causa di errori critici. Controllare i messaggi sopra.",
        "DATA_READY_PDF_INFO": "Dati per {num_tests} verifiche pronti. Avvio generazione PDF...",
        "PDF_CREATION_SPINNER": "⏳ Creazione del file PDF in corso (può richiedere tempo)...",
        "PDF_SUCCESS": "✅ Generazione PDF completata!",
        "PDF_DOWNLOAD_BUTTON_LABEL": "📥 Scarica PDF Generato",
        "PDF_DOWNLOAD_BUTTON_HELP": "Clicca per scaricare il file '{pdf_filename}'",
        "PDF_GENERATION_ERROR": "❌ Errore durante la creazione del file PDF. Controllare i messaggi sopra, specialmente quelli relativi a WeasyPrint.",
        "INITIAL_INFO": "Configura i parametri nella sidebar e premi 'Genera Verifiche PDF' o 'Esegui Test Funzionale'.",
        "VALIDATION_NO_MESSAGES": "Il test funzionale non ha prodotto messaggi specifici.",

        # Testo Intro (COMPLETO ITALIANO)
        "INTRO_TEXT": """
EvilProf è un'applicazione web realizzata con Streamlit che permette di generare rapidamente file PDF contenenti verifiche personalizzate.

Le caratteristiche principali includono:

- **Input da Excel:** Carica facilmente le tue domande da un file `.xlsx` o `.xls`.
- **Tipi di Domande:** Supporta sia domande a scelta multipla (con risposte casualizzate) sia domande a risposta aperta.
- **Personalizzazione:** Scegli il numero di verifiche da generare, il numero di domande per tipo (multiple/aperte) per ciascuna verifica e il nome della materia.
- **Randomizzazione Avanzata:** Le domande in ogni verifica sono selezionate casualmente dal pool disponibile nel file Excel. L'ordine delle risposte multiple è casuale.
- **Diversità Migliorata (con Fallback):** L'applicazione tenta di utilizzare una tecnica di **Campionamento Casuale Ponderato Senza Reinserimento (WRSwOR)** per selezionare le domande. Questo metodo:
    - Tenta di **garantire** che le domande usate in una verifica non vengano ripetute nella verifica *immediatamente successiva*. Ciò richiede che il numero totale di domande di un certo tipo (`n`) sia strettamente maggiore del doppio del numero di domande di quel tipo richieste per verifica (`k`), ovvero `n >= 2k`.
    - Tenta di **favorire statisticamente** la selezione di domande che non vengono utilizzate da più tempo. Per una buona rotazione e diversità a lungo termine, è **fortemente consigliato** avere un numero totale di domande almeno **tre volte superiore** (`n >= 3k`) a quelle richieste per singola verifica. L'app mostrerà un avviso se `n < 3k`.
    - **Fallback:** Se non ci sono abbastanza domande uniche disponibili per garantire la diversità rispetto al test precedente (`n <= 2k`), l'applicazione **passerà a un campionamento casuale semplice** da *tutte* le domande disponibili per quel tipo, **perdendo la garanzia di diversità** tra test adiacenti. Verrà mostrato un avviso rosso prominente in tal caso.
- **Output PDF:** Genera un singolo file PDF pronto per la stampa, con ogni verifica che inizia su una nuova pagina e un'intestazione per nome, data e classe.

**Struttura del File Excel**

Perché l'applicazione funzioni correttamente, il file Excel deve rispettare la seguente struttura **senza intestazioni di colonna**:

- **Colonna A:** Contiene il testo completo della domanda.
- **Colonne B, C, D, ...:** Contengono le diverse opzioni di risposta *solo* per le domande a scelta multipla. Devono esserci almeno due opzioni di risposta perché la domanda sia considerata a scelta multipla.
- **Domande Aperte:** Per una domanda aperta, lasciare semplicemente vuote le celle nelle colonne B, C, D, ...
- *Vedi immagine di esempio qui sotto.*

---
""",
        # Testi usati nel PDF
        "PDF_TEST_TITLE": "Verifica di {subject_name}",
        "PDF_NAME_LABEL": "Nome e Cognome:",
        "PDF_DATE_LABEL": "Data:",
        "PDF_CLASS_LABEL": "Classe:",
        "PDF_MISSING_QUESTION": "DOMANDA MANCANTE",
        "PDF_NO_OPTIONS": "<em>(Nessuna opzione di risposta fornita)</em>",

        # Messaggi specifici del file_handler (usati anche da test.py)
        "FH_READING_EXCEL": "⏳ Lettura file Excel: {file_name}...",
        "FH_USING_CACHE": "ℹ️ Utilizzo dati già caricati per: {file_name}",
        "FH_ROW_WARNING_ANSWERS_ONLY": "Attenzione: Riga Excel {row_num} ha risposte ma manca la domanda e sarà ignorata.",
        "FH_ROW_WARNING_ONE_ANSWER": "Attenzione: Domanda '{q_text}' (riga Excel {row_num}) ha solo 1 risposta ed è stata trattata come Aperta.",
        "FH_LOAD_COMPLETE": "✅ Dati caricati: {count} domande ({mc_count} a scelta multipla, {oe_count} aperte).",
        "FH_NO_VALID_QUESTIONS": "Errore: Nessuna domanda valida trovata nel file '{file_name}'.",
        "FH_UNEXPECTED_ERROR": "Errore imprevisto durante la lettura del file Excel '{file_name}': {error}",

        # Messaggi specifici del core_logic (usati anche da test.py)
        "CL_GENERATING_TEST_DATA": "⚙️ Generazione dati test {current_test}/{total_tests}...",
        "CL_VALIDATION_RUNNING": "Validazione {num_tests_generated} test generati...",
        "CL_FALLBACK_MC_WARNING": "[Test {test_num}] Fallback attivo per Scelta Multipla: non abbastanza domande diverse ({candidates}) rispetto al test precedente. Campiono da tutte ({total}).",
        "CL_FALLBACK_OE_WARNING": "[Test {test_num}] Fallback attivo per Aperte: non abbastanza domande diverse ({candidates}) rispetto al test precedente. Campiono da tutte ({total}).",
        "CL_CRITICAL_SAMPLING_ERROR_MC": "Errore Critico Test {test_num}: Impossibile campionare {k} MC da {n} totali.",
        "CL_CRITICAL_SAMPLING_ERROR_OE": "Errore Critico Test {test_num}: Impossibile campionare {k} Aperte da {n} totali.",
        "CL_CRITICAL_WRSWOR_ERROR_MC": "Errore Critico Test {test_num} (WRSwOR MC): {error}",
        "CL_CRITICAL_WRSWOR_ERROR_OE": "Errore Critico Test {test_num} (WRSwOR Aperte): {error}",
        "CL_FINAL_FALLBACK_ACTIVE": "‼️ ATTENZIONE GENERALE: Il fallback è stato attivato per almeno un test. La diversità tra test *non* è garantita per tutti. Controllare i messaggi di warning specifici per i dettagli.",
        "CL_FINAL_LOW_DIVERSITY_MC": "⚠️ Diversità Limitata (MC): Il totale domande ({total_mc}) è meno del triplo ({three_k}) delle richieste ({k}). Consigliato aumentare il pool di domande MC.",
        "CL_FINAL_LOW_DIVERSITY_OE": "⚠️ Diversità Limitata (Aperte): Il totale domande ({total_open}) è meno del triplo ({three_k}) delle richieste ({k}). Consigliato aumentare il pool di domande Aperte.",
        "CL_FINAL_OK_DIVERSITY": "✅ Dati per {num_tests} verifiche preparati (con diversità garantita).",
        "CL_VALIDATION_TEST_FAILED_GENERATION": "❌ Validazione Fallita: Errore durante la generazione dei dati di test.",
        "CL_VALIDATION_TEST_WRONG_Q_COUNT": "❌ Validazione Fallita: Test {test_num} ha {actual_count} domande invece di {expected_count}.",
        "CL_VALIDATION_TESTS_NO_INTERSECTION": "✅ Validazione Passata: Test 1 e Test 2 non hanno domande in comune.",
        "CL_VALIDATION_TESTS_INTERSECTION_WARNING": "⚠️ Validazione: Test 1 e Test 2 hanno domande in comune (indici: {intersection}). Atteso se il fallback è stato attivato durante il test.",
        "CL_VALIDATION_TESTS_WRONG_COUNT": "❌ Validazione Fallita: Numero di test generati ({actual_count}) non corretto ({expected_count}).",
        "CL_VALIDATION_COMPLETE_SUCCESS": "🎉 Test funzionale completato con successo (o con warning attesi).",
        "CL_VALIDATION_UNEXPECTED_ERROR": "❌ Errore imprevisto durante l'esecuzione del test funzionale: {error}",
        "CL_VALIDATION_INSUFFICIENT_MC_ERROR": "Test Fallito: Non abbastanza MC ({total}) per test ({k}).",
        "CL_VALIDATION_INSUFFICIENT_OE_ERROR": "Test Fallito: Non abbastanza Aperte ({total}) per test ({k}).",
        "CL_VALIDATION_INSUFFICIENT_MC_WARN": "Test Warning: Servono >{k} MC totali per testare efficacemente la non-ripetizione.",
        "CL_VALIDATION_INSUFFICIENT_OE_WARN": "Test Warning: Servono >{k} Aperte totali per testare efficacemente la non-ripetizione.",

        # Messaggi specifici del pdf_generator
        "PG_PDF_GENERATION_START": "⚙️ Inizio generazione PDF...",
        "PG_WEASYPRINT_UNAVAILABLE": "Libreria WeasyPrint non trovata o non funzionante. Impossibile generare PDF.",
        "PG_HTML_BUILDING": "⚙️ Costruzione documento HTML...",
        "PG_PDF_CONVERTING": "⚙️ Conversione HTML in PDF con WeasyPrint (potrebbe richiedere tempo)...",
        "PG_PDF_CONVERSION_COMPLETE": "⚙️ Conversione PDF completata.",
        "PG_WEASYPRINT_DEPENDENCY_ERROR": "ERRORE WeasyPrint: Dipendenze mancanti (GTK+/Pango/Cairo?). Dettagli: {error}",
        "PG_WEASYPRINT_OTHER_ERROR": "ERRORE durante la generazione PDF con WeasyPrint: {error}",

        # Nuove chiavi per test.py (Test Statistici)
        "TEST_FILE_NOT_FOUND": "ERRORE: File di test '{filename}' non trovato. Esegui prima lo script 'generate_test_excel.py'.",
        "TEST_LOADING_DATA": "Caricamento dati dal file di test '{filename}'...",
        "TEST_NO_QUESTIONS_FOUND": "ERRORE: Nessuna domanda valida trovata nel file di test '{filename}'.",
        "TEST_LOAD_SUCCESS": "Dati di test caricati: {count} domande ({mc} MC, {oe} OE).",
        "TEST_LOAD_ERROR": "ERRORE imprevisto durante il caricamento del file di test '{filename}': {error}",
        "TEST_ABORTED_LOAD_FAILED": "❌ Test annullato: impossibile caricare i dati di test.",
        "TEST_WRONG_QUESTION_COUNT": "ERRORE Dati Test: Trovate {mc} MC e {oe} OE domande, attese {expected} per tipo.",
        "TEST_RUNNING_SCENARIO": "--- Esecuzione Scenario Test {scenario} (MC={mc}, OE={oe}, N={n_sim}) ---",
        "TEST_SCENARIO_PASSED": "✅ Scenario Test {scenario}: PASSATO (Nessuna ripetizione consecutiva trovata).",
        "TEST_SCENARIO_ASSERT_FAILED": "❌ Scenario Test {scenario}: FALLITO Assertion ({failures}/{total} test consecutivi identici trovati).",
        "TEST_SCENARIO_GENERATION_FAILED": "❌ Scenario Test {scenario}: FALLITA la generazione dei dati necessari.",
        "TEST_SCENARIO_ASSERT_FAILED_EXPECTED": "⚠️ Scenario Test {scenario}: FALLITO Assertion ({failures}/{total} test consecutivi identici trovati - ATTESO a causa del fallback).",
        "TEST_SCENARIO_3_PASSED_WITH_FALLBACK": "ℹ️ Scenario Test 3: PASSATO nonostante il fallback fosse attivo (ripetizioni non trovate).",
        "TEST_ALL_SCENARIOS_COMPLETE": "--- Tutti gli scenari di test completati. Controllare i risultati sopra. ---",
        "STAT_TEST_GENERATING_SEQUENCE": "⚙️ Generazione sequenza test per k={k_mc}/{k_oe} (N={num_tests})...",
        "STAT_TEST_GENERATION_FAILED": "❌ Fallita generazione sequenza test per k={k_mc}/{k_oe}.",
        "STAT_TEST_CALCULATING_SIMILARITY": "⚙️ Calcolo similarità per k={k_mc}/{k_oe} (max dist={max_dist})...",
        "STAT_TEST_ANALYSIS_COMPLETE": "✅ Analisi similarità completata per k={k_mc}/{k_oe}.",
        "STAT_TEST_STARTING": "Avvio analisi statistica similarità per {num_k} valori di k (N={num_tests} test per k)...",
        "STAT_TEST_RUNNING_FOR_K": "--- Analisi per k = {k} ---",
        "STAT_TEST_RESULTS_FOR_K": "Risultati Medie Jaccard per k={k}: {results}",
        "STAT_TEST_FAILED_FOR_K": "❌ Analisi fallita per k = {k}.",
        "STAT_TEST_ALL_COMPLETE": "--- Analisi statistica di similarità completata. ---",
        "STAT_TEST_EXCEL_CREATED": "✅ File Excel con risultati statistici '{filename}' creato.",
        "STAT_TEST_EXCEL_SAVE_ERROR": "❌ Errore durante il salvataggio del file Excel '{filename}': {error}",
        "STAT_TEST_NO_DATA_FOR_EXCEL": "⚠️ Nessun dato dettagliato raccolto per creare il file Excel.",
        "DOWNLOAD_STATS_EXCEL_LABEL": "📊 Scarica Risultati Statistici (.xlsx)",
        "DOWNLOAD_STATS_EXCEL_HELP": "Scarica il file Excel con l'analisi di similarità Jaccard per distanza e k.",
    },
    "en": {
        # Titles & Headers
        "PAGE_TITLE": "EvilProf 😈",
        "MAIN_TITLE": "EvilProf 😈",
        "SUBHEADER": "Randomized and Diverse Test Generator, from Excel to PDF",
        "INSTRUCTIONS_HEADER": "ℹ️ Instructions & Excel File Preparation",
        "GENERATION_PARAMS_HEADER": "Generation Parameters",
        "VALIDATION_TEST_HEADER": "Functional Test",
        "SOURCE_CODE_HEADER": "Source Code",
        "OUTPUT_AREA_HEADER": "Output & Messages",
        "VALIDATION_RESULTS_HEADER": "--- Functional Test Results ---",
        "GENERATION_MESSAGES_HEADER": "--- Messages from Data Generation ---",
        "FOOTER_TEXT": "EvilProf v1.1 (Refactored) - [subnetdusk GitHub](https://github.com/subnetdusk/evilprof) - Streamlit",

        # Sidebar Widgets
        "UPLOAD_LABEL": "1. Upload Excel File (.xlsx, .xls)",
        "UPLOAD_HELP": "Drag and drop or select the Excel file with questions.",
        "SUBJECT_LABEL": "2. Subject Name",
        "SUBJECT_HELP": "Will appear in the title of each test.",
        "SUBJECT_DEFAULT": "Computer Science",
        "NUM_TESTS_LABEL": "3. Number of Tests to Generate",
        "NUM_TESTS_HELP": "How many different versions of the test to create?",
        "NUM_MC_LABEL": "4. Multiple Choice Questions / Test",
        "NUM_MC_HELP": "How many multiple-choice questions to include in each test.",
        "NUM_OPEN_LABEL": "5. Open-Ended Questions / Test",
        "NUM_OPEN_HELP": "How many open-ended questions to include in each test.",
        "GENERATE_BUTTON_LABEL": "🚀 Generate PDF Tests",
        "VALIDATE_BUTTON_LABEL": "🧪 Run Functional Test",
        "VALIDATE_BUTTON_HELP_NEW": "Runs internal test scenarios using 'test_questions.xlsx' to verify diversity and similarity logic.",
        "DOWNLOAD_SOURCE_BUTTON_LABEL": "📥 Download App Code (app.py)",
        "DOWNLOAD_SOURCE_CAPTION": "Download other (.py) files separately.",
        "SOURCE_UNAVAILABLE_WARNING": "Source code download unavailable: {error}",

        # Status / Error / Warning Messages (in app.py)
        "WEASYPRINT_ERROR": "🚨 **Warning:** The WeasyPrint library is not available or not functional. PDF generation is blocked. Ensure it is installed and its system dependencies (GTK+, Pango, Cairo) are present.",
        "IMAGE_CAPTION": "Example of valid Excel file structure",
        "IMAGE_NOT_FOUND_WARNING": "Note: Example image '{image_path}' not found.",
        "IMAGE_LOAD_ERROR": "Error loading image '{image_path}': {error}",
        "VALIDATION_START": "Starting Functional Test...",
        "GENERATION_START": "Starting Test Generation...",
        "UPLOAD_FIRST_WARNING": "⚠️ Please upload an Excel file first.",
        "LOADING_DATA_SPINNER": "⏳ Loading and validating questions...",
        "LOADING_DATA_VALIDATION_SPINNER": "⏳ Loading data for test...",
        "LOAD_ERROR": "Error loading data: {error_msg}",
        "NO_VALID_QUESTIONS_ERROR": "No valid questions found in the file. Cannot proceed.",
        "TOTAL_QUESTIONS_ZERO_ERROR": "ERROR: The total number of questions per test (Multiple Choice + Open) must be greater than zero.",
        "PARAMS_OK_INFO": "Parameters OK. Generating {num_tests} tests for '{subject_name}' with {num_mc_q} MC + {num_open_q} Open = {num_q_per_test} Questions/Test.",
        "MC_ZERO_ERROR": "ERROR: Requested {num_mc_q} multiple-choice questions, but 0 found in the file.",
        "OPEN_ZERO_ERROR": "ERROR: Requested {num_open_q} open-ended questions, but 0 found in the file.",
        "MC_INSUFFICIENT_ERROR": "CRITICAL ERROR: Not enough multiple-choice questions ({total_mc}) to meet the {num_mc_q} required per test.",
        "OPEN_INSUFFICIENT_ERROR": "CRITICAL ERROR: Not enough open-ended questions ({total_open}) to meet the {num_open_q} required per test.",
        "CORRECT_ERRORS_ERROR": "Please correct the errors above before generating.",
        "GENERATING_DATA_SPINNER": "⏳ Generating data for {num_tests} tests...",
        "VALIDATION_LOGIC_SPINNER": "⏳ Running functional test...",
        "GENERATION_FAILED_ERROR": "❌ Data generation failed due to critical errors. Check messages above.",
        "DATA_READY_PDF_INFO": "Data for {num_tests} tests ready. Starting PDF generation...",
        "PDF_CREATION_SPINNER": "⏳ Creating PDF file (this may take time)...",
        "PDF_SUCCESS": "✅ PDF Generation Complete!",
        "PDF_DOWNLOAD_BUTTON_LABEL": "📥 Download Generated PDF",
        "PDF_DOWNLOAD_BUTTON_HELP": "Click to download '{pdf_filename}'",
        "PDF_GENERATION_ERROR": "❌ Error during PDF creation. Check messages above, especially those related to WeasyPrint.",
        "INITIAL_INFO": "Configure parameters in the sidebar and press 'Generate PDF Tests' or 'Run Functional Test'.",
        "VALIDATION_NO_MESSAGES": "The functional test produced no specific messages.",

        # Intro Text (English - complete)
        "INTRO_TEXT": """
EvilProf is a web application built with Streamlit that allows you to quickly generate PDF files containing custom tests.

Main features include:

- **Input from Excel:** Easily load your questions from an `.xlsx` or `.xls` file.
- **Question Types:** Supports both multiple-choice questions (with randomized answers) and open-ended questions.
- **Customization:** Choose the number of tests to generate, the number of questions per type (multiple/open) for each test, and the subject name.
- **Advanced Randomization:** Questions in each test are randomly selected from the pool available in the Excel file. The order of multiple-choice answers is randomized.
- **Improved Diversity (with Fallback):** The application attempts to use a **Weighted Random Sampling without Replacement (WRSwOR)** technique to select questions. This method:
    - Attempts to **ensure** that questions used in one test are not repeated in the *immediately following* test. This requires the total number of questions of a certain type (`n`) to be strictly greater than twice the number of questions of that type required per test (`k`), i.e., `n >= 2k`.
    - Attempts to **statistically favor** the selection of questions that haven't been used for the longest time. For good long-term rotation and diversity, it is **strongly recommended** to have a total number of questions at least **three times greater** (`n >= 3k`) than those required per single test. The app will show a warning if `n < 3k`.
    - **Fallback:** If there are not enough unique questions available to ensure diversity compared to the previous test (`n <= 2k`), the application **will switch to simple random sampling** from *all* available questions of that type, **losing the guarantee of diversity** between adjacent tests. A prominent red warning will be displayed in this case.
- **PDF Output:** Generates a single PDF file ready for printing, with each test starting on a new page and a header for name, date, and class.

**Excel File Structure**

For the application to work correctly, the Excel file must adhere to the following structure **without column headers**:

- **Column A:** Contains the full text of the question.
- **Columns B, C, D, ...:** Contain the different answer options *only* for multiple-choice questions. There must be at least two answer options for the question to be considered multiple-choice.
- **Open-Ended Questions:** For an open-ended question, simply leave the cells in columns B, C, D, ... empty.
- *See example image below.*

---
""",
        # Texts used in PDF
        "PDF_TEST_TITLE": "Test for {subject_name}",
        "PDF_NAME_LABEL": "Name:",
        "PDF_DATE_LABEL": "Date:",
        "PDF_CLASS_LABEL": "Class:",
        "PDF_MISSING_QUESTION": "MISSING QUESTION",
        "PDF_NO_OPTIONS": "<em>(No answer options provided)</em>",

        # file_handler messages (also used by test.py)
        "FH_READING_EXCEL": "⏳ Reading Excel file: {file_name}...",
        "FH_USING_CACHE": "ℹ️ Using already loaded data for: {file_name}",
        "FH_ROW_WARNING_ANSWERS_ONLY": "Warning: Excel row {row_num} has answers but is missing the question and will be ignored.",
        "FH_ROW_WARNING_ONE_ANSWER": "Warning: Question '{q_text}' (Excel row {row_num}) has only 1 answer and was treated as Open-Ended.",
        "FH_LOAD_COMPLETE": "✅ Data loaded: {count} questions ({mc_count} multiple choice, {oe_count} open-ended).",
        "FH_NO_VALID_QUESTIONS": "Error: No valid questions found in file '{file_name}'.",
        "FH_UNEXPECTED_ERROR": "Unexpected error while reading Excel file '{file_name}': {error}",

        # core_logic messages (also used by test.py)
        "CL_GENERATING_TEST_DATA": "⚙️ Generating test data {current_test}/{total_tests}...",
        "CL_VALIDATION_RUNNING": "Validating {num_tests_generated} generated tests...",
        "CL_FALLBACK_MC_WARNING": "[Test {test_num}] Fallback active for Multiple Choice: not enough diverse questions ({candidates}) compared to the previous test. Sampling from all ({total}).",
        "CL_FALLBACK_OE_WARNING": "[Test {test_num}] Fallback active for Open-Ended: not enough diverse questions ({candidates}) compared to the previous test. Sampling from all ({total}).",
        "CL_CRITICAL_SAMPLING_ERROR_MC": "Critical Error Test {test_num}: Cannot sample {k} MC from {n} total.",
        "CL_CRITICAL_SAMPLING_ERROR_OE": "Critical Error Test {test_num}: Cannot sample {k} Open from {n} total.",
        "CL_CRITICAL_WRSWOR_ERROR_MC": "Critical Error Test {test_num} (WRSwOR MC): {error}",
        "CL_CRITICAL_WRSWOR_ERROR_OE": "Critical Error Test {test_num} (WRSwOR Open): {error}",
        "CL_FINAL_FALLBACK_ACTIVE": "‼️ GENERAL WARNING: Fallback was activated for at least one test. Diversity between tests is *not* guaranteed for all. Check specific warning messages for details.",
        "CL_FINAL_LOW_DIVERSITY_MC": "⚠️ Limited Diversity (MC): Total questions ({total_mc}) is less than triple ({three_k}) the requested per test ({k}). Consider increasing the MC question pool.",
        "CL_FINAL_LOW_DIVERSITY_OE": "⚠️ Limited Diversity (Open): Total questions ({total_open}) is less than triple ({three_k}) the requested per test ({k}). Consider increasing the Open question pool.",
        "CL_FINAL_OK_DIVERSITY": "✅ Data for {num_tests} tests prepared (with diversity guaranteed).",
        "CL_VALIDATION_TEST_FAILED_GENERATION": "❌ Validation Failed: Error during test data generation.",
        "CL_VALIDATION_TEST_WRONG_Q_COUNT": "❌ Validation Failed: Test {test_num} has {actual_count} questions instead of {expected_count}.",
        "CL_VALIDATION_TESTS_NO_INTERSECTION": "✅ Validation Passed: Test 1 and Test 2 have no questions in common.",
        "CL_VALIDATION_TESTS_INTERSECTION_WARNING": "⚠️ Validation: Test 1 and Test 2 have questions in common (indices: {intersection}). Expected if fallback was active during the test.",
        "CL_VALIDATION_TESTS_WRONG_COUNT": "❌ Validation Failed: Incorrect number of tests generated ({actual_count}) vs {expected_count}).",
        "CL_VALIDATION_COMPLETE_SUCCESS": "🎉 Functional test completed successfully (or with expected warnings).",
        "CL_VALIDATION_UNEXPECTED_ERROR": "❌ Unexpected error during functional test execution: {error}",
        "CL_VALIDATION_INSUFFICIENT_MC_ERROR": "Test Failed: Not enough MC ({total}) for test ({k}).",
        "CL_VALIDATION_INSUFFICIENT_OE_ERROR": "Test Failed: Not enough Open ({total}) for test ({k}).",
        "CL_VALIDATION_INSUFFICIENT_MC_WARN": "Test Warning: Need >{k} total MC questions to effectively test non-repetition.",
        "CL_VALIDATION_INSUFFICIENT_OE_WARN": "Test Warning: Need >{k} total Open questions to effectively test non-repetition.",

        # pdf_generator messages
        "PG_PDF_GENERATION_START": "⚙️ Starting PDF generation...",
        "PG_WEASYPRINT_UNAVAILABLE": "WeasyPrint library not found or not functional. Cannot generate PDF.",
        "PG_HTML_BUILDING": "⚙️ Building HTML document...",
        "PG_PDF_CONVERTING": "⚙️ Converting HTML to PDF with WeasyPrint (this may take time)...",
        "PG_PDF_CONVERSION_COMPLETE": "⚙️ PDF conversion complete.",
        "PG_WEASYPRINT_DEPENDENCY_ERROR": "ERROR WeasyPrint: Missing dependencies (GTK+/Pango/Cairo?). Details: {error}",
        "PG_WEASYPRINT_OTHER_ERROR": "ERROR during PDF generation with WeasyPrint: {error}",

        # New keys for test.py (Statistical Tests)
        "TEST_FILE_NOT_FOUND": "ERROR: Test file '{filename}' not found. Please run the 'generate_test_excel.py' script first.",
        "TEST_LOADING_DATA": "Loading data from test file '{filename}'...",
        "TEST_NO_QUESTIONS_FOUND": "ERROR: No valid questions found in test file '{filename}'.",
        "TEST_LOAD_SUCCESS": "Test data loaded: {count} questions ({mc} MC, {oe} OE).",
        "TEST_LOAD_ERROR": "Unexpected ERROR while loading test file '{filename}': {error}",
        "TEST_ABORTED_LOAD_FAILED": "❌ Test aborted: failed to load test data.",
        "TEST_WRONG_QUESTION_COUNT": "ERROR Test Data: Found {mc} MC and {oe} OE questions, expected {expected} of each.",
        "TEST_RUNNING_SCENARIO": "--- Running Test Scenario {scenario} (MC={mc}, OE={oe}, N={n_sim}) ---",
        "TEST_SCENARIO_PASSED": "✅ Test Scenario {scenario}: PASSED (No consecutive repetitions found).",
        "TEST_SCENARIO_ASSERT_FAILED": "❌ Test Scenario {scenario}: Assertion FAILED ({failures}/{total} identical consecutive tests found).",
        "TEST_SCENARIO_GENERATION_FAILED": "❌ Test Scenario {scenario}: Failed to generate necessary data.",
        "TEST_SCENARIO_ASSERT_FAILED_EXPECTED": "⚠️ Test Scenario {scenario}: Assertion FAILED ({failures}/{total} identical consecutive tests found - EXPECTED due to fallback).",
        "TEST_SCENARIO_3_PASSED_WITH_FALLBACK": "ℹ️ Test Scenario 3: PASSED although fallback was active (no repetitions found).",
        "TEST_ALL_SCENARIOS_COMPLETE": "--- All test scenarios completed. Check results above. ---",
        "STAT_TEST_GENERATING_SEQUENCE": "⚙️ Generating test sequence for k={k_mc}/{k_oe} (N={num_tests})...",
        "STAT_TEST_GENERATION_FAILED": "❌ Failed test sequence generation for k={k_mc}/{k_oe}.",
        "STAT_TEST_CALCULATING_SIMILARITY": "⚙️ Calculating similarity for k={k_mc}/{k_oe} (max dist={max_dist})...",
        "STAT_TEST_ANALYSIS_COMPLETE": "✅ Similarity analysis completed for k={k_mc}/{k_oe}.",
        "STAT_TEST_STARTING": "Starting statistical similarity analysis for {num_k} k-values (N={num_tests} tests per k)...",
        "STAT_TEST_RUNNING_FOR_K": "--- Analysis for k = {k} ---",
        "STAT_TEST_RESULTS_FOR_K": "Average Jaccard Results for k={k}: {results}",
        "STAT_TEST_FAILED_FOR_K": "❌ Analysis failed for k = {k}.",
        "STAT_TEST_ALL_COMPLETE": "--- Statistical similarity analysis completed. ---",
        "STAT_TEST_EXCEL_CREATED": "✅ Excel file with statistical results '{filename}' created.",
        "STAT_TEST_EXCEL_SAVE_ERROR": "❌ Error saving Excel file '{filename}': {error}",
        "STAT_TEST_NO_DATA_FOR_EXCEL": "⚠️ No detailed data collected to create the Excel file.",
        "DOWNLOAD_STATS_EXCEL_LABEL": "📊 Download Statistical Results (.xlsx)",
        "DOWNLOAD_STATS_EXCEL_HELP": "Download the Excel file with the Jaccard similarity analysis by distance and k.",
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
