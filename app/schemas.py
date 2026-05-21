from pydantic import BaseModel, Field


class CardBase(BaseModel):
    holder: str = Field(min_length=1)
    role: str = Field(min_length=1)
    status: str = "active"
    wallet_linked: bool = False
    wallet_provider: str | None = None
    daily_offline_limit_gbp: int = 0
    fingerprint_enrolled: bool = False
    requires_card_pin: bool = False
    notes: str | None = None


class CardCreate(CardBase):
    card_id: str = Field(min_length=1)
    allowed_readers: list[str] = Field(default_factory=list)


class CardUpdate(BaseModel):
    holder: str | None = None
    role: str | None = None
    status: str | None = None
    wallet_linked: bool | None = None
    wallet_provider: str | None = None
    daily_offline_limit_gbp: int | None = None
    fingerprint_enrolled: bool | None = None
    requires_card_pin: bool | None = None
    notes: str | None = None
    allowed_readers: list[str] | None = None


class Card(CardBase):
    card_id: str
    allowed_readers: list[str] = Field(default_factory=list)


class ReaderBase(BaseModel):
    name: str = Field(min_length=1)
    location: str | None = None
    action_type: str = "unlock"
    status: str = "active"


class ReaderCreate(ReaderBase):
    reader_id: str = Field(min_length=1)


class ReaderUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    action_type: str | None = None
    status: str | None = None


class Reader(ReaderBase):
    reader_id: str


class ScanRequest(BaseModel):
    card_id: str = Field(min_length=1)
    reader_id: str = Field(min_length=1)


class ScanResponse(BaseModel):
    allowed: bool
    action: str
    result: str
    reason: str
    card_id: str
    reader_id: str


class Event(BaseModel):
    id: int
    ts: str
    card_id: str
    reader_id: str
    holder: str | None
    role: str | None
    action: str
    result: str
    reason: str
