# services/model/training/main.py

"""
Brain-storm: how to train the data:
steps:
    1- selecotr
    2- save the best parametrs (MLflow)
    3- run the main model
"""


def load_data():
    """
    load data, with duckdb and return it in pd.Dataframe format
    """
    # TODO: Implement data loading logic → KAN-9
    return None


def split_data(df):
    """
    split data, based on the configurations' setup and return them
    """
    # TODO: Implement data splitting logic → KAN-9
    return None, None, None, None


def find_params(X_train, y_train):
    """
    Find best parameters for the training and so on
    """
    # TODO: Implement slector for finding best params → KAN-9
    return None


def train_model(X_train, y_train, best_params):
    """
    train data based on the best parameters
    """
    # TODO: Implement the logic for training the data → KAN-10


def evaluate(model, X_test, y_test):
    """
    apply the evaluations test based on the requested one in config
    It may be a whole module of itself!
    """
    # TODO: Implement the evaluations metrics → KAN-10


def run_training():
    # 1. Get data
    df = load_data()

    # 2. Split data
    X_train, X_test, y_train, y_test = split_data(df)

    # 3. Find params
    best_params = find_params(X_train, y_train)

    # 4. Train final model
    model = train_model(X_train, y_train, best_params)

    # 5. Evaluate
    evaluate(model, X_test, y_test)


if __name__ == "__main__":
    run_training()
