import pandas as pd


def split_data(df: pd.DataFrame,
               test_ratio: float,
               seed: int) -> tuple[pd.DataFrame]:
    """
    Split the dataset into train and test sets by randomly shuffling the order of the data,
    while fixing the random seed.

    Args:
        df (pd.DataFrame): The DataFrame to split.
        test_ratio (float): The proportion of data to use for testing.
        seed (int): The random seed for ensuring reproducibility.

    Returns:
        tuple[pd.DataFrame]: X_train, y_train, X_test, y_test
    """
    pass
