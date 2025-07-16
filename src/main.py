from src.components.pdf_extractor import PDFExtractor

extractor = PDFExtractor()
spans = extractor.extract(r"C:\Users\Brijesh\Downloads\E0CCG5S239.pdf")
for span in spans:
    print(span)