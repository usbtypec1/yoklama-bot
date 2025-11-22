# Yoklama bot

# Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/usbtypec1/yoklama-bot
   ```

2. Navigate to the project directory:
   ```bash
    cd yoklama-bot
    ```

3. Install the required dependencies:
    ```bash
   uv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   uv sync
    ```

4. Create `settings.toml` file in the project root directory and configure it according to your needs. You can refer to
   `settings.example.toml` for guidance.
5. Run the bot:
   ```bash
   python src/main.py
   ```