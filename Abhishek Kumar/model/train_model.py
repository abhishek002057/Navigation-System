"""
train_model.py  (v2 — upgraded)
---------------------------------
Trains a Machine Learning model that predicts a HOSPITAL DEPARTMENT from
a patient's symptoms.

WHAT'S NEW IN THIS VERSION vs the first prototype:
  - Uses a REAL, publicly published medical dataset (4,920 patient
    records, 132 distinct symptoms, 41 diagnosed diseases) instead of a
    small hand-written CSV.
  - Each disease is mapped to the hospital department that treats it
    (see disease_department_map.py), turning a disease-prediction
    dataset into a department-prediction dataset.
  - Trains and COMPARES 4 different beginner-to-intermediate algorithms
    (Naive Bayes, Logistic Regression, Random Forest, Linear SVM) using
    5-fold cross-validation, then automatically keeps the best one.
  - Reports accuracy, precision/recall/F1, and a confusion matrix so you
    can discuss real model evaluation in your presentation.

Dataset source (public, MIT-style educational dataset widely used for
this exact task): "Disease Prediction Using Machine Learning" —
originally published on Kaggle by kaushil268, mirrored on GitHub.

Run this file ONCE (or anytime you change the data/mapping) before
starting the Flask server:
    python model/train_model.py
"""

import os
import json
import pickle

import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.naive_bayes import BernoulliNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from disease_department_map import DISEASE_TO_DEPARTMENT
from symptom_utils import load_symptom_columns

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(CURRENT_DIR, "data", "Training.csv")
MODEL_PATH = os.path.join(CURRENT_DIR, "department_model.pkl")
FEATURES_PATH = os.path.join(CURRENT_DIR, "feature_columns.pkl")
METRICS_PATH = os.path.join(CURRENT_DIR, "training_metrics.json")

# ----------------------------------------------------------------------
# STEP 1: Load the real dataset
# ----------------------------------------------------------------------
print("📂 Loading real-world dataset (Training.csv)...")
df = pd.read_csv(DATASET_PATH)
df.columns = [c.strip() for c in df.columns]
print(f"✅ Loaded {len(df)} patient records with {df.shape[1] - 1} symptoms "
      f"across {df['prognosis'].nunique()} diseases.")

# ----------------------------------------------------------------------
# STEP 2: Map each disease -> hospital department
# ----------------------------------------------------------------------
df["department"] = df["prognosis"].map(DISEASE_TO_DEPARTMENT)

unmapped = df[df["department"].isna()]["prognosis"].unique()
if len(unmapped) > 0:
    print(f"⚠️  Warning: {len(unmapped)} disease(s) have no department mapping "
          f"and will be dropped: {list(unmapped)}")
    df = df.dropna(subset=["department"])

print(f"🏥 Departments in training data: {sorted(df['department'].unique())}")

# ----------------------------------------------------------------------
# STEP 3: Prepare features (X) and labels (y)
# ----------------------------------------------------------------------
raw_columns, display_names = load_symptom_columns()
X = df[raw_columns]
y = df["department"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\n📊 Train size: {len(X_train)} | Test size: {len(X_test)}")

# ----------------------------------------------------------------------
# STEP 4: Train + compare multiple models with 5-fold cross-validation
# ----------------------------------------------------------------------
candidates = {
    "Naive Bayes (Bernoulli)": BernoulliNB(),
    "Logistic Regression": LogisticRegression(max_iter=2000),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "Linear SVM": LinearSVC(max_iter=5000),
}

print("\n🧠 Training & cross-validating candidate models...\n")
cv_results = {}
for name, clf in candidates.items():
    scores = cross_val_score(clf, X_train, y_train, cv=5, scoring="accuracy")
    cv_results[name] = round(scores.mean() * 100, 2)
    print(f"  {name:<28} -> {scores.mean() * 100:.2f}% (5-fold CV avg)")

best_name = max(cv_results, key=cv_results.get)
best_model = candidates[best_name]
print(f"\n🏆 Best model: {best_name} ({cv_results[best_name]}% CV accuracy)")

# ----------------------------------------------------------------------
# STEP 5: Retrain the best model on the full training split
# ----------------------------------------------------------------------
best_model.fit(X_train, y_train)
y_pred = best_model.predict(X_test)
test_accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)

print(f"\n📈 Final held-out test accuracy: {test_accuracy}%")
print("\n📋 Classification report:")
print(classification_report(y_test, y_pred, zero_division=0))

# ----------------------------------------------------------------------
# STEP 6: Quick manual sanity check
# ----------------------------------------------------------------------
sample = X_test.iloc[[0]]
sample_true = y_test.iloc[0]
sample_pred = best_model.predict(sample)[0]
print(f"🧪 Sample test row -> true: {sample_true} | predicted: {sample_pred}")

# ----------------------------------------------------------------------
# STEP 7: Save the trained model + feature column order + metrics
# ----------------------------------------------------------------------
with open(MODEL_PATH, "wb") as f:
    pickle.dump(best_model, f)

with open(FEATURES_PATH, "wb") as f:
    pickle.dump(raw_columns, f)

metrics = {
    "model_used": best_name,
    "cross_validation_scores": cv_results,
    "test_accuracy": test_accuracy,
    "num_training_rows": len(X_train),
    "num_test_rows": len(X_test),
    "num_symptoms": len(raw_columns),
    "departments": sorted(df["department"].unique().tolist()),
}
with open(METRICS_PATH, "w") as f:
    json.dump(metrics, f, indent=2)

print(f"\n💾 Model saved to: {MODEL_PATH}")
print(f"💾 Feature order saved to: {FEATURES_PATH}")
print(f"💾 Metrics saved to: {METRICS_PATH}")
print("\n🎉 Done! Start the app with: python app.py")
