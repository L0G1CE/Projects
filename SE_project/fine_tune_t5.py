from transformers import T5Tokenizer, T5ForConditionalGeneration, Seq2SeqTrainer, Seq2SeqTrainingArguments, DataCollatorForSeq2Seq
from datasets import load_dataset, Dataset
import pandas as pd

# Load CSV
df = pd.read_csv("asl_data.csv")
dataset = Dataset.from_pandas(df)

# Model and tokenizer
model_name = "t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Preprocess
def preprocess(example):
    input_text = "fix: " + example["input"]
    model_input = tokenizer(input_text, max_length=64, truncation=True, padding="max_length")
    label = tokenizer(example["target"], max_length=64, truncation=True, padding="max_length")
    model_input["labels"] = label["input_ids"]
    return model_input

tokenized = dataset.map(preprocess, remove_columns=["input", "target"])

# Training arguments
args = Seq2SeqTrainingArguments(
    output_dir="t5_finetuned_asl",
    per_device_train_batch_size=4,
    num_train_epochs=20,
    learning_rate=5e-4,
    save_total_limit=1,
    fp16=False,
    logging_steps=10
)

trainer = Seq2SeqTrainer(
    model=model,
    args=args,
    train_dataset=tokenized,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
)

# Train
trainer.train()

# Save model
model.save_pretrained("t5_finetuned_asl/final_model")
tokenizer.save_pretrained("t5_finetuned_asl/final_model")
print("✅ Fine-tuning complete.")
