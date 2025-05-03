# config.py

INTRO_TEXT = """
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
"""

# Costanti
DEFAULT_SUBJECT = "Informatica"
DEFAULT_NUM_TESTS = 30
DEFAULT_NUM_MC = 8
DEFAULT_NUM_OPEN = 2
EXAMPLE_IMAGE_PATH = "excel_example.jpg"
