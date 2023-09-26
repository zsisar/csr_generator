# If you are using PyTorch backendpy
pip install torch==2.0.1
pip install transformers @ git+https://github.com/huggingface/transformers@de9255de27abfcae4a1f816b904915f0b1e23cd9
#lightning @ git+https://github.com/Lightning-AI/lightning@master
pip install tokenizers==0.13.3
pip install peft @ git+https://github.com/huggingface/peft.git@9f7492577ff91c51077308f98dade45bf32c268a
pip install jsonargparse[signatures]  # CLI
pip install bitsandbytes==0.39.1 # quantize
pip install accelerate @ git+https://github.com/huggingface/accelerate@e0f5e030098aada5e112708eee3537475dea3a83
pip install datasets==2.13.1  # quantize/gptq.py
pip install zstandard==0.19.0  # prepare_redpajama.py
pip install scipy
pip install loralib==0.1.1
pip install einops==0.6.1


def print_trainable_parameters(model):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}"
    )


def print_trainable_parameters(model):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}"
    )


from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["query_key_value"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, config)
print_trainable_parameters(model)


training_args = transformers.TrainingArguments(
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=True,
    save_total_limit=4,
    logging_steps=25,
    output_dir="output_dir", # give the location where you want to store checkpoints 
    save_strategy='epoch',
    optim="paged_adamw_8bit",
    lr_scheduler_type = 'cosine',
    warmup_ratio = 0.05,
)

trainer = transformers.Trainer(
    model=model,
    train_dataset=data,
    args=training_args,
    data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
)


model.config.use_cache = False  # silence the warnings. Please re-enable for inference!
trainer.train()


model.save_pretrained('location where you  want the model to be stored')


config = PeftConfig.from_pretrained("location where new model is stored")
model = AutoModelForCausalLM.from_pretrained(
    config.base_model_name_or_path,
#     load_in_8bit=True,
#     device_map='auto',
    trust_remote_code=True,

)

tokenizer = AutoTokenizer.from_pretrained(
    config.base_model_name_or_path)

model_inf = PeftModel.from_pretrained(model,"location where new model is stored" )



# create your own prompt  
prompt = f"""
    <human>: How can i use BDB Data Science LAB?
    <assistant>: 
    """.strip()

# encode the prompt 
encoding = tokenizer(prompt, return_tensors= "pt").to(model.device)

# set teh generation configuration params 
gen_config = model_inf.generation_config
gen_config.max_new_tokens = 200
gen_config.temperature = 0.2
gen_config.top_p = 0.7
gen_config.num_return_sequences = 1
gen_config.pad_token_id = tokenizer.eos_token_id
gen_config.eos_token_id = tokenizer.eos_token_id

# do the inference 
with torch.inference_mode():
    outputs = model.generate(input_ids = encoding.input_ids, attention_mask = encoding.attention_mask,generation_config = gen_config )
print(tokenizer.decode(outputs[0], skip_special_tokens = True ))