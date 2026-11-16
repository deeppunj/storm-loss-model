# step 8: a small language model reads each report and answers three questions
# the model runs on my Mac through Ollama (ollama.com), nothing goes online.
# before running:  ollama pull llama3.2:3b   (the Ollama app has to be open)
import json
import urllib.request

import pandas as pd

import config

# version 1 is the first prompt. Reading 15 of its false alarms showed that none of them
# mentions a person, and about half mention damage to homes or buildings, so version 2
# says that damage alone does not mean someone was hurt. Both are kept to compare them.
PROMPTS = {
    1: """Below is a tornado report from the NOAA Storm Events Database.
Answer only from what the text says. If the text does not mention something, answer no or none.

1. injured: does the text say that one or more people were injured? (yes or no)
2. killed: does the text say that one or more people were killed? (yes or no)
3. rating: the EF or F rating written in the text, as a digit 0 to 5, or none if no rating is written.

Report:
{text}""",
    2: """Below is a tornado report from the NOAA Storm Events Database.
Answer only from what the text says.

1. injured: answer yes only if the text clearly says that a person was injured or hurt.
   Damage to homes, buildings, vehicles or trees does not mean that anyone was injured.
   If the text does not say that a person was injured, answer no.
2. killed: answer yes only if the text clearly says that a person was killed or died.
   Otherwise answer no.
3. rating: the EF or F rating written in the text, as a digit 0 to 5, or none if no rating is written.
   Road names such as F.M. 1536 (Farm to Market road) are not ratings.

Report:
{text}""",
}
PROMPT = PROMPTS[config.PROMPT_VERSION] # this picks up the Prompt from config.py
ANSWERS_FILE = config.results_file("llm_answers")

# Ollama can force the reply into this shape, so every answer has the same fields
ANSWER_SHAPE = {
    "type": "object",
    "properties": {
        "injured": {"type": "string", "enum": ["yes", "no"]},
        "killed": {"type": "string", "enum": ["yes", "no"]},
        "rating": {"type": "string", "enum": ["0", "1", "2", "3", "4", "5", "none"]},
    },
    "required": ["injured", "killed", "rating"],
}


def ask_model(text):
    body = {
        "model": config.LLM_MODEL,
        "prompt": PROMPT.format(text=text),
        "format": ANSWER_SHAPE,
        "stream": False,
        "options": {"temperature": 0, "seed": config.RANDOM_SEED},  # same answer every run
    }
    request = urllib.request.Request(config.OLLAMA_URL + "/api/generate",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as reply:
        return json.loads(reply.read())["response"]


reports = pd.read_csv(config.NARRATIVES_FILE)
sample = reports[reports["in_llm_sample"]]

# answers already saved are not asked again, so I can stop and restart
config.RESULTS_DIR.mkdir(exist_ok=True)
if ANSWERS_FILE.exists():
    done = pd.read_csv(ANSWERS_FILE)
    rows = done.to_dict("records")
else:
    rows = []
done_ids = {row["event_id"] for row in rows}

try:
    urllib.request.urlopen(config.OLLAMA_URL, timeout=5)
except OSError:
    raise SystemExit("Ollama does not answer. Open the Ollama app and run: ollama pull "
                     + config.LLM_MODEL)

todo = sample[~sample["event_id"].isin(done_ids)]
print("Prompt version", config.PROMPT_VERSION)
print(f"Reports to read: {len(todo)} (already done: {len(done_ids)})")

for i, (_, report) in enumerate(todo.iterrows(), start=1):
    raw = ask_model(report["event_narrative"])
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError:
        answer = {}   # kept as empty, step 9 counts these
    rows.append({"event_id": report["event_id"],
                 "llm_injured": answer.get("injured"),
                 "llm_killed": answer.get("killed"),
                 "llm_rating": answer.get("rating"),
                 "raw_reply": raw})
    # save every 25 reports
    if i % 25 == 0 or i == len(todo):
        pd.DataFrame(rows).to_csv(ANSWERS_FILE, index=False)
        print(i, "of", len(todo))

print("Saved", ANSWERS_FILE)
