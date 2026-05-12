import mlflow
import mlflow.sklearn
import os

def clean_filename(path):
    import os
    return os.path.basename(path).replace(".csv", "")


def log_model(model, model_name, dataset_name, csv_file_path):

    file_name = os.path.basename(csv_file_path)
    run_name = f"{model_name}_{dataset_name}_{file_name}"

    with mlflow.start_run(run_name=run_name):

        mlflow.sklearn.log_model(model, "model")

        mlflow.set_tag("model_name", model_name)
        mlflow.set_tag("dataset", dataset_name)
        mlflow.set_tag("csv_file", file_name)
        mlflow.set_tag("run_name", run_name)

        print(f"Logged model: {run_name}")