import os
import pandas as pd

class StoreDatasetAsCsvService:
    
    @staticmethod
    def store_json_dataset_as_csv(filename: str, data: dict[str, list]) -> str:
        if not filename or not data:
            raise ValueError("Missing 'filename' or 'data'")

        # Check if all columns have the same length
        lengths = [len(col) for col in data.values()]
        if len(set(lengths)) != 1:
            raise ValueError("All columns must have the same number of values")

        # Create a DataFrame from the data
        df = pd.DataFrame(data)
        output_path = os.path.join("dataset", filename)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

        return output_path
