from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.admin.routes import router as admin_router
from src.auth.routes import router as auth_router
from src.categories.routes import router as categories_router
from src.providers.routes import router as providers_router
from src.requests.routes import router as requests_router
from src.reviews.routes import router as reviews_router

app = FastAPI(
    title="Local Service Marketplace API",
    description=(
        "A local service marketplace API for discovering providers, managing "
        "service requests, provider availability, reviews, and administration."
    ),
    contact={
        "name": "Developer",
        "url": "https://www.github.com/allhailbotgod",
        "email": "jayrad005@gmail.com",
    },
)

# Allow the deployed GitHub Pages frontend and local development servers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://allhailbotgod.github.io",
        "https://allhailbotgod.github.io/infofit-hackathon/",
    ],
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
