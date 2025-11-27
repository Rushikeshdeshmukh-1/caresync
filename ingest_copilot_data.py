from services.copilot_rag import CoPilotRAG
import logging

logging.basicConfig(level=logging.INFO)

def main():
    rag = CoPilotRAG()
    file_path = r"C:\Users\RUSHIKESH\Desktop\my all projects\2\data\AyurGenixAI_Dataset.xlsx"
    rag.ingest_excel(file_path)

if __name__ == "__main__":
    main()
