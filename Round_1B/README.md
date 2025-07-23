# Adobe India Hackathon: Connecting the Dots (Round 1B)

**Team Name:** Exemplary

**Participants:** Brijesh Patolia, Om Ramanuj, Krish Jain

---

## 1. Our Approach

This solution addresses the Round 1B "Persona-Driven Document Intelligence" challenge by building a sophisticated semantic analysis engine on top of our robust Round 1A structural parser. Our core philosophy is "Constraint-First Engineering," ensuring that our powerful AI pipeline operates flawlessly within the hackathon's strict offline, CPU-only, and time-limited environment.

Our methodology is an elite, **Section-First Contextual Analysis** pipeline:

* **Structural Scaffolding (1A Reuse):** We first leverage our proven `DocumentProcessor` from Round 1A to generate a high-quality, structured outline of each PDF. This provides a reliable "map" of all the headings and their locations.

* **Precise Content Isolation:** Instead of treating documents as a simple "bag of words," our system intelligently isolates the text content that belongs to each specific heading. This is achieved by slicing the full document text from the beginning of one heading to the beginning of the next, ensuring an unbreakable link between a piece of text and its parent section.

* **Context-Aware Chunking:** The isolated text for each section is then passed to a `TextChunker` (using `langchain`'s `RecursiveCharacterTextSplitter`). This breaks down the content into smaller, semantically coherent chunks that are ideal for analysis, while always retaining their link to the parent heading.

* **High-Performance Semantic Embedding:** We use a state-of-the-art sentence-transformer model to convert the persona's query and all text chunks into numerical vectors (embeddings). This is done in a single, highly optimized batch operation for maximum speed.

* **Efficient Relevance Ranking:** The relevance of each text chunk to the persona's query is calculated using a batched **dot product** operation. For the normalized embeddings our model produces, this is computationally faster than cosine similarity while being mathematically equivalent.

* **Intelligent Aggregation & Output:** The final rank for a section is determined by the score of its single most relevant text chunk. This ensures that the overall section ranking is driven by its most potent content and that the `subsection_analysis` is always populated with the most meaningful snippet, directly addressing the two most critical scoring criteria.

---

## 2. Models and Libraries Used

### Libraries:

* **PyMuPDF (fitz):** Reused from 1A for its unmatched speed in text extraction.
* **LangChain:** Used for its efficient and robust `RecursiveCharacterTextSplitter`.
* **Sentence-Transformers:** The core library for loading and running our text embedding model.
* **PyTorch:** The underlying framework for the AI model, used for all tensor and vector operations.

### Model:

* **multi-qa-MiniLM-L6-cos-v1:** This specific model was strategically chosen after thorough research. At only **80MB**, it is extremely small and fast, and it was specifically fine-tuned on over 215 million question-answer pairs. This makes it exceptionally good at "information retrieval" tasks like ours, where the "job-to-be-done" acts as a question and the document sections are potential answers. The model is included in the Docker image for complete offline execution.

---

## 3. How to Build and Run This Solution

This section provides the specific instructions for running the Round 1B solution. All commands should be executed relative to the `Round_1B` directory.

**Prerequisites:**
* Docker must be installed and running.

### Step 1: Navigate to the Round 1B Directory
After cloning the repository, first navigate into the `Round_1B` folder.
```bash
cd path/to/repository/Round_1B
```

### Step 2: Prepare Input and Output Directories
This folder should be populated with an `input/` directory that contains the `challenge1b_input.json` file and a `PDFs/` sub-folder with the required documents. An empty `output/` folder should also be present.

### Step 3: Build the Docker Image
From within the `Round_1B` directory, run the following command to build the Docker image for this specific task.
```bash
docker build -t adobe-hackathon-1b .
```

### Step 4: Run the Solution
Finally, run the container using the command below. This command mounts the input and output folders from the current (`Round_1B`) directory and runs the container in an isolated, offline environment.
```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none adobe-hackathon-1b
```
*(Note: The command above works directly on **Linux**, **macOS**, and **Windows PowerShell**. For the legacy **Windows Command Prompt (CMD)**, you must replace `${PWD}` with `%cd%`.)*

After the command finishes, the `output` folder inside `Round_1B` will contain the final `challenge1b_output.json` file.
