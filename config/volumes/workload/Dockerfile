FROM python:3.11-slim

WORKDIR /workload

# RUN python3 -m venv venv

# ENV PATH=/venv/bin:$PATH \
#     PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     VIRTUAL_ENV=/venv

# RUN pip install uv

# RUN --mount=source=dist,target=/dist uv pip install --no-cache /dist/*.whl

# CMD [ "workload" ]
# # without venv, need this:
# # RUN --mount=source=dist,target=/dist uv pip install --system --no-cache /dist/*.whl


# # To build:
# # rye build --wheel --clean && ╡docker build . --tag antithesis_workload_test

COPY . /workload
RUN pip install .
CMD [ "workload" ]
