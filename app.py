import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, confusion_matrix, precision_recall_curve
import shap
import joblib

# Load model and data
@st.cache_resource
def load_model_and_data():
    model = joblib.load("model.pkl")  # Replace with your model path
    data = pd.read_csv("data.csv")  # Replace with your dataset path
    return model, data

# Dashboard
st.title("Classifier Performance and Explainability Dashboard")

# Load model and data
model, data = load_model_and_data()

# Sidebar inputs
st.sidebar.header("User Inputs")
selected_threshold = st.sidebar.slider("Prediction Cutoff Probability", 0.0, 1.0, 0.5, 0.01)
selected_feature = st.sidebar.selectbox("Select Feature for SHAP Dependence Plot", data.columns[:-1])
selected_instance = st.sidebar.number_input("Select Data Point (Index)", 0, len(data) - 1, 0)

# Model predictions and probabilities
X = data.drop(columns=["target"])
y_true = data["target"]
y_pred_prob = model.predict_proba(X)[:, 1]
y_pred = (y_pred_prob >= selected_threshold).astype(int)

# Model Performance Section
st.header("Model Performance")

# Confusion Matrix
st.subheader("Confusion Matrix")
cm = confusion_matrix(y_true, y_pred)
st.write(f"Threshold: {selected_threshold}")
st.write(cm)

# ROC AUC Curve
st.subheader("ROC AUC Curve")
fpr, tpr, _ = roc_curve(y_true, y_pred_prob)
roc_auc = auc(fpr, tpr)
fig, ax = plt.subplots()
ax.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
ax.plot([0, 1], [0, 1], linestyle='--', color='gray')
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate")
ax.set_title("ROC Curve")
ax.legend()
st.pyplot(fig)

# Cumulative Precision Curve
st.subheader("Cumulative Precision Curve")
precision, recall, thresholds = precision_recall_curve(y_true, y_pred_prob)
fig, ax = plt.subplots()
ax.plot(recall, precision, label="Precision-Recall")
ax.set_xlabel("Recall")
ax.set_ylabel("Precision")
ax.set_title("Cumulative Precision Curve")
ax.legend()
st.pyplot(fig)

# SHAP Explainability Section
st.header("SHAP Explainability")

# SHAP values
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# Feature Importance
st.subheader("Feature Importance")
shap.summary_plot(shap_values[1], X, plot_type="bar", show=False)
st.pyplot(bbox_inches="tight")

# SHAP Dependence Plot
st.subheader("SHAP Dependence Plot")
fig, ax = plt.subplots()
shap.dependence_plot(selected_feature, shap_values[1], X, ax=ax, show=False)
st.pyplot(fig)

# SHAP Summary Plot
st.subheader("SHAP Summary Plot")
shap.summary_plot(shap_values[1], X, show=False)
st.pyplot(bbox_inches="tight")

# Individual Predictions Section
st.header("Individual Predictions")

# Prediction Output
st.subheader("Prediction Output")
pred_prob = y_pred_prob[selected_instance]
actual = y_true[selected_instance]
st.write(f"Predicted Probability: {pred_prob:.2f}")
st.write(f"Actual Value: {actual}")
fig, ax = plt.subplots()
ax.pie([pred_prob, 1 - pred_prob], labels=["Positive", "Negative"], autopct="%.1f%%")
ax.set_title("Prediction Probability")
st.pyplot(fig)

# Feature Contribution
st.subheader("Feature Contribution")
shap.force_plot(explainer.expected_value[1], shap_values[1][selected_instance], X.iloc[selected_instance], matplotlib=True)
st.pyplot(bbox_inches="tight")
