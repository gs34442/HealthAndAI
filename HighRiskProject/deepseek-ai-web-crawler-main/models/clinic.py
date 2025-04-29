from pydantic import BaseModel, Field


class Clinic(BaseModel):
    """
    Represents the data structure of a Clinic.
    """

    locationName: str
    operated: str
    address_street: str = Field(alias="address-street")
    address_city: str = Field(alias="address-city")
    tel: str
    distance: str
    website: str
    directions: str

    class Config:
        # allow_population_by_field_name = True  # Allow using field names instead of aliases
        populate_by_name = True  # Allow using field names instead of aliases