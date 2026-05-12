module.exports = {
  apps: [{
    name: "staging",
    script: "uv",
    args: "run uvicorn app.main:app --host 0.0.0.0 --port 8004",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "staging"
    }
  },
  {
    name: "production",
    script: "uv",
    args: "run uvicorn app.main:app --host 0.0.0.0 --port 8001",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "production"
    }
  },
  {
    name: "celery-worker",
    script: "uv",
    args: "run celery -A app.core.celery_app.celery_app worker -E --queues=default,email,pipeline --loglevel=info",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "staging"
    }
  },
  {
    name: "flower",
    script: "uv",
    args: "run celery -A app.core.celery_app.celery_app flower --port=5555",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "staging"
    }
  }
  ]
}
