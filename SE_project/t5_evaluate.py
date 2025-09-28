from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import load_metric
import pandas as pd

# Load model
tokenizer = AutoTokenizer.from_pretrained("t5_finetuned_asl/final_model")
model = AutoModelForSeq2SeqLM.from_pretrained("t5_finetuned_asl/final_model")

# Load dataset
df = pd.read_csv("asl_data.csv")

preds, refs = [], []
exact_match = 0

for i, row in df.iterrows():
    gloss = row["input"]
    target = row["target"].strip()
    input_text = "fix: " + gloss
    input_ids = tokenizer(input_text, return_tensors="pt").input_ids
    output = model.generate(input_ids, max_length=50)
    pred = tokenizer.decode(output[0], skip_special_tokens=True)

    preds.append(pred)
    refs.append([target])
    if pred.strip().lower() == target.lower():
        exact_match += 1

# Exact Match Accuracy
accuracy = round((exact_match / len(df)) * 100, 2)
print("🎯 Exact Match Accuracy:", accuracy, "%")

# BLEU Score
bleu = load_metric("bleu")
bleu.add_batch(predictions=[p.split() for p in preds], references=[[r[0].split()] for r in refs])
bleu_score = round(bleu.compute()["bleu"] * 100, 2)
print("📘 BLEU Score:", bleu_score)

# Save for report
output_df = pd.DataFrame({"input": df["input"], "target": df["target"], "prediction": preds})
output_df.to_csv("t5_predictions.csv", index=False)
