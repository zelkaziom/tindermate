from datetime import datetime

from pydantic import BaseModel, Field

from tinder.utils import calculate_age, resolve_gender
from type_aliases import AnyDict


class Interest(BaseModel):
    id: str
    name: str
    is_common: bool | None = None


class UserInterests(BaseModel):
    selected_interests: list[Interest]


class ExperimentInfo(BaseModel):
    user_interests: UserInterests


class Job(BaseModel):
    title: dict[str, str] | None = None
    company: dict[str, str] | None = None

    def as_string(self) -> str | None:
        if self.title is not None:
            return self.title.get("name")
        if self.company is not None:
            return self.company.get("name")
        return None


class School(BaseModel):
    name: str


class City(BaseModel):
    name: str


class Photo(BaseModel):
    id: str
    url: str


class User(BaseModel):
    id: str = Field(alias="_id")
    bio: str | None = None
    birth_date: datetime | None = None
    gender: int
    name: str
    photos: list[Photo]

    @property
    def age(self) -> int | None:
        if self.birth_date is None:
            return None
        return calculate_age(self.birth_date.date())

    @property
    def gender_str(self) -> str | None:
        return resolve_gender(self.gender)

    @property
    def bio_oneline(self) -> str | None:
        if self.bio is None:
            return None
        lines = []
        for line in self.bio.split("\n"):
            if line and (line := line.strip()):
                lines.append(line)
        return "; ".join(lines)


class Country(BaseModel):
    name: str


class PositionInfo(BaseModel):
    country: Country
    timezone: str


class LikedUser(User):
    jobs: list[Job] = Field(default=[])
    schools: list[School] = Field(default=[])
    city: City | None = None

    @property
    def school(self) -> str | None:
        return None if len(schools := self.schools) == 0 else schools[0].name

    @property
    def job(self) -> str | None:
        return None if len(jobs := self.jobs) == 0 else jobs[0].as_string()


class UserDetail(LikedUser):
    user_interests: UserInterests = UserInterests(selected_interests=[])

    @property
    def interests(self) -> list[str]:
        return [interest.name for interest in self.user_interests.selected_interests]


class CurrentUser(UserDetail):
    age_filter_min: int
    age_filter_max: int
    gender_filter: int
    distance_filter: int
    create_date: datetime
    pos_info: PositionInfo
    discoverable: bool

    @property
    def profile_link(self) -> str:
        return "https://tinder.com/app/profile"

    @property
    def gender_filter_str(self) -> str | None:
        return resolve_gender(self.gender_filter)


class LikedUserResult(BaseModel):
    type: str
    distance_mi: float
    user: LikedUser
    expire_time: int
    experiment_info: ExperimentInfo | None = None


class Message(BaseModel):
    match_id: str
    sent_date: datetime
    message: str
    to: str
    from_: str = Field(alias="from")
    timestamp: int

    def dict(self, *args, **kwargs) -> AnyDict:
        return super().dict(*args, **kwargs) | {"from": self.from_}


class Match(BaseModel):
    seen: AnyDict
    id: str
    closed: bool
    created_date: datetime
    dead: bool
    last_activity_date: datetime
    message_count: int
    messages: list[Message]
    participants: list[str]
    pending: bool
    is_super_like: bool
    is_boost_match: bool
    is_super_boost_match: bool
    is_primetime_boost_match: bool
    is_experiences_match: bool
    is_fast_match: bool
    is_preferences_match: bool
    is_matchmaker_match: bool
    is_opener: bool
    has_shown_initial_interest: bool
    person: User
    is_archived: bool

    @property
    def open_messages_link(self) -> str:
        return f"https://tinder.com/app/messages/{self.id}"


class MatchDetail(Match):
    person: UserDetail

    @classmethod
    def parse_obj(cls, obj: AnyDict) -> "MatchDetail":
        if "id" in obj["person"]:
            obj["person"]["_id"] = obj["person"]["id"]
        return super().parse_obj(obj)  # noqa
