# EvilProf 😈

Generatore di Verifiche Casuali da Excel a PDF - Versione Streamlit

Questa versione è hostata su [evilprof.streamlit.app](https://evilprof.streamlit.app/)

## Descrizione

**EvilProf** è un'applicazione web realizzata con Streamlit che permette di generare rapidamente file PDF contenenti verifiche personalizzate. L'applicazione legge le domande (a scelta multipla e/o aperte) da un file Excel strutturato in modo specifico e crea un numero definito di verifiche, ciascuna contenente un mix casuale di domande scelte dall'utente.

Funzionalità chiave è la possibilità di generare test adiacenti completamente diversi (con nessuna domanda in comune 😈).

## Caratteristiche Principali

* **Input da Excel:** Carica facilmente le tue domande da un file `.xlsx` o `.xls`.
* **Tipi di Domande:** Supporta sia domande a scelta multipla (con risposte casualizzate) sia domande a risposta aperta.
* **Personalizzazione:** Scegli il numero di verifiche da generare, il numero di domande per tipo (multiple/aperte) per ciascuna verifica e il nome della materia.
* **Randomizzazione Avanzata:** Le domande in ogni verifica sono selezionate casualmente dal pool disponibile nel file Excel. L'ordine delle risposte multiple è casuale.
* **Diversità Migliorata:** L'applicazione utilizza una tecnica di **Campionamento Casuale Ponderato Senza Reinserimento (WRSwOR)** basata sull'algoritmo A di Efraimidis e Spirakis (descritto in [questo paper](https://ethz.ch/content/dam/ethz/special-interest/baug/ivt/ivt-dam/vpl/reports/1101-1200/ab1141.pdf)) per selezionare le domande. Questo metodo:
    * **Garantisce** che le domande usate in una verifica non vengano ripetute nella verifica *immediatamente successiva*.
    * **Favorisce statisticamente** la selezione di domande che non vengono utilizzate da più tempo, promuovendo una maggiore rotazione e diversità tra le verifiche nel lungo periodo, senza richiedere un numero eccessivo di domande nel file di partenza.
* **Output PDF:** Genera un singolo file PDF pronto per la stampa, con ogni verifica che inizia su una nuova pagina e un'intestazione per nome, data e classe.

## Struttura del File Excel

Perché l'applicazione funzioni correttamente, il file Excel deve rispettare la seguente struttura **senza intestazioni di colonna**:

* **Colonna A:** Contiene il testo completo della domanda.
* **Colonne B, C, D, ...:** Contengono le diverse opzioni di risposta *solo* per le domande a scelta multipla. Devono esserci almeno due opzioni di risposta perché la domanda sia considerata a scelta multipla.
* **Domande Aperte:** Per una domanda aperta, lasciare semplicemente vuote le celle nelle colonne B, C, D, ...

*Esempio:*

![Esempio struttura file Excel](excel_example.jpg)

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

