import reflex as rx

config = rx.Config(
    app_name="hello",
    timeout=1800,
    redis_lock_expiration=60000,
)
