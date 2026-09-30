from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.admin.routes import router as admin_router
from src.auth.routes import router as auth_router
from src.categories.routes import router as categories_router
from src.providers.routes import router as providers_router
from src.requests.routes import router as requests_router
from src.reviews.routes import router as reviews_router

app = FastAPI(title="Local Service Marketplace API")

# The plain frontend is served by a small local development server.  Keep the
# browser policy limited to local development origins rather than allowing all
# cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(providers_router)
app.include_router(requests_router)
app.include_router(reviews_router)
app.include_router(admin_router)
