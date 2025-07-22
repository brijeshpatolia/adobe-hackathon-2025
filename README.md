# Adobe India Hackathon: Connecting the Dots (Round 1A)

**Team Name:** Exemplary

**Participant:** Brijesh Patolia , Om ramanuj , Krish Jain

---

### 1. Our Approach

Our solution is built around an intelligent, multi-stage pipeline designed to adapt to the diverse nature of PDF documents. We recognized that a one-size-fits-all approach would fail, as a visually-rich flyer requires a different analysis than a standard, text-heavy report.

Our methodology is as follows:

1.  **Rich Data Extraction (`PDFExtractor`)**: We start by using the `PyMuPDF` library to extract not just text, but a comprehensive set of metadata for every text span on a page. This includes font size, font name, color, and precise bounding box coordinates. A key feature is our custom logic to accurately determine the **background color** of text spans by sampling pixels, which is crucial for our visual analysis.

2.  **Baseline Style Analysis (`StyleAnalyzer`)**: Before we can find what's special (a heading), we must first understand what's normal. This component analyzes all text spans to determine the most common font size and style, establishing a "body text" profile. This baseline is the reference against which all potential headings are compared.

3.  **Intelligent Classifier Selection**: This is the core of our adaptive strategy. A dedicated function (`is_document_visually_driven`) analyzes the document's color palette.
    * If the document is primarily **monochrome**, it is passed to our `HeadingClassifier`.
    * If the document contains a significant amount of **color**, it is passed to our `VisualClassifier`.

4.  **Dual Classification Logic**:
    * **`HeadingClassifier`**: Optimized for traditional documents, this classifier identifies headings by looking for text that stands out stylistically from the body text baseline (e.g., larger font size, bold weight).
    * **`VisualClassifier`**: Designed for flyers, invitations, and other visually complex documents. This classifier gives more weight to visual cues like distinct text colors and background colors to identify headings, as font size alone is often not a reliable indicator in these layouts.

5.  **JSON Formatting (`JSONFormatter`)**: The final stage takes the classified outline and formats it into the precise JSON structure required by the hackathon, ensuring compliance with the submission standards.

### 2. Models and Libraries Used

* **Libraries**:
    * **`PyMuPDF` (fitz)**: This is the sole external library used. It was chosen for its high performance and its powerful, low-level access to PDF content, which was essential for our detailed style and color analysis.

* **Models**:
    * **No external or pre-trained models are used.** Our solution's intelligence comes from a custom-built, lightweight system of heuristics and rule-based logic. This ensures the Docker image is small, fast, and fully compliant with the offline execution and size constraints.

### 3. How to Build and Run the Solution

The entire solution is containerized using Docker for portability and to ensure it runs consistently in the judging environment.

**Prerequisites:**
* Docker must be installed and running.

**Step 1: Build the Docker Image**

Navigate to the root directory of the project (where the `Dockerfile` is located) and execute the following command to build the image:

```bash
docker build -t adobe-hackathon-solution .
```

**Step 2: Run the Container**

To process PDFs, place them in a local input directory and create an empty local output directory. Use the command below to run the container, making sure to provide the absolute paths to your local directories. The container will automatically process all PDFs from the input folder and save the corresponding JSON files to the output folder, as per the "Expected Execution" section of the hackathon rules.

```bash
docker run --rm -v /path/to/your/local_input:/app/input -v /path/to/your/local_output:/app/output adobe-hackathon-solution
```

*(Note: Replace `/path/to/your/local_input` and `/path/to/your/local_output` with the actual paths on your machine.)*
