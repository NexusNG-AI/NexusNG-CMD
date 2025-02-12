import os
import sys
import time
import json
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Initialisiere Rich console
console = Console()

# DeepSeek API Konfiguration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Verzeichnis für Chat-Speicherung
CHATS_DIR = os.path.join(os.path.expanduser("~"), ".nexusng_chats")

def generate_response(prompt):
    if not DEEPSEEK_API_KEY:
        console.print("[bold red]Error: DEEPSEEK_API_KEY is not set. Please check your .env file.[/bold red]")
        return "Error: API key not set"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=data, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        response_data = response.json()
        
        console.print(f"[bold blue]Debug: API Response[/bold blue]")
        console.print(response_data)
        
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"]
        else:
            console.print("[bold yellow]Warning: Unexpected API response format[/bold yellow]")
            return "Sorry, I couldn't generate a response. Please try again."
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error: An error occurred while calling the API: {e}[/bold red]")
        return f"Error: {str(e)}"

def animate_text(text):
    for char in text:
        console.print(char, end="")
        console.file.flush()
        time.sleep(0.02)
    console.print()

def save_chat(chat_name, messages):
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)
    with open(os.path.join(CHATS_DIR, f"{chat_name}.json"), "w") as f:
        json.dump(messages, f)

def load_chat(chat_name):
    try:
        with open(os.path.join(CHATS_DIR, f"{chat_name}.json"), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def list_chats():
    if not os.path.exists(CHATS_DIR):
        return []
    return [f.split('.')[0] for f in os.listdir(CHATS_DIR) if f.endswith('.json')]

def display_chat_history(messages):
    table = Table(show_header=False, expand=True)
    for msg in messages:
        if msg['role'] == 'user':
            table.add_row(Panel(msg['content'], style="bold yellow", title="You"))
        else:
            table.add_row(Panel(Markdown(msg['content']), style="cyan", title="NexusNG-CMD"))
    console.print(table)

def main():
    console.print(Panel.fit("[bold cyan]Welcome to NexusNG-CMD[/bold cyan]", border_style="bold green"))
    animate_text("Initializing AI system...")
    
    current_chat = "default"
    messages = load_chat(current_chat)

    while True:
        console.print(f"\n[bold magenta]Current Chat:[/bold magenta] {current_chat}")
        choice = Prompt.ask("Choose an action", choices=["chat", "new", "switch", "list", "exit"])
        
        if choice == "exit":
            animate_text("Thank you for using NexusNG-CMD. Goodbye!")
            sys.exit(0)
        elif choice == "new":
            new_chat = Prompt.ask("Enter new chat name")
            current_chat = new_chat
            messages = []
        elif choice == "switch":
            chats = list_chats()
            if not chats:
                console.print("[yellow]No existing chats found.[/yellow]")
                continue
            for i, chat in enumerate(chats, 1):
                console.print(f"{i}. {chat}")
            chat_choice = Prompt.ask("Choose a chat number", choices=[str(i) for i in range(1, len(chats)+1)])
            current_chat = chats[int(chat_choice)-1]
            messages = load_chat(current_chat)
        elif choice == "list":
            chats = list_chats()
            if not chats:
                console.print("[yellow]No existing chats found.[/yellow]")
            else:
                for chat in chats:
                    console.print(f"- {chat}")
            continue
        
        if choice == "chat":
            display_chat_history(messages)
            user_input = Prompt.ask("[bold yellow]You")
            
            with Live(console=console, refresh_per_second=4) as live:
                response = ""
                for _ in range(3):
                    response += "." 
                    live.update(Panel(f"[bold cyan]NexusNG-CMD is thinking{response}[/bold cyan]"))
                    time.sleep(0.5)
                
                ai_response = generate_response(user_input)
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": ai_response})
                
                live.update(Panel(Markdown(ai_response), title="[bold green]NexusNG-CMD Response[/bold green]", border_style="cyan"))
            
            save_chat(current_chat, messages)

if __name__ == "__main__":
    main()

