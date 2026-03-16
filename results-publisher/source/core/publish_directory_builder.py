from pathlib import Path
from models.schema import DataResultsInfo


class PublishPathBuilder:
    def build_publish_dir(
        self,
        data_results: DataResultsInfo,
        production_dir: str,
    ) -> str:
        """
        Build and create the publish directory for the analysis results.

        Final path format:
            /production_dir/year/av/shortname

        Args:
            data_results: Object with database_year, database_av and course_shortname.
            production_dir: Base production directory.

        Returns:
            The full path to the created/existing directory.
        """
        final_path = (
            Path(production_dir)
            / data_results.database_year
            / data_results.database_av
            / data_results.course_shortname
        )

        final_path.mkdir(parents=True, exist_ok=True)

        return str(final_path)