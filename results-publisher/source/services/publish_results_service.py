from models.schema import Result, PublishedResult
from core.result_builder import ResultBuilder
from core.analysis_info_reader import AnalysisInfoReader
from core.publish_directory_builder import PublishPathBuilder
from core.results_mapper import ResultMapper
from pathlib import Path
import shutil

class PublishResultsService:

    def __init__(self):
        self.publish_directory = "/app/published_results"
        self.result_mapper = ResultMapper()
        self.result_builder = ResultBuilder()
        self.analysis_info_reader = AnalysisInfoReader()
        self.publish_path_builder = PublishPathBuilder()

    def publish_results(self, results_directory: str) -> tuple[Result, PublishedResult]:
        """
        Publishes results from the specified directory to the publish directory.
            - results_directory: Path to the directory containing the analysis results to publish.
        Returns a tuple containing the original result and the published result.
        Raises an exception if the results cannot be published.
        """
        try:
            if not self.publish_directory:
                raise ValueError("Publish directory is not configured")
            
            analysis_info = self.analysis_info_reader.read_data_results(results_directory)
            result = self.result_builder.build_result(results_directory)
            publish_path = self.publish_path_builder.build_publish_dir(analysis_info, self.publish_directory)
            file_maps = self.result_mapper.get_file_maps()
            publised_result = PublishedResult(published_results_directory=publish_path, files={})

            for file_key, source_file in result.files.items():
                target_name = file_maps.get(source_file)
                if target_name is None:
                    raise ValueError(f"No target name mapping found for file: {source_file}")

                source_path = Path(f"{results_directory}/{source_file}")
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")

                target_path = Path(publish_path) / target_name
                shutil.copy2(source_path, target_path)

                publised_result.files[file_key] = str(target_path)

            return result, publised_result

        except Exception as e:
            print(f"An error occurred while publishing results: {e}")