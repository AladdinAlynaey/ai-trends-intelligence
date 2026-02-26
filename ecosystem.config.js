module.exports = {
    apps: [
        {
            name: "ai-trends",
            script: "/home/alaadin/Trends/venv/bin/python",
            args: "app.py",
            cwd: "/home/alaadin/Trends",
            interpreter: "none",
            autorestart: true,
            watch: true,
            watch_delay: 1000,
            ignore_watch: [
                "venv",
                "__pycache__",
                "data",
                ".git",
                "node_modules",
                "*.log",
                "*.pyc",
            ],
            max_restarts: 10,
            restart_delay: 5000,
            env: {
                FLASK_ENV: "production",
                FLASK_DEBUG: "0",
                FLASK_PORT: "5017",
            },
        },
    ],
};
