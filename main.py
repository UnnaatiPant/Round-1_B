import fitz  # PyMuPDF
import os
import json
from datetime import datetime

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            "page_number": i + 1,
            "text": text
        })
    return pages

def score_relevance(text, keywords):
    score = 0
    lowered = text.lower()
    for kw in keywords:
        score += lowered.count(kw.lower())
    return score

def get_keywords(persona_info):
    combined = f"{persona_info['persona']} {persona_info['job']}"
    return list(set(combined.lower().split()))

def process_documents(input_dir, persona_info):
    keywords = get_keywords(persona_info)
    results = []
    detailed = []

    for file in os.listdir(input_dir):
        if file.endswith(".pdf"):
            full_path = os.path.join(input_dir, file)
            try:
                pages = extract_text_by_page(full_path)
            except Exception as e:
                print(f"❌ Error reading {file}: {e}")
                continue

            for page in pages:
                score = score_relevance(page["text"], keywords)
                if score > 0:
                    results.append({
                        "document": file,
                        "page": page["page_number"],
                        "section_title": page["text"][:50].replace("\n", " "),
                        "importance_score": score
                    })
                    detailed.append({
                        "document": file,
                        "refined_text": page["text"][:1000],
                        "page": page["page_number"]
                    })

    results = sorted(results, key=lambda x: x["importance_score"], reverse=True)
    for idx, item in enumerate(results):
        item["importance_rank"] = idx + 1
        del item["importance_score"]

    return results, detailed

def main():
    input_dir = "input"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    print("📄 Scanning input directory...")
    try:
        files = os.listdir(input_dir)
        print("Input files found:", files)
    except Exception as e:
        print(f"❌ Failed to read input directory: {e}")
        return

    if "persona.json" not in files:
        print("❌ persona.json file is missing in input folder!")
        return

    try:
        with open(os.path.join(input_dir, "persona.json"), "r", encoding="utf-8") as f:
            persona_info = json.load(f)
        print("✅ Loaded persona:", persona_info)
    except Exception as e:
        print(f"❌ Error reading persona.json: {e}")
        return

    extracted, refined = process_documents(input_dir, persona_info)

    if not extracted:
        print("⚠️ No relevant sections found in PDFs.")
    else:
        print(f"✅ Found {len(extracted)} relevant sections.")

    output_json = {
        "metadata": {
            "documents": [f for f in files if f.endswith(".pdf")],
            "persona": persona_info.get("persona", ""),
            "job_to_be_done": persona_info.get("job", ""),
            "timestamp": datetime.now().isoformat()
        },
        "extracted_sections": extracted,
        "subsection_analysis": refined
    }

    output_path = os.path.join(output_dir, "summary.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        print(f"✅ summary.json successfully created at {output_path}")
    except Exception as e:
        print(f"❌ Failed to write summary.json: {e}")

if __name__ == "__main__":
    main()
