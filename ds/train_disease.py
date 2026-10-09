"""
ds/train_disease.py — Symptom-text -> disease classifier (REAL data).
Data: knowledge_base/Symptom2Disease.csv (label, text), stratified 80/20.
Models: TF-IDF(1-2gram) + LogReg(balanced) vs LinearSVC(calibrated).
Outputs: models/disease_clf.joblib, disease_labels.json, disease_metrics.csv,
         disease_confusion.png
"""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
MODEL_DIR = HERE / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def main():
    from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import LinearSVC
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import (accuracy_score, f1_score, top_k_accuracy_score,
                                 confusion_matrix)

    df = pd.read_csv(HERE.parent / "knowledge_base" / "Symptom2Disease.csv")
    df["text"] = df["text"].astype(str).str.strip().str.lower()
    df = df.dropna(subset=["label", "text"]).drop_duplicates()
    print(f"rows={len(df)} diseases={df['label'].nunique()}")
    X, y = df["text"].astype(str).tolist(), df["label"].astype(str).tolist()
    labels = sorted(set(y))
    print(f"top labels: {pd.Series(y).value_counts().head(5).to_dict()}")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    def make(clf):
        return Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=20000,
                                                   sublinear_tf=True)),
                         ("clf", clf)])

    # CalibratedClassifierCV wraps the full SVC pipeline (needs probas for top-3):
    svc_pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=20000, sublinear_tf=True)),
                         ("clf", LinearSVC(class_weight="balanced", C=0.5))])
    models = {
        "LogReg-TFIDF": make(LogisticRegression(class_weight="balanced", max_iter=2000, C=1.0)),
        "CalibratedSVC-TFIDF": CalibratedClassifierCV(svc_pipe, cv=3),
    }

    rows = []
    fitted = {}
    for name, m in models.items():
        m.fit(Xtr, ytr)
        fitted[name] = m
        pred = m.predict(Xte)
        try:
            top3 = top_k_accuracy_score(yte, m.predict_proba(Xte), k=3,
                                        labels=m.classes_)
        except Exception:
            top3 = float("nan")
        rows.append({"Model": name,
                     "Accuracy": round(float(accuracy_score(yte, pred)), 4),
                     "F1-macro": round(float(f1_score(yte, pred, average="macro")), 4),
                     "Top-3": round(float(top3), 4) if top3 == top3 else "n/a"})
        print(rows[-1])

    best_name = max(rows, key=lambda r: r["F1-macro"] if isinstance(r["F1-macro"], float) else -1)["Model"]
    best = fitted[best_name]
    joblib.dump(best, MODEL_DIR / "disease_clf.joblib")
    with open(MODEL_DIR / "disease_labels.json", "w") as f:
        json.dump({"model": best_name, "labels": sorted(set(y))}, f)
    mt = pd.DataFrame(rows)
    mt["Data Source"] = f"Symptom2Disease (n={len(df)}, real)"
    mt.to_csv(MODEL_DIR / "disease_metrics.csv", index=False)
    print(mt.to_string(index=False))

    # Confusion matrix (top-12 diseases by support)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    top12 = pd.Series(yte).value_counts().head(12).index.tolist()
    mask = pd.Series(yte).isin(top12)
    cm = confusion_matrix([t for t, k in zip(yte, mask.tolist()) if k],
                          [p for p, k in zip(best.predict(Xte).tolist(), mask.tolist()) if k],
                          labels=top12)
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(top12)), top12, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(top12)), top12, fontsize=8)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix top-12 ({best_name})")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(MODEL_DIR / "disease_confusion.png", dpi=150)
    plt.close()
    print(f"Saved disease_clf.joblib ({best_name}) + metrics + confusion")

    # Latency + size probe
    import time
    t0 = time.time()
    best.predict(Xte[:50])
    print(f"latency: {(time.time()-t0)/50*1000:.1f} ms/sample | "
          f"size: {(MODEL_DIR/'disease_clf.joblib').stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
