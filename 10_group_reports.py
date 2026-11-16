# step 10: group all reports by what they describe
# each text becomes a list of numbers (an embedding); texts about similar damage
# get similar numbers. k-means then puts close ones into the same group
# before running:  ollama pull nomic-embed-text
import json
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

import config


def embed(texts):
    # nomic-embed-text wants the task written in front of each text
    body = {"model": config.EMBED_MODEL,
            "input": ["clustering: " + t for t in texts]}
    request = urllib.request.Request(config.OLLAMA_URL + "/api/embed",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as reply:
        return json.loads(reply.read())["embeddings"]


reports = pd.read_csv(config.NARRATIVES_FILE)
texts = reports["event_narrative"].tolist()

# the embeddings take a few minutes, so I save them and reuse them
if config.EMBEDDINGS_FILE.exists():
    vectors = np.load(config.EMBEDDINGS_FILE)
else:
    vectors = []
    for start in range(0, len(texts), 50):
        vectors += embed(texts[start:start + 50])
        print(min(start + 50, len(texts)), "of", len(texts))
    vectors = np.array(vectors)
    np.save(config.EMBEDDINGS_FILE, vectors)

if len(vectors) != len(reports):
    raise SystemExit("Saved embeddings do not match the reports. "
                     "Delete data/raw/embeddings.npy and run again.")

# same length for every vector, so only the direction counts
vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

# how many groups: silhouette score, higher = groups sit further apart
scores = {}
for k in range(3, 9):
    labels = KMeans(n_clusters=k, n_init=10, random_state=config.RANDOM_SEED).fit_predict(vectors)
    scores[k] = silhouette_score(vectors, labels)
    print("k =", k, "silhouette", round(scores[k], 3))
k = config.N_CLUSTERS or max(scores, key=scores.get)
print("Using", k, "groups")

reports["group"] = KMeans(n_clusters=k, n_init=10,
                          random_state=config.RANDOM_SEED).fit_predict(vectors)

# words that stand out in each group help me name it
tfidf = TfidfVectorizer(stop_words="english", min_df=5)
words = tfidf.fit_transform(texts)
vocab = np.array(tfidf.get_feature_names_out())

# a word counts for a group when it is more common there than in all reports
all_weight = np.asarray(words.mean(axis=0)).ravel()

rows = []
for g in range(k):
    part = reports[reports["group"] == g]
    group_weight = np.asarray(words[(reports["group"] == g).to_numpy()].mean(axis=0)).ravel()
    mean_weight = group_weight - all_weight
    rows.append({"group": g,
                 "reports": len(part),
                 "top_words": ", ".join(vocab[mean_weight.argsort()[::-1][:8]]),
                 "median_damage_usd": part["damage_usd"].median(),
                 "total_damage_musd": part["damage_usd"].sum() / 1e6,
                 "with_injury_pct": 100 * (part["injuries_direct"] > 0).mean(),
                 "mean_noaa_rating": part["noaa_rating"].mean()})
groups = pd.DataFrame(rows).round(2)
print(groups.to_string(index=False))
groups.to_csv(config.RESULTS_DIR / "report_groups.csv", index=False)

# three example reports per group, to read before naming the groups
examples = pd.concat([reports[reports["group"] == g].sample(3, random_state=config.RANDOM_SEED)
                      for g in range(k)])
examples[["group", "event_id", "damage_usd", "event_narrative"]].to_csv(
    config.RESULTS_DIR / "report_group_examples.csv", index=False)

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(groups["group"].astype(str), groups["median_damage_usd"] / 1000)
ax.set_xlabel("group")
ax.set_ylabel("median damage per record (thousand USD)")
ax.set_title("Tornado reports grouped by their text, Texas 2000 to 2024")
fig.tight_layout()
fig.savefig(config.RESULTS_DIR / "report_groups.png", dpi=150)
print("Saved results/report_groups.csv, report_group_examples.csv and report_groups.png")
