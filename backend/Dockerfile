FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
# Seed pharmacy, at /seed so app.config.REPO_ROOT (/) finds it.
COPY --from=seed . /seed
# Saved AI recordings (photo reading and chat), at /eval/replay, so replay mode works in the container.
COPY --from=replay . /eval/replay
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
