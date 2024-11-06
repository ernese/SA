import os
import pandas as pd

class Saver:
    """
    A class responsible for saving the aggregated content (DataFrame) in CSV and JSON formats.
    """

    def __init__(self, content, save_dir='./data'):
        """
        Initializes the Saver class.

        Parameters:
            content: The aggregated content (usually a DataFrame containing scraped news data).
            save_dir (str): Directory where the files will be saved.
        """
        self.content = content
        self.save_dir = save_dir
        self.ensure_dir_exists()

    def ensure_dir_exists(self):
        """Ensure the save directory exists."""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def save(self):
        """
        Saves the aggregated content to CSV and JSON files.
        """
        if isinstance(self.content, pd.DataFrame):
            self.save_dataframe()
        else:
            print("Unsupported content format for saving. Expected DataFrame.")

    def save_dataframe(self):
        """
        Saves the aggregated DataFrame content to CSV and JSON.
        """
        try:
            csv_path = os.path.join(self.save_dir, 'news_info.csv')
            json_path = os.path.join(self.save_dir, 'news_info.json')

            self.content.to_csv(csv_path, index=False)
            self.content.to_json(json_path, orient='records', lines=True)
            print(f"Data saved successfully as CSV and JSON in {self.save_dir}.")
        except Exception as e:
            print(f"Error saving DataFrame content: {e}")
