from pydantic import BaseModel
import typing as t
import dateutil.parser


def time2timestamp(time_iso8601: str):
    d = dateutil.parser.parse(time_iso8601).timestamp()
    return int(d)


class Author(BaseModel):
    login: str


class Assets(BaseModel):
    url: str
    id: int
    name: str
    uploader: Author
    browser_download_url: str


class Release(BaseModel):
    url: str
    tag_name: str
    assets_url: str
    upload_url: str
    html_url: str
    id: int
    author: Author
    assets: t.Optional[t.List[t.Optional[Assets]]]
    body: t.Optional[str]
    published_at: str

    published_at_timestamp: t.Optional[int]

    def __init__(self, **data):
        super().__init__(**data)
        self.published_at_timestamp = time2timestamp(self.published_at)
