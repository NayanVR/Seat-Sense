from app.config import settings

DEFAULT_RADIUS = settings.radius

def verify_inside_radius(
    user_latitude: float,
    user_longitude: float,
    loc_latitude: float,
    loc_longitude: float,
    radius: float = DEFAULT_RADIUS,
) -> bool:
    distance = ((user_latitude - loc_latitude) ** 2 + (user_longitude - loc_longitude) ** 2) ** 0.5
    return distance <= radius

def verify_inside_audi_within_radius(
    user_latitude: float,
    user_longitude: float,
    radius: float = DEFAULT_RADIUS,
) -> bool:
    return verify_inside_radius(user_latitude, user_longitude, settings.audi_latitude, settings.audi_longitude, radius)