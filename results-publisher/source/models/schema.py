from dataclasses import dataclass

@dataclass
class Result:
    results_directory: str
    files: dict[str, str]

@dataclass
class PublishedResult:
    published_results_directory: str
    files: dict[str, str]

@dataclass
class PublishResultsRequest:
    results_directory: str

@dataclass
class PublishResultsResponse:
    message: str
    result: Result
    published_result: PublishedResult

@dataclass
class DataResultsInfo:
    database_av: str
    database_year: str
    course_shortname: str

