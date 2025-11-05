# Safasr Services Discord Bot

This is a custom Discord bot built for a client who was running a freelance Discord server. Its features include a ticket system, support system, custom service orders, and verification.

### Note on Configuration

This bot was hard-coded for a specific server and is intended as a portfolio piece. The channel IDs, role IDs, and other configurations are specific to that server's setup and are left in the code for reference. Please modify config.py with IDs in your own server prior to running, otherwise it will not work.

## 🚀 Setup and Running

This project uses [Poetry](https://python-poetry.org/) for dependency management.

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/TimothyBritcliffe/Safasr-Discord-Bot
    cd Safasr-Services-Discord-Bot
    ```

2.  **Create your environment file:**
    * Create a file named `.env` in the main folder.
    * Add your bot token to it:
        ```
        TOKEN=YOUR_BOT_TOKEN_GOES_HERE
        ```

3.  **Install dependencies:**
    ```sh
    poetry install
    ```

4.  **Run the bot:**
    ```sh
    poetry run python main.py
    ```
