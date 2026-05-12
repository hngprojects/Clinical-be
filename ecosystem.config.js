module.exports = {
  apps: [{
    name: "staging",
    script: process.env.HOME + "/.local/bin/uv",
    args: "run uvicorn app.main:app --host 0.0.0.0 --port 8000",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "staging"
    }
  },
  {
    name: "production",
    script: process.env.HOME + "/.local/bin/uv",
    args: "run uvicorn app.main:app --host 0.0.0.0 --port 8001",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "production"
    }
  },
  {
    name: "celery-worker",
    script: process.env.HOME + "/.local/bin/uv",
    args: "run celery -A app.core.celery_app.celery_app worker -E --queues=default,email,pipeline --loglevel=info",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "staging"
    }
  },
  {
    name: "flower",
    script: process.env.HOME + "/.local/bin/uv",
    args: "run celery -A app.core.celery_app.celery_app flower --port=5555",
    cwd: __dirname,
    interpreter: "none",
    env: {
      NODE_ENV: "staging"
    }
  }
  ]
}
