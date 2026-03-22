FROM python:3.12-slim

WORKDIR /backend

RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=$GITHUB_TOKEN

RUN pip install --no-cache-dir --root-user-action ignore git+https://${GITHUB_TOKEN}@github.com/astralien3000/mybackend.git@master#egg=mybackend

EXPOSE 80

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "80"]
