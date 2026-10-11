FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de
COPY --from=ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5 /uv /usr/local/bin/uv
COPY --from=docker:29.4.1-cli@sha256:17b5c235f40be7432a7c0914c154e9278aed63bad4afe5607e4f91840696a9f8 /usr/local/bin/docker /usr/local/bin/docker
WORKDIR /opt/fyp-phase8-linux-v1
COPY linux-source.tar.gz /tmp/linux-source.tar.gz
RUN tar -xzf /tmp/linux-source.tar.gz -C . && rm /tmp/linux-source.tar.gz
RUN uv sync --locked --no-install-project
RUN uv venv .venv-analysis && uv pip install --python .venv-analysis/bin/python -r research/study/requirements.txt
ENV PATH="/opt/fyp-phase8-linux-v1/.venv/bin:$PATH" PYTHONPATH="/opt/fyp-phase8-linux-v1" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
# Local boot validation mounts only the local daemon socket; no credentials enter this image.
CMD ["python", "artifacts/phase-8-linux-setup/v1/runner.py", "--help"]
