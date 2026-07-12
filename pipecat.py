import os
import subprocess
import sys

# 1. Define the relative path to the bot.py file
bot_path = os.path.join("pipecat-project", "quickstart", "server", "bot.py")

# 2. Run the bot script using the current virtual environment's Python executable
# 'cwd' ensures that bot.py runs inside its own directory and can find its local .env file
process = subprocess.Popen(
    [sys.executable, "bot.py"],
    cwd=os.path.dirname(bot_path)
)

print(f"Started bot.py with PID {process.pid}")


