# EvilProf 😈

Generatore di Verifiche Casuali da Excel a PDF - Versione Streamlit

Questa versione è hostata su [evilprof.streamlit.app](https://evilprof.streamlit.app/)

## Descrizione

**EvilProf** è un'applicazione web realizzata con Streamlit che permette di generare rapidamente file PDF contenenti verifiche personalizzate. L'applicazione legge le domande (a scelta multipla e/o aperte) da un file Excel strutturato in modo specifico e crea un numero definito di verifiche, ciascuna contenente un mix casuale di domande scelte dall'utente.

Funzionalità chiave è la possibilità di generare test adiacenti completamente diversi (con nessuna domanda in comune).

Le caratteristiche principali includono:

* **Input da Excel:** Carica facilmente le tue domande da un file `.xlsx` o `.xls`.
* **Tipi di Domande:** Supporta sia domande a scelta multipla (con risposte casualizzate) sia domande a risposta aperta.
* **Personalizzazione:** Scegli il numero di verifiche da generare, il numero di domande per tipo (multiple/aperte) per ciascuna verifica e il nome della materia.
* **Randomizzazione:** Le domande in ogni verifica sono selezionate casualmente dal pool disponibile nel file Excel. Anche l'ordine delle risposte multiple è casuale.
* **Opzione "Garantire Test Diversi":** Possibilità di assicurare che due verifiche consecutive non utilizzino lo stesso set di domande (richiede un numero sufficiente di domande nel file sorgente).
* **Output PDF:** Genera un singolo file PDF pronto per la stampa, con ogni verifica che inizia su una nuova pagina e un'intestazione per nome, data e classe.
* **Interfaccia Web Semplice:** Grazie a Streamlit, l'interfaccia è intuitiva e facile da usare direttamente nel browser.

## Struttura del File Excel

Perché l'applicazione funzioni correttamente, il file Excel deve rispettare la seguente struttura **senza intestazioni di colonna**:

* **Colonna A:** Contiene il testo completo della domanda.
* **Colonne B, C, D, ...:** Contengono le diverse opzioni di risposta *solo* per le domande a scelta multipla. Devono esserci almeno due opzioni di risposta perché la domanda sia considerata a scelta multipla.
* **Domande Aperte:** Per una domanda aperta, lasciare semplicemente vuote le celle nelle colonne B, C, D, ...

**Esempio Visivo:**

![Esempio struttura file Excel](excel_example.jpg)
*(Assicurati che il file `excel_example.jpg` sia presente nel repository)*

## Come Usare l'Applicazione (Interfaccia Web)

1.  **Avvia l'App:** Esegui l'applicazione Streamlit (vedi sezione "Esecuzione Locale" o accedi all'URL se deployata).
2.  **Carica File:** Usa il riquadro "1. File Excel (.xlsx, .xls)" nella sidebar per caricare il tuo file Excel preparato.
3.  **Imposta Parametri:**
    * Inserisci il nome della **Materia**.
    * Definisci il **Numero di Verifiche** da generare.
    * Specifica il numero di **Domande a Scelta Multipla** e **Domande Aperte** desiderate per *ogni* verifica.
    * Seleziona/Deseleziona l'opzione "**Garantire test adiacenti diversi?**" (leggi le istruzioni nell'app per i requisiti sul numero di domande).
4.  **Genera:** Clicca sul pulsante "🚀 Genera Verifiche PDF".
5.  **Scarica:** Se la generazione va a buon fine (potrebbe richiedere qualche secondo), apparirà un pulsante "📥 Scarica PDF Generato" per scaricare il file PDF risultante.
6.  **Codice Sorgente:** Puoi scaricare il codice Python di questa app usando il link nella sidebar.

## Esecuzione Locale

Per eseguire EvilProf sul tuo computer:

1.  **Prerequisiti:**
    * Assicurati di avere **Python** installato (versione 3.7 o superiore).
    * Potrebbe essere necessario installare le dipendenze di sistema per `WeasyPrint` (come GTK+). Consulta la [documentazione di WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/install.html) per le istruzioni specifiche per il tuo sistema operativo (Linux, macOS, Windows).
2.  **Clona Repository:** Scarica o clona questo repository GitHub:
    ```bash
    git clone [https://github.com/subnetdusk/evilprof.git](https://github.com/subnetdusk/evilprof.git)
    cd evilprof
    ```
3.  **Installa Dipendenze Python:** Crea un ambiente virtuale (consigliato) e installa le librerie necessarie dal file `requirements.txt`:
    ```bash
    python -m venv venv
    # Attiva l'ambiente virtuale (esempi)
    # Windows: .\venv\Scripts\activate
    # Linux/macOS: source venv/bin/activate
    pip install -r requirements.txt
    ```
4.  **Avvia Streamlit:** Esegui il comando:
    ```bash
    streamlit run evilprof_app.py
    ```
5.  **Apri nel Browser:** Streamlit dovrebbe aprire automaticamente l'applicazione nel tuo browser web predefinito (solitamente all'indirizzo `http://localhost:8501`).

