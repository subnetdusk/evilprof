# localization.py (con INTRO_TEXT italiano completo)

TEXTS = {
    "it": {
        # ... [altre chiavi italiane come definite prima] ...

        "SUBJECT_DEFAULT": "Informatica",
        "IMAGE_CAPTION": "Esempio di struttura file Excel valida",

        # Testo Intro (ORA COMPLETO)
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

        # ... [resto delle chiavi italiane come prima] ...
    },
    "en": {
        # ... [altre chiavi inglesi come definite prima] ...

        "SUBJECT_DEFAULT": "Computer Science",
        "IMAGE_CAPTION": "Example of valid Excel file structure",

        # Testo Intro (Inglese - completo come prima)
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
        # Testi usati nel PDF
        "PDF_TEST_TITLE": "Test for {subject_name}",
        "PDF_NAME_LABEL": "Name:",
        "PDF_DATE_LABEL": "Date:",
        "PDF_CLASS_LABEL": "Class:",
        "PDF_MISSING_QUESTION": "MISSING QUESTION",
        "PDF_NO_OPTIONS": "<em>(No answer options provided)</em>",

        # ... [resto delle chiavi inglesi come prima] ...
    }
}

# Funzione helper (invariata)
def get_text(lang_code, key):
    return TEXTS.get(lang_code, TEXTS["en"]).get(key, f"MISSING_TEXT[{key}]")

# Funzione helper (invariata)
def format_text(lang_code, key, **kwargs):
     raw_text = get_text(lang_code, key)
     try:
         return raw_text.format(**kwargs)
     except KeyError as e:
         print(f"WARN: Missing placeholder {e} in text key '{key}' for lang '{lang_code}'")
         return raw_text
     except: # Catch other potential formatting errors
         print(f"WARN: Formatting error for text key '{key}' with args {kwargs} for lang '{lang_code}'")
         return raw_text
